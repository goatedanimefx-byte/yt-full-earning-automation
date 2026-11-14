#!/usr/bin/env python3
"""
media.py - ffmpeg/ffprobe helpers. Real durations only, never nominal values.
"""

import json
import subprocess
import sys
from pathlib import Path

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


def run(cmd, quiet=True):
    """Run a command, return (ok, stdout+stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return False, "%s not found on PATH" % cmd[0]
    out = (r.stdout or "") + (r.stderr or "")
    if not quiet and out:
        print(out[-2000:])
    return r.returncode == 0, out


def probe_duration(path) -> float:
    """Exact media duration in seconds, 0.0 when unknown."""
    ok, out = run([
        FFPROBE, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ])
    if not ok:
        return 0.0
    try:
        return round(float(out.strip().splitlines()[0]), 3)
    except Exception:
        return 0.0


def probe_streams(path) -> dict:
    ok, out = run([
        FFPROBE, "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ])
    if not ok:
        return {}
    try:
        return json.loads(out)
    except Exception:
        return {}


def has_stream(path, kind="audio") -> bool:
    info = probe_streams(path)
    return any(s.get("codec_type") == kind for s in info.get("streams", []))


def video_encoder_args(crf=23, preset="veryfast") -> list:
    return ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


# ---------------------------------------------------------------- building

def concat_video(parts, out_path, crf=23, preset="veryfast"):
    """Concat video parts by re-encoding so every join is frame-exact."""
    parts = [str(p) for p in parts if Path(p).exists()]
    if not parts:
        raise RuntimeError("concat_video: no input parts exist")
    if len(parts) == 1:
        ok, out = run([FFMPEG, "-y", "-i", parts[0], "-c", "copy", str(out_path)])
        if not ok:
            raise RuntimeError("copy failed: " + out[-800:])
        return out_path

    args = [FFMPEG, "-y"]
    for p in parts:
        args += ["-i", p]
    # normalise every input to the same format, then concat
    chains = []
    for i in range(len(parts)):
        chains.append(
            "[%d:v]scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1,fps=30,format=yuv420p[v%d]" % (i, i)
        )
    concat_in = "".join("[v%d]" % i for i in range(len(parts)))
    fc = ";".join(chains) + ";%sconcat=n=%d:v=1:a=0[vout]" % (concat_in, len(parts))
    args += ["-filter_complex", fc, "-map", "[vout]"]
    args += video_encoder_args(crf, preset) + [str(out_path)]
    ok, out = run(args)
    if not ok:
        raise RuntimeError("concat_video failed: " + out[-1500:])
    return out_path


def concat_audio(parts, out_path):
    """Sample-accurate audio concat via the concat filter."""
    parts = [str(p) for p in parts if Path(p).exists()]
    if not parts:
        raise RuntimeError("concat_audio: no input parts exist")
    args = [FFMPEG, "-y"]
    for p in parts:
        args += ["-i", p]
    concat_in = "".join("[%d:a]" % i for i in range(len(parts)))
    fc = "%sconcat=n=%d:v=0:a=1[aout]" % (concat_in, len(parts))
    args += ["-filter_complex", fc, "-map", "[aout]",
             "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(out_path)]
    ok, out = run(args)
    if not ok:
        raise RuntimeError("concat_audio failed: " + out[-1500:])
    return out_path


def concat_av(parts, out_path, crf=23, preset="veryfast"):
    """Concat video+audio parts in one pass, frame- and sample-accurate."""
    parts = [str(p) for p in parts if Path(p).exists()]
    if not parts:
        raise RuntimeError("concat_av: no input parts exist")
    args = [FFMPEG, "-y"]
    for p in parts:
        args += ["-i", p]
    chains = []
    for i in range(len(parts)):
        chains.append(
            "[%d:v]scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1,fps=30,format=yuv420p[v%d]" % (i, i)
        )
        chains.append("[%d:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a%d]" % (i, i))
    # the concat filter wants stream pairs interleaved: [v0][a0][v1][a1]...
    pairs = "".join("[v%d][a%d]" % (i, i) for i in range(len(parts)))
    fc = ";".join(chains) + ";%sconcat=n=%d:v=1:a=1[vout][aout]" % (pairs, len(parts))
    args += ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]"]
    args += video_encoder_args(crf, preset)
    args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out_path)]
    ok, out = run(args)
    if not ok:
        raise RuntimeError("concat_av failed: " + out[-1500:])
    return out_path


def loudnorm(src, dst, target_i=-14.0, target_tp=-1.5, target_lra=11.0):
    """Two-pass loudness normalisation to the target LUFS."""
    ok, out = run([
        FFMPEG, "-y", "-i", str(src), "-af",
        "loudnorm=I=%s:TP=%s:LRA=%s:print_format=json" % (target_i, target_tp, target_lra),
        "-f", "null", "-",
    ])
    measured = {}
    if ok:
        start = out.rfind("{")
        end = out.rfind("}")
        if start != -1 and end > start:
            try:
                measured = json.loads(out[start:end + 1])
            except Exception:
                measured = {}

    if measured.get("input_i") not in (None, "-inf"):
        af = ("loudnorm=I=%s:TP=%s:LRA=%s:measured_I=%s:measured_TP=%s:"
              "measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true" % (
                  target_i, target_tp, target_lra,
                  measured.get("input_i"), measured.get("input_tp"),
                  measured.get("input_lra"), measured.get("input_thresh"),
                  measured.get("target_offset", 0.0)))
    else:
        af = "loudnorm=I=%s:TP=%s:LRA=%s" % (target_i, target_tp, target_lra)

    ok, out = run([FFMPEG, "-y", "-i", str(src), "-af", af,
                   "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(dst)])
    if not ok:
        raise RuntimeError("loudnorm failed: " + out[-1200:])
    return dst


def mux(video, audio, out_path, crf=23, preset="veryfast", bgm=None, bgm_gain=0.12):
    """Mux video + voice (+ optional ducked BGM). No -shortest truncation."""
    args = [FFMPEG, "-y", "-i", str(video), "-i", str(audio)]
    if bgm and Path(bgm).exists():
        args += ["-stream_loop", "-1", "-i", str(bgm)]
        fc = ("[2:a]volume=%s,aloop=loop=-1:size=2e9[bg];"
              "[1:a][bg]amix=inputs=2:duration=first:dropout_transition=2,"
              "alimiter=limit=0.95[aout]" % bgm_gain)
        args += ["-filter_complex", fc, "-map", "0:v", "-map", "[aout]"]
    else:
        args += ["-map", "0:v", "-map", "1:a"]

    args += video_encoder_args(crf, preset)
    args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out_path)]
    ok, out = run(args)
    if not ok:
        raise RuntimeError("mux failed: " + out[-1500:])
    return out_path


def run_bytes(cmd):
    """Run a command and return raw stdout bytes (for rawvideo pipes)."""
    try:
        r = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        return False, b""
    return r.returncode == 0, r.stdout or b""


# ---------------------------------------------------------------- frame checks
#
# freezedetect/blackdetect report an event count, not a duration, and they
# misfire on noisy footage. These decode a small grey proxy and measure it.

def sample_gray(path, fps=2, width=64, height=36):
    ok, raw = run_bytes([
        FFMPEG, "-v", "error", "-an", "-i", str(path), "-vf",
        "fps=%d,format=gray,scale=%d:%d" % (fps, width, height),
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ])
    if not ok:
        return []
    frame = width * height
    return [raw[i:i + frame] for i in range(0, len(raw) - frame + 1, frame)]


def _mad(a, b):
    n = min(len(a), len(b))
    if not n:
        return 0.0
    return sum(abs(a[i] - b[i]) for i in range(n)) / float(n)


def _contrast(f):
    n = len(f) or 1
    mean = sum(f) / float(n)
    return (sum((b - mean) ** 2 for b in f) / float(n)) ** 0.5


def motion_score(path, fps=2):
    """(ok, motion, contrast). motion = max mean-abs-diff between frames."""
    frames = sample_gray(path, fps=fps)
    if len(frames) < 2:
        return False, 0.0, 0.0
    motion = max(_mad(frames[i], frames[i + 1]) for i in range(len(frames) - 1))
    contrast = max(_contrast(f) for f in frames[:8])
    ok = motion >= 3.0 and contrast >= 6.0
    return ok, round(motion, 2), round(contrast, 2)


def freeze_ratio(path, fps=2, threshold=1.5):
    """Fraction of sampled frame pairs that are effectively identical."""
    frames = sample_gray(path, fps=fps)
    if len(frames) < 2:
        return 1.0
    frozen = sum(1 for i in range(len(frames) - 1)
                 if _mad(frames[i], frames[i + 1]) < threshold)
    return round(frozen / float(len(frames) - 1), 4)


def black_ratio(path, fps=1, mean_max=10.0, contrast_max=8.0):
    """Fraction of sampled frames that are essentially a black frame."""
    frames = sample_gray(path, fps=fps)
    if not frames:
        return 0.0
    dark = 0
    for f in frames:
        n = len(f) or 1
        mean = sum(f) / float(n)
        if mean < mean_max and _contrast(f) < contrast_max:
            dark += 1
    return round(dark / float(len(frames)), 4)


# kept so older callers keep working
def blackframe_ratio(path, threshold=0.02, sample_fps=1):
    return black_ratio(path, fps=sample_fps)


def die(msg, code=1):
    print("FATAL: %s" % msg, file=sys.stderr)
    raise SystemExit(code)

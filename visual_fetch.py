#!/usr/bin/env python3
"""
visual_fetch.py - real motion first, Pexels only as fallback, flat colour = hard failure.

Order for every shot:
  1. procedural animation rendered with ffmpeg (gradients / mandelbrot / life / cellauto)
  2. Pexels stock footage (only if a key exists and generation genuinely failed)
  3. FAIL THE RUN. A solid colour frame is never written as a "visual".

Every generated file is verified with a real motion check: frames are sampled,
decoded to raw grey, and compared. If the picture does not change, the shot is
rejected and the next generator is tried.
"""

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import media
import paths

try:
    import requests
except ImportError:  # requests is optional; only Pexels needs it
    requests = None

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# ---------------------------------------------------------------- look

PALETTES = {
    "history": ["0x120c06", "0x6b4b2a", "0x2b1d10", "0x8a6a3f"],
    "tech":    ["0x0a1220", "0x1d4ed8", "0x0f766e", "0x312e81"],
    "science": ["0x061018", "0x0e7490", "0x4c1d95", "0x134e4a"],
    "general": ["0x0b1220", "0x334155", "0x0f766e", "0x1e293b"],
}

HUE_SHIFT = {"history": 18, "tech": 200, "science": 168, "general": 120}

# segment type -> preferred look
STYLE_FOR_TYPE = {
    "intro": "fractal",
    "context": "archive",
    "main": "plasma",
    "conclusion": "archive",
    "cta": "particles",
}

GEN_ORDER = {
    "plasma":    ["plasma", "fractal", "tunnel", "particles", "motion"],
    "fractal":   ["fractal", "plasma", "tunnel", "particles", "motion"],
    "particles": ["particles", "tunnel", "plasma", "fractal", "motion"],
    "archive":   ["archive", "plasma", "fractal", "particles", "motion"],
    "tunnel":    ["tunnel", "particles", "plasma", "fractal", "motion"],
}

# ---------------------------------------------------------------- capability

_FILTERS = None


def filter_list():
    global _FILTERS
    if _FILTERS is None:
        ok, out = media.run(["ffmpeg", "-hide_banner", "-filters"])
        names = set()
        if ok:
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 2 and len(parts[0]) == 3:
                    names.add(parts[1])
        _FILTERS = names
    return _FILTERS


def can_animate() -> bool:
    """True when ffmpeg exists.

    Filter-name probing was a false negative on newer runner images, and it hid
    the real ffmpeg errors. Every generator now reports its own failure instead,
    and GEN_ORDER ends with a fallback that only needs ancient filters.
    """
    ok, _ = media.run(["ffmpeg", "-version"])
    return ok


def ffmpeg_info() -> str:
    """One-line ffmpeg build string for the run log."""
    ok, out = media.run(["ffmpeg", "-version"])
    if not ok:
        return "ffmpeg: NOT AVAILABLE"
    return (out.splitlines() or ["ffmpeg: unknown"])[0].strip()


# ---------------------------------------------------------------- verification

def sample_frames(path, width=64, height=36, fps=2):
    """Decode the clip to tiny raw grey frames for a motion check."""
    return media.sample_gray(path, fps=fps, width=width, height=height)


def motion_score(path):
    """(ok, motion, contrast) measured on real decoded frames."""
    return media.motion_score(path)


def is_flat(path) -> bool:
    ok, motion, contrast = motion_score(path)
    return not ok


# ---------------------------------------------------------------- generators

def _encode(src, vf, out, dur, size, crf=23):
    w, h = size.split("x")
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", src]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-t", str(dur), "-r", "30", "-s", size]
    cmd += media.video_encoder_args(crf, "veryfast")
    cmd += [str(out)]
    ok, log = media.run(cmd)
    return ok, log


def gen_plasma(style, out, dur, size, seed, category):
    w, h = [int(x) for x in size.split("x")]
    big = "%dx%d" % (int(w * 1.25) // 2 * 2, int(h * 1.25) // 2 * 2)
    c = PALETTES.get(category, PALETTES["general"])
    src = ("gradients=s=%s:r=30:c0=%s:c1=%s:c2=%s:c3=%s:n=4:type=spiral:"
           "speed=0.008:seed=%d" % (big, c[0], c[1], c[2], c[3], seed))
    vf = ("crop=%d:%d:x='(in_w-out_w)/2+70*sin(t/6)':y='(in_h-out_h)/2+45*cos(t/8)',"
          "scale=%s,hue=h='12*sin(t/9)+%d':s=1.08,vignette=PI/5,"
          "noise=alls=7:allf=t+u,eq=contrast=1.08:saturation=1.12" % (w, h, size, HUE_SHIFT.get(category, 120)))
    return _encode(src, vf, out, dur, size)


def gen_fractal(style, out, dur, size, seed, category):
    frames = max(30, int(dur * 30))
    src = ("mandelbrot=s=%s:r=30:maxiter=600:start_scale=2.6:end_scale=0.06:"
           "end_pts=%d:start_x=-0.743644:start_y=-0.131826" % (size, frames))
    vf = ("hue=h='18*t+%d':s=1.25,eq=contrast=1.15:brightness=-0.02,"
          "vignette=PI/4,noise=alls=5:allf=t+u" % HUE_SHIFT.get(category, 120))
    return _encode(src, vf, out, dur, size)


def gen_particles(style, out, dur, size, seed, category):
    src = ("life=s=480x270:r=30:mold=10:ratio=0.12:death_color=#080b12:"
           "life_color=#7dd3fc:stitch=0")
    vf = ("scale=%s:flags=neighbor,gblur=sigma=1.2,hue=h='30*sin(t/7)+%d',"
          "noise=alls=4:allf=t+u,vignette=PI/5,eq=contrast=1.1" % (size, HUE_SHIFT.get(category, 120)))
    return _encode(src, vf, out, dur, size)


def gen_tunnel(style, out, dur, size, seed, category):
    src = "cellauto=s=480x270:r=30:rule=110:scroll=1:pattern=random:random_fill_ratio=0.4"
    vf = ("scale=%s:flags=bicubic,gblur=sigma=2.4,hue=h='40*sin(t/5)+%d':s=1.3,"
          "noise=alls=6:allf=t+u,vignette=PI/4.5" % (size, HUE_SHIFT.get(category, 120)))
    return _encode(src, vf, out, dur, size)


def gen_archive(style, out, dur, size, seed, category):
    w, h = [int(x) for x in size.split("x")]
    big = "%dx%d" % (int(w * 1.25) // 2 * 2, int(h * 1.25) // 2 * 2)
    src = ("gradients=s=%s:r=30:c0=0x120c06:c1=0x6b4b2a:c2=0x2b1d10:n=3:"
           "type=radial:speed=0.006:seed=%d" % (big, seed))
    vf = ("crop=%d:%d:x='(in_w-out_w)/2+50*sin(t/9)':y='(in_h-out_h)/2+30*cos(t/11)',"
          "scale=%s,eq=saturation=0.55:contrast=1.14,"
          "vignette=PI/3.5,noise=alls=14:allf=t+u" % (w, h, size))
    return _encode(src, vf, out, dur, size)


def gen_motion(style, out, dur, size, seed, category):
    """Last resort: only uses filters that have shipped for a decade."""
    w, h = [int(x) for x in size.split("x")]
    big = "%dx%d" % (int(w * 1.2) // 2 * 2, int(h * 1.2) // 2 * 2)
    src = "testsrc2=s=%s:r=30" % big
    vf = ("crop=%d:%d:x='(in_w-out_w)/2+60*sin(t/7)':y='(in_h-out_h)/2+40*cos(t/9)',"
          "scale=%s,gblur=sigma=6,eq=contrast=1.2:saturation=0.85:brightness=-0.06,"
          "vignette=PI/4" % (w, h, size))
    return _encode(src, vf, out, dur, size)


GENERATORS = {
    "plasma": gen_plasma,
    "fractal": gen_fractal,
    "particles": gen_particles,
    "tunnel": gen_tunnel,
    "archive": gen_archive,
    "motion": gen_motion,
}


# ---------------------------------------------------------------- pexels

def pexels_search(query, per_page=5):
    if not PEXELS_API_KEY or requests is None:
        return []
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            timeout=20,
        )
        if r.status_code == 200:
            return r.json().get("videos", [])
        print("pexels: HTTP %s" % r.status_code)
    except Exception as exc:
        print("pexels search failed: %s" % exc)
    return []


def pexels_download(video, out_dir):
    best = max(video.get("video_files", []), key=lambda x: x.get("height", 0) or 0)
    url = best.get("link")
    if not url:
        return None
    dest = Path(out_dir) / ("pexels_%s.mp4" % video.get("id"))
    if dest.exists() and dest.stat().st_size > 1024:
        return dest
    try:
        with requests.get(url, stream=True, timeout=90) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return dest
    except Exception as exc:
        print("pexels download failed: %s" % exc)
        return None


def pexels_visual(query, out, dur, size, seed, category):
    """Stock footage + Ken Burns. Verified like everything else."""
    for video in pexels_search(query):
        src = pexels_download(video, Path(out).parent)
        if not src:
            continue
        vf = ("scale=%s:force_original_aspect_ratio=increase,crop=%s,"
              "zoompan=z='min(zoom+0.0008,1.25)':d=1:x='iw/2-(iw/zoom/2)':"
              "y='ih/2-(ih/zoom/2)':s=%s:fps=30,setsar=1" % (size, size, size))
        ok, log = media.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-vf", vf,
            "-t", str(dur), "-r", "30",
        ] + media.video_encoder_args(23, "veryfast") + [str(out)])
        if ok and not is_flat(out):
            return {"source": "pexels", "credit": video.get("url", ""), "query": query}
        print("pexels clip rejected (flat or unreadable)")
    return None


# ---------------------------------------------------------------- per shot

def animate_shot(style, out, dur, size, seed, category, query="", allow_pexels=True):
    """Render one shot. Raises if nothing real can be produced."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = max(2.0, float(dur))
    style = style if style in GEN_ORDER else "plasma"
    attempts = []

    if can_animate():
        for name in GEN_ORDER[style]:
            fn = GENERATORS[name]
            try:
                ok, log = fn(style, out, dur, size, seed, category)
            except Exception as exc:
                attempts.append((name, "crash: %s" % exc))
                continue
            if not ok:
                attempts.append((name, "ffmpeg failed: %s" % (log or "")[-160:]))
                continue
            good, motion, contrast = motion_score(out)
            attempts.append((name, "motion=%.2f contrast=%.2f %s" % (motion, contrast, "OK" if good else "FLAT")))
            if good:
                return {"source": "generated", "generator": name,
                        "motion": motion, "contrast": contrast, "attempts": attempts}
    else:
        attempts.append(("ffmpeg", "ffmpeg is not available on this runner"))

    if allow_pexels:
        got = pexels_visual(query or style, out, dur, size, seed, category)
        if got:
            ok, motion, contrast = motion_score(out)
            if ok:
                got.update({"motion": motion, "contrast": contrast, "attempts": attempts})
                return got

    raise RuntimeError(
        "no real motion could be produced for %s (style=%s, %.1fs).\n"
        "attempts:\n  %s\n"
        "Refusing to write a flat colour frame." % (
            out.name, style, dur,
            "\n  ".join("%s: %s" % a for a in attempts) or "none")
    )


# ---------------------------------------------------------------- pipeline

def _shot_list(script):
    """Flatten the script into renderable shots."""
    shots = script.get("shots") or []
    if shots:
        out = []
        for i, s in enumerate(shots):
            out.append({
                "shot_index": i,
                "segment_index": s.get("segment_index", 0),
                "type": s.get("type", "main"),
                "duration_sec": float(s.get("duration_sec") or 6.0),
                "text": s.get("text", ""),
                "start": s.get("start"),
            })
        return out

    out = []
    i = 0
    for si, seg in enumerate(script.get("segments", [])):
        dur = float(seg.get("duration_sec") or 20)
        pieces = max(1, int(round(dur / 8.0)))
        each = dur / pieces
        for _ in range(pieces):
            out.append({
                "shot_index": i,
                "segment_index": si,
                "type": seg.get("type", "main"),
                "duration_sec": round(each, 3),
                "text": (seg.get("voiceover") or "")[:120],
                "start": None,
            })
            i += 1
    return out


def fetch_visuals_for_script(script, limit=None, allow_pexels=True, strict=True):
    topic = script.get("topic", "doc")
    category = script.get("category", "general")
    orientation = paths.orientation_of(script)
    size = script.get("size") or paths.size_for(orientation)

    vdir = paths.visual_dir(topic)
    shots = _shot_list(script)
    if limit:
        shots = shots[:limit]
    if not shots:
        raise RuntimeError("script has no shots to render")

    print("visuals: %d shot(s) at %s (%s)" % (len(shots), size, category))

    manifest = []
    failures = []
    for shot in shots:
        idx = shot["shot_index"]
        style = STYLE_FOR_TYPE.get(shot["type"], "plasma")
        out = vdir / ("shot_%03d.mp4" % idx)
        seed = 1000 + idx * 37
        query = " ".join((shot["text"] or shot["type"]).split()[:6])
        try:
            info = animate_shot(style, out, shot["duration_sec"], size, seed,
                                category, query=query, allow_pexels=allow_pexels)
            entry = {
                "shot_index": idx,
                "segment_index": shot["segment_index"],
                "type": shot["type"],
                "style": style,
                "category": category,
                "path": str(out),
                "duration_sec": shot["duration_sec"],
                "size": size,
                "query": query,
                "source": info["source"],
                "generator": info.get("generator"),
                "motion": info.get("motion"),
                "contrast": info.get("contrast"),
                "credit": info.get("credit", ""),
            }
            manifest.append(entry)
            print("  shot %03d  %-9s %-9s motion=%s" % (
                idx, info["source"], info.get("generator") or "-", info.get("motion")))
        except Exception as exc:
            failures.append({"shot_index": idx, "error": str(exc)})
            print("  shot %03d  FAILED: %s" % (idx, exc))

    paths.save_json(vdir / "visual_manifest.json", manifest)
    paths.save_json(vdir / "motion_report.json", {
        "topic": topic,
        "requested": len(shots),
        "rendered": len(manifest),
        "failed": failures,
        "flat_colour_written": False,
    })

    if failures and strict:
        raise RuntimeError(
            "%d of %d shots produced no real motion. Run aborted so a flat "
            "colour video is never published." % (len(failures), len(shots)))

    return manifest


def main(argv):
    if not argv:
        print("usage: visual_fetch.py <script.json|topic> [--limit N] [--preview] [--no-pexels] [--lenient]")
        return 2

    target = argv[0]
    limit = None
    allow_pexels = True
    strict = True
    for i, a in enumerate(argv):
        if a == "--limit" and i + 1 < len(argv):
            limit = int(argv[i + 1])
        if a == "--preview":
            limit = 3
        if a == "--no-pexels":
            allow_pexels = False
        if a == "--lenient":
            strict = False

    script = paths.resolve_script(target)
    got = fetch_visuals_for_script(script, limit=limit,
                                   allow_pexels=allow_pexels, strict=strict)
    print("visuals ready: %d shot(s)" % len(got))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

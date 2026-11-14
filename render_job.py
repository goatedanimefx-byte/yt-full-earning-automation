#!/usr/bin/env python3
"""
render_job.py - public render worker: render exactly one SILENT chunk.

The plan (jobs/<slug>.json) is the only thing this repo receives. It carries
shot types, durations, seeds and the chunk layout - no narration, no audio, no
private data. Audio is muxed later, in the private repo.

usage: render_job.py jobs/<slug>.json <chunk_index>
"""

import json
import sys
from pathlib import Path

import media
import paths
import visual_fetch


def load_plan(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_chunk(plan, index, crf=23):
    index = int(index)
    slug = plan["slug"]
    size = plan.get("size") or "1920x1080"
    category = plan.get("category", "general")

    chunk = next((c for c in plan["chunks"] if int(c["index"]) == index), None)
    if chunk is None:
        raise RuntimeError("chunk %s not in plan (indices %s)" % (index, plan.get("indices")))

    cdir = paths.chunk_dir(slug)
    work = cdir / ("work_%02d" % index)
    work.mkdir(parents=True, exist_ok=True)

    print("chunk %02d: %d shot(s), %.3fs, %s" % (
        index, len(chunk["shots"]), float(chunk["duration_sec"]), size))
    print("  %s" % visual_fetch.ffmpeg_info())

    parts = []
    for shot in chunk["shots"]:
        style = visual_fetch.STYLE_FOR_TYPE.get(shot.get("type"), "plasma")
        out = work / ("shot_%03d.mp4" % int(shot["shot_index"]))
        info = visual_fetch.animate_shot(
            style, out, float(shot["duration_sec"]), size, shot.get("seed", 1000),
            category,
            query=" ".join((shot.get("text") or shot.get("type") or "").split()[:6]),
            allow_pexels=bool(visual_fetch.PEXELS_API_KEY),
        )
        exact = work / ("exact_%03d.mp4" % int(shot["shot_index"]))
        ok, log = media.run([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(out),
            "-t", "%.3f" % float(shot["duration_sec"]), "-r", "30", "-s", size,
        ] + media.video_encoder_args(crf, "veryfast") + [str(exact)])
        if not ok:
            raise RuntimeError("trim failed for shot %s: %s" % (shot["shot_index"], log[-500:]))
        parts.append(exact)
        print("  shot %03d %-9s %-9s motion=%s" % (
            int(shot["shot_index"]), info["source"], info.get("generator") or "-",
            info.get("motion")))

    silent = work / "video.mp4"
    media.concat_video(parts, silent, crf=crf)

    # one final pass: guarantee the chunk is exactly the planned length
    target = float(chunk["duration_sec"])
    out = cdir / ("chunk-%02d.mp4" % index)
    ok, log = media.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(silent),
        "-t", "%.3f" % target, "-r", "30", "-s", size,
    ] + media.video_encoder_args(crf, "veryfast") + [str(out)])
    if not ok:
        raise RuntimeError("final trim failed: %s" % log[-500:])

    dur = media.probe_duration(out)
    flat = media.blackframe_ratio(out)
    freeze = media.freeze_ratio(out)
    print("chunk %02d done: %.2fs (planned %.2fs) black=%.0f%% freeze=%.0f%%"
          % (index, dur, target, flat * 100, freeze * 100))

    if abs(dur - target) > 0.5:
        raise RuntimeError("chunk %02d is %.2fs, planned %.2fs" % (index, dur, target))
    if flat > 0.5:
        raise RuntimeError("chunk %02d is more than 50%% black" % index)
    if freeze > 0.5:
        raise RuntimeError("chunk %02d is more than 50%% frozen" % index)

    paths.gha_output(chunk=out, duration=dur)
    return out


def main(argv):
    if len(argv) < 2:
        print("usage: render_job.py <plan.json> <chunk_index>")
        return 2
    plan = load_plan(argv[0])
    out = render_chunk(plan, argv[1])
    print("OK %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

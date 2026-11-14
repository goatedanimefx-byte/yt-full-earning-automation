#!/usr/bin/env python3
"""
render_job.py - public render worker: render exactly one SILENT chunk.

The plan (jobs/<slug>.json) is the only thing this repo receives: shot types,
durations, seeds, labels and the chunk layout. No narration, no audio, no
private data.

The chunk is authored as HTML + GSAP (hf_scenes.py / hf_build.py) and rendered
by HyperFrames, which drives headless Chrome and encodes the frames itself. No
ffmpeg procedural generators are used anywhere in this path.

usage: render_job.py jobs/<slug>.json <chunk_index>
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import hf_build
import media
import paths

HYPERFRAMES = os.getenv("HYPERFRAMES_BIN", "hyperframes")


def load_plan(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_chunk(plan, index, crf=None, quality=None, workers=None):
    index = int(index)
    slug = plan["slug"]
    fps = int(plan.get("fps") or hf_build.FPS)
    crf = int(crf or os.getenv("CRF") or 20)
    quality = quality or os.getenv("HF_QUALITY") or "draft"
    workers = str(workers or os.getenv("HF_WORKERS") or "auto")

    chunk = next((c for c in plan["chunks"] if int(c["index"]) == index), None)
    if chunk is None:
        raise RuntimeError("chunk %s not in plan (indices %s)" % (index, plan.get("indices")))
    n_shots = len(chunk.get("shots") or [])

    cdir = paths.chunk_dir(slug)
    comp, target = hf_build.build_chunk(plan, index, cdir)

    out = cdir / ("chunk-%02d.mp4" % index)
    if out.exists():
        out.unlink()

    cmd = [HYPERFRAMES, "render", str(comp),
           "-o", str(out),
           "-f", str(fps),
           "-q", quality,
           "--crf", str(crf),
           "-w", workers]
    env = dict(os.environ)
    env["HYPERFRAMES_RENDER_LOCK"] = "off"     # 20 jobs must not serialise
    env["HYPERFRAMES_NO_UPDATE_CHECK"] = "1"
    env.setdefault("HYPERFRAMES_EXTRACT_CACHE_DIR", "off")

    print("chunk %02d: %d shot(s), %.3fs -> %s" % (index, n_shots, target, out))
    print("  %s" % " ".join(cmd))
    t0 = time.time()
    proc = subprocess.run(cmd, env=env)
    took = time.time() - t0
    if proc.returncode != 0:
        raise RuntimeError("hyperframes exited %d after %.1fs" % (proc.returncode, took))
    if not out.exists() or out.stat().st_size < 10000:
        raise RuntimeError("hyperframes produced no usable output at %s" % out)

    dur = media.probe_duration(out)
    flat = media.blackframe_ratio(out)
    freeze = media.freeze_ratio(out)
    mb = out.stat().st_size / (1024.0 * 1024.0)
    print("chunk %02d done: %.2fs (planned %.2fs) black=%.0f%% freeze=%.0f%% %.1fMB in %.0fs"
          % (index, dur, target, flat * 100, freeze * 100, mb, took))

    if abs(dur - target) > 1.0:
        raise RuntimeError("chunk %02d is %.2fs, planned %.2fs" % (index, dur, target))
    if flat > 0.5:
        raise RuntimeError("chunk %02d is more than 50%% black" % index)
    if freeze > 0.98:
        raise RuntimeError("chunk %02d is more than 98%% frozen" % index)

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

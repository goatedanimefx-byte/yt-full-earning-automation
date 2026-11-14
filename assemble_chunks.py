#!/usr/bin/env python3
"""
assemble_chunks.py - join the rendered silent chunks into one silent draft.

usage: assemble_chunks.py <plan.json> <chunks_dir>

Chunks arrive from 20 matrix jobs in arbitrary order, so they are sorted by
index and verified against the plan before and after the join.
"""

import json
import sys
from pathlib import Path

import media
import paths


def load_plan(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_chunks(chunks_dir, indices):
    root = Path(chunks_dir)
    found = {}
    for p in root.rglob("chunk-*.mp4"):
        try:
            i = int(p.stem.split("-")[-1])
        except ValueError:
            continue
        found[i] = p
    missing = [i for i in indices if i not in found]
    if missing:
        raise RuntimeError("missing chunk(s) %s in %s" % (missing, root))
    return [found[i] for i in indices]


def assemble(plan, chunks_dir, crf=23):
    slug = plan["slug"]
    indices = [int(i) for i in plan["indices"]]
    parts = find_chunks(chunks_dir, indices)

    durs = [media.probe_duration(p) for p in parts]
    print("chunks: %d, %.2fs total" % (len(parts), sum(durs)))

    expected = float(plan["total_duration_sec"])
    if abs(sum(durs) - expected) > max(1.0, expected * 0.005):
        raise RuntimeError("chunk total %.2fs vs plan %.2fs" % (sum(durs), expected))

    out = paths.final_dir(slug) / "draft_silent.mp4"
    media.concat_video(parts, out, crf=crf)

    got = media.probe_duration(out)
    black = media.blackframe_ratio(out)
    freeze = media.freeze_ratio(out)
    print("draft_silent: %s" % out)
    print("duration: %.2fs (plan %.2fs, drift %.2fs)" % (got, expected, abs(got - expected)))
    print("black: %.0f%%  freeze: %.0f%%" % (black * 100, freeze * 100))

    if abs(got - expected) > max(1.0, expected * 0.005):
        raise RuntimeError("assembled duration drift %.2fs" % abs(got - expected))
    if black > 0.25:
        raise RuntimeError("draft is %.0f%% black" % (black * 100))
    if freeze > 0.35:
        raise RuntimeError("draft is %.0f%% frozen" % (freeze * 100))

    paths.gha_output(draft=out, duration=got)
    return out


def main(argv):
    if len(argv) < 2:
        print("usage: assemble_chunks.py <plan.json> <chunks_dir>")
        return 2
    plan = load_plan(argv[0])
    out = assemble(plan, argv[1])
    print("OK %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

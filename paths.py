#!/usr/bin/env python3
"""
paths.py - single source of truth for every path in the engine.

Canonical layout (no media ever committed):

  outputs/
    brief.json
    script_<slug>.json
    metrics.json
    <slug>/
      audio/manifest.json, seg_00.wav ...
      visuals/visual_manifest.json, shot_000.mp4 ...
      chunks.json
      chunks/chunk-00.mp4 ...
      final/draft.mp4
      clips/*.mp4
      thumbnail.jpg, subtitles.srt, seo.json, chapters.txt
  memory/
    playbook.json
    playbook_versions/
    state/revision_<slug>.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"
MEMORY = ROOT / "memory"
STATE = MEMORY / "state"


def slugify(topic: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (topic or "doc").lower()).strip("_")
    return s[:60] or "doc"


def work_dir(topic: str) -> Path:
    p = OUTPUTS / slugify(topic)
    p.mkdir(parents=True, exist_ok=True)
    return p


def audio_dir(topic: str) -> Path:
    p = work_dir(topic) / "audio"
    p.mkdir(parents=True, exist_ok=True)
    return p


def visual_dir(topic: str) -> Path:
    p = work_dir(topic) / "visuals"
    p.mkdir(parents=True, exist_ok=True)
    return p


def chunk_dir(topic: str) -> Path:
    p = work_dir(topic) / "chunks"
    p.mkdir(parents=True, exist_ok=True)
    return p


def final_dir(topic: str) -> Path:
    p = work_dir(topic) / "final"
    p.mkdir(parents=True, exist_ok=True)
    return p


def clip_dir(topic: str) -> Path:
    p = work_dir(topic) / "clips"
    p.mkdir(parents=True, exist_ok=True)
    return p


def script_path(topic: str) -> Path:
    return OUTPUTS / f"script_{slugify(topic)}.json"


def brief_path() -> Path:
    return OUTPUTS / "brief.json"


def chunks_path(topic: str) -> Path:
    return work_dir(topic) / "chunks.json"


def metrics_path() -> Path:
    return OUTPUTS / "metrics.json"


def playbook_path() -> Path:
    return MEMORY / "playbook.json"


def revision_path(topic: str) -> Path:
    STATE.mkdir(parents=True, exist_ok=True)
    return STATE / f"revision_{slugify(topic)}.json"


# ---------------------------------------------------------------- manifests

def find_audio_manifest(topic: str) -> Path:
    """Canonical first, then the legacy voice_gen layout."""
    for p in (audio_dir(topic) / "manifest.json",
              OUTPUTS / "audio" / slugify(topic) / "manifest.json"):
        if p.exists():
            return p
    raise FileNotFoundError(
        "audio manifest not found for %r (looked in %s)" % (topic, audio_dir(topic))
    )


def find_visual_manifest(topic: str) -> Path:
    for p in (visual_dir(topic) / "visual_manifest.json",
              OUTPUTS / "visuals" / slugify(topic) / "visual_manifest.json"):
        if p.exists():
            return p
    raise FileNotFoundError(
        "visual manifest not found for %r (looked in %s)" % (topic, visual_dir(topic))
    )


# ---------------------------------------------------------------- json io

def load_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print("WARN could not read %s: %s" % (p, exc))
        return default


def save_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("wrote %s" % p)
    return p


def load_script(topic: str) -> dict:
    p = script_path(topic)
    if not p.exists():
        raise FileNotFoundError("script not found: %s" % p)
    return load_json(p)


def resolve_script(arg: str) -> dict:
    """Accept either a script json path or a raw topic string."""
    p = Path(arg)
    if p.suffix == ".json" and p.exists():
        return load_json(p)
    if script_path(arg).exists():
        return load_script(arg)
    raise FileNotFoundError("no script for %r (pass a .json path or a topic)" % arg)


def size_for(orientation: str) -> str:
    return "1080x1920" if str(orientation).lower() in ("vertical", "9:16", "portrait") else "1920x1080"


def orientation_of(script: dict) -> str:
    return script.get("orientation") or "horizontal"


def gha_output(**kv):
    """Write step outputs for GitHub Actions (replaces the deprecated set-output)."""
    import os
    p = os.getenv("GITHUB_OUTPUT")
    if not p:
        return
    with open(p, "a", encoding="utf-8") as f:
        for k, v in kv.items():
            f.write("%s=%s\n" % (k, v))


def gha_summary(markdown: str):
    """Append a markdown block to the workflow run summary."""
    import os
    p = os.getenv("GITHUB_STEP_SUMMARY")
    if not p:
        return
    with open(p, "a", encoding="utf-8") as f:
        f.write(markdown.rstrip() + "\n")

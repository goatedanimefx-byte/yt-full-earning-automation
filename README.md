# yt-full-earning-automation — public render worker

This repo does **one thing**: it renders silent video chunks for a documentary job.
It is public so rendering runs on free GitHub Actions minutes.

## What is here

| File | Purpose |
| --- | --- |
| `.github/workflows/render.yml` | 20-way matrix render + assemble |
| `render_job.py` | renders one chunk (silent) from a plan |
| `assemble_chunks.py` | joins the 20 chunks into `draft_silent.mp4` |
| `media.py`, `visual_fetch.py`, `paths.py` | ffmpeg helpers + procedural motion generators |

## What is NOT here

- No narration, no scripts, no audio, no research, no SEO, no product data.
- No YouTube cookies, no Gumroad token, no Telegram token, no private config.
- No media files are ever committed. Rendered video only exists as a workflow
  artifact for the run that produced it.

## Input contract

A job is a single file `jobs/<slug>.json` committed by the private repo:

```json
{
  "slug": "the_lost_library_of_alexandria",
  "category": "history",
  "size": "1920x1080",
  "n_chunks": 20,
  "indices": [0, 1, "...19"],
  "total_duration_sec": 601.2,
  "chunks": [
    {
      "index": 0,
      "start": 0.0,
      "duration_sec": 30.4,
      "shots": [
        {"shot_index": 0, "type": "intro", "duration_sec": 5.1, "seed": 1000, "text": "..."}
      ]
    }
  ]
}
```

## Running a job

```bash
gh workflow run render.yml --repo goatedanimefx-byte/yt-full-earning-automation \
  -f job=the_lost_library_of_alexandria
```

Artifacts: `chunk-00 ... chunk-19` (1 day) and `draft` (silent mp4, 3 days).
The private repo downloads `draft` and muxes the narration onto it.

#!/usr/bin/env python3
"""
FFmpeg Stitch - Combine audio + visuals into final documentary
Optimized for GitHub Actions: CRF 28, 5000k bitrate
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "outputs"

def get_video_duration(path: str) -> float:
    """Get video duration via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0

def create_concat_file(audio_files: list, output_dir: Path) -> Path:
    """Create concat file for audio sequence."""
    
    concat_path = output_dir / "concat_list.txt"
    
    with open(concat_path, "w") as f:
        for af in audio_files:
            # FFmpeg requires absolute paths and escaped special chars
            abs_path = Path(af["audio_path"]).resolve()
            duration = af.get("duration_sec", 30)
            f.write(f"file '{abs_path}'\n")
            f.write(f"duration {duration}\n")
    
    return concat_path

def create_filter_complex(audio_concat: str, video_files: list) -> str:
    """Create FFmpeg filter complex for mixing."""
    
    # Chain: audio concat → normalize → video overlay
    # This is simplified - real version needs per-segment mapping
    return f"[0:a]anull[outa]"

def stitch_documentary(
    audio_manifest: dict,
    visual_manifest: list,
    output_name: str = "documentary",
    crf: int = 28,
    bitrate: str = "5000k"
) -> Path:
    """Combine audio and visuals into final MP4."""
    
    script_name = audio_manifest.get("script_topic", "doc").lower().replace(" ", "_")
    work_dir = OUTPUT_DIR / script_name
    audio_dir = work_dir / "audio"
    visual_dir = work_dir / "visuals"
    
    output_dir = work_dir / "final"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{output_name}.mp4"
    
    # Build concat file for audio
    audio_files = audio_manifest.get("audio_files", [])
    concat_file = create_concat_file(audio_files, work_dir)
    
    print(f"Concatenating {len(audio_files)} audio segments...")
    
    # Step 1: Concatenate all audio segments
    concat_audio = work_dir / "combined_audio.mp3"
    
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(concat_audio)
    ]
    
    print(f"Running: {' '.join(cmd_concat)}")
    result = subprocess.run(cmd_concat, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"FFmpeg concat error: {result.stderr}")
        # Fallback: use first audio file only
        concat_audio = audio_files[0]["audio_path"]
    
    # Step 2: Find video files and create final output
    video_files = []
    for v in visual_manifest:
        vp = Path(v["path"])
        if vp.exists() and vp.suffix == ".mp4":
            video_files.append(str(vp))
    
    if not video_files:
        # Generate color background if no videos
        print("No video assets - creating color bars")
        color_video = work_dir / "color_bg.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:d={audio_manifest.get('total_duration_sec', 600)}",
            "-c:v", "libx264", "-t", str(audio_manifest.get("total_duration_sec", 600)),
            str(color_video)
        ], capture_output=True)
        video_files = [str(color_video)]
    
    # Step 3: Overlay audio on video
    # Using longest video, trimming to audio length
    cmd_stitch = [
        "ffmpeg", "-y",
        "-i", video_files[0],  # Primary video
        "-i", str(concat_audio),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(crf),
        "-b:v", bitrate,
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-fflags", "+genpts",
        str(output_path)
    ]
    
    print(f"Stitching with CRF {crf}, bitrate {bitrate}...")
    print(f"Running: {' '.join(cmd_stitch)}")
    
    result = subprocess.run(cmd_stitch, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"FFmpeg stitch error: {result.stderr}")
        raise Exception("Video stitching failed")
    
    # Verify output
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        duration = get_video_duration(str(output_path))
        print(f"✓ Documentary created: {output_path}")
        print(f"  Size: {size_mb:.1f} MB")
        print(f"  Duration: {duration:.1f}s")
    
    return output_path

def process_full_documentary(script_topic: str):
    """Run full pipeline for a topic."""
    
    script_name = script_topic.lower().replace(" ", "_")
    
    # Load manifests
    script_file = OUTPUT_DIR / f"script_{script_name}.json"
    audio_manifest_file = OUTPUT_DIR / script_name / "audio" / "manifest.json"
    visual_manifest_file = OUTPUT_DIR / script_name / "visuals" / "visual_manifest.json"
    
    with open(audio_manifest_file) as f:
        audio_manifest = json.load(f)
    
    with open(visual_manifest_file) as f:
        visual_manifest = json.load(f)
    
    # Stitch
    output = stitch_documentary(audio_manifest, visual_manifest, script_name)
    return output

if __name__ == "__main__":
    import sys
    
    topic = sys.argv[1] if len(sys.argv) > 1 else "the_rise_of_ai_in_filmmaking"
    output = process_full_documentary(topic)
    print(f"Final output: {output}")
#!/usr/bin/env python3
"""
CTA / Promo Injector - Add promo segment in video
"""

import subprocess
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs"

def create_promo_segment(
    promo_text: str = "Check out our digital products!",
    product_link: str = "your-gumroad-link.com",
    duration: int = 15
) -> Path:
    """Create promo video segment."""
    
    # Generate promo video with text overlay
    promo_dir = OUTPUT_DIR / "promo"
    promo_dir.mkdir(parents=True, exist_ok=True)
    
    # Create color background with text
    output_path = promo_dir / f"promo_{duration}s.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1920x1080:d={duration}",
        "-vf", f"drawtext=text='{promo_text}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2,drawtext=text='{product_link}':fontcolor=yellow:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2+80",
        "-c:v", "libx264", "-t", str(duration),
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True)
    
    # Generate promo audio
    promo_audio = promo_dir / f"promo_{duration}s.mp3"
    # Would use TTS for promo audio
    
    print(f"Promo segment: {output_path}")
    return output_path

def inject_promo_into_video(video_path: str, promo_path: str, output_path: str, position: str = "end") -> Path:
    """Insert promo segment into main video."""
    
    if position == "end":
        # Concatenate video + promo
        concat_file = OUTPUT_DIR / "concat.txt"
        with open(concat_file, "w") as f:
            f.write(f"file '{video_path}'\n")
            f.write(f"file '{promo_path}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", output_path
        ]
    else:
        # Insert at specific position (more complex)
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-i", promo_path,
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1[outv]",
            "-map", "[outv]", "-c:v", "libx264", "-crf", "28",
            output_path
        ]
    
    subprocess.run(cmd, capture_output=True)
    print(f"Promo injected: {output_path}")
    return Path(output_path)

if __name__ == "__main__":
    print("Promo Injector Ready")
#!/usr/bin/env python3
"""
Social Clips - Auto-create short clips from long videos
Creates 60s shorts/reels from full documentary
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "outputs" / "clips"

class SocialClipGenerator:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_clip(
        self,
        video_path: str,
        start_sec: int = 0,
        duration: int = 60,
        title: str = "clip",
        format: str = "vertical"  # vertical (9:16) or horizontal (16:9)
    ) -> Path:
        """Create a social media clip from video."""
        
        output_name = f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = self.output_dir / output_name
        
        if format == "vertical":
            # Crop to 9:16 for shorts/reels
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_sec),
                "-i", video_path,
                "-t", str(duration),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-crf", "28",
                "-c:a", "aac", "-b:a", "128k",
                str(output_path)
            ]
        else:
            # Standard 16:9
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_sec),
                "-i", video_path,
                "-t", str(duration),
                "-c:v", "libx264", "-crf", "28",
                "-c:a", "aac", "-b:a", "128k",
                str(output_path)
            ]
        
        subprocess.run(cmd, capture_output=True)
        
        if output_path.exists():
            print(f"Clip created: {output_path}")
            return output_path
        return None
    
    def create_auto_clips(self, video_path: str, script: dict, num_clips: int = 3) -> list:
        """Automatically create clips based on script segments."""
        clips = []
        segments = script.get("segments", [])
        
        # Take key segments (intro, main highlights, conclusion)
        key_segments = [s for s in segments if s.get("type") in ["intro", "main", "conclusion"]]
        
        # Calculate duration per clip (max 60s each)
        total_duration = sum(s.get("duration_sec", 30) for s in key_segments)
        clip_duration = min(60, total_duration // min(num_clips, len(key_segments)))
        
        current_time = 0
        for i in range(min(num_clips, len(key_segments))):
            segment = key_segments[i]
            clip = self.create_clip(
                video_path,
                start_sec=current_time,
                duration=clip_duration,
                title=f"clip_{i+1}",
                format="vertical"
            )
            
            if clip:
                clips.append({
                    "path": str(clip),
                    "segment": segment.get("type"),
                    "duration": clip_duration
                })
            
            current_time += clip_duration
        
        return clips

if __name__ == "__main__":
    gen = SocialClipGenerator()
    print("Social Clip Generator Ready")
#!/usr/bin/env python3
"""
Asset Validator - Check all assets before upload
Validates: videos, images, audio for errors
"""

import subprocess
from pathlib import Path
import json

class AssetValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_video(self, video_path: str) -> bool:
        """Check if video is valid and not corrupted."""
        
        if not Path(video_path).exists():
            self.errors.append(f"Video not found: {video_path}")
            return False
        
        # Check video duration using ffprobe
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            duration = float(result.stdout.strip())
            if duration < 10:  # Less than 10 seconds is suspicious
                self.warnings.append(f"Video too short: {duration}s")
            print(f"✓ Video valid: {duration}s")
            return True
        except:
            self.errors.append(f"Video corrupted or unreadable: {video_path}")
            return False
    
    def validate_audio(self, audio_path: str) -> bool:
        """Check if audio is valid."""
        
        if not Path(audio_path).exists():
            self.errors.append(f"Audio not found: {audio_path}")
            return False
        
        # Check audio with ffprobe
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "stream=codec_name,duration",
            "-of", "json", audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            data = json.loads(result.stdout)
            if "streams" in data and len(data["streams"]) > 0:
                print(f"✓ Audio valid: {data['streams'][0].get('codec_name', 'unknown')}")
                return True
        except:
            pass
        
        self.errors.append(f"Audio corrupted: {audio_path}")
        return False
    
    def validate_image(self, image_path: str) -> bool:
        """Check if image is valid."""
        
        if not Path(image_path).exists():
            self.warnings.append(f"Image not found: {image_path}")
            return False
        
        # Check file size (too small = problem)
        size = Path(image_path).stat().st_size
        if size < 1000:  # Less than 1KB is suspicious
            self.warnings.append(f"Image too small: {size} bytes")
            return False
        
        print(f"✓ Image valid: {size} bytes")
        return True
    
    def validate_all(self, output_dir: Path) -> dict:
        """Validate all assets in output directory."""
        
        print("🔍 Validating assets...")
        
        # Check final video
        final_dir = output_dir / "final"
        if final_dir.exists():
            for video in final_dir.glob("*.mp4"):
                self.validate_video(str(video))
        
        # Check audio
        audio_dir = output_dir / "audio"
        if audio_dir.exists():
            for audio in audio_dir.glob("*.wav"):
                self.validate_audio(str(audio))
            for audio in audio_dir.glob("*.mp3"):
                self.validate_audio(str(audio))
        
        # Check thumbnails
        thumb_dir = output_dir / "thumbnails"
        if thumb_dir.exists():
            for img in thumb_dir.glob("*.jpg"):
                self.validate_image(str(img))
        
        # Check subtitles
        sub_dir = output_dir / "subtitles"
        if sub_dir.exists():
            for sub in sub_dir.glob("*.srt"):
                if sub.stat().st_size < 100:
                    self.warnings.append(f"Subtitle file too small: {sub}")
        
        # Summary
        is_valid = len(self.errors) == 0
        
        result = {
            "valid": is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        if is_valid:
            print("✅ All assets validated successfully!")
        else:
            print(f"❌ Validation failed: {len(self.errors)} errors")
        
        if self.warnings:
            print(f"⚠️ Warnings: {len(self.warnings)}")
        
        return result

if __name__ == "__main__":
    validator = AssetValidator()
    print("Asset Validator Ready")
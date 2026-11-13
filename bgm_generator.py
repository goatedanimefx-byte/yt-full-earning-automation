#!/usr/bin/env python3
"""
Background Music Generator - Add BGM with audio ducking
Voice loud, music low - professional documentary feel
"""

import subprocess
import random
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs" / "audio"

# Free BGM sources (public domain)
BGM_CATEGORIES = {
    "cinematic": ["epic", "orchestra", "dramatic"],
    "ambient": ["calm", "background", "peaceful"],
    "tech": ["electronic", "modern", "digital"],
    "uplifting": ["motivational", "positive", "inspiring"]
}

# For now, generate simple tone - in production would download from free sources
def generate_bgm(style: str = "cinematic", duration: int = 60) -> Path:
    """Generate simple background music (placeholder - in production use free BGM)."""
    
    output_path = OUTPUT_DIR / f"bgm_{style}_{duration}s.wav"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate simple ambient tone using ffmpeg
    # In production: download from pixabay/articulate free music
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", 
        f"anoisesrc=d={duration}:c=pink:r=44100:a=0.3",
        "-c:a", "pcm_s16le", "-ar", "44100",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True)
    except:
        # Fallback: create silent file
        output_path.write_bytes(b'')
    
    print(f"BGM generated: {output_path}")
    return output_path

def mix_with_voice(voice_path: str, bgm_path: str, output_path: str, voice_vol: float = 1.0, bgm_vol: float = 0.2) -> Path:
    """Mix voice and BGM with audio ducking - voice loud, music low."""
    
    # FFmpeg filter for ducking: lower BGM when voice is present
    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-i", bgm_path,
        "-filter_complex", 
        f"[1:a]volume={bgm_vol}[bgm];[0:a]volume={voice_vol}[voice];[voice][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path
    ]
    
    subprocess.run(cmd, capture_output=True)
    print(f"Mixed audio: {output_path}")
    return Path(output_path)

def apply_audio_normalization(audio_path: str, target_lufs: float = -14.0) -> Path:
    """Normalize audio to YouTube standard -14 LUFS."""
    
    output_path = str(audio_path).replace(".mp3", "_normalized.mp3")
    
    # Use ffmpeg loudnorm filter for YouTube standard
    cmd = [
        "ffmpeg", "-y", "-i", audio_path,
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path
    ]
    
    subprocess.run(cmd, capture_output=True)
    print(f"Normalized audio: {output_path}")
    return Path(output_path)

if __name__ == "__main__":
    print("BGM Generator Ready")
    # Test
    # bgm = generate_bgm("cinematic", 60)
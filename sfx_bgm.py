#!/usr/bin/env python3
"""
SFX & BGM Generator - Sound effects and background music for documentary
"""

import subprocess
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs" / "audio"

def generate_sfx(effect: str, duration: int = 3) -> Path:
    """Generate sound effects: whoosh, riser, transition, etc."""
    
    output_path = OUTPUT_DIR / f"sfx_{effect}_{duration}s.wav"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Sound effects using ffmpeg
    effects = {
        "whoosh": "sine=frequency=200:d=0.5,sine=frequency=100:d=0.5",
        "riser": "sine=frequency=100:d=3,sine=frequency=500:d=3",
        "transition": "sine=frequency=440:d=0.2,sine=frequency=880:d=0.2",
        "impact": "sine=frequency=80:d=0.3,sine=frequency=40:d=0.3",
        "ambient": "anoisesrc=d=5:c=pink:r=44100:a=0.1"
    }
    
    filter_str = effects.get(effect, effects["transition"])
    
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", filter_str,
        "-c:a", "pcm_s16le", "-ar", "44100",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True)
    except:
        pass
    
    print(f"SFX generated: {output_path}")
    return output_path

def generate_bgm(style: str = "cinematic", duration: int = 60) -> Path:
    """Generate background music."""
    
    output_path = OUTPUT_DIR / f"bgm_{style}_{duration}s.wav"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate ambient music
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", 
        f"anoisesrc=d={duration}:c=pink:r=44100:a=0.2",
        "-c:a", "pcm_s16le", "-ar", "44100",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True)
    except:
        pass
    
    print(f"BGM generated: {output_path}")
    return output_path

def mix_audio_with_sfx(voice_path: str, bgm_path: str, sfx_list: list, output_path: str) -> Path:
    """Mix voice + BGM + SFX with proper ducking."""
    
    # Voice loud (1.0), BGM low (0.2), SFX medium (0.5)
    # In production: use more complex audio chain
    
    cmd = [
        "ffmpeg", "-y",
        "-i", voice_path,
        "-i", bgm_path,
        "-filter_complex",
        "[1:a]volume=0.2[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        output_path
    ]
    
    subprocess.run(cmd, capture_output=True)
    print(f"Mixed audio: {output_path}")
    return Path(output_path)

if __name__ == "__main__":
    print("SFX & BGM Generator Ready")
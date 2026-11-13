#!/usr/bin/env python3
"""
Voice Generator - Kitten TTS Nano 0.8 (free, local, no API)
"""

import json
import subprocess
from pathlib import Path
import sys

# Check if kitten is installed, install if not
def ensure_kitten():
    try:
        from kittentts import KittenTTS
        return True
    except ImportError:
        print("Installing KittenTTS...")
        subprocess.run([sys.executable, "-m", "pip", "install", 
                       "https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl",
                       "-q"], check=True)
        from kittentts import KittenTTS
        return True

OUTPUT_DIR = Path(__file__).parent / "outputs" / "audio"

# Kitten TTS voices (free, built-in)
VOICES = ["Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo"]
VOICE_MAP = {
    "intro": "Bruno",
    "context": "Jasper",
    "main": "Jasper",
    "conclusion": "Luna",
    "cta": "Bruno"
}

# Cache loaded model
_model = None

def get_model():
    global _model
    if _model is None:
        ensure_kitten()
        from kittentts import KittenTTS
        _model = KittenTTS("KittenML/kitten-tts-nano-0.8-int8")
    return _model

def text_to_speech(text: str, voice: str = "Jasper", speed: float = 1.0) -> bytes:
    """Convert text to speech via Kitten TTS (returns numpy, we save as wav)."""
    model = get_model()
    audio = model.generate(text, voice=voice, speed=speed)
    return audio

def generate_segment_audio(segment: dict, output_dir: Path) -> Path:
    """Generate audio for a single script segment using Kitten TTS."""
    import soundfile as sf
    
    voiceover = segment.get("voiceover", "")
    segment_type = segment.get("type", "main")
    
    # Select voice based on segment type
    voice = VOICE_MAP.get(segment_type, "Jasper")
    
    audio_np = text_to_speech(voiceover, voice=voice, speed=1.0)
    
    output_path = output_dir / f"{segment_type}_{segment.get('duration_sec', 0)}s.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as WAV (Kitten returns numpy array at 24kHz)
    sf.write(output_path, audio_np, 24000)
    
    print(f"Audio generated: {output_path}")
    return output_path

def generate_full_audio(script: dict) -> list:
    """Generate audio for all segments (parallel for speed)."""
    
    script_name = script.get("topic", "doc").lower().replace(" ", "_")
    output_dir = OUTPUT_DIR / script_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    audio_files = []
    
    # Process sequentially to avoid rate limits
    for i, segment in enumerate(script.get("segments", [])):
        print(f"Processing segment {i+1}/{len(script['segments'])}")
        audio_path = generate_segment_audio(segment, output_dir)
        audio_files.append({
            "segment_index": i,
            "type": segment.get("type"),
            "duration_sec": segment.get("duration_sec"),
            "audio_path": str(audio_path)
        })
    
    # Save manifest
    manifest = {
        "script_topic": script.get("topic"),
        "audio_files": audio_files,
        "total_duration_sec": sum(s.get("duration_sec", 0) for s in script.get("segments", []))
    }
    
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest saved: {manifest_path}")
    return audio_files

if __name__ == "__main__":
    import sys
    
    # Load script from file
    script_file = sys.argv[1] if len(sys.argv) > 1 else "outputs/script_the_rise_of_ai_in_filmmaking.json"
    
    with open(script_file) as f:
        script = json.load(f)
    
    audio_files = generate_full_audio(script)
    print(f"Generated {len(audio_files)} audio files")
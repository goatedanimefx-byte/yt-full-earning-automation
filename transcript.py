#!/usr/bin/env python3
"""
Transcript Generator - Auto-subtitles from script
Uses the TTS script text to generate subtitles
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "outputs" / "subtitles"

class TranscriptGenerator:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_subtitles(self, script: dict, format: str = "srt") -> Path:
        """Generate subtitles from script segments."""
        
        script_name = script.get("topic", "doc").replace(" ", "_").lower()
        output_path = self.output_dir / f"{script_name}.{format}"
        
        subtitle_content = ""
        current_time = 0
        
        for i, segment in enumerate(script.get("segments", [])):
            text = segment.get("voiceover", "")
            duration = segment.get("duration_sec", 30)
            
            if format == "srt":
                subtitle_content += self._create_srt_block(i+1, current_time, duration, text)
            else:  # vtt
                subtitle_content += self._create_vtt_block(current_time, duration, text)
            
            current_time += duration
        
        output_path.write_text(subtitle_content, encoding="utf-8")
        print(f"Subtitles: {output_path}")
        return output_path
    
    def _create_srt_block(self, index: int, start_sec: int, duration: int, text: str) -> str:
        """Create SRT format subtitle block."""
        start = self._format_srt_time(start_sec)
        end = self._format_srt_time(start_sec + duration)
        
        # Split long text into multiple lines
        lines = self._split_text(text, 42)
        
        return f"{index}\n{start} --> {end}\n{lines}\n\n"
    
    def _create_vtt_block(self, start_sec: int, duration: int, text: str) -> str:
        """Create VTT format subtitle block."""
        start = self._format_vtt_time(start_sec)
        end = self._format_vtt_time(start_sec + duration)
        
        lines = self._split_text(text, 42)
        
        return f"{start} --> {end}\n{lines}\n\n"
    
    def _format_srt_time(self, seconds: int) -> str:
        """Format time for SRT (HH:MM:SS,mmm)."""
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d},000"
    
    def _format_vtt_time(self, seconds: int) -> str:
        """Format time for VTT (HH:MM:SS.mmm)."""
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.000"
    
    def _split_text(self, text: str, max_len: int = 42) -> str:
        """Split text into lines."""
        words = text.split()
        lines = []
        current = ""
        
        for word in words:
            if len(current + " " + word) <= max_len:
                current = (current + " " + word).strip()
            else:
                if current:
                    lines.append(current)
                current = word
        
        if current:
            lines.append(current)
        
        return "\n".join(lines)

if __name__ == "__main__":
    tg = TranscriptGenerator()
    print("Transcript Generator Ready")
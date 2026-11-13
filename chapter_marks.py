#!/usr/bin/env python3
"""
Chapter Marks - Auto-generate YouTube timestamps
Creates chapter markers from script segments
"""

from datetime import datetime

class ChapterGenerator:
    def __init__(self):
        pass
    
    def generate_chapters(self, script: dict) -> list:
        """Generate chapter markers from script segments."""
        chapters = []
        current_time = 0
        
        for segment in script.get("segments", []):
            segment_type = segment.get("type", "main")
            duration = segment.get("duration_sec", 30)
            topic = script.get("topic", "Documentary")
            
            # Create chapter title based on segment type
            titles = {
                "intro": "Introduction",
                "context": "Background & Context",
                "main": "Main Content",
                "conclusion": "Conclusion",
                "cta": "Call to Action"
            }
            
            title = titles.get(segment_type, "Part")
            
            chapters.append({
                "time": self._format_time(current_time),
                "title": f"{title} - {topic}"
            })
            
            current_time += duration
        
        return chapters
    
    def _format_time(self, seconds: int) -> str:
        """Format time as MM:SS or HH:MM:SS."""
        hrs = seconds // 3600
        mins = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hrs > 0:
            return f"{hrs}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"
    
    def format_for_youtube(self, chapters: list) -> str:
        """Format chapters for YouTube description."""
        lines = ["📋 Chapters:", ""]
        for ch in chapters:
            lines.append(f"{ch['time']} {ch['title']}")
        return "\n".join(lines)
    
    def format_as_list(self, chapters: list) -> str:
        """Format as numbered list."""
        lines = []
        for i, ch in enumerate(chapters, 1):
            lines.append(f"{i}. {ch['time']} - {ch['title']}")
        return "\n".join(lines)

if __name__ == "__main__":
    cg = ChapterGenerator()
    print("Chapter Generator Ready")
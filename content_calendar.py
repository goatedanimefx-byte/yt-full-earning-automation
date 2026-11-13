#!/usr/bin/env python3
"""
Content Calendar - Schedule and plan posts ahead
Manages publishing schedule for videos
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

MEMORY_DIR = Path(__file__).parent / "memory"
CALENDAR_FILE = MEMORY_DIR / "content_calendar.json"

class ContentCalendar:
    def __init__(self):
        self.calendar_file = CALENDAR_FILE
        self.schedule = self._load_schedule()
    
    def _load_schedule(self) -> dict:
        if self.calendar_file.exists():
            return json.loads(self.calendar_file.read_text())
        return {"scheduled": [], "completed": []}
    
    def _save_schedule(self):
        self.calendar_file.write_text(json.dumps(self.schedule, indent=2))
    
    def schedule_video(self, topic: str, publish_date: str, format: str = "horizontal") -> dict:
        """Schedule a video for publishing."""
        entry = {
            "id": f"video_{len(self.schedule['scheduled']) + 1}",
            "topic": topic,
            "format": format,
            "publish_date": publish_date,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        self.schedule["scheduled"].append(entry)
        self._save_schedule()
        
        return entry
    
    def get_upcoming(self, days: int = 7) -> list:
        """Get scheduled videos for next N days."""
        upcoming = []
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        for entry in self.schedule["scheduled"]:
            pub_date = datetime.fromisoformat(entry["publish_date"])
            if now <= pub_date <= end_date:
                upcoming.append(entry)
        
        return sorted(upcoming, key=lambda x: x["publish_date"])
    
    def mark_completed(self, video_id: str):
        """Mark a video as completed."""
        for entry in self.schedule["scheduled"]:
            if entry["id"] == video_id:
                entry["status"] = "completed"
                entry["completed_at"] = datetime.now().isoformat()
                self.schedule["completed"].append(entry)
                self.schedule["scheduled"].remove(entry)
                self._save_schedule()
                break
    
    def get_best_post_times(self) -> dict:
        """Get best times to post based on engagement (placeholder)."""
        # In real system, would analyze past performance
        return {
            "youtube": ["14:00", "18:00", "20:00"],
            "instagram": ["12:00", "17:00", "21:00"],
            "tiktok": ["16:00", "20:00", "22:00"]
        }

if __name__ == "__main__":
    cal = ContentCalendar()
    print("Content Calendar Ready")
    print(f"Upcoming: {cal.get_upcoming()}")
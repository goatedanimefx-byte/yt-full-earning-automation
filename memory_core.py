#!/usr/bin/env python3
"""
Memory Core - The brain of the documentary engine
Stores all data, learns from past, improves continuously
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

MEMORY_DIR = Path(__file__).parent / "memory"

class MemorySystem:
    def __init__(self):
        self.analytics_dir = MEMORY_DIR / "analytics"
        self.sales_dir = MEMORY_DIR / "sales"
        self.topics_dir = MEMORY_DIR / "topics"
        self.mistakes_dir = MEMORY_DIR / "mistakes"
        self.thumbnails_dir = MEMORY_DIR / "thumbnails"
        self.scripts_dir = MEMORY_DIR / "scripts"
        self.backups_dir = MEMORY_DIR / "backups"
        self.competitors_dir = MEMORY_DIR / "competitors"
        
        # Create all directories
        for d in [self.analytics_dir, self.sales_dir, self.topics_dir, 
                  self.mistakes_dir, self.thumbnails_dir, self.scripts_dir,
                  self.backups_dir, self.competitors_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    # ============== ANALYTICS ==============
    def save_analytics(self, video_id: str, data: dict):
        """Save video performance data."""
        file_path = self.analytics_dir / f"{video_id}.json"
        data["saved_at"] = datetime.now().isoformat()
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_video_analytics(self, video_id: str) -> dict:
        """Get analytics for specific video."""
        file_path = self.analytics_dir / f"{video_id}.json"
        if file_path.exists():
            return json.loads(file_path.read_text())
        return {}
    
    def get_all_analytics(self) -> List[dict]:
        """Get all video analytics."""
        results = []
        for f in self.analytics_dir.glob("*.json"):
            results.append(json.loads(f.read_text()))
        return sorted(results, key=lambda x: x.get("saved_at", ""), reverse=True)
    
    def get_avg_views(self) -> float:
        """Calculate average views across all videos."""
        all_analytics = self.get_all_analytics()
        if not all_analytics:
            return 0
        views = [a.get("views", 0) for a in all_analytics]
        return sum(views) / len(views) if views else 0
    
    # ============== SALES ==============
    def save_sale(self, video_id: str, product_id: str, revenue: float):
        """Record a sale."""
        sales_file = self.sales_dir / f"{video_id}.json"
        sales = []
        if sales_file.exists():
            sales = json.loads(sales_file.read_text())
        sales.append({
            "product_id": product_id,
            "revenue": revenue,
            "date": datetime.now().isoformat()
        })
        with open(sales_file, "w") as f:
            json.dump(sales, f, indent=2)
    
    def get_total_revenue(self) -> float:
        """Get total revenue from all videos."""
        total = 0
        for f in self.sales_dir.glob("*.json"):
            sales = json.loads(f.read_text())
            total += sum(s.get("revenue", 0) for s in sales)
        return total
    
    # ============== TOPICS ==============
    def save_topic_performance(self, topic: str, views: int, sales: float):
        """Save how a topic performed."""
        topic_file = self.topics_dir / f"{topic.lower().replace(' ', '_')}.json"
        data = {}
        if topic_file.exists():
            data = json.loads(topic_file.read_text())
        
        if "runs" not in data:
            data["runs"] = []
        data["runs"].append({
            "views": views,
            "sales": sales,
            "date": datetime.now().isoformat()
        })
        data["avg_views"] = sum(r["views"] for r in data["runs"]) / len(data["runs"])
        data["avg_sales"] = sum(r["sales"] for r in data["runs"]) / len(data["runs"])
        
        with open(topic_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_best_topics(self) -> List[str]:
        """Get topics with best performance."""
        topics = []
        for f in self.topics_dir.glob("*.json"):
            data = json.loads(f.read_text())
            topics.append((f.stem, data.get("avg_views", 0), data.get("avg_sales", 0)))
        return sorted(topics, key=lambda x: x[1], reverse=True)[:5]
    
    def get_worst_topics(self) -> List[str]:
        """Get topics that performed poorly."""
        topics = []
        for f in self.topics_dir.glob("*.json"):
            data = json.loads(f.read_text())
            topics.append((f.stem, data.get("avg_views", 0), data.get("avg_sales", 0)))
        return sorted(topics, key=lambda x: x[1])[:5]
    
    # ============== MISTAKES ==============
    def log_mistake(self, video_id: str, mistake_type: str, description: str, fix: str):
        """Log a mistake and how it was fixed."""
        mistake_file = self.mistakes_dir / f"{datetime.now().strftime('%Y%m')}.json"
        mistakes = []
        if mistake_file.exists():
            mistakes = json.loads(mistake_file.read_text())
        
        mistakes.append({
            "video_id": video_id,
            "type": mistake_type,
            "description": description,
            "fix_applied": fix,
            "date": datetime.now().isoformat()
        })
        
        with open(mistake_file, "w") as f:
            json.dump(mistakes, f, indent=2)
    
    def get_recent_mistakes(self) -> List[dict]:
        """Get recent mistakes for learning."""
        mistakes = []
        for f in self.mistakes_dir.glob("*.json"):
            mistakes.extend(json.loads(f.read_text()))
        return sorted(mistakes, key=lambda x: x.get("date", ""), reverse=True)[:10]
    
    # ============== LEARNINGS ==============
    def generate_learnings(self) -> dict:
        """Generate AI learnings from all data."""
        analytics = self.get_all_analytics()
        total_videos = len(analytics)
        avg_views = self.get_avg_views()
        total_revenue = self.get_total_revenue()
        best_topics = self.get_best_topics()
        worst_topics = self.get_worst_topics()
        recent_mistakes = self.get_recent_mistakes()
        
        learnings = {
            "total_videos": total_videos,
            "avg_views": avg_views,
            "total_revenue": total_revenue,
            "best_topics": best_topics,
            "worst_topics": worst_topics,
            "common_mistakes": [m["type"] for m in recent_mistakes[:5]],
            "recommendations": self._generate_recommendations(analytics, avg_views),
            "updated_at": datetime.now().isoformat()
        }
        
        # Save learnings
        with open(MEMORY_DIR / "learnings.json", "w") as f:
            json.dump(learnings, f, indent=2)
        
        return learnings
    
    def _generate_recommendations(self, analytics: List[dict], avg_views: float) -> List[str]:
        """Generate recommendations based on data."""
        recommendations = []
        
        if avg_views < 1000:
            recommendations.append("Low views - try different thumbnail style")
            recommendations.append("Change title formula - add numbers/keywords")
        
        if not analytics:
            recommendations.append("Need more data - keep producing!")
        
        # Check for patterns
        low_performers = [a for a in analytics if a.get("views", 0) < avg_views * 0.5]
        if len(low_performers) > 3:
            recommendations.append(f"{len(low_performers)} videos underperforming - review topics")
        
        return recommendations
    
    def get_improvements_for_next_video(self) -> dict:
        """Get actionable improvements for next video."""
        learnings = self.generate_learnings()
        
        improvements = {
            "topics_to_try": [t[0] for t in learnings.get("best_topics", [])[:3]],
            "topics_to_avoid": [t[0] for t in learnings.get("worst_topics", [])[:3]],
            "recommendations": learnings.get("recommendations", []),
            "avoid_mistakes": list(set(learnings.get("common_mistakes", [])))
        }
        
        return improvements

# Global instance
_memory = None
def get_memory() -> MemorySystem:
    global _memory
    if _memory is None:
        _memory = MemorySystem()
    return _memory

if __name__ == "__main__":
    mem = get_memory()
    print("Memory System Ready")
    print(f"Total Videos: {len(mem.get_all_analytics())}")
    print(f"Average Views: {mem.get_avg_views():.0f}")
    print(f"Total Revenue: ${mem.get_total_revenue():.2f}")
    print(f"\nImprovements for next video:")
    imp = mem.get_improvements_for_next_video()
    print(f"  Topics to try: {imp['topics_to_try']}")
    print(f"  Recommendations: {imp['recommendations']}")
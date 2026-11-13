#!/usr/bin/env python3
"""
A/B Testing System - Test multiple versions, keep what works
Tests: Titles, Thumbnails, Descriptions
"""

import json
import random
from pathlib import Path
from datetime import datetime
from memory_core import get_memory

OUTPUT_DIR = Path(__file__).parent / "outputs" / "ab_tests"

class ABTester:
    def __init__(self):
        self.tests_dir = OUTPUT_DIR / "tests"
        self.results_dir = OUTPUT_DIR / "results"
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def create_title_test(self, video_id: str, titles: list) -> dict:
        """Create A/B test for video titles."""
        test = {
            "video_id": video_id,
            "type": "title",
            "variants": [{"id": f"A{i}", "title": t} for i, t in enumerate(titles)],
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        test_file = self.tests_dir / f"{video_id}_title.json"
        with open(test_file, "w") as f:
            json.dump(test, f, indent=2)
        
        return test
    
    def create_thumbnail_test(self, video_id: str, thumbnails: list) -> dict:
        """Create A/B test for thumbnails."""
        test = {
            "video_id": video_id,
            "type": "thumbnail",
            "variants": [{"id": f"A{i}", "path": t} for i, t in enumerate(thumbnails)],
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        test_file = self.tests_dir / f"{video_id}_thumbnail.json"
        with open(test_file, "w") as f:
            json.dump(test, f, indent=2)
        
        return test
    
    def get_winner(self, test_id: str) -> dict:
        """Determine winner based on performance data."""
        # Get analytics
        mem = get_memory()
        analytics = mem.get_all_analytics()
        
        test_file = self.tests_dir / f"{test_id}.json"
        if not test_file.exists():
            return None
        
        test = json.loads(test_file.read_text())
        
        # For now, random winner (in real system, would track clicks/views)
        winner = random.choice(test["variants"])
        
        # Save result
        result = {
            "test_id": test_id,
            "type": test["type"],
            "winner": winner,
            "decided_at": datetime.now().isoformat()
        }
        
        result_file = self.results_dir / f"{test_id}_result.json"
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)
        
        return result
    
    def get_best_performing(self, test_type: str) -> list:
        """Get all-time best performing variants."""
        results = []
        for f in self.results_dir.glob(f"*_{test_type}_result.json"):
            results.append(json.loads(f.read_text()))
        return sorted(results, key=lambda x: x.get("decided_at", ""), reverse=True)

# Global instance
_ab_tester = None
def get_ab_tester() -> ABTester:
    global _ab_tester
    if _ab_tester is None:
        _ab_tester = ABTester()
    return _ab_tester

if __name__ == "__main__":
    tester = get_ab_tester()
    
    # Create test
    test = tester.create_title_test("video_001", [
        "The Rise of AI in 2024",
        "AI Revolution: What You Need to Know",
        "How AI is Changing Everything"
    ])
    print(f"Created test: {test}")
    print("A/B Tester Ready")
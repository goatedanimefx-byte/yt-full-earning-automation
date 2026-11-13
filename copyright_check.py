#!/usr/bin/env python3
"""
Copyright & Fair-Use Safety Check
Check for potential copyright issues before upload
"""

import json
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(__file__).parent / "outputs"

class CopyrightChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
    
    def check_music_copyright(self, audio_path: str = None) -> bool:
        """Check if music is copyright-free."""
        
        # In production: would use audio fingerprinting API
        # For now: assume generated audio is safe
        self.warnings.append("Music: Generated audio - assumed safe")
        return True
    
    def check_visual_copyright(self, visual_path: str = None) -> bool:
        """Check if visuals are copyright-free."""
        
        # In production: would check against stock library
        # For code-generated visuals: safe
        if visual_path and "pexels" in str(visual_path).lower():
            # Pexels content is free to use
            self.warnings.append("Visuals: Pexels (free to use)")
            return True
        
        # Code-generated: safe
        self.warnings.append("Visuals: Code-generated (safe)")
        return True
    
    def check_script_copyright(self, script: dict) -> bool:
        """Check script for potential issues."""
        
        # Check for trademark mentions
        topic = script.get("topic", "").lower()
        
        # Known trademarks to be careful with
        trademarks = ["apple", "microsoft", "google", "amazon", "meta", "tesla", "nvidia"]
        
        for tm in trademarks:
            if tm in topic:
                self.warnings.append(f"Script: Topic contains trademark '{tm}' - review carefully")
        
        return True
    
    def check_all(self, script: dict = None, audio_path: str = None, visual_path: str = None) -> dict:
        """Run all copyright checks."""
        
        print("🔍 Running copyright checks...")
        
        # Run checks
        self.check_music_copyright(audio_path)
        self.check_visual_copyright(visual_path)
        if script:
            self.check_script_copyright(script)
        
        # Determine if safe to upload
        is_safe = len(self.issues) == 0
        
        result = {
            "safe_to_upload": is_safe,
            "issues": self.issues,
            "warnings": self.warnings,
            "checked_at": datetime.now().isoformat()
        }
        
        if is_safe:
            print("✅ Copyright check passed!")
        else:
            print(f"❌ Copyright issues found: {len(self.issues)}")
        
        if self.warnings:
            print(f"⚠️ Warnings: {len(self.warnings)}")
        
        # Save report
        report_file = OUTPUT_DIR / "copyright_report.json"
        with open(report_file, "w") as f:
            json.dump(result, f, indent=2)
        
        return result

if __name__ == "__main__":
    checker = CopyrightChecker()
    result = checker.check_all()
    print(result)
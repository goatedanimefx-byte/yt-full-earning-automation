#!/usr/bin/env python3
"""
Backup System - Auto-backup memory data
Saves to local folder + optional cloud
"""

import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent / "memory"
BACKUP_DIR = MEMORY_DIR / "backups"

class BackupSystem:
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, label: str = None) -> Path:
        """Create backup of all memory data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = label or "backup"
        backup_name = f"{label}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # Create backup folder
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all memory folders
        folders = ["analytics", "sales", "topics", "mistakes", "thumbnails", "scripts", "competitors"]
        
        for folder in folders:
            src = MEMORY_DIR / folder
            if src.exists():
                dst = backup_path / folder
                shutil.copytree(src, dst, dirs_exist_ok=True)
        
        # Copy learnings
        if (MEMORY_DIR / "learnings.json").exists():
            shutil.copy(MEMORY_DIR / "learnings.json", backup_path / "learnings.json")
        
        # Save backup metadata
        meta = {
            "created_at": datetime.now().isoformat(),
            "label": label,
            "folders_backed": folders
        }
        with open(backup_path / "meta.json", "w") as f:
            json.dump(meta, f, indent=2)
        
        print(f"Backup created: {backup_path}")
        return backup_path
    
    def restore_backup(self, backup_path: Path):
        """Restore from a backup."""
        if not backup_path.exists():
            print(f"Backup not found: {backup_path}")
            return
        
        # Restore folders
        folders = ["analytics", "sales", "topics", "mistakes", "thumbnails", "scripts", "competitors"]
        
        for folder in folders:
            src = backup_path / folder
            dst = MEMORY_DIR / folder
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
        
        # Restore learnings
        if (backup_path / "learnings.json").exists():
            shutil.copy(backup_path / "learnings.json", MEMORY_DIR / "learnings.json")
        
        print(f"Restored from: {backup_path}")
    
    def list_backups(self) -> list:
        """List all available backups."""
        backups = []
        for d in self.backup_dir.iterdir():
            if d.is_dir():
                meta_file = d / "meta.json"
                if meta_file.exists():
                    meta = json.loads(meta_file.read_text())
                    backups.append({
                        "path": str(d),
                        "created_at": meta.get("created_at"),
                        "label": meta.get("label")
                    })
        return sorted(backups, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def auto_backup(self):
        """Create automatic daily backup."""
        today = datetime.now().strftime("%Y%m%d")
        existing = list(self.backup_dir.glob(f"auto_{today}_*"))
        
        if not existing:
            self.create_backup(label=f"auto_{today}")
            print("Auto-backup completed")

if __name__ == "__main__":
    bs = BackupSystem()
    bs.auto_backup()
    print("\nAvailable backups:")
    for b in bs.list_backups():
        print(f"  {b['created_at']} - {b['label']}")
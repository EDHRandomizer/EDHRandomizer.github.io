#!/usr/bin/env python3
"""
Sync perks.json from data/ to docs/data/
This ensures both the API (uses data/perks.json) and frontend (uses docs/data/perks.json) have the same file.
"""
import shutil
from pathlib import Path

def sync_perks():
    source = Path(__file__).parent / 'data' / 'perks.json'
    dest = Path(__file__).parent / 'docs' / 'data' / 'perks.json'
    
    # Create destination directory if it doesn't exist
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy file
    shutil.copy2(source, dest)
    
    print(f"✓ Synced {source} → {dest}")

if __name__ == '__main__':
    sync_perks()

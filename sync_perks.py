#!/usr/bin/env python3
"""
Sync perks.json from data/ to docs/data/
This ensures both the API (uses data/perks.json) and frontend (uses docs/data/perks.json) have the same file.
Also removes UTF-8 BOM if present.
"""
import shutil
from pathlib import Path

def sync_perks():
    source = Path(__file__).parent / 'data' / 'perks.json'
    dest = Path(__file__).parent / 'docs' / 'data' / 'perks.json'
    
    # Create destination directory if it doesn't exist
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    # Read source with BOM handling
    with open(source, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Write both files without BOM
    with open(source, 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Synced (BOM removed) {source} → {dest}")

if __name__ == '__main__':
    sync_perks()

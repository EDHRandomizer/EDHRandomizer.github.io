#!/usr/bin/env python3
"""
Sync perks.json from data/ to docs/data/ and api/
This ensures the API (uses api/perks.json), backend (uses data/perks.json), 
and frontend (uses docs/data/perks.json) all have the same file.
Also removes UTF-8 BOM if present.
"""
import shutil
from pathlib import Path

def sync_perks():
    source = Path(__file__).parent / 'data' / 'perks.json'
    dest_docs = Path(__file__).parent / 'docs' / 'data' / 'perks.json'
    dest_api = Path(__file__).parent / 'api' / 'perks.json'
    
    # Create destination directories if they don't exist
    dest_docs.parent.mkdir(parents=True, exist_ok=True)
    dest_api.parent.mkdir(parents=True, exist_ok=True)
    
    # Read source with BOM handling
    with open(source, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # Write all three files without BOM
    with open(source, 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open(dest_docs, 'w', encoding='utf-8') as f:
        f.write(content)
    
    with open(dest_api, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Synced (BOM removed):")
    print(f"  {source}")
    print(f"  → {dest_docs}")
    print(f"  → {dest_api}")

if __name__ == '__main__':
    sync_perks()

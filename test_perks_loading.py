"""
Test that perks.json loads correctly from both API and frontend paths
"""
import json
import os
from pathlib import Path

def test_perks_json_exists():
    """Verify perks.json exists in the correct location"""
    repo_root = Path(__file__).parent
    perks_path = repo_root / 'data' / 'perks.json'
    
    assert perks_path.exists(), f"perks.json not found at {perks_path}"
    print(f"✓ perks.json exists at {perks_path}")

def test_perks_json_valid():
    """Verify perks.json is valid JSON"""
    repo_root = Path(__file__).parent
    perks_path = repo_root / 'data' / 'perks.json'
    
    with open(perks_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert 'version' in data, "perks.json missing 'version' field"
    assert 'perkTypes' in data, "perks.json missing 'perkTypes' field"
    assert 'rarityWeights' in data, "perks.json missing 'rarityWeights' field"
    
    print(f"✓ perks.json is valid JSON with version {data['version']}")
    print(f"✓ Found {len(data['perkTypes'])} perk types")

def test_perks_no_bom():
    """Verify perks.json has no UTF-8 BOM"""
    repo_root = Path(__file__).parent
    perks_path = repo_root / 'data' / 'perks.json'
    
    with open(perks_path, 'rb') as f:
        first_bytes = f.read(3)
    
    # UTF-8 BOM is EF BB BF
    assert first_bytes != b'\xef\xbb\xbf', "perks.json has UTF-8 BOM - this will break JSON parsing!"
    print("✓ perks.json has no BOM")

def test_perks_files_in_sync():
    """Verify both perks.json files are in sync"""
    repo_root = Path(__file__).parent
    source_path = repo_root / 'data' / 'perks.json'
    docs_path = repo_root / 'docs' / 'data' / 'perks.json'
    
    if not docs_path.exists():
        print("⚠️  docs/data/perks.json doesn't exist - run sync_perks.py")
        return
    
    with open(source_path, 'rb') as f:
        source_content = f.read()
    
    with open(docs_path, 'rb') as f:
        docs_content = f.read()
    
    assert source_content == docs_content, "perks.json files are out of sync! Run sync_perks.py"
    print("✓ data/perks.json and docs/data/perks.json are in sync")

def test_scangtech_jptech_exist():
    """Verify ScangTech and JpTech perks are present"""
    repo_root = Path(__file__).parent
    perks_path = repo_root / 'data' / 'perks.json'
    
    with open(perks_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    perk_types = {pt['type'] for pt in data['perkTypes']}
    
    assert 'scangtech_cards' in perk_types, "ScangTech perk type missing"
    assert 'jptech_cards' in perk_types, "JpTech perk type missing"
    
    # Verify the perks have the correct structure
    scangtech = next(pt for pt in data['perkTypes'] if pt['type'] == 'scangtech_cards')
    jptech = next(pt for pt in data['perkTypes'] if pt['type'] == 'jptech_cards')
    
    assert len(scangtech['perks']) == 2, "ScangTech should have 2 perks (uncommon and rare)"
    assert len(jptech['perks']) == 2, "JpTech should have 2 perks (uncommon and rare)"
    
    # Check Moxfield deck IDs
    for perk in scangtech['perks']:
        assert perk['effects']['moxfieldDeck'] == 'S-Pxf1bY5kmaHlWiKN1Wug', "ScangTech has wrong Moxfield deck"
    
    for perk in jptech['perks']:
        assert perk['effects']['moxfieldDeck'] == 'Ba27o7m7QUaDUL0zE_j6fQ', "JpTech has wrong Moxfield deck"
    
    print("✓ ScangTech and JpTech perks exist with correct structure")

def test_api_can_load_perks():
    """Verify API path resolution works"""
    repo_root = Path(__file__).parent
    api_dir = repo_root / 'api'
    
    # Simulate API's path resolution: api/../data/perks.json
    perks_path = api_dir / '..' / 'data' / 'perks.json'
    perks_path = perks_path.resolve()
    
    assert perks_path.exists(), f"API cannot resolve perks.json at {perks_path}"
    
    with open(perks_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert 'perkTypes' in data, "API perks.json is invalid"
    print(f"✓ API can load perks.json from {perks_path}")

def test_frontend_can_load_perks():
    """Verify frontend path resolution works"""
    repo_root = Path(__file__).parent
    docs_js_dir = repo_root / 'docs' / 'js' / 'game-session'
    
    # Simulate frontend's path resolution: docs/js/game-session/../data/perks.json
    # Which resolves to docs/data/perks.json... but we changed it to ../data/perks.json
    # So from docs/js/game-session/../../../data/perks.json = data/perks.json
    perks_path = docs_js_dir / '..' / '..' / '..' / 'data' / 'perks.json'
    perks_path = perks_path.resolve()
    
    assert perks_path.exists(), f"Frontend cannot resolve perks.json at {perks_path}"
    
    with open(perks_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert 'perkTypes' in data, "Frontend perks.json is invalid"
    print(f"✓ Frontend can load perks.json from {perks_path}")

if __name__ == '__main__':
    print("Testing perks.json loading...\n")
    
    test_perks_json_exists()
    test_perks_json_valid()
    test_perks_no_bom()
    test_perks_files_in_sync()
    test_scangtech_jptech_exist()
    test_api_can_load_perks()
    test_frontend_can_load_perks()
    
    print("\n✅ All perks.json tests passed!")

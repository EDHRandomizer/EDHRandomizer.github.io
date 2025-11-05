"""
Test the pack generator locally to debug issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from index import generate_packs

print("=" * 60)
print("Testing Pack Generator Locally")
print("=" * 60 + "\n")

# Test 1: Simple pack with default config
print("Test 1: Generate pack for Atraxa with default config")
print("-" * 60)
try:
    config = {
        "packTypes": [
            {
                "name": "Test Pack",
                "count": 1,
                "slots": [
                    {"cardType": "weighted", "budget": "expensive", "bracket": 2, "count": 1},
                    {"cardType": "weighted", "budget": "budget", "bracket": 2, "count": 5},
                    {"cardType": "lands", "budget": "any", "bracket": 2, "count": 3}
                ]
            }
        ]
    }
    
    print("Calling generate_packs...")
    packs = generate_packs("atraxa-grand-unifier", config, bracket=2)
    
    print(f"✓ Packs generated: {len(packs)}")
    for pack in packs:
        print(f"\n  Pack: {pack['name']}")
        print(f"  Cards ({len(pack['cards'])}):")
        for i, card in enumerate(pack['cards'], 1):
            print(f"    {i}. {card}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Local test complete!")
print("=" * 60)


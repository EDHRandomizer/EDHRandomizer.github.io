"""
Test pack generation locally with a specific pack code configuration
"""
import sys
sys.path.insert(0, 'api')

from pack_generator import generate_packs
import json

# Pack config from FRHQTISL
commander_slug = "ardyn-the-usurper"
bracket = 2

config = {
    "packTypes": [
        {
            "count": 5,
            "slots": [
                {"cardType": "weighted", "budget": "expensive", "bracket": "any", "count": 1},
                {"cardType": "weighted", "budget": "budget", "bracket": "any", "count": 11},
                {"cardType": "lands", "budget": "any", "bracket": "any", "count": 3}
            ]
        },
        {
            "name": "Bracket 3",
            "count": 1,
            "slots": [
                {"cardType": "weighted", "budget": "expensive", "bracket": "3", "count": 1},
                {"cardType": "weighted", "budget": "budget", "bracket": "3", "count": 11},
                {"cardType": "lands", "budget": "any", "bracket": "any", "count": 3}
            ]
        },
        {
            "name": "Expensive Lands",
            "source": "edhrec",
            "count": 1,
            "useCommanderColorIdentity": True,
            "slots": [
                {"cardType": "lands", "budget": "expensive", "bracket": "any", "count": 15}
            ]
        }
    ]
}

print(f"Testing pack generation for: {commander_slug}")
print(f"Bracket: {bracket}")
print(f"\nPack configuration:")
print(json.dumps(config, indent=2))
print("\n" + "="*80 + "\n")

try:
    packs = generate_packs(commander_slug, config, bracket=bracket)
    
    print(f"✅ Generated {len(packs)} packs:\n")
    
    for i, pack in enumerate(packs, 1):
        pack_name = pack.get('name', 'Unknown')
        cards = pack.get('cards', [])
        card_count = len(cards)
        
        status = "✅" if card_count == 15 else f"⚠️  ({card_count}/15)"
        print(f"{status} Pack {i}: {pack_name}")
        print(f"     Cards: {card_count}")
        
        if cards:
            print(f"     First 5: {cards[:5]}")
            if card_count < 15:
                print(f"     All cards: {cards}")
        else:
            print(f"     ❌ NO CARDS!")
        print()
    
    # Summary
    total_cards = sum(len(pack.get('cards', [])) for pack in packs)
    print("="*80)
    print(f"SUMMARY:")
    print(f"  Total packs: {len(packs)}")
    print(f"  Total cards: {total_cards}")
    print(f"  Average cards per pack: {total_cards / len(packs):.1f}")
    
    # Check if all packs have 15 cards
    all_full = all(len(pack.get('cards', [])) == 15 for pack in packs)
    if all_full:
        print(f"\n✅ All packs have exactly 15 cards!")
    else:
        short_packs = [p for p in packs if len(p.get('cards', [])) < 15]
        print(f"\n⚠️  {len(short_packs)} pack(s) have fewer than 15 cards:")
        for pack in short_packs:
            print(f"     - {pack.get('name')}: {len(pack.get('cards', []))} cards")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

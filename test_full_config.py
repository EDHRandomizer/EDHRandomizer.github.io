"""
Test full pack configuration like what would be generated in a real session
"""
import requests
import json

# Full config from a session with perks
commander_slug = "ardyn-the-usurper"
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

print(f"Testing FULL config deployment...")
print(f"Commander: {commander_slug}\n")

# Make request to Vercel API
url = "https://edhrandomizer-api.vercel.app/api/generate-packs"
payload = {
    "commander_url": f"https://edhrec.com/commanders/{commander_slug}",
    "config": config,
    "bracket": 2
}

try:
    print(f"Sending request to: {url}")
    response = requests.post(url, json=payload, timeout=60)
    
    print(f"Status: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        packs = data.get('packs', [])
        
        print(f"✅ Generated {len(packs)} pack(s):\n")
        
        all_15 = True
        for i, pack in enumerate(packs, 1):
            pack_name = pack.get('name', 'Unknown')
            cards = pack.get('cards', [])
            card_count = len(cards)
            
            if card_count != 15:
                all_15 = False
            
            status = "✅" if card_count == 15 else f"❌ ({card_count}/15)"
            print(f"{status} Pack {i}: {pack_name}")
            print(f"     Cards: {card_count}")
            if card_count < 15:
                print(f"     All cards: {cards}")
            else:
                print(f"     First 5: {cards[:5]}")
            print()
        
        print("="*80)
        if all_15:
            print("✅ ALL PACKS HAVE 15 CARDS - FIX IS WORKING!")
        else:
            print("❌ SOME PACKS HAVE < 15 CARDS - FIX NOT WORKING ON DEPLOYED API")
            print("\nThis might mean:")
            print("  1. Vercel is still caching old code")
            print("  2. The fix didn't fully deploy")
            print("  3. There's an issue with the pack generation logic")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

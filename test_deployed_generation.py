"""
Test the deployed pack generation API directly
"""
import requests
import json

# Test the pack generation endpoint with the config from FRHQTISL
commander_slug = "ardyn-the-usurper"
config = {
    "packTypes": [
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

print(f"Testing deployed API pack generation...")
print(f"Commander: {commander_slug}")
print(f"Config: {json.dumps(config, indent=2)}\n")

# Make request to Vercel API
url = "https://edhrandomizer-api.vercel.app/api/generate-packs"
payload = {
    "commander_url": f"https://edhrec.com/commanders/{commander_slug}",
    "config": config,
    "bracket": 2
}

try:
    print(f"Sending request to: {url}")
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Status: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        packs = data.get('packs', [])
        
        print(f"✅ Generated {len(packs)} pack(s):\n")
        
        for i, pack in enumerate(packs, 1):
            pack_name = pack.get('name', 'Unknown')
            cards = pack.get('cards', [])
            card_count = len(cards)
            
            status = "✅" if card_count == 15 else f"⚠️  ({card_count}/15)"
            print(f"{status} Pack {i}: {pack_name}")
            print(f"     Cards: {card_count}")
            
            if cards:
                print(f"     Cards: {cards}")
            else:
                print(f"     ❌ NO CARDS!")
            print()
        
        if len(packs) > 0 and len(packs[0].get('cards', [])) == 15:
            print("✅ UTILITY LANDS FIX IS DEPLOYED!")
        else:
            print("❌ Utility lands fix NOT deployed yet - Vercel may still be building")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

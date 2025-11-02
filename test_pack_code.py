"""
Test pack code API endpoint
Usage: python test_pack_code.py <PACK_CODE>
Example: python test_pack_code.py N6J9EEB4
"""

import requests
import json
import sys

def test_pack_code(pack_code):
    """Test fetching pack data from the API"""
    
    # Sanitize pack code (uppercase, remove spaces)
    pack_code = pack_code.strip().upper().replace(' ', '')
    
    print(f"Testing pack code: {pack_code}")
    print(f"Length: {len(pack_code)} characters")
    
    if len(pack_code) != 8:
        print(f"❌ Invalid pack code length! Expected 8 characters, got {len(pack_code)}")
        return
    
    print("-" * 60)
    
    # API URL
    api_url = f"https://edhrandomizer-api.vercel.app/api/sessions/pack/{pack_code}"
    print(f"Fetching from: {api_url}")
    print("-" * 60)
    
    try:
        # Make request
        response = requests.get(api_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)} chars")
        print("-" * 60)
        
        if response.status_code == 404:
            print("❌ Pack code not found!")
            print("\nPossible reasons:")
            print("  - Pack code doesn't exist")
            print("  - Session expired (24 hour TTL)")
            print("  - Vercel function restarted (in-memory sessions lost)")
            print("\nResponse body:")
            print(response.text)
            return
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        # Parse JSON
        try:
            data = response.json()
            print("✅ Successfully parsed JSON response\n")
            
            # Display data
            print("Commander URL:")
            print(f"  {data.get('commanderUrl', 'N/A')}")
            print()
            
            print("Pack Config:")
            if 'config' in data:
                config = data['config']
                print(f"  Pack Types: {len(config.get('packTypes', []))}")
                for i, pack_type in enumerate(config.get('packTypes', []), 1):
                    print(f"    {i}. {pack_type}")
                print()
            else:
                print("  N/A")
                print()
            
            print("Powerups:")
            if 'powerups' in data and data['powerups']:
                for i, powerup in enumerate(data['powerups'], 1):
                    name = powerup.get('name', 'Unknown')
                    desc = powerup.get('description', '')
                    print(f"  {i}. {name}")
                    if desc:
                        print(f"     {desc}")
            else:
                print("  No powerups")
            print()
            
            print("-" * 60)
            print("Full JSON Response:")
            print(json.dumps(data, indent=2))
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Response text: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 10 seconds")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check your internet connection")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pack_code.py <PACK_CODE>")
        print("Example: python test_pack_code.py N6J9EEB4")
        sys.exit(1)
    
    pack_code = sys.argv[1]
    test_pack_code(pack_code)

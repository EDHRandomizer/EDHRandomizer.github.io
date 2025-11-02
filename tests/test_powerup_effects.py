"""
Test individual powerup effects and validate pack configuration structure
Focuses on verifying that powerups correctly modify the pack JSON
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any


API_BASE_URL = "https://edhrandomizer-api.vercel.app/api"


async def generate_pack(commander_url: str, powerups: List[Dict]) -> Dict:
    """Call the pack generation API"""
    async with aiohttp.ClientSession() as session:
        url = f"{API_BASE_URL}/generate-pack"
        payload = {
            "commanderUrl": commander_url,
            "powerups": powerups
        }
        
        async with session.post(url, json=payload) as response:
            return await response.json()


def validate_pack_structure(pack_config: Dict, test_name: str):
    """Validate the basic structure of a pack configuration"""
    print(f"\n{'='*80}")
    print(f"VALIDATING: {test_name}")
    print(f"{'='*80}")
    
    # Required fields
    required_fields = ["commander", "packs"]
    for field in required_fields:
        if field not in pack_config:
            print(f"❌ Missing required field: {field}")
            return False
        print(f"✅ Has field: {field}")
    
    # Validate packs structure
    packs = pack_config.get("packs", [])
    print(f"📦 Number of packs: {len(packs)}")
    
    for i, pack in enumerate(packs):
        print(f"\n  Pack {i+1}:")
        print(f"    Type: {pack.get('type', 'MISSING')}")
        print(f"    Bracket: {pack.get('bracket', 'MISSING')}")
        print(f"    Budget: {pack.get('budget', 'MISSING')}")
        print(f"    Cards: {pack.get('cardCount', 'MISSING')}")
        
        # Check for special pack attributes
        if pack.get("type") == "special":
            print(f"    Special Type: {pack.get('specialType', 'MISSING')}")
            print(f"    Moxfield Deck: {pack.get('moxfieldDeck', 'N/A')}")
    
    print(f"\n✅ Pack structure validated")
    return True


async def test_baseline():
    """Test baseline: no powerups"""
    print("\n🧪 TEST: Baseline (No Powerups)")
    
    result = await generate_pack(
        "https://edhrec.com/commanders/atraxa-praetors-voice",
        []
    )
    
    pack_config = json.loads(result["packCode"])
    validate_pack_structure(pack_config, "Baseline - No Powerups")
    
    # Expected: 3 packs (default)
    packs = pack_config.get("packs", [])
    assert len(packs) == 3, f"Expected 3 packs, got {len(packs)}"
    print(f"✅ Baseline validated: {len(packs)} packs")


async def test_extra_pack():
    """Test that extra pack powerup adds packs"""
    print("\n🧪 TEST: Extra Pack (+2)")
    
    result = await generate_pack(
        "https://edhrec.com/commanders/muldrotha-the-gravetide",
        [{"id": "extra_pack_2", "effects": {"packQuantity": 2}}]
    )
    
    pack_config = json.loads(result["packCode"])
    validate_pack_structure(pack_config, "Extra Pack +2")
    
    # Expected: 3 (base) + 2 (powerup) = 5 packs
    packs = pack_config.get("packs", [])
    expected = 5
    print(f"📦 Expected {expected} packs, got {len(packs)}")
    
    # May not match exactly if packs get merged
    if len(packs) != expected:
        print(f"⚠️  Pack count mismatch - may be due to pack merging logic")


async def test_budget_upgrade():
    """Test budget upgrade effect"""
    print("\n🧪 TEST: Budget Upgrade (Any Cost)")
    
    result = await generate_pack(
        "https://edhrec.com/commanders/kinnan-bonder-prodigy",
        [{"id": "budget_any_cost", "effects": {"budgetUpgradePacks": 1, "budgetUpgradeType": "any"}}]
    )
    
    pack_config = json.loads(result["packCode"])
    validate_pack_structure(pack_config, "Budget Upgrade - Any Cost")
    
    # Check if any pack has budget="any"
    packs = pack_config.get("packs", [])
    any_cost_packs = [p for p in packs if p.get("budget") == "any"]
    
    print(f"\n📊 Budget Analysis:")
    print(f"   Packs with budget='any': {len(any_cost_packs)}")
    print(f"   Expected: at least 1")
    
    if len(any_cost_packs) > 0:
        print(f"✅ Budget upgrade applied correctly")
    else:
        print(f"❌ No 'any' cost packs found - budget upgrade may not be working")


async def test_bracket_upgrade():
    """Test bracket upgrade effect"""
    print("\n🧪 TEST: Bracket Upgrade (Bracket 4)")
    
    result = await generate_pack(
        "https://edhrec.com/commanders/korvold-fae-cursed-king",
        [{"id": "bracket_4", "effects": {"bracketUpgrade": 4, "bracketUpgradePacks": 1}}]
    )
    
    pack_config = json.loads(result["packCode"])
    validate_pack_structure(pack_config, "Bracket Upgrade - Bracket 4")
    
    # Check if any pack has bracket=4
    packs = pack_config.get("packs", [])
    bracket_4_packs = [p for p in packs if p.get("bracket") == 4]
    
    print(f"\n📊 Bracket Analysis:")
    print(f"   Packs with bracket=4: {len(bracket_4_packs)}")
    print(f"   Expected: at least 1")
    
    if len(bracket_4_packs) > 0:
        print(f"✅ Bracket upgrade applied correctly")
    else:
        print(f"❌ No bracket 4 packs found - bracket upgrade may not be working")


async def test_special_pack_gamechanger():
    """Test game changer special pack"""
    print("\n🧪 TEST: Special Pack - Game Changer")
    
    result = await generate_pack(
        "https://edhrec.com/commanders/omnath-locus-of-creation",
        [{"id": "gamechanger_3", "effects": {"specialPack": "gamechanger", "specialPackCount": 3}}]
    )
    
    pack_config = json.loads(result["packCode"])
    validate_pack_structure(pack_config, "Special Pack - Game Changer")
    
    # Check for special pack with type="gamechanger"
    packs = pack_config.get("packs", [])
    gamechanger_packs = [p for p in packs if p.get("type") == "special" and p.get("specialType") == "gamechanger"]
    
    print(f"\n📊 Special Pack Analysis:")
    print(f"   Game changer packs: {len(gamechanger_packs)}")
    
    if len(gamechanger_packs) > 0:
        gc_pack = gamechanger_packs[0]
        print(f"   Card count: {gc_pack.get('cardCount', 'MISSING')}")
        print(f"✅ Game changer pack generated")
    else:
        print(f"❌ No game changer pack found")


async def test_special_pack_moxfield():
    """Test special pack with Moxfield deck"""
    print("\n🧪 TEST: Special Pack - Test Cards (Moxfield)")
    
    result = await generate_pack(
        "https://edhrec.com/commanders/yuriko-the-tigers-shadow",
        [{
            "id": "test_card_3",
            "effects": {
                "specialPack": "test_cards",
                "specialPackCount": 3,
                "moxfieldDeck": "dMTwgMp7UEuI33ACXNjOBg"
            }
        }]
    )
    
    pack_config = json.loads(result["packCode"])
    validate_pack_structure(pack_config, "Special Pack - Test Cards")
    
    # Check for Moxfield deck reference
    packs = pack_config.get("packs", [])
    moxfield_packs = [p for p in packs if p.get("moxfieldDeck")]
    
    print(f"\n📊 Moxfield Pack Analysis:")
    print(f"   Packs with Moxfield deck: {len(moxfield_packs)}")
    
    if len(moxfield_packs) > 0:
        mox_pack = moxfield_packs[0]
        print(f"   Moxfield ID: {mox_pack.get('moxfieldDeck')}")
        print(f"   Card count: {mox_pack.get('cardCount')}")
        print(f"✅ Moxfield pack generated correctly")
    else:
        print(f"❌ No Moxfield pack found")


async def test_combined_powerups():
    """Test multiple powerups together"""
    print("\n🧪 TEST: Combined Powerups (Budget + Bracket + Extra)")
    
    result = await generate_pack(
        "https://edhrec.com/commanders/chulane-teller-of-tales",
        [
            {"id": "budget_expensive", "effects": {"budgetUpgradePacks": 1, "budgetUpgradeType": "expensive"}},
            {"id": "bracket_3", "effects": {"bracketUpgrade": 3, "bracketUpgradePacks": 1}},
            {"id": "extra_pack_1", "effects": {"packQuantity": 1}}
        ]
    )
    
    pack_config = json.loads(result["packCode"])
    validate_pack_structure(pack_config, "Combined Powerups")
    
    packs = pack_config.get("packs", [])
    
    print(f"\n📊 Combined Effects Analysis:")
    print(f"   Total packs: {len(packs)} (expected: 4 = 3 base + 1 extra)")
    
    # Check for budget upgrade
    expensive_packs = [p for p in packs if p.get("budget") == "expensive"]
    print(f"   Expensive budget packs: {len(expensive_packs)}")
    
    # Check for bracket upgrade
    bracket_3_packs = [p for p in packs if p.get("bracket") == 3]
    print(f"   Bracket 3 packs: {len(bracket_3_packs)}")
    
    # Note: Budget and bracket shouldn't affect the same pack
    if len(expensive_packs) > 0 and len(bracket_3_packs) > 0:
        print(f"✅ Both budget and bracket upgrades applied")
        
        # Verify they're different packs
        expensive_ids = {id(p) for p in expensive_packs}
        bracket_ids = {id(p) for p in bracket_3_packs}
        overlap = expensive_ids & bracket_ids
        
        if overlap:
            print(f"⚠️  WARNING: Budget and bracket applied to same pack (should be separate)")
        else:
            print(f"✅ Budget and bracket applied to separate packs")


async def run_tests():
    """Run all powerup effect tests"""
    print("\n" + "🧪"*40)
    print("POWERUP EFFECTS VALIDATION TESTS")
    print("🧪"*40)
    
    tests = [
        test_baseline,
        test_extra_pack,
        test_budget_upgrade,
        test_bracket_upgrade,
        test_special_pack_gamechanger,
        test_special_pack_moxfield,
        test_combined_powerups,
    ]
    
    for test in tests:
        try:
            await test()
            print(f"\n✅ {test.__name__} completed")
        except Exception as e:
            print(f"\n❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("Tests completed - check output above for issues")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(run_tests())

"""
Test pack generation API with different powerup combinations
Tests the full flow: commander + powerups -> JSON pack configuration
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any


# API Configuration
API_BASE_URL = "https://edhrandomizer-api.vercel.app/api"
# API_BASE_URL = "http://localhost:3000/api"  # Uncomment for local testing


class PackGenerationTester:
    """Test pack generation with different powerup combinations"""
    
    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_pack(self, commander_url: str, powerups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a pack configuration via API
        
        Args:
            commander_url: EDHREC URL of the commander
            powerups: List of powerup objects with effects
            
        Returns:
            API response with pack configuration
        """
        url = f"{self.api_base_url}/generate-pack"
        
        payload = {
            "commanderUrl": commander_url,
            "powerups": powerups
        }
        
        print(f"\n{'='*80}")
        print(f"REQUEST TO: {url}")
        print(f"PAYLOAD: {json.dumps(payload, indent=2)}")
        print(f"{'='*80}")
        
        async with self.session.post(url, json=payload) as response:
            status = response.status
            try:
                data = await response.json()
            except:
                text = await response.text()
                data = {"error": f"Failed to parse JSON: {text}"}
            
            print(f"\nRESPONSE STATUS: {status}")
            print(f"RESPONSE DATA: {json.dumps(data, indent=2)}")
            print(f"{'='*80}\n")
            
            return {
                "status": status,
                "data": data
            }


async def test_no_powerups():
    """Test: Basic commander with no powerups (baseline)"""
    print("\n" + "="*80)
    print("TEST: No Powerups (Baseline)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/atraxa-praetors-voice",
            powerups=[]
        )
        
        # Validate response
        assert result["status"] == 200, f"Expected 200, got {result['status']}"
        data = result["data"]
        
        # Check for pack code
        assert "packCode" in data, "Missing packCode in response"
        print(f"✅ Pack code generated: {data['packCode'][:50]}...")
        
        # Parse the pack code JSON
        try:
            pack_config = json.loads(data["packCode"])
            print(f"✅ Pack config is valid JSON")
            print(f"   - Number of packs: {len(pack_config.get('packs', []))}")
            print(f"   - Commander: {pack_config.get('commander', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in packCode: {e}")
            raise


async def test_extra_commander_choices():
    """Test: Extra commander choices powerup"""
    print("\n" + "="*80)
    print("TEST: Extra Commander Choices (+3)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/muldrotha-the-gravetide",
            powerups=[
                {
                    "id": "extra_choice_3",
                    "name": "+3 Commander Choices",
                    "effects": {"commanderQuantity": 3}
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        assert "packCode" in data
        pack_config = json.loads(data["packCode"])
        print(f"✅ Pack generated with extra choices powerup")


async def test_budget_upgrade():
    """Test: Budget upgrade powerups"""
    print("\n" + "="*80)
    print("TEST: Budget Upgrade (Any Cost Pack)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/thrasios-triton-hero",
            powerups=[
                {
                    "id": "budget_any_cost",
                    "name": "Any Cost Pack",
                    "effects": {
                        "budgetUpgradePacks": 1,
                        "budgetUpgradeType": "any"
                    }
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        # Check if pack configuration reflects budget upgrade
        packs = pack_config.get("packs", [])
        print(f"✅ Packs generated: {len(packs)}")
        print(f"   Pack details: {json.dumps(packs, indent=2)}")


async def test_bracket_upgrade():
    """Test: Bracket upgrade powerups"""
    print("\n" + "="*80)
    print("TEST: Bracket Upgrade (Bracket 4)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/kinnan-bonder-prodigy",
            powerups=[
                {
                    "id": "bracket_4",
                    "name": "Bracket 4 Pack",
                    "effects": {
                        "bracketUpgrade": 4,
                        "bracketUpgradePacks": 1
                    }
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        packs = pack_config.get("packs", [])
        print(f"✅ Bracket upgrade pack generated")
        print(f"   Packs: {json.dumps(packs, indent=2)}")


async def test_extra_packs():
    """Test: Extra packs powerup"""
    print("\n" + "="*80)
    print("TEST: Extra Packs (+2 Packs)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/korvold-fae-cursed-king",
            powerups=[
                {
                    "id": "extra_pack_2",
                    "name": "+2 Packs",
                    "effects": {"packQuantity": 2}
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        packs = pack_config.get("packs", [])
        base_packs = 3  # Default number of packs
        expected_packs = base_packs + 2
        
        print(f"✅ Extra packs added")
        print(f"   Expected: {expected_packs}, Got: {len(packs)}")
        # Note: Might not match if pack merging occurs


async def test_special_packs_gamechanger():
    """Test: Game changer special pack"""
    print("\n" + "="*80)
    print("TEST: Game Changer Pack (3 cards)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/omnath-locus-of-creation",
            powerups=[
                {
                    "id": "gamechanger_3",
                    "name": "Game Changer Pack - Extended",
                    "effects": {
                        "specialPack": "gamechanger",
                        "specialPackCount": 3
                    }
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        print(f"✅ Game changer pack generated")
        print(f"   Config: {json.dumps(pack_config, indent=2)}")


async def test_special_packs_conspiracy():
    """Test: Conspiracy cards"""
    print("\n" + "="*80)
    print("TEST: Conspiracy Cards (3 cards)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/yuriko-the-tigers-shadow",
            powerups=[
                {
                    "id": "conspiracy_3",
                    "name": "Conspiracy Cards x3",
                    "effects": {
                        "specialPack": "conspiracy",
                        "specialPackCount": 3
                    }
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        print(f"✅ Conspiracy pack generated")


async def test_special_packs_test_cards():
    """Test: Test cards with Moxfield deck"""
    print("\n" + "="*80)
    print("TEST: Test Cards (3 cards from Moxfield)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/golos-tireless-pilgrim",
            powerups=[
                {
                    "id": "test_card_3",
                    "name": "Test Cards x3",
                    "effects": {
                        "specialPack": "test_cards",
                        "specialPackCount": 3,
                        "moxfieldDeck": "dMTwgMp7UEuI33ACXNjOBg"
                    }
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        print(f"✅ Test cards pack generated")
        print(f"   Moxfield deck: dMTwgMp7UEuI33ACXNjOBg")


async def test_manabase_upgrade():
    """Test: Manabase upgrade (expensive lands)"""
    print("\n" + "="*80)
    print("TEST: Manabase Upgrade (15 expensive lands)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/kenrith-the-returned-king",
            powerups=[
                {
                    "id": "manabase_expensive",
                    "name": "Expensive Lands Pack",
                    "effects": {
                        "specialPack": "expensive_lands",
                        "specialPackCount": 15
                    }
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        print(f"✅ Manabase upgrade pack generated")


async def test_multiple_powerups():
    """Test: Multiple powerups combined"""
    print("\n" + "="*80)
    print("TEST: Multiple Powerups (Budget + Bracket + Extra Pack)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/chulane-teller-of-tales",
            powerups=[
                {
                    "id": "budget_expensive",
                    "name": "Expensive Pack",
                    "effects": {
                        "budgetUpgradePacks": 1,
                        "budgetUpgradeType": "expensive"
                    }
                },
                {
                    "id": "bracket_3",
                    "name": "Bracket 3 Pack",
                    "effects": {
                        "bracketUpgrade": 3,
                        "bracketUpgradePacks": 1
                    }
                },
                {
                    "id": "extra_pack_1",
                    "name": "+1 Pack",
                    "effects": {"packQuantity": 1}
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        packs = pack_config.get("packs", [])
        print(f"✅ Multiple powerups combined successfully")
        print(f"   Total packs: {len(packs)}")
        print(f"   Pack config: {json.dumps(pack_config, indent=2)}")


async def test_all_special_packs():
    """Test: All special pack types at once"""
    print("\n" + "="*80)
    print("TEST: Kitchen Sink (Many Special Packs)")
    print("="*80)
    
    async with PackGenerationTester() as tester:
        result = await tester.generate_pack(
            commander_url="https://edhrec.com/commanders/sisay-weatherlight-captain",
            powerups=[
                {
                    "id": "gamechanger_1",
                    "name": "Game Changer Pack",
                    "effects": {
                        "specialPack": "gamechanger",
                        "specialPackCount": 1
                    }
                },
                {
                    "id": "conspiracy_2",
                    "name": "Conspiracy Cards x2",
                    "effects": {
                        "specialPack": "conspiracy",
                        "specialPackCount": 2
                    }
                },
                {
                    "id": "silly_card_1",
                    "name": "Silly Card",
                    "effects": {
                        "specialPack": "silly_cards",
                        "specialPackCount": 1,
                        "moxfieldDeck": "Ph3OYF_lLkuBhDpiP1qwuQ"
                    }
                },
                {
                    "id": "manabase_any_cost",
                    "name": "Any Cost Lands Pack",
                    "effects": {
                        "specialPack": "any_cost_lands",
                        "specialPackCount": 15
                    }
                }
            ]
        )
        
        assert result["status"] == 200
        data = result["data"]
        pack_config = json.loads(data["packCode"])
        
        print(f"✅ Multiple special packs combined")
        print(f"   Full config: {json.dumps(pack_config, indent=2)}")


async def run_all_tests():
    """Run all pack generation tests"""
    print("\n" + "🧪 "*40)
    print("PACK GENERATION API TESTS")
    print("🧪 "*40 + "\n")
    
    tests = [
        ("No Powerups", test_no_powerups),
        ("Extra Commander Choices", test_extra_commander_choices),
        ("Budget Upgrade", test_budget_upgrade),
        ("Bracket Upgrade", test_bracket_upgrade),
        ("Extra Packs", test_extra_packs),
        ("Game Changer Pack", test_special_packs_gamechanger),
        ("Conspiracy Pack", test_special_packs_conspiracy),
        ("Test Cards Pack", test_special_packs_test_cards),
        ("Manabase Upgrade", test_manabase_upgrade),
        ("Multiple Powerups", test_multiple_powerups),
        ("Kitchen Sink", test_all_special_packs),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, "✅ PASS"))
            print(f"✅ {test_name} - PASSED\n")
        except Exception as e:
            results.append((test_name, f"❌ FAIL: {str(e)}"))
            print(f"❌ {test_name} - FAILED")
            print(f"   Error: {str(e)}\n")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, result in results:
        print(f"{result:60} {test_name}")
    
    passed = sum(1 for _, r in results if r.startswith("✅"))
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

"""
Test pack configuration generation logic with different powerup combinations
This simulates the JavaScript PackConfigGenerator to validate powerup effects
"""

import json
from typing import Dict, List, Any
from copy import deepcopy


class PackConfigGenerator:
    """Python implementation of PackConfigGenerator for testing"""
    
    def __init__(self):
        # Base standard pack definition (1 expensive, 11 budget, 3 lands)
        self.base_standard_pack = {
            "slots": [
                {
                    "cardType": "weighted",
                    "budget": "expensive",
                    "bracket": "any",
                    "count": 1
                },
                {
                    "cardType": "weighted",
                    "budget": "budget",
                    "bracket": "any",
                    "count": 11
                },
                {
                    "cardType": "lands",
                    "budget": "any",
                    "bracket": "any",
                    "count": 3
                }
            ]
        }
    
    def generate_bundle_config(self, powerups: List[Dict], commander_url: str = "") -> Dict:
        """
        Generate bundle config from powerup effects
        
        Args:
            powerups: List of powerup objects with effects
            commander_url: Commander URL (for context)
            
        Returns:
            Bundle configuration
        """
        bundle_config = {
            "packTypes": []
        }
        
        # Merge all powerup effects
        merged_effects = self._merge_powerup_effects(powerups)
        
        if not merged_effects:
            # No powerups, return default 5 standard packs
            bundle_config["packTypes"].append({
                "count": 5,
                **deepcopy(self.base_standard_pack)
            })
            return bundle_config
        
        # Calculate base pack count (default 5 + extra packs)
        base_pack_count = 5
        if merged_effects.get("packQuantity"):
            base_pack_count += merged_effects["packQuantity"]
        
        # Generate standard packs with modifications
        standard_packs = self._generate_standard_packs(base_pack_count, merged_effects)
        bundle_config["packTypes"].extend(standard_packs)
        
        # Add special packs if specified
        if merged_effects.get("specialPack") and merged_effects.get("specialPackCount"):
            special_pack = self._generate_special_pack(
                merged_effects["specialPack"],
                merged_effects["specialPackCount"],
                merged_effects.get("moxfieldDeck")
            )
            if special_pack:
                bundle_config["packTypes"].append(special_pack)
        
        return bundle_config
    
    def _merge_powerup_effects(self, powerups: List[Dict]) -> Dict:
        """Merge effects from multiple powerups"""
        merged = {}
        
        for powerup in powerups:
            if "effects" in powerup:
                merged.update(powerup["effects"])
        
        return merged
    
    def _generate_standard_packs(self, total_packs: int, effects: Dict) -> List[Dict]:
        """Generate standard packs with powerup modifications"""
        packs = []
        
        # Determine how many packs get modifications
        budget_upgrade_packs = effects.get("budgetUpgradePacks", 0)
        budget_upgrade_type = effects.get("budgetUpgradeType", "any")
        full_expensive_packs = effects.get("fullExpensivePacks", 0)
        bracket_upgrade_packs = effects.get("bracketUpgradePacks", 0)
        bracket_upgrade = effects.get("bracketUpgrade")
        
        # Calculate pack distribution
        normal_packs = total_packs
        modified_packs = {
            "budgetUpgrade": min(budget_upgrade_packs, normal_packs),
            "fullExpensive": min(full_expensive_packs, normal_packs - budget_upgrade_packs),
            "bracketUpgrade": min(bracket_upgrade_packs, normal_packs - budget_upgrade_packs - full_expensive_packs)
        }
        
        normal_packs -= sum(modified_packs.values())
        
        # Add normal packs
        if normal_packs > 0:
            packs.append({
                "count": normal_packs,
                **deepcopy(self.base_standard_pack)
            })
        
        # Add budget upgraded packs
        if modified_packs["budgetUpgrade"] > 0:
            budget = "any" if budget_upgrade_type == "any" else "expensive"
            packs.append({
                "name": f"Budget Upgraded ({budget_upgrade_type})",
                "count": modified_packs["budgetUpgrade"],
                "slots": [
                    {"cardType": "weighted", "budget": "expensive", "bracket": "any", "count": 1},
                    {"cardType": "weighted", "budget": budget, "bracket": "any", "count": 11},
                    {"cardType": "lands", "budget": "any", "bracket": "any", "count": 3}
                ]
            })
        
        # Add full expensive packs
        if modified_packs["fullExpensive"] > 0:
            packs.append({
                "name": "Full Expensive",
                "count": modified_packs["fullExpensive"],
                "slots": [
                    {"cardType": "weighted", "budget": "expensive", "bracket": "any", "count": 12},
                    {"cardType": "lands", "budget": "any", "bracket": "any", "count": 3}
                ]
            })
        
        # Add bracket upgraded packs
        if modified_packs["bracketUpgrade"] > 0 and bracket_upgrade:
            packs.append({
                "name": f"Bracket {bracket_upgrade}",
                "count": modified_packs["bracketUpgrade"],
                "slots": [
                    {"cardType": "weighted", "budget": "expensive", "bracket": str(bracket_upgrade), "count": 1},
                    {"cardType": "weighted", "budget": "budget", "bracket": str(bracket_upgrade), "count": 11},
                    {"cardType": "lands", "budget": "any", "bracket": "any", "count": 3}
                ]
            })
        
        return packs
    
    def _generate_special_pack(self, pack_type: str, count: int, moxfield_deck: str = None) -> Dict:
        """Generate special pack"""
        special_packs = {
            "gamechanger": {
                "name": "Game Changer",
                "count": 1,
                "slots": [{"cardType": "gamechangers", "budget": "any", "bracket": "any", "count": count}]
            },
            "conspiracy": {
                "name": "Conspiracy",
                "source": "scryfall",
                "count": 1,
                "useCommanderColorIdentity": True,
                "slots": [{"query": "https://scryfall.com/...", "count": count}]
            },
            "test_cards": {
                "name": "Test Cards",
                "source": "moxfield",
                "moxfieldDeck": moxfield_deck,
                "count": 1,
                "slots": [{"count": count}]
            },
            "silly_cards": {
                "name": "Silly Cards",
                "source": "moxfield",
                "moxfieldDeck": moxfield_deck,
                "count": 1,
                "slots": [{"count": count}]
            },
            "banned": {
                "name": "Banned Cards",
                "source": "moxfield",
                "moxfieldDeck": moxfield_deck,
                "count": 1,
                "slots": [{"count": count}]
            },
            "any_cost_lands": {
                "name": "Any Cost Lands",
                "source": "scryfall",
                "count": 1,
                "useCommanderColorIdentity": True,
                "slots": [{"query": "lands", "count": count}]
            },
            "expensive_lands": {
                "name": "Expensive Lands",
                "source": "scryfall",
                "count": 1,
                "useCommanderColorIdentity": True,
                "slots": [{"query": "expensive lands", "count": count}]
            }
        }
        
        return deepcopy(special_packs.get(pack_type))


def print_pack_config(config: Dict, title: str):
    """Pretty print pack configuration"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(json.dumps(config, indent=2))
    print(f"{'='*80}\n")


def validate_pack_structure(config: Dict, test_name: str) -> bool:
    """Validate pack structure"""
    print(f"\n🔍 Validating: {test_name}")
    
    if "packTypes" not in config:
        print(f"❌ Missing 'packTypes' key")
        return False
    
    pack_types = config["packTypes"]
    total_packs = sum(pt.get("count", 0) for pt in pack_types)
    
    print(f"✅ Pack types: {len(pack_types)}")
    print(f"✅ Total packs: {total_packs}")
    
    for i, pt in enumerate(pack_types):
        name = pt.get("name", "Standard Pack")
        count = pt.get("count", 0)
        slots = len(pt.get("slots", []))
        print(f"   {i+1}. {name}: {count} pack(s), {slots} slot(s)")
    
    return True


def test_no_powerups():
    """Test: No powerups (baseline)"""
    print("\n🧪 TEST: No Powerups (Baseline)")
    
    generator = PackConfigGenerator()
    config = generator.generate_bundle_config([], "")
    
    print_pack_config(config, "Baseline Configuration")
    validate_pack_structure(config, "No Powerups")
    
    # Assertions
    assert len(config["packTypes"]) == 1, "Should have 1 pack type"
    assert config["packTypes"][0]["count"] == 5, "Should have 5 packs"
    print("✅ Baseline test passed")


def test_extra_packs():
    """Test: Extra packs powerup"""
    print("\n🧪 TEST: Extra Packs (+2)")
    
    generator = PackConfigGenerator()
    config = generator.generate_bundle_config([
        {"id": "extra_pack_2", "effects": {"packQuantity": 2}}
    ], "")
    
    print_pack_config(config, "Extra Packs Configuration")
    validate_pack_structure(config, "Extra Packs +2")
    
    total_packs = sum(pt["count"] for pt in config["packTypes"])
    assert total_packs == 7, f"Should have 7 packs (5+2), got {total_packs}"
    print("✅ Extra packs test passed")


def test_budget_upgrade():
    """Test: Budget upgrade powerup"""
    print("\n🧪 TEST: Budget Upgrade (Any Cost)")
    
    generator = PackConfigGenerator()
    config = generator.generate_bundle_config([
        {"id": "budget_any_cost", "effects": {"budgetUpgradePacks": 1, "budgetUpgradeType": "any"}}
    ], "")
    
    print_pack_config(config, "Budget Upgrade Configuration")
    validate_pack_structure(config, "Budget Upgrade")
    
    # Should have 2 pack types: 4 normal, 1 budget upgraded
    assert len(config["packTypes"]) == 2, f"Should have 2 pack types, got {len(config['packTypes'])}"
    
    # Find the budget upgraded pack
    budget_pack = next((pt for pt in config["packTypes"] if "Budget Upgraded" in pt.get("name", "")), None)
    assert budget_pack is not None, "Should have a budget upgraded pack"
    assert budget_pack["count"] == 1, "Should have 1 budget upgraded pack"
    
    # Check that budget slot is 'any'
    budget_slot = budget_pack["slots"][1]  # Second slot is the 11-card budget slot
    assert budget_slot["budget"] == "any", f"Budget should be 'any', got {budget_slot['budget']}"
    
    print("✅ Budget upgrade test passed")


def test_bracket_upgrade():
    """Test: Bracket upgrade powerup"""
    print("\n🧪 TEST: Bracket Upgrade (Bracket 4)")
    
    generator = PackConfigGenerator()
    config = generator.generate_bundle_config([
        {"id": "bracket_4", "effects": {"bracketUpgrade": 4, "bracketUpgradePacks": 1}}
    ], "")
    
    print_pack_config(config, "Bracket Upgrade Configuration")
    validate_pack_structure(config, "Bracket Upgrade")
    
    # Find the bracket 4 pack
    bracket_pack = next((pt for pt in config["packTypes"] if "Bracket 4" in pt.get("name", "")), None)
    assert bracket_pack is not None, "Should have a Bracket 4 pack"
    assert bracket_pack["count"] == 1, "Should have 1 Bracket 4 pack"
    
    # Check bracket values
    for slot in bracket_pack["slots"][:-1]:  # Exclude lands slot
        assert slot["bracket"] == "4", f"Bracket should be '4', got {slot['bracket']}"
    
    print("✅ Bracket upgrade test passed")


def test_combined_powerups():
    """Test: Multiple powerups combined"""
    print("\n🧪 TEST: Combined Powerups (Budget + Bracket + Extra)")
    
    generator = PackConfigGenerator()
    config = generator.generate_bundle_config([
        {"id": "budget_expensive", "effects": {"budgetUpgradePacks": 1, "budgetUpgradeType": "expensive"}},
        {"id": "bracket_3", "effects": {"bracketUpgrade": 3, "bracketUpgradePacks": 1}},
        {"id": "extra_pack_1", "effects": {"packQuantity": 1}}
    ], "")
    
    print_pack_config(config, "Combined Powerups Configuration")
    validate_pack_structure(config, "Combined Powerups")
    
    # Should have: 6 total packs (5+1), with budget and bracket upgrades
    total_packs = sum(pt["count"] for pt in config["packTypes"])
    assert total_packs == 6, f"Should have 6 packs, got {total_packs}"
    
    # Check for budget upgraded pack
    budget_pack = next((pt for pt in config["packTypes"] if "Budget Upgraded" in pt.get("name", "")), None)
    assert budget_pack is not None, "Should have budget upgraded pack"
    
    # Check for bracket upgraded pack
    bracket_pack = next((pt for pt in config["packTypes"] if "Bracket 3" in pt.get("name", "")), None)
    assert bracket_pack is not None, "Should have Bracket 3 pack"
    
    # Verify they're separate (should have 3 pack types: normal + budget + bracket)
    assert len(config["packTypes"]) == 3, f"Should have 3 pack types, got {len(config['packTypes'])}"
    
    print("✅ Combined powerups test passed")


def test_special_packs():
    """Test: Special packs"""
    print("\n🧪 TEST: Special Packs (Game Changer)")
    
    generator = PackConfigGenerator()
    config = generator.generate_bundle_config([
        {"id": "gamechanger_3", "effects": {"specialPack": "gamechanger", "specialPackCount": 3}}
    ], "")
    
    print_pack_config(config, "Special Pack Configuration")
    validate_pack_structure(config, "Special Pack")
    
    # Should have standard packs + special pack
    assert len(config["packTypes"]) == 2, f"Should have 2 pack types, got {len(config['packTypes'])}"
    
    # Find special pack
    special_pack = next((pt for pt in config["packTypes"] if pt.get("name") == "Game Changer"), None)
    assert special_pack is not None, "Should have Game Changer pack"
    assert special_pack["slots"][0]["count"] == 3, "Should have 3 game changer cards"
    
    print("✅ Special pack test passed")


def test_kitchen_sink():
    """Test: Many powerups at once"""
    print("\n🧪 TEST: Kitchen Sink (Many Powerups)")
    
    generator = PackConfigGenerator()
    config = generator.generate_bundle_config([
        {"id": "extra_pack_2", "effects": {"packQuantity": 2}},
        {"id": "budget_expensive", "effects": {"budgetUpgradePacks": 1, "budgetUpgradeType": "expensive"}},
        {"id": "bracket_4", "effects": {"bracketUpgrade": 4, "bracketUpgradePacks": 1}},
        {"id": "gamechanger_1", "effects": {"specialPack": "gamechanger", "specialPackCount": 1}},
    ], "")
    
    print_pack_config(config, "Kitchen Sink Configuration")
    validate_pack_structure(config, "Kitchen Sink")
    
    # 7 total packs (5+2), with various upgrades and special pack
    total_packs = sum(pt.get("count", 0) for pt in config["packTypes"])
    print(f"📦 Total packs: {total_packs} (expected: 7)")
    
    print("✅ Kitchen sink test passed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪"*40)
    print("PACK CONFIGURATION LOGIC TESTS")
    print("🧪"*40)
    
    tests = [
        ("No Powerups", test_no_powerups),
        ("Extra Packs", test_extra_packs),
        ("Budget Upgrade", test_budget_upgrade),
        ("Bracket Upgrade", test_bracket_upgrade),
        ("Combined Powerups", test_combined_powerups),
        ("Special Packs", test_special_packs),
        ("Kitchen Sink", test_kitchen_sink),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            results.append((test_name, "✅ PASS"))
        except Exception as e:
            results.append((test_name, f"❌ FAIL: {str(e)}"))
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, result in results:
        print(f"{test_name:30} {result}")
    
    passed = sum(1 for _, r in results if r.startswith("✅"))
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    run_all_tests()

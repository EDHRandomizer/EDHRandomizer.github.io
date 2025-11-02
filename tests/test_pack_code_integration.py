"""
Integration Test for Pack Code Generation
Tests the full flow: Create session → Roll powerups → Lock commander → Get pack code → Verify pack config

This test validates:
1. Session creation and powerup rolling
2. Pack code generation with actual powerup effects
3. API returns correct pack configuration matching powerup effects
4. All special pack types are properly included
5. Moxfield deck IDs are correctly passed through
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any

# API endpoint
API_BASE = "https://edhrandomizer-api.vercel.app/api/sessions"

class PackCodeIntegrationTest:
    """Integration test for pack code generation"""
    
    def __init__(self):
        self.session_code = None
        self.player_id = None
        self.pack_code = None
        
    async def create_session(self, session: aiohttp.ClientSession, powerups_count: int = 3) -> Dict[str, Any]:
        """Create a new session"""
        print(f"\n📝 Creating session with {powerups_count} powerups...")
        
        async with session.post(f"{API_BASE}/create", json={
            "playerName": "Integration Test",
            "powerupsCount": powerups_count
        }) as response:
            assert response.status == 200, f"Failed to create session: {response.status}"
            data = await response.json()
            
            self.session_code = data['sessionCode']
            self.player_id = data['playerId']
            
            print(f"✅ Session created: {self.session_code}")
            print(f"   Player ID: {self.player_id}")
            
            return data
    
    async def roll_powerups(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Roll powerups for all players"""
        print(f"\n🎲 Rolling powerups...")
        
        async with session.post(f"{API_BASE}/roll-powerups", json={
            "sessionCode": self.session_code,
            "playerId": self.player_id
        }) as response:
            assert response.status == 200, f"Failed to roll powerups: {response.status}"
            data = await response.json()
            
            # Get our player's powerups
            player = next(p for p in data['players'] if p['id'] == self.player_id)
            powerups = player['powerups']
            
            print(f"✅ Rolled {len(powerups)} powerups:")
            for i, powerup in enumerate(powerups, 1):
                print(f"   {i}. [{powerup['rarity'].upper():8}] {powerup['name']}")
                if powerup.get('effects'):
                    print(f"      Effects: {json.dumps(powerup['effects'], indent=14)}")
            
            return data
    
    async def lock_commander(self, session: aiohttp.ClientSession, commander_url: str = None) -> Dict[str, Any]:
        """Lock in a commander"""
        if not commander_url:
            commander_url = "https://edhrec.com/commanders/aragorn-the-uniter"
        
        print(f"\n🔒 Locking commander: {commander_url}")
        
        async with session.post(f"{API_BASE}/lock-commander", json={
            "sessionCode": self.session_code,
            "playerId": self.player_id,
            "commanderUrl": commander_url,
            "commanderData": {
                "name": "Aragorn, the Uniter",
                "colors": ["W", "U", "B", "R", "G"],
                "selectedCommanderIndex": 0
            }
        }) as response:
            assert response.status == 200, f"Failed to lock commander: {response.status}"
            data = await response.json()
            
            # Get pack code
            player = next(p for p in data['players'] if p['id'] == self.player_id)
            self.pack_code = player['packCode']
            
            print(f"✅ Commander locked")
            print(f"   Pack Code: {self.pack_code}")
            
            return data
    
    async def get_pack_config(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Get pack configuration by pack code"""
        print(f"\n📦 Fetching pack config for code: {self.pack_code}")
        
        async with session.get(f"{API_BASE}/pack/{self.pack_code}") as response:
            assert response.status == 200, f"Failed to get pack config: {response.status}"
            data = await response.json()
            
            print(f"✅ Pack config retrieved")
            print(f"   Commander URL: {data.get('commanderUrl', 'N/A')}")
            print(f"   Powerups: {len(data.get('powerups', []))}")
            print(f"   Pack Types: {len(data.get('config', {}).get('packTypes', []))}")
            
            return data
    
    def verify_pack_config(self, powerups: List[Dict], pack_data: Dict[str, Any]) -> List[str]:
        """Verify pack configuration matches powerup effects"""
        print(f"\n🔍 Verifying pack configuration...")
        
        errors = []
        config = pack_data.get('config', {})
        pack_types = config.get('packTypes', [])
        
        # Calculate expected effects from powerups
        expected_effects = self.calculate_expected_effects(powerups)
        
        print(f"\n📊 Expected Effects:")
        for key, value in expected_effects.items():
            if value:
                print(f"   {key}: {value}")
        
        # Verify base pack count
        total_packs = sum(pt.get('count', 0) for pt in pack_types)
        expected_total = 5 + expected_effects['packQuantity']
        
        print(f"\n📦 Pack Count Verification:")
        print(f"   Expected total packs: {expected_total}")
        print(f"   Actual total packs: {total_packs}")
        
        if total_packs != expected_total:
            errors.append(f"Pack count mismatch: expected {expected_total}, got {total_packs}")
        
        # Verify special packs
        if expected_effects['specialPacks']:
            print(f"\n🎁 Special Pack Verification:")
            for special_pack_info in expected_effects['specialPacks']:
                pack_type = special_pack_info['type']
                expected_count = special_pack_info['count']
                moxfield_deck = special_pack_info.get('moxfieldDeck')
                
                # Find this special pack in pack_types
                matching_pack = None
                for pt in pack_types:
                    # Match by name or source
                    if (pack_type in pt.get('name', '').lower() or 
                        (pt.get('source') == 'moxfield' and moxfield_deck)):
                        matching_pack = pt
                        break
                
                if not matching_pack:
                    errors.append(f"Special pack '{pack_type}' not found in pack config")
                    print(f"   ❌ Missing: {pack_type} (count: {expected_count})")
                else:
                    actual_count = matching_pack['slots'][0].get('count', 0)
                    print(f"   ✅ Found: {matching_pack.get('name', pack_type)}")
                    print(f"      Expected count: {expected_count}, Actual: {actual_count}")
                    
                    if actual_count != expected_count:
                        errors.append(f"Special pack '{pack_type}' count mismatch: expected {expected_count}, got {actual_count}")
                    
                    # Verify moxfieldDeck if present
                    if moxfield_deck:
                        actual_deck = matching_pack['slots'][0].get('moxfieldDeck')
                        print(f"      Expected Moxfield deck: {moxfield_deck}")
                        print(f"      Actual Moxfield deck: {actual_deck}")
                        
                        if actual_deck != moxfield_deck:
                            errors.append(f"Moxfield deck mismatch for '{pack_type}': expected {moxfield_deck}, got {actual_deck}")
        
        # Verify budget/bracket upgrades
        if expected_effects['budgetUpgradePacks'] > 0:
            budget_packs = [pt for pt in pack_types if 'Budget' in pt.get('name', '')]
            if not budget_packs:
                errors.append(f"Expected {expected_effects['budgetUpgradePacks']} budget upgrade packs, found 0")
            else:
                print(f"\n💰 Budget Upgrade Verification:")
                print(f"   Found {len(budget_packs)} budget upgrade pack(s)")
        
        if expected_effects['bracketUpgrade']:
            bracket_packs = [pt for pt in pack_types if 'Bracket' in pt.get('name', '')]
            if not bracket_packs:
                errors.append(f"Expected bracket {expected_effects['bracketUpgrade']} pack, found none")
            else:
                print(f"\n⬆️  Bracket Upgrade Verification:")
                print(f"   Found {len(bracket_packs)} bracket upgrade pack(s)")
        
        # Verify powerups array in response
        response_powerups = pack_data.get('powerups', [])
        print(f"\n🎯 Powerup Display Verification:")
        print(f"   Expected powerups in response: {len(powerups)}")
        print(f"   Actual powerups in response: {len(response_powerups)}")
        
        if len(response_powerups) != len(powerups):
            errors.append(f"Powerup count mismatch in response: expected {len(powerups)}, got {len(response_powerups)}")
        
        for i, powerup in enumerate(response_powerups, 1):
            print(f"   {i}. {powerup.get('name', 'Unknown')} ({powerup.get('rarity', 'unknown')})")
        
        return errors
    
    def calculate_expected_effects(self, powerups: List[Dict]) -> Dict[str, Any]:
        """Calculate expected combined effects from powerups"""
        effects = {
            'packQuantity': 0,
            'budgetUpgradePacks': 0,
            'bracketUpgrade': None,
            'specialPacks': [],
            'distributionShift': 0
        }
        
        for powerup in powerups:
            powerup_effects = powerup.get('effects', {})
            
            effects['packQuantity'] += powerup_effects.get('packQuantity', 0)
            effects['budgetUpgradePacks'] += powerup_effects.get('budgetUpgradePacks', 0)
            effects['distributionShift'] += powerup_effects.get('distributionShift', 0)
            
            if powerup_effects.get('bracketUpgrade'):
                if effects['bracketUpgrade'] is None or powerup_effects['bracketUpgrade'] > effects['bracketUpgrade']:
                    effects['bracketUpgrade'] = powerup_effects['bracketUpgrade']
            
            if powerup_effects.get('specialPack'):
                effects['specialPacks'].append({
                    'type': powerup_effects['specialPack'],
                    'count': powerup_effects.get('specialPackCount', 1),
                    'moxfieldDeck': powerup_effects.get('moxfieldDeck')
                })
        
        return effects
    
    async def run_test(self, powerups_count: int = 3, commander_url: str = None):
        """Run complete integration test"""
        print("=" * 80)
        print("🧪 PACK CODE INTEGRATION TEST")
        print("=" * 80)
        
        async with aiohttp.ClientSession() as session:
            try:
                # 1. Create session
                await self.create_session(session, powerups_count)
                
                # 2. Roll powerups
                session_data = await self.roll_powerups(session)
                player = next(p for p in session_data['players'] if p['id'] == self.player_id)
                powerups = player['powerups']
                
                # 3. Lock commander (triggers pack code generation)
                await self.lock_commander(session, commander_url)
                
                # 4. Get pack config
                pack_data = await self.get_pack_config(session)
                
                # 5. Verify pack config
                errors = self.verify_pack_config(powerups, pack_data)
                
                # Report results
                print("\n" + "=" * 80)
                if errors:
                    print("❌ TEST FAILED")
                    print("=" * 80)
                    print("\nErrors found:")
                    for i, error in enumerate(errors, 1):
                        print(f"  {i}. {error}")
                    return False
                else:
                    print("✅ TEST PASSED")
                    print("=" * 80)
                    print("\nAll verifications successful!")
                    print(f"  • Session: {self.session_code}")
                    print(f"  • Pack Code: {self.pack_code}")
                    print(f"  • Powerups: {len(powerups)}")
                    print(f"  • Pack Types: {len(pack_data['config']['packTypes'])}")
                    return True
                    
            except Exception as e:
                print(f"\n❌ TEST ERROR: {e}")
                import traceback
                traceback.print_exc()
                return False


async def test_basic_flow():
    """Test basic flow with 3 powerups"""
    test = PackCodeIntegrationTest()
    return await test.run_test(powerups_count=3)


async def test_many_powerups():
    """Test with maximum powerups to increase chance of special packs"""
    test = PackCodeIntegrationTest()
    return await test.run_test(powerups_count=5)


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "🧪" * 40)
    print("RUNNING ALL INTEGRATION TESTS")
    print("🧪" * 40 + "\n")
    
    results = []
    
    # Test 1: Basic flow
    print("\n📋 Test 1: Basic Flow (3 powerups)")
    results.append(await test_basic_flow())
    
    # Test 2: Many powerups
    print("\n📋 Test 2: Many Powerups (5 powerups)")
    results.append(await test_many_powerups())
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    # Run all tests
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

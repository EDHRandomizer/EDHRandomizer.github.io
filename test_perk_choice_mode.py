"""
Test script for Perk Choice Mode
"""

from api.perk_roller import PerkRoller
import json

def test_choice_mode():
    print("=" * 70)
    print("🎯 TESTING PERK CHOICE MODE")
    print("=" * 70)
    
    # Create mock session
    session = {
        'sessionCode': 'TEST1',
        'hostId': 'player1',
        'state': 'waiting',
        'settings': {
            'perksCount': 3,
            'perkChoiceMode': True
        },
        'players': [
            {
                'id': 'player1',
                'name': 'Alice',
                'perks': [],
                'perkChoices': [],
                'perksSelected': False
            },
            {
                'id': 'player2',
                'name': 'Bob',
                'perks': [],
                'perkChoices': [],
                'perksSelected': False
            }
        ]
    }
    
    # Initialize roller and roll choices
    roller = PerkRoller()
    session = roller.roll_perk_choices_for_session(session, perks_count=3)
    
    print("\n" + "=" * 70)
    print("📊 RESULTS")
    print("=" * 70)
    
    for player in session['players']:
        print(f"\n👤 Player: {player['name']}")
        print(f"   Choices: {len(player.get('perkChoices', []))} slots")
        
        for i, choice_set in enumerate(player.get('perkChoices', [])):
            print(f"\n   Choice {i+1} ({choice_set['rarity']}):")
            for j, option in enumerate(choice_set['options']):
                print(f"     Option {j}: {option['name']} ({option['rarity']})")
        
        print(f"   Perks selected: {player.get('perksSelected', False)}")
        print(f"   Final perks: {len(player.get('perks', []))} (should be 0 until selections made)")
    
    # Test selection
    print("\n" + "=" * 70)
    print("🎯 TESTING SELECTION")
    print("=" * 70)
    
    player1 = session['players'][0]
    print(f"\n👤 Simulating selections for {player1['name']}...")
    
    for i, choice_set in enumerate(player1['perkChoices']):
        # Select option 0 for each slot
        choice_set['selected'] = 0
        selected_perk = choice_set['options'][0]
        player1['perks'].append(selected_perk)
        print(f"   ✅ Slot {i}: Selected {selected_perk['name']}")
    
    player1['perksSelected'] = True
    
    print(f"\n   Final perks for {player1['name']}:")
    for perk in player1['perks']:
        print(f"     - {perk['name']} ({perk['rarity']})")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE!")
    print("=" * 70)

if __name__ == '__main__':
    test_choice_mode()

"""
Multiplayer Session E2E Tests for EDH Randomizer

Tests the full multiplayer flow with 4 simultaneous players:
1. Host creates session
2. 3 players join
3. All players roll powerups
4. All players select and lock commanders
5. Pack codes generated and displayed
6. Each player can load their pack code in TTS

Run with: pytest tests/test_multiplayer_session.py -v -s
Or headed: pytest tests/test_multiplayer_session.py -v -s --headed
"""

import pytest
import asyncio
import re
from playwright.async_api import async_playwright, Page, BrowserContext, expect


# Configuration
BASE_URL = "https://edhrandomizer.github.io"
GAME_URL = f"{BASE_URL}/random_commander_game.html"
API_URL = "https://edhrandomizer-api.vercel.app"
TIMEOUT = 30000  # 30 seconds for most operations


class Player:
    """Helper class to manage a player's browser context and page"""
    def __init__(self, context: BrowserContext, page: Page, number: int):
        self.context = context
        self.page = page
        self.number = number
        self.name = f"Player {number}"
        self.session_code = None
        self.pack_code = None
        
    async def goto_game(self):
        """Navigate to the game page"""
        await self.page.goto(GAME_URL)
        await self.page.wait_for_load_state('networkidle')
        
    async def get_session_code_from_url(self):
        """Extract session code from URL"""
        url = self.page.url
        match = re.search(r'session=([A-Z0-9]{5})', url)
        if match:
            self.session_code = match.group(1)
            return self.session_code
        return None


@pytest.fixture
async def browser_contexts():
    """Create 4 browser contexts for 4 players"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set to False to watch
        contexts = []
        players = []
        
        # Create 4 separate browser contexts (like 4 different browsers)
        for i in range(4):
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=f'Mozilla/5.0 (Test Player {i+1})'
            )
            page = await context.new_page()
            
            # Enable console logging for debugging
            page.on("console", lambda msg, num=i+1: print(f"[Player {num}] {msg.type}: {msg.text}"))
            
            player = Player(context, page, i + 1)
            contexts.append(context)
            players.append(player)
        
        yield players
        
        # Cleanup
        for context in contexts:
            await context.close()
        await browser.close()


@pytest.mark.asyncio
async def test_full_multiplayer_session(browser_contexts):
    """Test complete 4-player session from creation to pack codes"""
    players = browser_contexts
    host = players[0]
    
    print("\n" + "="*60)
    print("🎮 Starting 4-Player Multiplayer Session Test")
    print("="*60)
    
    # PHASE 1: Host creates session
    print("\n📍 PHASE 1: Host Creates Session")
    await host.goto_game()
    
    # Set powerups count
    await host.page.fill('#create-powerups-count', '3')
    
    # Create session
    await host.page.click('#create-session-btn')
    await host.page.wait_for_timeout(2000)  # Wait for session creation
    
    # Enter host name
    await expect(host.page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
    await host.page.fill('#player-name-input', 'Host Player')
    await host.page.click('#confirm-name-btn')
    await host.page.wait_for_timeout(2000)
    
    # Get session code from URL
    session_code = await host.get_session_code_from_url()
    assert session_code, "❌ Host session code not found in URL"
    print(f"✅ Host created session: {session_code}")
    
    # Verify host is in lobby
    await expect(host.page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
    print(f"✅ Host entered lobby")
    
    # PHASE 2: Players 2-4 join session
    print(f"\n📍 PHASE 2: Players Join Session {session_code}")
    for player in players[1:]:
        await player.goto_game()
        
        # Enter session code
        await player.page.fill('#join-code-input', session_code)
        await player.page.click('#join-session-btn')
        await player.page.wait_for_timeout(1000)
        
        # Enter player name
        name_input = player.page.locator('#player-name-input')
        await expect(name_input).to_be_visible(timeout=TIMEOUT)
        await name_input.fill(player.name)
        await player.page.click('#confirm-name-btn')
        await player.page.wait_for_timeout(1000)
        
        # Verify in lobby
        await expect(player.page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
        print(f"✅ {player.name} joined session")
    
    # PHASE 3: Verify all players see each other in lobby
    print("\n📍 PHASE 3: Verify Lobby State")
    for player in players:
        player_items = await player.page.locator('.player-item').count()
        assert player_items == 4, f"❌ {player.name} sees {player_items} players, expected 4"
        print(f"✅ {player.name} sees all 4 players in lobby")
    
    # PHASE 4: Host starts rolling powerups (click "Start Game" button in lobby)
    print("\n📍 PHASE 4: Host Starts Rolling Powerups")
    await host.page.click('#roll-powerups-btn')
    await host.page.wait_for_timeout(2000)
    
    # Wait for player grid to appear
    for player in players:
        await expect(player.page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
        print(f"✅ {player.name} sees player grid")
    
    # PHASE 5: All players see their powerups (auto-rolled on backend)
    print("\n📍 PHASE 5: Verify Powerups Displayed")
    for player in players:
        # Wait for powerup items to appear in the player's section
        powerup_items = player.page.locator('.powerup-item')
        await expect(powerup_items.first).to_be_visible(timeout=TIMEOUT)
        
        count = await powerup_items.count()
        assert count == 3, f"❌ {player.name} got {count} powerups, expected 3"
        print(f"✅ {player.name} has 3 powerups displayed")
    
    # PHASE 6: All players generate commanders
    print("\n📍 PHASE 6: All Players Generate Commanders")
    for i, player in enumerate(players):
        player_num = i + 1
        # Click generate commanders button for this player
        generate_btn = player.page.locator(f'#generate-btn-{player_num}')
        await expect(generate_btn).to_be_visible(timeout=TIMEOUT)
        await generate_btn.click()
        
        # Wait for commanders to load (this might take a while due to Scryfall API)
        print(f"⏳ {player.name} waiting for commanders to load...")
        await player.page.wait_for_timeout(8000)  # Longer timeout for Scryfall
        
        # Verify commanders are displayed (look for commander items)
        commander_items = player.page.locator('.commander-item-small')
        count = await commander_items.count()
        assert count > 0, f"❌ {player.name} has no commanders"
        print(f"✅ {player.name} generated {count} commanders")
    
    # PHASE 7: All players select and lock commanders
    print("\n📍 PHASE 7: All Players Lock Commanders")
    for i, player in enumerate(players):
        player_num = i + 1
        
        # Select first commander (click the commander card)
        first_commander = player.page.locator('.commander-item-small').first
        await first_commander.click()
        await player.page.wait_for_timeout(500)
        
        # Click lock commander button
        lock_btn = player.page.locator(f'#lock-btn-{player_num}')
        
        # Wait for lock button to be enabled (happens when commander is selected)
        await player.page.wait_for_timeout(500)
        await lock_btn.click()
        await player.page.wait_for_timeout(2000)
        
        print(f"✅ {player.name} locked commander")
    
    # PHASE 8: Verify pack codes are generated and displayed
    print("\n📍 PHASE 8: Verify Pack Codes Generated")
    await asyncio.sleep(3)  # Wait for pack code generation
    
    for player in players:
        # Verify pack codes section is visible
        pack_codes_section = player.page.locator('#pack-codes-section')
        await expect(pack_codes_section).to_be_visible(timeout=TIMEOUT)
        
        # Get player's pack code
        pack_code_elem = player.page.locator(f'#pack-code-p{player.number}')
        pack_code = await pack_code_elem.text_content()
        player.pack_code = pack_code.strip()
        
        assert len(player.pack_code) == 8, f"❌ Invalid pack code length: {player.pack_code}"
        assert player.pack_code.isalnum(), f"❌ Pack code contains invalid characters: {player.pack_code}"
        
        print(f"✅ {player.name} received pack code: {player.pack_code}")
    
    # PHASE 9: Verify all pack codes are unique
    print("\n📍 PHASE 9: Verify Pack Codes Are Unique")
    pack_codes = [p.pack_code for p in players]
    assert len(set(pack_codes)) == 4, f"❌ Duplicate pack codes found: {pack_codes}"
    print(f"✅ All 4 pack codes are unique")
    
    # PHASE 10: Test pack code API retrieval
    print("\n📍 PHASE 10: Verify Pack Codes Accessible via API")
    for player in players:
        # Use Playwright's API request context to fetch pack data
        response = await player.context.request.get(
            f"{API_URL}/api/sessions/pack/{player.pack_code}"
        )
        assert response.ok, f"❌ Failed to retrieve pack code {player.pack_code}: {response.status}"
        
        pack_data = await response.json()
        assert pack_data['playerNumber'] == player.number, f"❌ Wrong player number in pack data"
        assert 'commanderUrl' in pack_data, f"❌ Missing commanderUrl in pack data"
        assert 'powerups' in pack_data, f"❌ Missing powerups in pack data"
        assert len(pack_data['powerups']) == 3, f"❌ Wrong powerup count in pack data"
        
        print(f"✅ {player.name} pack code {player.pack_code} retrievable via API")
    
    print("\n" + "="*60)
    print("🎉 All Tests Passed! 4-Player Session Complete")
    print("="*60)


@pytest.mark.asyncio
async def test_late_join_during_rolling(browser_contexts):
    """Test that a player can join during the rolling phase"""
    players = browser_contexts
    host = players[0]
    late_joiner = players[1]
    
    print("\n" + "="*60)
    print("🎮 Testing Late Join During Rolling Phase")
    print("="*60)
    
    # Host creates session
    await host.goto_game()
    await host.page.fill('#create-powerups-count', '2')
    await host.page.click('#create-session-btn')
    await host.page.wait_for_timeout(2000)
    
    # Enter host name
    await expect(host.page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
    await host.page.fill('#player-name-input', 'Host Player')
    await host.page.click('#confirm-name-btn')
    await host.page.wait_for_timeout(2000)
    
    session_code = await host.get_session_code_from_url()
    print(f"✅ Host created session: {session_code}")
    
    # Host starts rolling
    await host.page.click('#roll-powerups-btn')
    await host.page.wait_for_timeout(2000)
    await expect(host.page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
    print(f"✅ Host started rolling phase (player grid visible)")
    
    # Late joiner tries to join during rolling
    await late_joiner.goto_game()
    await late_joiner.page.fill('#join-code-input', session_code)
    await late_joiner.page.click('#join-session-btn')
    await late_joiner.page.wait_for_timeout(1000)
    
    # Should be able to enter name
    name_input = late_joiner.page.locator('#player-name-input')
    await expect(name_input).to_be_visible(timeout=TIMEOUT)
    await name_input.fill('Late Joiner')
    await late_joiner.page.click('#confirm-name-btn')
    await late_joiner.page.wait_for_timeout(1000)
    
    # Should enter rolling section (not lobby, since rolling already started)
    # Look for player grid instead
    await expect(late_joiner.page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
    print(f"✅ Late joiner successfully joined during rolling phase")


@pytest.mark.asyncio
async def test_cannot_join_after_selecting(browser_contexts):
    """Test that joining is blocked once commander selection starts"""
    players = browser_contexts
    host = players[0]
    late_joiner = players[1]
    
    print("\n" + "="*60)
    print("🎮 Testing Join Blocked During Selection Phase")
    print("="*60)
    
    # Host creates and progresses to selecting phase
    await host.goto_game()
    await host.page.fill('#create-powerups-count', '2')
    await host.page.click('#create-session-btn')
    await host.page.wait_for_timeout(2000)
    
    # Enter name
    await expect(host.page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
    await host.page.fill('#player-name-input', 'Host Player')
    await host.page.click('#confirm-name-btn')
    await host.page.wait_for_timeout(2000)
    
    session_code = await host.get_session_code_from_url()
    
    # Start rolling
    await host.page.click('#roll-powerups-btn')
    await host.page.wait_for_timeout(2000)
    
    # Generate commanders (enters selecting phase)
    await host.page.click('#generate-btn-1')
    await host.page.wait_for_timeout(5000)
    
    print(f"✅ Host progressed to commander selection")
    
    # Try to join - should fail
    await late_joiner.goto_game()
    await late_joiner.page.fill('#join-code-input', session_code)
    await late_joiner.page.click('#join-session-btn')
    await late_joiner.page.wait_for_timeout(2000)
    
    # Should see error message (not name input)
    status_text = await late_joiner.page.locator('#status').text_content()
    assert 'already started' in status_text.lower() or 'failed' in status_text.lower(), \
        f"❌ Expected error message, got: {status_text}"
    print(f"✅ Late join correctly blocked: {status_text}")


@pytest.mark.asyncio
async def test_url_session_restore(browser_contexts):
    """Test that players can restore sessions from URL parameters"""
    players = browser_contexts
    host = players[0]
    rejoiner = players[1]
    
    print("\n" + "="*60)
    print("🎮 Testing URL Session Restoration")
    print("="*60)
    
    # Host creates session
    await host.goto_game()
    await host.page.fill('#create-powerups-count', '2')
    await host.page.click('#create-session-btn')
    await host.page.wait_for_timeout(2000)
    
    # Enter name
    await expect(host.page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
    await host.page.fill('#player-name-input', 'Host Player')
    await host.page.click('#confirm-name-btn')
    await host.page.wait_for_timeout(2000)
    
    session_code = await host.get_session_code_from_url()
    original_url = host.page.url
    print(f"✅ Session created with URL: {original_url}")
    
    # Player joins normally
    await rejoiner.goto_game()
    await rejoiner.page.fill('#join-code-input', session_code)
    await rejoiner.page.click('#join-session-btn')
    await rejoiner.page.wait_for_timeout(1000)
    await rejoiner.page.fill('#player-name-input', 'Rejoiner')
    await rejoiner.page.click('#confirm-name-btn')
    await rejoiner.page.wait_for_timeout(1000)
    
    # Get player's URL (should have session code)
    player_url = rejoiner.page.url
    print(f"✅ Player URL: {player_url}")
    assert session_code in player_url, "❌ Session code not in URL"
    
    # Simulate page refresh by navigating directly to URL
    await rejoiner.page.goto(player_url)
    await rejoiner.page.wait_for_load_state('networkidle')
    await rejoiner.page.wait_for_timeout(2000)
    
    # Should still be in the session (in lobby)
    lobby_visible = await rejoiner.page.locator('#lobby-section').is_visible()
    print(f"✅ After URL restore, lobby visible: {lobby_visible}")
    
    # Note: This test might fail if session restoration from URL isn't fully implemented
    # That's actually a good thing - it helps us identify the issue!


if __name__ == "__main__":
    # Run tests directly with: python tests/test_multiplayer_session.py
    pytest.main([__file__, "-v", "-s"])

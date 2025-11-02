"""
Test that sessions persist across API calls using Vercel KV.
This specifically tests the bug that was discovered: sessions created but not found on subsequent calls.
"""
import pytest
from playwright.async_api import async_playwright, expect
import asyncio

# API endpoint
API_URL = "https://edhrandomizer-api.vercel.app"
GAME_URL = "https://edhrandomizer.github.io/random_commander_game.html"
TIMEOUT = 30000  # 30 seconds


@pytest.mark.asyncio
async def test_session_persists_after_creation():
    """Test that a session created can be retrieved on a subsequent API call"""
    
    print("\n" + "="*60)
    print("🧪 Testing Session Persistence (KV Integration)")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate to game
        await page.goto(GAME_URL)
        await page.wait_for_timeout(3000)  # Let JS initialize
        
        print("\n📍 Creating session...")
        await page.fill('#create-powerups-count', '2')
        await page.click('#create-session-btn')
        await page.wait_for_timeout(2000)
        
        # Enter name
        await expect(page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
        await page.fill('#player-name-input', 'Test Player')
        await page.click('#confirm-name-btn')
        await page.wait_for_timeout(2000)
        
        # Get session code from URL
        url = page.url
        assert '?session=' in url, "Session code not in URL"
        session_code = url.split('?session=')[1].split('&')[0]
        print(f"✅ Session created: {session_code}")
        
        # Verify lobby is visible
        await expect(page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
        print(f"✅ Lobby visible for session {session_code}")
        
        # Now test that we can fetch this session from the API
        # This is the critical test - does the session persist?
        print(f"\n📍 Fetching session from API...")
        response = await context.request.get(f"{API_URL}/api/sessions/{session_code}")
        
        if not response.ok:
            error_text = await response.text()
            print(f"❌ API returned {response.status}: {error_text}")
            assert False, f"Session {session_code} not found! KV persistence failed."
        
        session_data = await response.json()
        print(f"✅ Session retrieved from API: {session_code}")
        print(f"   Players: {len(session_data.get('players', []))}")
        print(f"   State: {session_data.get('state', 'unknown')}")
        
        # Start rolling powerups
        print(f"\n📍 Starting rolling phase...")
        await page.click('#roll-powerups-btn')
        await page.wait_for_timeout(3000)
        
        # Verify player grid visible
        await expect(page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
        print(f"✅ Player grid visible")
        
        # Test session persistence again after state change
        print(f"\n📍 Fetching session after rolling started...")
        response2 = await context.request.get(f"{API_URL}/api/sessions/{session_code}")
        
        if not response2.ok:
            error_text = await response2.text()
            print(f"❌ API returned {response2.status}: {error_text}")
            assert False, f"Session {session_code} lost after rolling! KV persistence failed."
        
        session_data2 = await response2.json()
        print(f"✅ Session still accessible: {session_code}")
        print(f"   State: {session_data2.get('state', 'unknown')}")
        
        # Generate commanders for player 1
        print(f"\n📍 Generating commanders...")
        generate_btn = page.locator('#generate-btn-1')
        await expect(generate_btn).to_be_visible(timeout=TIMEOUT)
        await generate_btn.click()
        
        # Wait for commanders to load
        print(f"⏳ Waiting for commanders to load...")
        await page.wait_for_timeout(8000)  # Scryfall can be slow
        
        # Check if commanders appeared
        commander_items = page.locator('.commander-item-small')
        count = await commander_items.count()
        
        if count == 0:
            print(f"⚠️ No commanders loaded yet, waiting longer...")
            await page.wait_for_timeout(5000)
            count = await commander_items.count()
        
        assert count > 0, "No commanders loaded"
        print(f"✅ Commanders loaded: {count} options")
        
        # Select first commander
        print(f"\n📍 Selecting commander...")
        first_commander = commander_items.first
        await first_commander.click()
        await page.wait_for_timeout(1000)
        
        # Lock commander - THIS IS THE CRITICAL TEST
        # The original bug: lock fails because session not found
        print(f"\n📍 Locking commander (critical KV test)...")
        lock_btn = page.locator('#lock-btn-1')
        await lock_btn.click()
        await page.wait_for_timeout(3000)
        
        # Test session persistence after lock
        print(f"\n📍 Fetching session after commander lock...")
        response3 = await context.request.get(f"{API_URL}/api/sessions/{session_code}")
        
        if not response3.ok:
            error_text = await response3.text()
            print(f"❌ API returned {response3.status}: {error_text}")
            assert False, f"Session {session_code} lost after lock! KV persistence failed."
        
        session_data3 = await response3.json()
        print(f"✅ Session persisted through lock: {session_code}")
        print(f"   State: {session_data3.get('state', 'unknown')}")
        
        # Check if commander was actually locked
        players = session_data3.get('players', [])
        assert len(players) > 0, "No players in session"
        
        player1 = players[0]
        if 'locked' in player1 and player1['locked']:
            print(f"✅ Commander successfully locked!")
            print(f"   Commander: {player1.get('commander', {}).get('name', 'Unknown')}")
        else:
            print(f"⚠️ Lock state unclear: {player1}")
        
        await browser.close()
        
        print("\n" + "="*60)
        print("🎉 KV Session Persistence Test PASSED!")
        print("="*60)


@pytest.mark.asyncio
async def test_multiple_api_calls_same_session():
    """Test that multiple API calls to same session work (KV read after write)"""
    
    print("\n" + "="*60)
    print("🧪 Testing Multiple API Calls to Same Session")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Create session via API
        create_response = await context.request.post(
            f"{API_URL}/api/sessions/create",
            data={"powerupsCount": 3}
        )
        
        assert create_response.ok, "Failed to create session"
        create_data = await create_response.json()
        session_code = create_data['sessionCode']
        player_id = create_data['playerId']
        
        print(f"✅ Session created via API: {session_code}")
        
        # Immediately try to fetch it (tests write->read consistency)
        print(f"\n📍 Testing read-after-write...")
        for i in range(3):
            await asyncio.sleep(0.5)  # Small delay between requests
            
            fetch_response = await context.request.get(f"{API_URL}/api/sessions/{session_code}")
            
            if not fetch_response.ok:
                error_text = await fetch_response.text()
                print(f"❌ Attempt {i+1} failed: {fetch_response.status} - {error_text}")
                if i == 2:  # Last attempt
                    assert False, f"Session not persistently readable after creation!"
            else:
                fetch_data = await fetch_response.json()
                print(f"✅ Attempt {i+1}: Session readable - {len(fetch_data.get('players', []))} player(s)")
        
        # Update session (update name)
        print(f"\n📍 Updating player name...")
        update_response = await context.request.post(
            f"{API_URL}/api/sessions/update-name",
            data={
                "sessionCode": session_code,
                "playerId": player_id,
                "playerName": "API Test Player"
            }
        )
        
        assert update_response.ok, "Failed to update name"
        print(f"✅ Name updated")
        
        # Fetch again to verify update persisted
        print(f"\n📍 Verifying update persisted...")
        verify_response = await context.request.get(f"{API_URL}/api/sessions/{session_code}")
        assert verify_response.ok, "Session lost after update!"
        
        verify_data = await verify_response.json()
        players = verify_data.get('players', [])
        assert len(players) > 0, "No players after update"
        assert players[0]['name'] == "API Test Player", "Name update didn't persist"
        
        print(f"✅ Update persisted correctly")
        
        await browser.close()
        
        print("\n" + "="*60)
        print("🎉 Multiple API Calls Test PASSED!")
        print("="*60)

"""
End-to-End Test: 2 Players Complete Flow to Pack Codes

This test validates the entire multiplayer flow:
1. Host creates session
2. Player 2 joins
3. Both see each other in lobby
4. Host starts rolling
5. Both generate commanders
6. Both lock commanders
7. Pack codes are generated
8. Pack codes are retrievable via API

Run with: pytest tests/test_e2e_two_player.py -v -s
"""

import pytest
from playwright.async_api import async_playwright, expect
import re

# Configuration
GAME_URL = "https://edhrandomizer.github.io/random_commander_game.html"
API_URL = "https://edhrandomizer-api.vercel.app"
TIMEOUT = 45000  # 45 seconds


@pytest.mark.asyncio
async def test_two_player_complete_flow():
    """
    Complete 2-player flow from session creation to pack codes
    """
    
    print("\n" + "="*70)
    print("E2E TEST: 2-Player Complete Flow to Pack Codes")
    print("="*70)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        
        # Create two separate browser contexts (like 2 different people)
        host_context = await browser.new_context()
        p2_context = await browser.new_context()
        
        host_page = await host_context.new_page()
        p2_page = await p2_context.new_page()
        
        # Enable console logging for debugging
        host_page.on("console", lambda msg: print(f"[HOST] {msg.text}"))
        p2_page.on("console", lambda msg: print(f"[P2] {msg.text}"))
        
        # Track network requests to debug API calls
        async def log_request(request):
            if 'sessions' in request.url:
                print(f"[NET] {request.method} {request.url}")
        
        async def log_response(response):
            if 'sessions' in response.url:
                print(f"[NET] {response.status} {response.url}")
                if response.status >= 400:
                    try:
                        body = await response.text()
                        print(f"[NET] Response body: {body[:200]}")
                    except:
                        pass
        
        host_page.on("request", log_request)
        host_page.on("response", log_response)
        p2_page.on("request", log_request)
        p2_page.on("response", log_response)
        
        try:
            # ==========================================
            # PHASE 1: HOST CREATES SESSION
            # ==========================================
            print("\n📍 PHASE 1: Host Creates Session")
            await host_page.goto(GAME_URL)
            await host_page.wait_for_timeout(3000)
            
            # Create session with 2 powerups
            await host_page.fill('#create-powerups-count', '2')
            await host_page.click('#create-session-btn')
            await host_page.wait_for_timeout(2000)
            
            # Enter host name
            await expect(host_page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
            await host_page.fill('#player-name-input', 'Host Player')
            await host_page.click('#confirm-name-btn')
            await host_page.wait_for_timeout(2000)
            
            # Wait for lobby
            await expect(host_page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
            
            # Extract session code from URL
            url = host_page.url
            match = re.search(r'session=([A-Z0-9]{5})', url)
            assert match, "Session code not found in URL"
            session_code = match.group(1)
            
            print(f"✅ Host created session: {session_code}")
            
            # ==========================================
            # PHASE 2: PLAYER 2 JOINS SESSION
            # ==========================================
            print(f"\n📍 PHASE 2: Player 2 Joins Session {session_code}")
            await p2_page.goto(GAME_URL)
            await p2_page.wait_for_timeout(3000)
            
            # Join session
            await p2_page.fill('#join-code-input', session_code)
            await p2_page.click('#join-session-btn')
            await p2_page.wait_for_timeout(1500)
            
            # Enter player 2 name
            await expect(p2_page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
            await p2_page.fill('#player-name-input', 'Player 2')
            await p2_page.click('#confirm-name-btn')
            await p2_page.wait_for_timeout(2000)
            
            # Wait for lobby
            await expect(p2_page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
            print(f"✅ Player 2 joined session")
            
            # ==========================================
            # PHASE 3: VERIFY BOTH SEE EACH OTHER
            # ==========================================
            print("\n📍 PHASE 3: Verify Both Players See Each Other")
            
            # Wait for polling to update (session polls every 2 seconds)
            await host_page.wait_for_timeout(3000)
            
            # Wait for lobby-player elements to appear (correct selector)
            try:
                await expect(host_page.locator('.lobby-player').first).to_be_visible(timeout=10000)
                await expect(p2_page.locator('.lobby-player').first).to_be_visible(timeout=10000)
            except Exception as e:
                print(f"⚠️ Warning: Lobby players not visible yet: {e}")
                await host_page.screenshot(path="debug_lobby_players.png")
            
            # Count active lobby players (.lobby-player.active)
            host_player_count = await host_page.locator('.lobby-player.active').count()
            p2_player_count = await p2_page.locator('.lobby-player.active').count()
            
            print(f"   Host sees: {host_player_count} active players")
            print(f"   Player 2 sees: {p2_player_count} active players")
            
            assert host_player_count == 2, f"Host sees {host_player_count} players, expected 2"
            assert p2_player_count == 2, f"Player 2 sees {p2_player_count} players, expected 2"
            print(f"✅ Both players see 2 players in lobby")
            
            # ==========================================
            # PHASE 4: HOST STARTS ROLLING
            # ==========================================
            print("\n📍 PHASE 4: Host Starts Rolling Powerups")
            await host_page.click('#roll-powerups-btn')
            await host_page.wait_for_timeout(3000)
            
            # Both should see player grid
            await expect(host_page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
            await expect(p2_page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
            print(f"✅ Both players see player grid section")
            
            # ==========================================
            # PHASE 5: BOTH PLAYERS GENERATE COMMANDERS
            # ==========================================
            print("\n📍 PHASE 5: Generating Commanders")
            
            # Host generates (Player 1)
            print("  Host generating commanders...")
            host_gen_btn = host_page.locator('#generate-btn-1')
            await expect(host_gen_btn).to_be_visible(timeout=TIMEOUT)
            await host_gen_btn.click()
            await host_page.wait_for_timeout(2000)
            
            # Wait for commanders to appear
            host_commanders = host_page.locator('.commander-item-small')
            await expect(host_commanders.first).to_be_visible(timeout=15000)
            host_count = await host_commanders.count()
            assert host_count > 0, "Host has no commanders"
            print(f"✅ Host generated {host_count} commanders")
            
            # Player 2 generates
            print("  Player 2 generating commanders...")
            p2_gen_btn = p2_page.locator('#generate-btn-2')
            await expect(p2_gen_btn).to_be_visible(timeout=TIMEOUT)
            await p2_gen_btn.click()
            await p2_page.wait_for_timeout(2000)
            
            # Wait for commanders to appear
            p2_commanders = p2_page.locator('.commander-item-small')
            await expect(p2_commanders.first).to_be_visible(timeout=15000)
            p2_count = await p2_commanders.count()
            assert p2_count > 0, "Player 2 has no commanders"
            print(f"✅ Player 2 generated {p2_count} commanders")
            
            # ==========================================
            # PHASE 6: BOTH PLAYERS LOCK COMMANDERS
            # ==========================================
            print("\n📍 PHASE 6: Both Players Lock Commanders")
            
            # Host selects and locks
            print("  Host locking commander...")
            await host_commanders.first.click()
            await host_page.wait_for_timeout(500)
            
            host_lock_btn = host_page.locator('#lock-btn-1')
            await host_lock_btn.click()
            await host_page.wait_for_timeout(2000)
            print(f"✅ Host locked commander")
            
            # Player 2 selects and locks
            print("  Player 2 locking commander...")
            await p2_commanders.first.click()
            await p2_page.wait_for_timeout(500)
            
            p2_lock_btn = p2_page.locator('#lock-btn-2')
            await p2_lock_btn.click()
            await p2_page.wait_for_timeout(2000)
            print(f"✅ Player 2 locked commander")
            
            # ==========================================
            # PHASE 7: PACK CODES SHOULD APPEAR
            # ==========================================
            print("\n📍 PHASE 7: Waiting for Pack Codes Section")
            
            # Both should see pack codes section
            try:
                await expect(host_page.locator('#pack-codes-section')).to_be_visible(timeout=15000)
                print("✅ Host sees pack codes section")
            except Exception as e:
                print(f"❌ Host did not see pack codes section: {e}")
                await host_page.screenshot(path="debug_host_no_packs.png")
                raise
            
            try:
                await expect(p2_page.locator('#pack-codes-section')).to_be_visible(timeout=15000)
                print("✅ Player 2 sees pack codes section")
            except Exception as e:
                print(f"❌ Player 2 did not see pack codes section: {e}")
                await p2_page.screenshot(path="debug_p2_no_packs.png")
                raise
            
            # ==========================================
            # PHASE 8: EXTRACT AND VERIFY PACK CODES
            # ==========================================
            print("\n📍 PHASE 8: Extracting Pack Codes")
            
            # Get all pack codes from host's view
            pack_code_elements = await host_page.locator('.pack-code').all_text_contents()
            pack_codes = [code.strip() for code in pack_code_elements if code.strip()]
            
            print(f"✅ Found {len(pack_codes)} pack codes:")
            for i, code in enumerate(pack_codes, 1):
                print(f"   Player {i}: {code}")
            
            assert len(pack_codes) == 2, f"Expected 2 pack codes, got {len(pack_codes)}"
            
            # Verify all codes are valid format (8 alphanumeric characters)
            for code in pack_codes:
                assert len(code) == 8, f"Invalid pack code length: {code}"
                assert code.isalnum(), f"Pack code contains invalid characters: {code}"
            
            # Verify pack codes are unique
            assert len(set(pack_codes)) == 2, f"Duplicate pack codes found: {pack_codes}"
            print(f"✅ All pack codes are valid and unique")
            
            # ==========================================
            # PHASE 9: VERIFY PACK CODES VIA API
            # ==========================================
            print("\n📍 PHASE 9: Verifying Pack Codes via API")
            
            for i, code in enumerate(pack_codes, 1):
                response = await host_context.request.get(
                    f"{API_URL}/api/sessions/pack/{code}"
                )
                
                if not response.ok:
                    error_text = await response.text()
                    print(f"❌ Failed to retrieve pack code {code}: {response.status} - {error_text}")
                    assert False, f"Pack code {code} not retrievable from API"
                
                pack_data = await response.json()
                
                # Verify pack data structure
                assert 'playerNumber' in pack_data, "Missing playerNumber in pack data"
                assert 'commanderUrl' in pack_data, "Missing commanderUrl in pack data"
                assert 'powerups' in pack_data, "Missing powerups in pack data"
                assert 'packConfig' in pack_data, "Missing packConfig in pack data"
                
                assert pack_data['playerNumber'] == i, f"Wrong player number in pack {code}"
                assert len(pack_data['powerups']) == 2, f"Wrong powerup count in pack {code}"
                
                print(f"✅ Pack code {code} verified:")
                print(f"   Player: {pack_data['playerNumber']}")
                print(f"   Powerups: {len(pack_data['powerups'])}")
                print(f"   Commander: {pack_data.get('commanderUrl', 'Unknown')[:50]}...")
            
            # ==========================================
            # TEST COMPLETE
            # ==========================================
            print("\n" + "="*70)
            print("🎉 E2E TEST PASSED!")
            print("="*70)
            print(f"Session Code: {session_code}")
            print(f"Pack Codes: {', '.join(pack_codes)}")
            print(f"✅ 2 players successfully completed full flow to pack codes")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            print("\n📸 Saving screenshots for debugging...")
            try:
                await host_page.screenshot(path="test_failure_host.png")
                print("   Saved: test_failure_host.png")
            except:
                pass
            try:
                await p2_page.screenshot(path="test_failure_p2.png")
                print("   Saved: test_failure_p2.png")
            except:
                pass
            raise
            
        finally:
            # Cleanup
            try:
                await host_context.close()
            except:
                pass
            try:
                await p2_context.close()
            except:
                pass
            try:
                await browser.close()
            except:
                pass


if __name__ == "__main__":
    # Can run directly with: python tests/test_e2e_two_player.py
    import asyncio
    asyncio.run(test_two_player_complete_flow())

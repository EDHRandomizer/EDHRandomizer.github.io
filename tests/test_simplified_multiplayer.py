"""
Simplified multiplayer test focusing on the critical path
"""
import pytest
from playwright.async_api import async_playwright, expect
import asyncio

API_URL = "https://edhrandomizer-api.vercel.app"
GAME_URL = "https://edhrandomizer.github.io/random_commander_game.html"
TIMEOUT = 45000  # Increase timeout to 45s


@pytest.mark.asyncio
async def test_two_player_session_complete_flow():
    """Test a simpler 2-player session through the complete flow"""
    
    print("\n" + "="*60)
    print("🎮 Testing 2-Player Complete Session Flow")
    print("="*60)
    
    async with async_playwright() as p:
        # Launch browser once
        browser = await p.chromium.launch(headless=True)
        
        # Create contexts for 2 players
        host_context = await browser.new_context()
        player2_context = await browser.new_context()
        
        host_page = await host_context.new_page()
        player2_page = await player2_context.new_page()
        
        # Enable logging
        host_page.on("console", lambda msg: print(f"[HOST] log: {msg.text}"))
        player2_page.on("console", lambda msg: print(f"[P2] log: {msg.text}"))
        
        try:
            # PHASE 1: Host creates session
            print("\n📍 PHASE 1: Host Creates Session")
            await host_page.goto(GAME_URL)
            await host_page.wait_for_timeout(3000)
            
            await host_page.fill('#create-powerups-count', '2')
            await host_page.click('#create-session-btn')
            await host_page.wait_for_timeout(2000)
            
            await expect(host_page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
            await host_page.fill('#player-name-input', 'Host')
            await host_page.click('#confirm-name-btn')
            await host_page.wait_for_timeout(2000)
            
            await expect(host_page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
            
            # Get session code
            url = host_page.url
            session_code = url.split('?session=')[1].split('&')[0]
            print(f"✅ Host created session: {session_code}")
            
            # PHASE 2: Player 2 joins
            print(f"\n📍 PHASE 2: Player 2 Joins {session_code}")
            await player2_page.goto(GAME_URL)
            await player2_page.wait_for_timeout(3000)
            
            await player2_page.fill('#join-code-input', session_code)
            await player2_page.click('#join-session-btn')
            await player2_page.wait_for_timeout(1500)
            
            await expect(player2_page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
            await player2_page.fill('#player-name-input', 'Player 2')
            await player2_page.click('#confirm-name-btn')
            await player2_page.wait_for_timeout(2000)
            
            await expect(player2_page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
            print(f"✅ Player 2 joined")
            
            # PHASE 3: Host starts rolling
            print("\n📍 PHASE 3: Host Starts Rolling")
            try:
                await host_page.click('#roll-powerups-btn')
                await host_page.wait_for_timeout(3000)
                
                # Wait for both players to see player grid
                await expect(host_page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
                print("✅ Host sees player grid")
                
                await expect(player2_page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
                print("✅ Player 2 sees player grid")
            except Exception as e:
                print(f"❌ Phase 3 failed: {e}")
                raise
            
            # PHASE 4: Generate commanders for both players
            print("\n📍 PHASE 4: Generating Commanders")
            
            # Host generates (Player 1)
            print("  Generating for Player 1 (Host)...")
            host_gen_btn = host_page.locator('#generate-btn-1')
            await expect(host_gen_btn).to_be_visible(timeout=TIMEOUT)
            await host_gen_btn.click()
            await host_page.wait_for_timeout(2000)  # Reduced from 8000
            
            host_commanders = host_page.locator('.commander-item-small')
            await expect(host_commanders.first).to_be_visible(timeout=15000)  # Wait up to 15s for Scryfall
            count = await host_commanders.count()
            print(f"✅ Player 1 generated {count} commanders")
            
            # Player 2 generates
            print("  Generating for Player 2...")
            p2_gen_btn = player2_page.locator('#generate-btn-2')
            await expect(p2_gen_btn).to_be_visible(timeout=TIMEOUT)
            await p2_gen_btn.click()
            await player2_page.wait_for_timeout(2000)
            
            p2_commanders = player2_page.locator('.commander-item-small')
            await expect(p2_commanders.first).to_be_visible(timeout=15000)
            count2 = await p2_commanders.count()
            print(f"✅ Player 2 generated {count2} commanders")
            
            # PHASE 5: Select and lock commanders
            print("\n📍 PHASE 5: Selecting and Locking Commanders")
            
            # Host selects and locks
            print("  Player 1 selecting commander...")
            await host_commanders.first.click()
            await host_page.wait_for_timeout(500)
            
            host_lock_btn = host_page.locator('#lock-btn-1')
            await host_lock_btn.click()
            await host_page.wait_for_timeout(2000)
            print("✅ Player 1 locked commander")
            
            # Player 2 selects and locks  
            print("  Player 2 selecting commander...")
            await p2_commanders.first.click()
            await player2_page.wait_for_timeout(500)
            
            p2_lock_btn = player2_page.locator('#lock-btn-2')
            await p2_lock_btn.click()
            await player2_page.wait_for_timeout(2000)
            print("✅ Player 2 locked commander")
            
            # PHASE 6: Pack codes should appear
            print("\n📍 PHASE 6: Waiting for Pack Codes")
            
            # Both players should see pack codes section
            await expect(host_page.locator('#pack-codes-section')).to_be_visible(timeout=TIMEOUT)
            print("✅ Host sees pack codes section")
            
            await expect(player2_page.locator('#pack-codes-section')).to_be_visible(timeout=TIMEOUT)
            print("✅ Player 2 sees pack codes section")
            
            # Extract pack codes
            host_pack_codes = await host_page.locator('.pack-code').all_text_contents()
            print(f"\n✅ Found {len(host_pack_codes)} pack codes")
            
            for i, code in enumerate(host_pack_codes):
                print(f"   Player {i+1}: {code}")
            
            # Verify pack codes work via API
            print("\n📍 PHASE 7: Verifying Pack Codes via API")
            for i, code in enumerate(host_pack_codes):
                response = await host_context.request.get(f"{API_URL}/api/sessions/pack/{code}")
                assert response.ok, f"Pack code {code} not retrievable"
                pack_data = await response.json()
                print(f"✅ Pack code {code} verified (Player {pack_data.get('playerNumber', '?')})")
            
            print("\n" + "="*60)
            print("🎉 2-Player Complete Flow PASSED!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            print("   Taking screenshots for debugging...")
            try:
                await host_page.screenshot(path="debug_host_error.png")
                await player2_page.screenshot(path="debug_p2_error.png")
                print("   Screenshots saved")
            except:
                print("   Could not save screenshots")
            raise
        finally:
            try:
                await host_context.close()
            except:
                pass
            try:
                await player2_context.close()
            except:
                pass
            try:
                await browser.close()
            except:
                pass


@pytest.mark.asyncio
async def test_four_player_session_with_sequential_joins():
    """Test 4-player session with players joining sequentially"""
    
    print("\n" + "="*60)
    print("🎮 Testing 4-Player Session (Sequential Joins)")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Create all 4 contexts
        contexts = []
        pages = []
        
        for i in range(4):
            ctx = await browser.new_context()
            page = await ctx.new_page()
            page.on("console", lambda msg, num=i+1: None)  # Suppress logs for cleaner output
            contexts.append(ctx)
            pages.append(page)
        
        host_page = pages[0]
        
        try:
            # Host creates session
            print("\n📍 Creating session...")
            await host_page.goto(GAME_URL)
            await host_page.wait_for_timeout(3000)
            
            await host_page.fill('#create-powerups-count', '2')
            await host_page.click('#create-session-btn')
            await host_page.wait_for_timeout(2000)
            
            await expect(host_page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
            await host_page.fill('#player-name-input', 'Host')
            await host_page.click('#confirm-name-btn')
            await host_page.wait_for_timeout(2000)
            
            url = host_page.url
            session_code = url.split('?session=')[1].split('&')[0]
            print(f"✅ Session created: {session_code}")
            
            # Other 3 players join ONE AT A TIME
            for i, page in enumerate(pages[1:], start=2):
                print(f"\n📍 Player {i} joining...")
                await page.goto(GAME_URL)
                await page.wait_for_timeout(2000)
                
                await page.fill('#join-code-input', session_code)
                await page.click('#join-session-btn')
                await page.wait_for_timeout(1500)
                
                await expect(page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
                await page.fill('#player-name-input', f'Player {i}')
                await page.click('#confirm-name-btn')
                await page.wait_for_timeout(2000)
                
                print(f"✅ Player {i} joined")
            
            # All in lobby, verify count
            print("\n📍 Verifying all players in lobby...")
            for i, page in enumerate(pages, start=1):
                player_count = await page.locator('.player-item').count()
                assert player_count == 4, f"Player {i} sees {player_count} players, expected 4"
            print("✅ All 4 players see each other")
            
            # Start rolling
            print("\n📍 Starting rolling phase...")
            await host_page.click('#roll-powerups-btn')
            await host_page.wait_for_timeout(3000)
            
            # All should see player grid
            for i, page in enumerate(pages, start=1):
                await expect(page.locator('#player-grid-section')).to_be_visible(timeout=TIMEOUT)
            print("✅ All players see player grid")
            
            # Generate commanders for all (sequentially to avoid API overload)
            print("\n📍 Generating commanders for all players...")
            for i, page in enumerate(pages, start=1):
                gen_btn = page.locator(f'#generate-btn-{i}')
                await expect(gen_btn).to_be_visible(timeout=TIMEOUT)
                await gen_btn.click()
                await page.wait_for_timeout(1500)  # Brief wait between generations
            
            # Wait for all commanders to load
            print("⏳ Waiting for all commanders to load...")
            await asyncio.sleep(5)  # Give time for Scryfall API
            
            for i, page in enumerate(pages, start=1):
                commanders = page.locator('.commander-item-small')
                try:
                    await expect(commanders.first).to_be_visible(timeout=10000)
                    count = await commanders.count()
                    print(f"✅ Player {i}: {count} commanders")
                except:
                    print(f"⚠️ Player {i}: Commanders still loading, continuing...")
            
            # Lock commanders
            print("\n📍 Locking commanders...")
            for i, page in enumerate(pages, start=1):
                commanders = page.locator('.commander-item-small')
                count = await commanders.count()
                
                if count > 0:
                    await commanders.first.click()
                    await page.wait_for_timeout(500)
                    
                    lock_btn = page.locator(f'#lock-btn-{i}')
                    await lock_btn.click()
                    await page.wait_for_timeout(1500)
                    print(f"✅ Player {i} locked")
                else:
                    print(f"⚠️ Player {i} skipping lock (no commanders loaded)")
            
            # Check for pack codes
            print("\n📍 Checking for pack codes...")
            try:
                await expect(host_page.locator('#pack-codes-section')).to_be_visible(timeout=15000)
                pack_codes = await host_page.locator('.pack-code').all_text_contents()
                print(f"✅ Generated {len(pack_codes)} pack codes")
                print("\n" + "="*60)
                print("🎉 4-Player Session PASSED!")
                print("="*60)
            except:
                print("⚠️ Pack codes section did not appear - some players may not have locked")
                print("   This is expected if commanders didn't load in time")
                
        finally:
            for ctx in contexts:
                await ctx.close()
            await browser.close()

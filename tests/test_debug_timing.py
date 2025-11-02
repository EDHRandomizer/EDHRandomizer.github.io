"""
Debug test to identify where the timing issues occur
"""
import pytest
from playwright.async_api import async_playwright, expect
import asyncio

API_URL = "https://edhrandomizer-api.vercel.app"
GAME_URL = "https://edhrandomizer.github.io/random_commander_game.html"
TIMEOUT = 30000


@pytest.mark.asyncio
async def test_rolling_phase_timing():
    """Test specifically the rolling phase to see where it hangs"""
    
    print("\n" + "="*60)
    print("🔍 DEBUG: Testing Rolling Phase Timing")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use headed mode to see what's happening
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging to see what's happening
        page.on("console", lambda msg: print(f"[BROWSER] {msg.text}"))
        
        print("\n📍 Step 1: Navigate to game")
        await page.goto(GAME_URL)
        await page.wait_for_timeout(3000)
        print("✅ Page loaded")
        
        print("\n📍 Step 2: Create session with 2 powerups")
        await page.fill('#create-powerups-count', '2')
        await page.click('#create-session-btn')
        await page.wait_for_timeout(2000)
        print("✅ Create session clicked")
        
        print("\n📍 Step 3: Enter name")
        await expect(page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
        await page.fill('#player-name-input', 'Test Player')
        await page.click('#confirm-name-btn')
        await page.wait_for_timeout(2000)
        print("✅ Name entered")
        
        print("\n📍 Step 4: Verify lobby visible")
        await expect(page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
        print("✅ Lobby visible")
        
        print("\n📍 Step 5: Click 'Start Game' (roll-powerups-btn)")
        roll_btn = page.locator('#roll-powerups-btn')
        
        # Check if button exists
        is_visible = await roll_btn.is_visible()
        print(f"   Roll button visible: {is_visible}")
        
        if not is_visible:
            print("❌ Roll button not visible! Looking for alternatives...")
            # Take screenshot for debugging
            await page.screenshot(path="debug_lobby.png")
            print("   Screenshot saved to debug_lobby.png")
            
            # List all buttons
            buttons = await page.locator('button').all()
            print(f"\n   Found {len(buttons)} buttons on page:")
            for i, btn in enumerate(buttons[:10]):  # Show first 10
                text = await btn.text_content()
                btn_id = await btn.get_attribute('id')
                is_vis = await btn.is_visible()
                print(f"   {i+1}. ID: {btn_id}, Text: {text}, Visible: {is_vis}")
        else:
            print("✅ Roll button found and visible")
            
            # Click it
            await roll_btn.click()
            print("✅ Roll button clicked")
            await page.wait_for_timeout(3000)
            
            print("\n📍 Step 6: Wait for player grid section")
            player_grid = page.locator('#player-grid-section')
            
            # Check if it appeared
            try:
                await expect(player_grid).to_be_visible(timeout=10000)
                print("✅ Player grid section appeared!")
            except Exception as e:
                print(f"❌ Player grid did NOT appear within 10s: {e}")
                await page.screenshot(path="debug_after_roll.png")
                print("   Screenshot saved to debug_after_roll.png")
                
                # Check what IS visible
                print("\n   Checking what sections are visible:")
                sections = ['#join-create-section', '#enter-name-section', '#lobby-section', 
                           '#player-grid-section', '#pack-codes-section']
                for section_id in sections:
                    is_vis = await page.locator(section_id).is_visible()
                    print(f"   {section_id}: {is_vis}")
        
        print("\n📍 Keeping browser open for 5 seconds for manual inspection...")
        await page.wait_for_timeout(5000)
        
        await browser.close()
        print("\n✅ Debug test complete")


@pytest.mark.asyncio
async def test_generate_commanders_timing():
    """Test specifically commander generation timing"""
    
    print("\n" + "="*60)
    print("🔍 DEBUG: Testing Commander Generation Timing")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        page.on("console", lambda msg: print(f"[BROWSER] {msg.text}"))
        
        # Quick setup to rolling phase
        await page.goto(GAME_URL)
        await page.wait_for_timeout(3000)
        
        await page.fill('#create-powerups-count', '2')
        await page.click('#create-session-btn')
        await page.wait_for_timeout(2000)
        
        await expect(page.locator('#enter-name-section')).to_be_visible(timeout=TIMEOUT)
        await page.fill('#player-name-input', 'Test Player')
        await page.click('#confirm-name-btn')
        await page.wait_for_timeout(2000)
        
        await expect(page.locator('#lobby-section')).to_be_visible(timeout=TIMEOUT)
        print("✅ Setup complete, in lobby")
        
        # Start rolling
        print("\n📍 Starting rolling phase...")
        await page.click('#roll-powerups-btn')
        await page.wait_for_timeout(3000)
        
        # Wait for player grid
        try:
            await expect(page.locator('#player-grid-section')).to_be_visible(timeout=15000)
            print("✅ Player grid visible")
        except Exception as e:
            print(f"❌ Player grid timeout: {e}")
            await page.screenshot(path="debug_no_grid.png")
            await browser.close()
            pytest.fail("Player grid never appeared")
        
        # Look for generate button
        print("\n📍 Looking for generate button...")
        generate_btn = page.locator('#generate-btn-1')
        
        try:
            await expect(generate_btn).to_be_visible(timeout=10000)
            print("✅ Generate button found")
            
            # Click generate
            print("\n📍 Clicking generate commanders...")
            await generate_btn.click()
            print("✅ Generate clicked, waiting for commanders...")
            
            # Wait and watch for commanders
            for i in range(15):  # Check every second for 15 seconds
                await page.wait_for_timeout(1000)
                count = await page.locator('.commander-item-small').count()
                print(f"   After {i+1}s: {count} commanders")
                
                if count > 0:
                    print(f"✅ Commanders appeared after {i+1} seconds!")
                    break
            
            if count == 0:
                print("❌ No commanders appeared after 15 seconds")
                await page.screenshot(path="debug_no_commanders.png")
        
        except Exception as e:
            print(f"❌ Generate button not found: {e}")
            await page.screenshot(path="debug_no_generate_btn.png")
        
        print("\n📍 Keeping browser open for inspection...")
        await page.wait_for_timeout(10000)
        
        await browser.close()
        print("\n✅ Debug test complete")


@pytest.mark.asyncio  
async def test_element_selectors():
    """Verify all element selectors match actual HTML"""
    
    print("\n" + "="*60)
    print("🔍 DEBUG: Verifying Element Selectors")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(GAME_URL)
        await page.wait_for_timeout(3000)
        
        # Check all expected elements exist
        elements_to_check = {
            '#join-create-section': 'Join/Create Section',
            '#create-session-btn': 'Create Session Button',
            '#create-powerups-count': 'Powerups Count Input',
            '#join-code-input': 'Join Code Input',
            '#join-session-btn': 'Join Session Button',
            '#enter-name-section': 'Enter Name Section (after create)',
            '#player-name-input': 'Player Name Input',
            '#confirm-name-btn': 'Confirm Name Button',
            '#lobby-section': 'Lobby Section (after name)',
            '#roll-powerups-btn': 'Roll Powerups Button',
            '#player-grid-section': 'Player Grid Section (after roll)',
            '#pack-codes-section': 'Pack Codes Section (after all lock)',
        }
        
        print("\nChecking initial page state:")
        for selector, name in elements_to_check.items():
            exists = await page.locator(selector).count() > 0
            visible = await page.locator(selector).is_visible() if exists else False
            print(f"  {name}")
            print(f"    Selector: {selector}")
            print(f"    Exists: {exists}, Visible: {visible}")
        
        await browser.close()
        print("\n✅ Element check complete")

"""
Simple smoke test to verify basic page load and session creation
"""

import pytest
from playwright.async_api import async_playwright, expect


BASE_URL = "https://edhrandomizer.github.io"
GAME_URL = f"{BASE_URL}/random_commander_game.html"


@pytest.mark.asyncio
async def test_page_loads():
    """Test that the game page loads successfully"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("\n🌐 Loading game page...")
        await page.goto(GAME_URL, wait_until='networkidle', timeout=30000)
        
        # Check title
        title = await page.title()
        print(f"✅ Page loaded: {title}")
        
        # Check that main section exists
        join_create_section = page.locator('#join-create-section')
        await expect(join_create_section).to_be_visible(timeout=10000)
        print("✅ Join/Create section is visible")
        
        # Check create button exists
        create_btn = page.locator('#create-session-btn')
        await expect(create_btn).to_be_visible(timeout=10000)
        print("✅ Create session button is visible")
        
        await context.close()
        await browser.close()
        
        print("🎉 Smoke test passed!")


@pytest.mark.asyncio
async def test_create_session_ui():
    """Test creating a session and getting to lobby"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"[Console] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[Page Error] {err}"))
        
        print("\n🌐 Loading game page...")
        await page.goto(GAME_URL, wait_until='networkidle', timeout=30000)
        
        print("✍️ Setting perks count...")
        perks_input = page.locator('#create-perks-count')
        await perks_input.fill('2')
        
        print("🖱️ Clicking create session button...")
        create_btn = page.locator('#create-session-btn')
        await create_btn.click()
        
        # Wait for navigation or state change
        print("⏳ Waiting for enter name section...")
        enter_name_section = page.locator('#enter-name-section')
        
        try:
            await expect(enter_name_section).to_be_visible(timeout=15000)
            print("✅ Enter name section is visible!")
            
            # Enter a name
            print("✍️ Entering player name...")
            name_input = page.locator('#player-name-input')
            await name_input.fill('Test Player')
            
            confirm_btn = page.locator('#confirm-name-btn')
            await confirm_btn.click()
            
            # Now should reach lobby
            print("⏳ Waiting for lobby section...")
            lobby_section = page.locator('#lobby-section')
            await expect(lobby_section).to_be_visible(timeout=15000)
            print("✅ Lobby section is visible!")
            
            # Check URL for session code
            url = page.url
            print(f"📍 Current URL: {url}")
            
            if 'session=' in url:
                import re
                match = re.search(r'session=([A-Z0-9]{5})', url)
                if match:
                    session_code = match.group(1)
                    print(f"✅ Session code found: {session_code}")
            
        except Exception as e:
            print(f"❌ Failed to reach lobby: {e}")
            
            # Debug: take screenshot
            await page.screenshot(path='test_failure.png')
            print("📸 Screenshot saved to test_failure.png")
            
            # Debug: print current visible sections
            sections = ['#join-create-section', '#enter-name-section', '#lobby-section', '#player-grid-section', '#pack-codes-section']
            for section in sections:
                is_visible = await page.locator(section).is_visible()
                print(f"  {section}: visible={is_visible}")
            
            raise
        
        await context.close()
        await browser.close()
        
        print("🎉 Create session test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

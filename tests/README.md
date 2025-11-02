# Multiplayer Session E2E Tests

Automated end-to-end tests for the EDH Randomizer multiplayer session flow.

## Setup

1. **Install test dependencies:**
```bash
pip install pytest pytest-asyncio playwright
```

2. **Install Playwright browsers:**
```bash
playwright install chromium
```

## Running Tests

### Run all tests (headless)
```bash
pytest tests/test_multiplayer_session.py -v -s
```

### Run with visible browser (watch the test)
```bash
pytest tests/test_multiplayer_session.py -v -s --headed
```

### Run specific test
```bash
pytest tests/test_multiplayer_session.py::test_full_multiplayer_session -v -s
```

### Run with more detailed output
```bash
pytest tests/test_multiplayer_session.py -vv -s --tb=short
```

## Test Coverage

### ✅ `test_full_multiplayer_session`
Complete 4-player flow from start to finish:
1. Host creates session with name and powerups count
2. 3 additional players join using session code
3. All players enter names and reach lobby
4. Host starts rolling phase
5. All players roll powerups (3 each)
6. All players generate commanders
7. All players select and lock commanders
8. Pack codes generated for all players
9. Verify pack codes are unique
10. Verify pack codes accessible via API

### ✅ `test_late_join_during_rolling`
Tests that players can join sessions that are already in the rolling phase.

### ✅ `test_cannot_join_after_selecting`
Verifies that joining is properly blocked once commander selection has started.

### ✅ `test_url_session_restore`
Tests session restoration from URL parameters (detecting if this feature needs work).

## What These Tests Will Catch

### Session Management Issues
- Session codes not generated correctly
- Players not added to sessions properly
- Session state not syncing between players

### URL Parameter Issues
- Session codes not added to URL
- URL restoration not working
- Player IDs lost on page refresh

### Race Conditions
- Multiple players joining simultaneously
- State transitions while players are joining
- API calls overlapping or timing out

### API Integration
- Pack code storage/retrieval failures
- Session not found errors
- Powerup data not persisting

### UI State Management
- Players stuck on wrong screen
- Buttons not appearing/clickable
- Sections not becoming visible

## Debugging Failed Tests

### Console Logs
Tests print console messages from all 4 browser tabs with `[Player X]` prefix.

### Screenshots on Failure
Add this to `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
```

### Run Headed Mode
Watch the test execute in real browsers:
```bash
pytest tests/test_multiplayer_session.py -v -s --headed --slowmo=1000
```

### Check API Logs
Monitor Vercel deployment logs during test runs:
```bash
vercel logs edhrandomizer-api --follow
```

## Common Issues and Solutions

### Issue: "Session not found" errors
**Likely cause:** Session expiring between steps or URL not persisting session code
**Check:** URL handling in `random_commander_game.html`, session TTL in API

### Issue: Players stuck in wrong phase
**Likely cause:** Session state not syncing properly
**Check:** WebSocket/polling implementation, state transition logic

### Issue: Pack codes not generated
**Likely cause:** API not receiving lock events or Vercel KV not configured
**Check:** Lock commander API endpoint, Vercel KV setup

### Issue: Tests timeout
**Likely cause:** Scryfall API slow or UI not updating
**Check:** Increase `TIMEOUT` constant, verify Scryfall API response times

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio playwright
          playwright install chromium --with-deps
      - name: Run tests
        run: pytest tests/test_multiplayer_session.py -v
```

## Performance Testing

To test with more players or different configurations, modify the test:

```python
@pytest.fixture
async def browser_contexts():
    # Change this number to test more players
    num_players = 4  # Try 2, 3, or 4
    
    for i in range(num_players):
        # ... rest of fixture
```

## Next Steps

1. **Add more test scenarios:**
   - Player disconnect/reconnect
   - Session timeout behavior
   - Invalid session codes
   - Full session (5th player tries to join)

2. **Add performance tests:**
   - Measure time for each phase
   - Track API response times
   - Monitor memory usage

3. **Add visual regression tests:**
   - Screenshot comparison for UI
   - Verify powerup display
   - Check pack code styling

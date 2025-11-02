# Test Results & Bug Fixes - 2025-11-02

## Tests Created
- ✅ `test_simple_smoke.py` - Basic page load and session creation
- ✅ `test_multiplayer_session.py` - Full 4-player multiplayer flow
- ✅ Test runner scripts for Windows and Unix

## Bugs Found by Tests

### CRITICAL: Sessions Lost on Vercel Serverless  (FIXED ✅)
**Issue:** Sessions were stored only in-memory (`SESSIONS` dict), which is reset on every Vercel serverless function invocation. This caused "Session not found" errors immediately after creation.

**Symptom:** 
```
Error: Session not found (404)
```
Even though session was just created seconds before.

**Root Cause:** 
Vercel serverless functions don't maintain state between invocations. Each API call gets fresh memory.

**Fix:**
- Added `store_session()`, `get_session()`, `update_session()`, `delete_session()` functions
- Sessions now stored in Vercel KV (Redis) with 2-hour TTL
- Falls back to in-memory for local development
- All handlers updated to use KV-backed storage

**Code Changed:**
- `api/sessions.py`: Added session KV storage functions
- Updated all `handle_*` methods to use `get_session()` and `update_session()`

**Test Status:** ✅ PASSING
- `test_simple_smoke.py::test_create_session_ui` - PASS
- `test_simple_smoke.py::test_page_loads` - PASS

## Tests In Progress

### `test_late_join_during_rolling`
Testing if players can join sessions during the rolling phase.

**Status:** Running...

### `test_full_multiplayer_session`
Complete 4-player flow from creation to pack codes.

**Status:** Not yet run

### `test_cannot_join_after_selecting`
Verify joins are blocked after commander selection starts.

**Status:** Not yet run

### `test_url_session_restore`
Test if players can restore sessions from URL parameters.

**Status:** Not yet run

## Next Steps

1. ✅ Wait for current test to complete
2. ⏳ Run full 4-player test
3. ⏳ Fix any additional bugs found
4. ⏳ Run all tests until they pass
5. ⏳ Add to CI/CD pipeline

## Test Framework

**Framework:** Playwright with Python
**Why:** 
- Multiple browser contexts (4 simultaneous players)
- Async/await support
- Auto-waiting and retries
- Console logging from all browsers
- Already using Playwright for EDHREC scraping

**Run Commands:**
```powershell
# Setup
.\run_tests.ps1 -Setup

# Run tests
.\run_tests.ps1               # Headless
.\run_tests.ps1 -Headed       # Watch browsers
.\run_tests.ps1 -Headed -Slow # Slow motion debug
```

## Impact

The E2E tests have already found and helped fix a critical bug that would have been very difficult to debug manually. The "Session not found" errors only happen on Vercel (serverless), not in local development, making them hard to reproduce.

This validates the investment in comprehensive testing!

# Player Disconnection & Reconnection - Implementation Summary

## Problem Statement

Players who disconnect (page refresh, network issues, browser crash) during a game session would completely break the game flow, as other players couldn't advance without everyone selecting a commander.

## Solutions Implemented

### 1. Disconnection Detection & Visual Feedback

**Backend Changes (`api/sessions.py`):**
- Added `isConnected` (boolean) and `lastSeen` (timestamp) fields to player objects
- Modified `touch_session()` to accept optional `player_id` parameter
- Automatically marks players as disconnected if no activity for 30+ seconds
- Players marked as connected when they send heartbeats

**Frontend Changes (`docs/random_commander_game.html`):**
- Added CSS styling for `.disconnected` class on lobby players and player sections
- Striped background pattern and red border for disconnected players
- "⚠️ Disconnected" badges displayed prominently
- Grayed-out player sections during commander selection
- Updated `updateLobbyPlayers()` and `updatePlayerStatuses()` to show disconnection status

**Visual Indicators:**
- Lobby: Striped background, red border, "⚠️ Disconnected" text
- Selection: Grayed section, "⚠️ DISCONNECTED" badge, status shows disconnected

### 2. Automatic Reconnection

**Backend (`api/sessions.py`):**
- New endpoint: `POST /api/sessions/rejoin`
  - Accepts `sessionCode` and `playerId`
  - Validates player exists in session
  - Updates player's `isConnected` and `lastSeen` fields
  - Returns full session data

**Frontend (`docs/js/game-session/sessionManager.js`):**
- New method: `rejoinSession(sessionCode, playerId)`
- New method: `savePlayerIdToStorage(sessionCode, playerId)` - stores player ID in localStorage
- New method: `getPlayerIdFromStorage(sessionCode)` - retrieves stored player ID
- Modified `createSession()` and `joinSession()` to auto-save player IDs
- Player IDs stored with 12-hour expiration

**Frontend (`docs/random_commander_game.html`):**
- Modified `checkURLParameters()` to attempt automatic reconnection
- Checks for stored player ID when session code found in URL
- Automatically calls `rejoinSession()` with stored credentials
- Navigates to correct screen based on session state
- Falls back to normal join flow if reconnection fails

**Reconnection Flow:**
1. Player disconnects (refresh/crash)
2. Returns to game page (session code in URL)
3. Game retrieves stored player ID from localStorage
4. Attempts to rejoin with existing player ID
5. On success: returns to appropriate screen
6. On failure: shows manual join form

### 3. Heartbeat System

**Backend (`api/sessions.py`):**
- New endpoint: `POST /api/sessions/heartbeat`
  - Updates player's `lastSeen` timestamp
  - Marks player as connected
  - Silent operation (no error response if fails)

**Frontend (`docs/js/game-session/sessionManager.js`):**
- New method: `sendHeartbeat()`
- Called automatically every 3rd polling cycle (~15-24 seconds)
- Silently fails to avoid interrupting gameplay
- Integrated into `startPolling()` method

### 4. Force Advance (Host Only)

**Backend (`api/sessions.py`):**
- New endpoint: `POST /api/sessions/force-advance`
  - Host-only (verified by `hostId`)
  - For each unlocked player:
    - If player has generated commanders: randomly selects one
    - If player hasn't generated commanders: creates placeholder
  - Marks all players as `commanderLocked = True`
  - Calls `generate_pack_codes_internal()` to create pack codes
  - Sets session state to `'complete'`

**Frontend (`docs/random_commander_game.html`):**
- Added "Host Controls" section in player grid
- New button: "⏭️ Force Advance to Pack Codes"
- Only visible to host during commander selection
- Confirmation dialog shows:
  - Number of unlocked players
  - What will happen to each type of player
  - Requires explicit confirmation
- Calls `sessionManager.forceAdvance()` on confirmation
- Navigates to pack codes screen on success

**Frontend (`docs/js/game-session/sessionManager.js`):**
- New method: `forceAdvance()`
- Calls `/force-advance` endpoint
- Returns updated session data with pack codes

### 5. Kick Player (Host Only)

**Backend (`api/sessions.py`):**
- New endpoint: `POST /api/sessions/kick`
  - Accepts `sessionCode`, `playerId` (host), and `kickPlayerId`
  - Host-only (verified by `hostId`)
  - Validates host can't kick themselves
  - Removes player from session's player list
  - Renumbers remaining players sequentially
  - Returns updated session data and kicked player info

**Frontend (`docs/js/game-session/sessionManager.js`):**
- New method: `kickPlayer(kickPlayerId)`
- Calls `/kick` endpoint with current session and player IDs
- Returns updated session data

**Frontend (`docs/random_commander_game.html`):**
- **Lobby Screen:**
  - Modified `updateLobbyPlayers()` to show kick button
  - Kick button appears next to each player (not on host's own card)
  - Changed lobby player layout to flexbox for button positioning
  - Added `kickPlayerFromLobby()` function with confirmation dialog
  
- **Commander Selection Screen:**
  - Modified `createPlayerSection()` to add kick button
  - Button positioned in top-right corner of player card
  - Only visible to host, not on their own card
  - Added `kickPlayerFromGame()` function with confirmation dialog
  
- **Kicked Player Detection:**
  - Modified `startPolling()` to detect when current player is no longer in session
  - Shows notification: "You have been removed from the session by the host"
  - Auto-redirects to join screen after 3 seconds
  - Pre-fills session code for easy rejoin

**UI/UX:**
- Red "❌ Kick" button with hover effect
- Confirmation dialog explains player can rejoin
- Kicked player sees friendly notification
- Session code pre-populated for rejoining
- CSS styling for `.kick-btn` class

### 5. Documentation

Created comprehensive guide (`docs/RECONNECTION_GUIDE.md`) covering:
- Overview of all features
- How disconnection detection works
- Automatic reconnection flow
- Manual rejoin process
- Force advance functionality
- Kick player functionality (host controls)
- Technical details (API endpoints, methods, data structures)
- Best practices for players and hosts
- Troubleshooting common issues
- Example scenarios (including kick/rejoin)
- Future improvement ideas

## Files Modified

### Backend
- `api/sessions.py`:
  - Added player fields: `isConnected`, `lastSeen`
  - Modified: `touch_session()` to track player activity
  - New handler: `handle_rejoin_session()`
  - New handler: `handle_force_advance()`
  - New handler: `handle_heartbeat()`
  - Updated routing in `do_POST()`

### Frontend
- `docs/js/game-session/sessionManager.js`:
  - New method: `rejoinSession()`
  - New method: `forceAdvance()`
  - New method: `sendHeartbeat()`
  - New method: `savePlayerIdToStorage()`
  - New method: `getPlayerIdFromStorage()`
  - Modified: `createSession()` to save player ID
  - Modified: `joinSession()` to save player ID
  - Modified: `startPolling()` to send heartbeats

- `docs/random_commander_game.html`:
  - Added CSS for `.disconnected` class (lobby and player sections)
  - Added CSS for `.kick-btn` class
  - Modified lobby player layout to flexbox
  - Added host controls section with force advance button
  - Modified: `updateLobbyPlayers()` to show disconnection status and kick buttons
  - Modified: `updatePlayerStatuses()` to show disconnection status
  - Modified: `createPlayerSection()` to add kick button on player cards
  - Modified: `renderPlayerGrid()` to show/hide host controls
  - Modified: `checkURLParameters()` to attempt auto-reconnection
  - Modified: `startPolling()` to detect kicked players
  - Added: `kickPlayerFromLobby()` function
  - Added: `kickPlayerFromGame()` function
  - Added event handler for force advance button

### Documentation
- `docs/RECONNECTION_GUIDE.md`: New comprehensive guide

## Testing Recommendations

### Manual Testing Scenarios

1. **Disconnection Detection:**
   - Join a session
   - Wait 30+ seconds without activity
   - Verify you're marked as disconnected

2. **Automatic Reconnection:**
   - Join/create a session
   - Refresh the page
   - Verify automatic rejoin
   - Verify you're on the correct screen

3. **Manual Reconnection:**
   - Join a session
   - Close browser
   - Open browser, navigate to game
   - Manually enter session code
   - Verify you can join as new player (if slots available)

4. **Force Advance:**
   - Create session as host
   - Have 2+ players
   - Have some players lock in, some don't
   - Click force advance
   - Verify pack codes generated for all
   - Verify commanders auto-selected correctly

5. **Visual Indicators:**
   - Have player disconnect
   - Verify "⚠️ Disconnected" shown in lobby
   - Verify disconnected styling during selection
   - Have player reconnect
   - Verify indicators clear

6. **Kick Player:**
   - Join session as host with 2+ players
   - Click kick button on another player
   - Verify confirmation dialog
   - Confirm kick
   - Verify player removed from session
   - Verify kicked player sees notification
   - Have kicked player rejoin
   - Verify they can rejoin successfully

### Automated Testing (Future)

Suggested test cases:
- `test_player_disconnection.py`: Test 30-second timeout
- `test_player_reconnection.py`: Test rejoin endpoint
- `test_force_advance.py`: Test auto-commander selection
- `test_kick_player.py`: Test kick endpoint and player removal
- `test_heartbeat.py`: Test heartbeat updates
- E2E test: Full disconnection/reconnection flow
- E2E test: Kick and rejoin flow

## Known Limitations

1. **Session Full:** Can't rejoin if all 4 slots filled with different players
2. **Phase Restriction:** Can't join as new player after "rolling" phase
3. **Storage Expiration:** Player IDs expire after 12 hours
4. **No Host Transfer:** If host disconnects permanently, can't transfer host role
5. **localStorage Only:** Won't work in private/incognito mode with storage disabled

## Deployment Notes

1. **No database migrations needed** - session data is in-memory/Redis
2. **Backward compatible** - old sessions will work (missing fields default to connected)
3. **localStorage requirement** - inform users to allow localStorage
4. **Mobile testing** - test on mobile browsers that may handle localStorage differently

## Future Enhancements

1. ~~**Kick Player:**~~ ✅ **IMPLEMENTED** - Allow host to remove disconnected players
2. **Transfer Host:** Transfer host role if host disconnects
3. **Persistent Sessions:** Store full session in database for longer persistence
4. **Reconnect Notifications:** Toast messages when players reconnect
5. **Connection Quality:** Show latency/connection strength indicator
6. **Player Notes:** Let players mark themselves as "AFK" or "Disconnected"
7. **Ban Player:** Prevent specific player from rejoining (unlike kick which allows rejoin)
8. **Spectator Mode:** Allow kicked/left players to watch without participating

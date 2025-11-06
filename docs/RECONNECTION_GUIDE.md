# Player Reconnection & Disconnection Handling Guide

## Overview

The EDH Randomizer game mode now supports robust disconnection detection and player reconnection, allowing games to continue even when players temporarily lose connection or refresh their browser.

## Features

### 1. Automatic Disconnection Detection

**How it works:**
- Every player sends a "heartbeat" to the server every 3 polling cycles (approximately every 15-24 seconds)
- If a player hasn't been seen for more than 30 seconds, they are marked as disconnected
- Disconnected players are visually indicated in the lobby and during commander selection

**Visual Indicators:**
- **In Lobby:** Disconnected players show a striped background pattern with an "⚠️ Disconnected" badge
- **During Selection:** Disconnected player sections are grayed out with a "⚠️ DISCONNECTED" label
- Status shows "⚠️ Disconnected" instead of "Selecting..." or "🔒 Locked"

### 2. Automatic Reconnection

**How it works:**
- When you join or create a session, your Player ID is automatically saved to browser localStorage
- If you refresh the page or navigate away and come back, the game will automatically detect your stored Player ID
- The game attempts to rejoin you to your existing session without needing to enter your name again

**Reconnection Flow:**
1. Player's browser crashes, refreshes, or loses connection
2. Player returns to the game page (URL with session code is preserved in browser history)
3. Game automatically detects stored Player ID for that session
4. Player is seamlessly rejoined to the same session
5. Game navigates to the appropriate screen based on session state:
   - **Waiting:** Returns to lobby
   - **Selecting:** Shows perk reveal then commander selection
   - **Complete:** Shows pack codes

**Storage Duration:**
- Player IDs are stored for 12 hours
- After 12 hours, you'll need to join as a new player

### 3. Manual Rejoin

**If automatic reconnection fails:**
1. Join the session normally using the session code
2. You will be added as a new player if there are open slots
3. Note: You won't be able to rejoin if the session is full (4 players) or has progressed beyond the rolling phase

**Session Joining Rules:**
- New players can join during "waiting" or "rolling" phases
- Once commander selection has started, no new players can join
- Maximum 4 players per session

### 4. Force Advance (Host Only)

When one or more players are disconnected or taking too long to select a commander, the host can force the game to advance to pack codes.

**How to use:**
1. Only visible to the session host during commander selection
2. Click the "⏭️ Force Advance to Pack Codes" button
3. Confirm the action (you'll see how many players haven't locked in)

**What happens when forced:**
- **Players who generated commanders:** A random commander from their list is automatically selected
- **Players who haven't generated commanders:** Get a placeholder commander entry
- **All players:** Pack codes are immediately generated
- Game advances to the pack codes screen

**Use cases:**
- A player disconnected and won't return
- A player is taking too long to decide
- Network issues are preventing normal game flow
- You want to bypass the selection phase for testing

### 5. Kick Player (Host Only)

The host can manually remove any player from the session at any time. This is useful as a fallback if automatic disconnection detection doesn't work properly, or if you need to remove an inactive/problematic player.

**How to use:**
1. Only visible to the session host
2. Click the "❌ Kick" button next to any player (except yourself)
3. Confirm the action
4. Player is immediately removed from the session

**What happens when a player is kicked:**
- Player is removed from the session
- Remaining players are automatically renumbered
- Kicked player sees a notification: "You have been removed from the session by the host"
- Kicked player is redirected to the join screen after 3 seconds
- **Player can rejoin** using the same session code if slots are available

**Where kick buttons appear:**
- **In Lobby:** Small red "❌ Kick" button next to each player's name
- **During Selection:** Small red "❌ Kick" button in top-right corner of each player's card

**Use cases:**
- Player is inactive and automatic disconnection hasn't triggered yet
- Player left but their session slot is still occupied
- You need to free up a slot for someone else
- Testing/troubleshooting session management

**Important notes:**
- You cannot kick yourself (obviously!)
- You cannot kick if you're not the host
- Kicked players can immediately rejoin if there are open slots
- Kicking doesn't ban players - it just removes them from the current session state

## Technical Details

### Backend Changes

**New Player Fields:**
```python
{
    'isConnected': True/False,  # Current connection status
    'lastSeen': timestamp       # Last heartbeat timestamp
}
```

**New API Endpoints:**

1. **POST `/api/sessions/rejoin`**
   - Allows player to reconnect with existing player ID
   - Validates that player belongs to the session
   - Updates connection status

2. **POST `/api/sessions/force-advance`**
   - Host-only endpoint
   - Automatically selects commanders for unlocked players
   - Generates pack codes immediately

3. **POST `/api/sessions/heartbeat`**
   - Updates player's `lastSeen` timestamp
   - Marks player as connected
   - Called automatically during polling

4. **POST `/api/sessions/kick`**
   - Host-only endpoint
   - Removes specified player from session
   - Renumbers remaining players
   - Returns updated session data

### Frontend Changes

**SessionManager Methods:**
- `rejoinSession(sessionCode, playerId)` - Rejoin with existing player ID
- `forceAdvance()` - Force advance to pack codes (host only)
- `kickPlayer(kickPlayerId)` - Remove player from session (host only)
- `sendHeartbeat()` - Mark player as connected
- `savePlayerIdToStorage(sessionCode, playerId)` - Store player ID in localStorage
- `getPlayerIdFromStorage(sessionCode)` - Retrieve stored player ID

**UI Updates:**
- Disconnected player styling (opacity, striped background, badges)
- Host controls section with force advance button
- Kick buttons on player cards (lobby and selection screens)
- Automatic reconnection on page load
- Confirmation dialogs for force advance and kick
- Kicked player notification with auto-redirect

## Best Practices

### For Players

1. **Keep the browser tab open** during the game to maintain connection
2. **Bookmark or copy the session URL** in case you need to reconnect
3. **If you disconnect**, refresh the page - you should auto-reconnect
4. **If auto-reconnect fails**, manually join using the session code

### For Hosts

1. **Wait 30-60 seconds** before marking a player as truly disconnected
2. **Use Force Advance** when:
   - A player is confirmed to have left
   - You need to complete the game despite disconnections
   - Testing the system
3. **Don't use Force Advance** if:
   - A player just disconnected temporarily
   - Someone is actively selecting their commander
4. **Use Kick Player** when:
   - Automatic disconnection hasn't triggered for an inactive player
   - You need to free up a slot immediately
   - A player is unresponsive and blocking progress
5. **Don't kick players** unnecessarily:
   - Give them time to reconnect if they just disconnected
   - Remember they can rejoin, so kicking doesn't solve persistent issues

## Troubleshooting

### Player can't reconnect

**Problem:** Page refresh doesn't auto-reconnect
**Solutions:**
1. Check that the session code is still in the URL
2. Try manually joining with the session code
3. Clear browser localStorage and join as a new player (if slots available)

### Player stuck as "Disconnected"

**Problem:** Player is connected but still shows as disconnected
**Solutions:**
1. Wait 15-30 seconds for next heartbeat cycle
2. Refresh the page to force reconnection
3. Player should actively interact with the page (generate commanders, etc.)

### Force Advance not working

**Problem:** Button doesn't appear or doesn't work
**Solutions:**
1. Verify you are the host (creator) of the session
2. Check that you're on the commander selection screen
3. Refresh the page and try again
4. Check browser console for errors

### Lost Player ID

**Problem:** Player ID was stored but can't be found
**Causes:**
- Player ID expired (>12 hours old)
- Browser localStorage was cleared
- Different browser/device than originally used

**Solution:** Join as a new player if slots are available

## Example Scenarios

### Scenario 1: Player Refreshes Browser

1. Player is in middle of selecting commander
2. Browser crashes or player refreshes
3. Page reloads with session code in URL
4. Game detects stored Player ID
5. Player automatically rejoins
6. Player returns to commander selection screen

### Scenario 2: Player Loses Network Connection

1. Player's network drops during selection
2. After 30 seconds, marked as disconnected
3. Other players see "⚠️ Disconnected" indicator
4. Player's network returns
5. Player automatically sends heartbeat
6. Player marked as connected again

### Scenario 3: Host Forces Advance

1. 3 of 4 players have locked in commanders
2. 4th player is disconnected
3. Host clicks "Force Advance to Pack Codes"
4. System randomly selects commander for disconnected player
5. Pack codes generated for all 4 players
6. Game moves to pack codes screen

### Scenario 4: Host Kicks Inactive Player

1. Player joins but becomes unresponsive
2. Host waits for disconnection detection (30 seconds)
3. Player still shows as connected but isn't responding
4. Host clicks "❌ Kick" button next to player's name
5. Player is removed from session
6. Player sees notification "You have been removed from the session"
7. Player is redirected to join screen with session code pre-filled
8. Player can choose to rejoin or leave

### Scenario 5: Kicked Player Rejoins

1. Player was kicked from session
2. Session still has open slots (< 4 players)
3. Player clicks "Join Session" with pre-filled code
4. Player enters name and rejoins
5. Gets new player number and starts fresh
6. Original selection progress is lost (fresh start)

## Future Improvements

Potential enhancements for consideration:

1. ~~**Kick Player**~~ ✅ **IMPLEMENTED** - Allow host to remove disconnected players
2. **Transfer Host** - Transfer host role if original host disconnects
3. **Session Persistence** - Save full session state to allow longer breaks
4. **Reconnect Notifications** - Show toast when players reconnect
5. **Connection Quality Indicator** - Show network strength/latency
6. **Auto-pause** - Pause timer/selection when player disconnects
7. **Ban Player** - Prevent specific player from rejoining session
8. **Spectator Mode** - Allow kicked/left players to watch without participating

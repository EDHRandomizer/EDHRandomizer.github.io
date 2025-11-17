# Perk Choice Mode - Issues Found

## 🚨 Critical Issues

### 1. **Mid-Game Join Missing Fields** (CRITICAL)
**Location:** `api/sessions.py` - `handle_join_session()`
**Problem:** When players join during 'selecting' state, they don't get `perkChoices` or `perksSelected` fields initialized.

**Current code:**
```python
session['players'].append({
    'id': player_id,
    'number': player_number,
    'name': player_name,
    'perks': perks,
    'hasSeenPerks': False,
    'commanders': [],
    # ❌ MISSING: perkChoices
    # ❌ MISSING: perksSelected
    ...
})
```

**Impact:**
- Player joins mid-game
- Frontend tries to access `player.perkChoices` → undefined/error
- Or player bypasses perk selection entirely

**Fix:** Add the missing fields when joining.

---

### 2. **Commander Generation Not Blocked** (CRITICAL)
**Location:** `docs/random_commander_game.html` - `renderPlayerSection()`
**Problem:** UI shows "Generate Commanders" button based only on `!player.commandersGenerated`, doesn't check if perks are selected in choice mode.

**Current logic:**
```javascript
${isCurrentPlayer && !player.commanderLocked && !player.commandersGenerated ? `
    <button ... onclick="generateCommanders(...)">
```

**Impact:**
- In choice mode, player can click "Generate Commanders" without selecting all perks
- Creates invalid state where commander generation happens with incomplete perk data
- Pack config won't include all perk effects

**Fix:** Check `perksSelected` in choice mode before showing button.

---

### 3. **No Late-Joiner Perk Handling** (HIGH)
**Location:** `api/perk_roller.py` - `roll_perk_choices_for_session()`
**Problem:** If a player joins after perks are rolled, they have no mechanism to get perk choices.

**Current behavior:**
- Perks rolled for initial players only
- Late joiner has empty `perkChoices`
- No way to generate choices for just one player

**Impact:**
- Player joins during 'selecting' state
- They never get perk choices
- Can't participate in perk selection phase
- May proceed without any perks

**Potential solutions:**
1. Block joining after perks rolled
2. Auto-assign random perks to late joiners (no choice)
3. Generate choices for late joiners dynamically (complex - affects rarity distribution)

---

## ⚠️ Medium Issues

### 4. **No UI Feedback During Selection Process**
**Location:** `docs/random_commander_game.html` - `showPerkChoices()`
**Problem:** No indication of how many perks selected vs. remaining.

**Impact:**
- Player might think they're done after selecting 2/3
- No progress indicator

**Fix:** Add "Selected X of Y perks" counter.

---

### 5. **Reconnection Handling Unclear**
**Location:** Frontend polling/reconnection logic
**Problem:** If player disconnects mid-selection and reconnects, unclear if their partial selections are preserved.

**Current state:**
- Backend stores selections (✅)
- Frontend re-renders from backend data (probably ✅)
- But needs testing to confirm

---

### 6. **No Visual Distinction in Lobby**
**Location:** Lobby screen
**Problem:** Players don't know choice mode is enabled until perk reveal.

**Impact:**
- Players might be confused by different experience
- No warning that selection will take longer

**Fix:** Show indicator in lobby settings display.

---

## 💡 Minor Issues

### 7. **Error Handling in Selection**
**Location:** `showPerkChoices()` click handler
**Problem:** If API call fails, perk remains selectable but state is inconsistent.

**Current:**
```javascript
try {
    const result = await sessionManager.selectPerk(slotIndex, optionIndex);
    // ... update UI
} catch (error) {
    showStatus('Failed to select perk: ' + error.message);
    // ❌ Card still shows as selected in UI
}
```

**Fix:** Revert visual state on error.

---

### 8. **No Timeout/Idle Player Handling**
**Problem:** If one player doesn't select perks, whole session stuck.

**Current behavior:**
- No timeout
- No host override to skip/random-select for idle player

**Impact:**
- Griefing potential
- Stuck sessions

**Fix:** Add timeout or host force-advance option.

---

### 9. **Mobile Responsiveness**
**Problem:** Choice cards might not look good on mobile (two cards side-by-side).

**Fix needed:** Test and adjust CSS for small screens.

---

## 📋 Summary Priority

| Priority | Issue | Impact | Effort |
|----------|-------|--------|--------|
| 🔴 P0 | Mid-game join missing fields | Breaks game | 5 min |
| 🔴 P0 | Commander gen not blocked | Invalid state | 10 min |
| 🟠 P1 | Late-joiner perk handling | Gameplay issue | 30 min |
| 🟡 P2 | Progress indicator | UX | 15 min |
| 🟡 P2 | Lobby indicator | UX | 5 min |
| 🟢 P3 | Error recovery | Polish | 10 min |
| 🟢 P3 | Timeout handling | Polish | 20 min |

## 🔧 Recommended Fixes (Immediate)

1. **Add missing fields to mid-game join** (5 min fix)
2. **Block commander generation until perks selected** (10 min fix)
3. **Block joining after perks rolled OR auto-assign** (30 min fix)

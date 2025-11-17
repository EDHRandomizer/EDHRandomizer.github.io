# Perk Choice Mode Implementation

## Overview
Implemented an alternate perk selection system where players choose between 2 perks of the same rarity for each slot, instead of receiving randomly assigned perks.

## Features
- **Toggle Setting**: Checkbox in lobby creation (like Avatar Mode)
- **Fair Distribution**: Maintains 44/29/17/8 rarity distribution and normal luck curve
- **Interactive Selection**: Players see pairs of perks and click to choose
- **Progress Tracking**: System tracks which slots are selected, only proceeds when all choices made
- **Type Deduplication**: Ensures each pair offers different perk types

## Architecture

### Backend (`api/sessions.py`)
- Added `perkChoiceMode` setting to session creation
- Added `perkChoices` and `perksSelected` fields to player data
- New endpoint: `POST /select-perk` - records player's choice for a specific slot

### Perk Rolling (`api/perk_roller.py`)
- New method: `roll_perk_choices_for_session()` - generates 2 options per slot per player
- Logic:
  1. Pre-allocate rarities using same fairness system (44/29/17/8 + luck distribution)
  2. For each player's rarity slot, generate 2 perks of that rarity
  3. Store as `perkChoices` array instead of final `perks` array
  4. Players select choices via API, building their `perks` array progressively

### Frontend (`docs/random_commander_game.html`, `sessionManager.js`)
- Checkbox: `create-perk-choice-mode` in lobby settings
- Modified `showPerkReveal()` to detect choice mode and route to `showPerkChoices()`
- New function: `showPerkChoices()` - renders clickable perk pairs
- New API method: `sessionManager.selectPerk(slotIndex, optionIndex)`
- Visual feedback: Selected perks show ✅, unselected are dimmed after choice made

## Usage

### Creating a Session
1. Check "Perk Choice Mode" when creating a lobby
2. Start game as normal

### Player Experience
1. After perks are rolled, players see "Choose Your Perks" screen
2. Each choice shows 2 cards of same rarity
3. Click a card to select it (✅ appears, other option dims)
4. Once all choices made, automatically proceeds to commander selection

### Testing
Run test script:
```bash
python test_perk_choice_mode.py
```

## Backward Compatibility
- Default: `perkChoiceMode: false` (original random assignment)
- Existing sessions work unchanged
- Mode cannot be changed mid-session

## Technical Notes
- Rarity distribution calculated globally before splitting into choices
- Luck system applies to average value of choice pairs
- Selection state persisted on backend for reconnection support
- Frontend polls for other players' selection progress

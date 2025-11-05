# Guide: Adding New Perks

This guide explains how to add new perks to the EDH Randomizer system.

## Overview

Perks are special modifiers that affect either **commander selection** or **pack drafting**. The system supports three pack sources:
- **EDHRec** - Cards from commander-specific EDHRec data
- **Scryfall** - Cards from Scryfall search queries
- **Moxfield** - Cards from Moxfield decklists

## File Structure

```
data/perks.json           # Master perk definitions (source of truth)
docs/data/perks.json      # Frontend copy (synced from data/)
api/sessions.py           # Special pack templates for drafting perks
```

## Step-by-Step Guide

### 1. Determine Perk Type

**Commander Selection Perks** - Affect which commanders are offered:
- Distribution shifts (more/less popular)
- Color filtering
- Extra commander choices
- Salt mode

**Drafting Perks** - Add extra packs or modify pack contents:
- Extra regular packs
- Special card packs (Scryfall queries, Moxfield decks)
- Budget/bracket upgrades
- Manabase packs

### 2. Add Special Pack Template (Drafting Perks Only)

If your perk adds a special pack, add a template to `api/sessions.py` in the `special_pack_templates` dictionary:

#### EDHRec Pack Example
```python
'your_pack_name': {
    'name': 'Display Name',
    'source': 'edhrec',
    'count': 1,
    'slots': [{
        'cardType': 'creatures',      # creatures, instants, sorceries, etc.
        'budget': 'any',               # any, budget, expensive
        'bracket': 'any',              # any, 1, 2, 3, 4
        'count': 15
    }]
}
```

#### Scryfall Pack Example
```python
'your_pack_name': {
    'name': 'Display Name',
    'source': 'scryfall',
    'count': 1,
    'useCommanderColorIdentity': True,  # Auto-filter by commander colors
    'slots': [{
        'query': 'https://scryfall.com/search?q=is%3Amdfc+type%3Aland',
        'count': 15
    }]
}
```

**Tip:** Build your query on [Scryfall.com](https://scryfall.com) first, then copy the URL.

#### Moxfield Pack Example
```python
'your_pack_name': {
    'name': 'Display Name',
    'source': 'moxfield',
    'count': 1,
    'useCommanderColorIdentity': True,  # Auto-filter by commander colors
    'slots': [{
        'deckUrl': None,  # Will be filled from perk effect
        'count': 3
    }]
}
```

### 3. Add Perk Definition to perks.json

Edit `data/perks.json` and add a new perk type:

#### Commander Selection Perk
```json
{
  "type": "your_perk_type",
  "name": "Display Name",
  "mutuallyExclusive": true,
  "perks": [
    {
      "id": "your_perk_id",
      "name": "Perk Name",
      "rarity": "common",
      "description": "What the perk does",
      "perkPhase": "commander_selection",
      "effects": {
        "distributionShift": -100,
        "commanderQuantity": 1,
        "colorFilterMode": "exclude",
        "saltMode": "salty"
      }
    }
  ]
}
```

#### Drafting Perk
```json
{
  "type": "your_perk_type",
  "name": "Display Name",
  "mutuallyExclusive": false,
  "perks": [
    {
      "id": "your_perk_id",
      "name": "Perk Name",
      "rarity": "uncommon",
      "description": "Get 15 special cards",
      "perkPhase": "drafting",
      "effects": {
        "specialPack": "your_pack_name",
        "specialPackCount": 15,
        "moxfieldDeck": "deck-id-here"
      }
    }
  ]
}
```

### 4. Perk Properties Reference

#### Top Level
- **type** - Unique identifier for the perk category
- **name** - Display name for the category
- **mutuallyExclusive** - `true` = only one perk from this type can be rolled

#### Individual Perk
- **id** - Unique identifier
- **name** - Display name (shown to player)
- **rarity** - `common`, `uncommon`, `rare`, or `mythic`
- **weightMultiplier** - (Optional) Multiplier for probability (default: 1.0)
  - `1.5` = 50% more likely than other perks of same rarity
  - `0.5` = 50% less likely than other perks of same rarity
  - `2.0` = Twice as likely (use sparingly)
- **description** - Explanation of what the perk does
- **perkPhase** - `commander_selection` or `drafting`
- **effects** - Object containing perk effects (see below)

#### Effect Types

**Commander Selection:**
```json
{
  "distributionShift": -100,          // Shift popularity (-500 to 500)
  "commanderQuantity": 3,             // Extra commanders to choose from
  "colorFilterMode": "exclude",       // "exclude", "include", or "exact"
  "colorFilterCount": 1,              // Number of colors to filter
  "saltMode": "salty"                 // Use salty commander pool
}
```

**Color Filter Modes:**
- `"exclude"`: Player selects colors to exclude (colorless commanders included)
- `"include"`: Player selects colors that must be in commander (colorless commanders excluded)
- `"exact"`: Player selects exact color identity (checkbox for colorless 'C' is available)

**Drafting:**
```json
{
  "packQuantity": 1,                  // Extra regular packs
  "specialPack": "pack_name",         // Special pack template name
  "specialPackCount": 15,             // Cards in special pack
  "moxfieldDeck": "deck-id",          // Moxfield deck ID (for moxfield source)
  "budgetUpgradePacks": 1,            // Extra packs with budget filter
  "budgetUpgradeType": "expensive",   // "any" or "expensive"
  "bracketUpgrade": 4,                // Bracket level (1-4)
  "bracketUpgradePacks": 1,           // Extra packs at bracket
  "manual": true                      // Manual/physical powerup (no code effect)
}
```

### 5. Rarity Weights

Default distribution:
- **Common:** 45%
- **Uncommon:** 30%
- **Rare:** 18%
- **Mythic:** 7%

**Weight Multipliers:**

You can fine-tune individual perk probabilities using `weightMultiplier`:
- Omit the field (or set to `1.0`) for default probability
- Use `1.5` to make a perk 50% more common
- Use `0.5` to make a perk 50% less common
- Use `2.0` to double the probability

**Example:**
```json
{
  "id": "color_restrict",
  "name": "Restrict 1 Color",
  "rarity": "common",
  "weightMultiplier": 1.5,  // 50% more common than other commons
  "description": "Exclude one color from commander pool"
}
```

**Calculation:**
```
Effective Weight = Base Rarity Weight × Weight Multiplier
Example: 45 (common) × 1.5 = 67.5 effective weight
```

### 6. Sync and Test

```bash
# Sync perks.json to frontend
python sync_perks.py

# Run tests to verify
python test_perks_loading.py

# Commit changes
git add -A
git commit -m "Add [perk name] perk"
git push
```

### 7. Deployment

- **Vercel** (API) auto-deploys when you push to main
- **GitHub Pages** (Frontend) auto-deploys when you push to main
- Wait ~1-2 minutes for deployments to complete

## Examples

### Example 1: Simple Extra Pack Perk
```json
{
  "type": "extra_packs",
  "name": "Extra Packs",
  "mutuallyExclusive": false,
  "perks": [
    {
      "id": "extra_pack_1",
      "name": "+1 Pack",
      "rarity": "common",
      "description": "Get 1 extra regular pack",
      "perkPhase": "drafting",
      "effects": {
        "packQuantity": 1
      }
    }
  ]
}
```

### Example 2: Scryfall Query Perk

**Step 1:** Add template to `api/sessions.py`:
```python
'mdfc_lands': {
    'name': 'MDFC Lands',
    'source': 'scryfall',
    'count': 1,
    'useCommanderColorIdentity': True,
    'slots': [{
        'query': 'https://scryfall.com/search?q=is%3Amdfc+type%3Aland',
        'count': 1
    }]
}
```

**Step 2:** Add to `data/perks.json`:
```json
{
  "type": "mdfc_lands",
  "name": "MDFC Lands",
  "mutuallyExclusive": false,
  "perks": [
    {
      "id": "mdfc_pilled",
      "name": "MDFC-Pilled",
      "rarity": "common",
      "description": "Get a pack of 15 MDFC lands",
      "perkPhase": "drafting",
      "effects": {
        "specialPack": "mdfc_lands",
        "specialPackCount": 15
      }
    }
  ]
}
```

### Example 3: Moxfield Deck Perk

**Step 1:** Add template to `api/sessions.py`:
```python
'banned': {
    'name': 'Banned Card',
    'source': 'moxfield',
    'count': 1,
    'useCommanderColorIdentity': True,
    'slots': [{
        'deckUrl': None,  # Filled from perk effect
        'count': 1
    }]
}
```

**Step 2:** Add to `data/perks.json`:
```json
{
  "type": "banned_cards",
  "name": "Banned Cards",
  "mutuallyExclusive": false,
  "perks": [
    {
      "id": "banned_cards_3",
      "name": "Banned Cards",
      "rarity": "mythic",
      "description": "Get 3 random banned cards",
      "perkPhase": "drafting",
      "effects": {
        "specialPack": "banned",
        "specialPackCount": 3,
        "moxfieldDeck": "5OpLbDPxxkG6yAmxTT7YjA"
      }
    }
  ]
}
```

## Important Notes

### Duplicate Prevention
The system automatically prevents the same card from appearing multiple times across:
- Different packs
- Different sources (EDHRec, Scryfall, Moxfield)
- All pack types in a single generation

### Color Identity Filtering
When `useCommanderColorIdentity: true`:
- Scryfall queries automatically append color identity filter
- Moxfield decks are filtered to match commander colors
- EDHRec already provides color-filtered cards

### VS Code Encoding Issue
⚠️ **Important:** VS Code may add a UTF-8 BOM when saving JSON files, which breaks the parser.

After editing `data/perks.json`, always run:
```bash
python sync_perks.py
python test_perks_loading.py
```

The test will catch BOM issues and the sync script fixes encoding.

## Troubleshooting

**Perk not appearing in rolls:**
1. Check JSON syntax with `python test_perks_loading.py`
2. Verify perk type is in `perkTypes` array
3. Check rarity is valid: `common`, `uncommon`, `rare`, `mythic`
4. Run `python sync_perks.py` to update frontend

**Special pack not generating:**
1. Verify special pack template name matches `effects.specialPack`
2. For Moxfield: check deck ID is correct
3. For Scryfall: test query on scryfall.com first
4. Check API logs for errors

**Cards filtered incorrectly:**
1. Verify `useCommanderColorIdentity` setting
2. Test Scryfall query without color filters first
3. Check if commander color identity is being passed correctly

## Testing Your Perk

1. **Local test:**
   ```bash
   python test_perks_loading.py
   ```

2. **Create test session:**
   - Go to https://edhrandomizer.github.io/random_commander_game.html
   - Create session with 5+ perks
   - Roll perks multiple times to see if yours appears
   - Lock in commander and generate packs
   - Verify special packs appear correctly

3. **Check pack code:**
   - Copy pack code
   - Use in TTS: `edhrandomizer [CODE]`
   - Verify packs spawn correctly

## Questions?

Check existing perks in `data/perks.json` for more examples, or look at the special pack templates in `api/sessions.py` for supported features.

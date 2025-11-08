# EDH Pack Generator - Complete JSON Configuration Guide

**Version:** 2.0  
**Last Updated:** November 7, 2025  
**API Endpoint:** `https://edhrandomizer-api.vercel.app/api/index`

This is the master reference for creating custom JSON pack configurations for the EDH Pack Generator system. Use this guide to create unique, fun pack configurations for your playgroup.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [JSON Configuration Structure](#json-configuration-structure)
3. [Pack Sources (EDHRec, Scryfall, Moxfield)](#pack-sources)
4. [EDHRec Pack Configuration](#edhrec-pack-configuration)
5. [Scryfall Pack Configuration](#scryfall-pack-configuration)
6. [Moxfield Pack Configuration](#moxfield-pack-configuration)
7. [Complete Field Reference](#complete-field-reference)
8. [Examples Library](#examples-library)
9. [Best Practices & Tips](#best-practices--tips)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

The EDH Pack Generator creates randomized booster packs for Commander gameplay. It supports three card sources:

1. **EDHRec** - Generates packs from EDHRec's commander recommendations (requires commander URL)
2. **Scryfall** - Uses Scryfall search queries for custom card pools
3. **Moxfield** - Pulls cards from existing Moxfield decklists

### How It Works

1. **Upload JSON config** to a public URL (GitHub, Vercel, etc.) or host locally
2. **Paste URL** into TTS mod "Pack Config URL" field
3. **Click Generate** - API fetches config, validates, and creates packs
4. **Packs spawn** in Tabletop Simulator with custom names and compositions

### Key Features

- **Mix pack types** - Combine EDHRec, Scryfall, and Moxfield in one config
- **Custom pack names** - Name your packs anything you want
- **Flexible slots** - Each pack can have multiple slot types with different rules
- **Commander color filtering** - Automatically filter cards by commander colors
- **Power level control** - Target specific brackets (2-4) or budget tiers
- **Duplicate prevention** - Global setting prevents same card in multiple packs

---

## JSON Configuration Structure

### Root Structure

```json
{
  "packTypes": [
    {
      "name": "My Custom Pack",
      "source": "edhrec",
      "count": 3,
      "useCommanderColorIdentity": true,
      "slots": [
        { /* slot configuration */ }
      ]
    }
  ]
}
```

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `packTypes` | Array | ✅ Yes | Array of pack type definitions. Each pack type can generate multiple packs. |

### Pack Type Object

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | String | ❌ No | Auto-generated | Pack display name. If omitted, API generates intelligent name based on source and commander. |
| `source` | String | ❌ No | `"edhrec"` | Card source: `"edhrec"`, `"scryfall"`, or `"moxfield"` |
| `count` | Number | ✅ Yes | - | Number of packs to generate of this type |
| `useCommanderColorIdentity` | Boolean | ❌ No | `true` for EDHRec, `false` for Moxfield | Whether to filter cards by commander color identity |
| `slots` | Array | ✅ Yes | - | Array of slot definitions. Each slot adds cards to the pack. |

---

## Pack Sources

### EDHRec Source (`"source": "edhrec"`)

**Requires:** Commander URL in TTS mod  
**Best For:** Commander-specific recommendations, synergy-focused packs, power level control

```json
{
  "name": "Atraxa Synergy Pack",
  "source": "edhrec",
  "count": 3,
  "useCommanderColorIdentity": true,
  "slots": [
    { "cardType": "highsynergycards", "count": 10, "bracket": 3 },
    { "cardType": "weighted", "count": 5, "budget": "budget", "bracket": 2 }
  ]
}
```

### Scryfall Source (`"source": "scryfall"`)

**Requires:** Nothing (commander URL optional for color filtering)  
**Best For:** Theme packs, banned cards, specific mechanics, custom queries

```json
{
  "name": "Banned Commander Cards",
  "source": "scryfall",
  "count": 2,
  "useCommanderColorIdentity": false,
  "slots": [
    { 
      "query": "https://scryfall.com/search?q=banned%3Acommander",
      "count": 15 
    }
  ]
}
```

### Moxfield Source (`"source": "moxfield"`)

**Requires:** Nothing (commander URL optional for color filtering)  
**Best For:** Curated card pools, existing decklists, specific card sets

```json
{
  "name": "Precon Upgrade Pool",
  "source": "moxfield",
  "count": 3,
  "useCommanderColorIdentity": true,
  "slots": [
    { 
      "deckUrl": "https://moxfield.com/decks/YOUR-DECK-ID",
      "count": 15 
    }
  ]
}
```

---

## EDHRec Pack Configuration

### Slot Fields for EDHRec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `cardType` | String | ✅ Yes | - | Card selection strategy (see table below) |
| `count` | Number | ✅ Yes | - | Number of cards for this slot |
| `budget` | String | ❌ No | `"any"` | Budget tier: `"any"`, `"budget"`, `"expensive"` |
| `bracket` | Number/String | ❌ No | `"any"` | Power bracket: `"any"`, `2`, `3`, `4` (use 4 for gamechangers) |

### Available `cardType` Values

#### Selection Strategies

| cardType | Description | Use Case |
|----------|-------------|----------|
| `weighted` | Uses average deck type distribution (realistic mana curve) | Balanced, playable packs |
| `random` | Equal probability across all card types | Chaotic variety |

#### Specific Card Types

| cardType | Description |
|----------|-------------|
| `creatures` | Creature cards only |
| `instants` | Instant cards only |
| `sorceries` | Sorcery cards only |
| `enchantments` | Enchantment cards only |
| `planeswalkers` | Planeswalker cards only |
| `battles` | Battle cards only |
| `lands` | Land cards (non-basic utility lands) |
| `utilityartifacts` | Utility artifact cards |
| `manaartifacts` | Mana-producing artifacts |

#### EDHRec Categories

| cardType | Description |
|----------|-------------|
| `newcards` | Recently released cards for this commander |
| `highsynergycards` | Cards with high synergy rating |
| `highsynergy` | Deterministic highest synergy picks (no randomness; always takes the top synergy scores first) |
| `topcards` | Most popular cards for this commander |
| `gamechangers` | High-impact, game-changing cards (use bracket 4) |

### Budget Tiers

| Value | Description | Typical Price Range |
|-------|-------------|---------------------|
| `"any"` | All price ranges (uses TTS mod setting) | - |
| `"budget"` | Budget-friendly cards | < $5 typically |
| `"expensive"` | Premium cards | > $5 typically |

### Power Brackets

| Value | Path | Description |
|-------|------|-------------|
| `"any"` | Default | Uses TTS mod bracket setting |
| `2` | `/core` | Budget-friendly, foundational cards |
| `3` | `/upgraded` | Mid-power optimized decks |
| `4` | `/optimized` | High-power competitive cards |

**Note:** Use bracket `4` for `gamechangers` type, as brackets 2-3 have minimal game changers.

### EDHRec Examples

#### Balanced Starter Pack
```json
{
  "name": "Balanced Starter",
  "source": "edhrec",
  "count": 5,
  "slots": [
    { "cardType": "weighted", "count": 12, "budget": "budget", "bracket": 2 },
    { "cardType": "lands", "count": 3, "budget": "any", "bracket": 2 }
  ]
}
```

#### Synergy Focus
```json
{
  "name": "High Synergy Build",
  "source": "edhrec",
  "count": 3,
  "slots": [
    { "cardType": "highsynergycards", "count": 8, "bracket": 3 },
    { "cardType": "topcards", "count": 5, "bracket": 3 },
    { "cardType": "lands", "count": 2, "bracket": 2 }
  ]
}
```

#### Game Changers Pack
```json
{
  "name": "Game Changers",
  "source": "edhrec",
  "count": 2,
  "slots": [
    { "cardType": "gamechangers", "count": 10, "bracket": 4 },
    { "cardType": "weighted", "count": 5, "bracket": 4 }
  ]
}
```

#### Budget Creatures
```json
{
  "name": "Budget Creatures",
  "source": "edhrec",
  "count": 4,
  "slots": [
    { "cardType": "creatures", "count": 15, "budget": "budget", "bracket": 2 }
  ]
}
```

---

## Scryfall Pack Configuration

### Slot Fields for Scryfall

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | String | ✅ Yes | - | Full Scryfall search URL or query string |
| `count` | Number | ✅ Yes | - | Number of random cards to select from query results |
| `useCommanderColorIdentity` | Boolean | ❌ No | Pack-level setting | Override pack-level color filtering for this slot |
| `colorComplexityWeighting` | Boolean | ❌ No | `true` | Enable aggressive weighting toward multi-color cards. Multipliers: colorless=1x, mono=1x, dual=3x, triple=10x, four=20x, five=30x |

### Scryfall Query Tips

1. **Use full URLs** - Copy directly from Scryfall search page
2. **URL encode special characters** - `%3A` for `:`, `%20` for space, `%22` for `"`
3. **Test queries** on Scryfall.com first
4. **Common operators:**
   - `banned:commander` - Banned in Commander
   - `legal:commander` - Legal in Commander
   - `type:creature` - Creature cards
   - `cmc<=3` - Mana value 3 or less
   - `color:WU` - White and/or blue cards
   - `is:spell` - Non-land cards
   - `rarity:mythic` - Mythic rares only
   - `set:mh3` - From Modern Horizons 3
   - `oracle:"draw a card"` - Text search

### Scryfall Examples

#### Banned Cards Chaos
```json
{
  "name": "Banned Chaos",
  "source": "scryfall",
  "count": 3,
  "useCommanderColorIdentity": false,
  "slots": [
    {
      "query": "https://scryfall.com/search?q=banned%3Acommander+-t%3Aconspiracy+-o%3Aante",
      "count": 15
    }
  ]
}
```

#### Cheap Instants
```json
{
  "name": "Budget Interaction",
  "source": "scryfall",
  "count": 5,
  "useCommanderColorIdentity": true,
  "slots": [
    {
      "query": "https://scryfall.com/search?q=type%3Ainstant+cmc%3C%3D3+usd%3C1",
      "count": 10
    }
  ]
}
```

#### Planeswalker Pack
```json
{
  "name": "Planeswalker Friends",
  "source": "scryfall",
  "count": 2,
  "slots": [
    {
      "query": "https://scryfall.com/search?q=type%3Aplaneswalker+legal%3Acommander",
      "count": 8,
      "useCommanderColorIdentity": true
    }
  ]
}
```

#### Specific Set
```json
{
  "name": "Modern Horizons 3",
  "source": "scryfall",
  "count": 4,
  "slots": [
    {
      "query": "https://scryfall.com/search?q=set%3Amh3+is%3Aspell",
      "count": 15
    }
  ]
}
```

---

## Moxfield Pack Configuration

### Slot Fields for Moxfield

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `deckUrl` | String | ✅ Yes | - | Full Moxfield deck URL |
| `count` | Number | ✅ Yes | - | Number of random cards to select from deck |
| `useCommanderColorIdentity` | Boolean | ❌ No | Pack-level setting | Override pack-level color filtering for this slot |
| `colorComplexityWeighting` | Boolean | ❌ No | `true` | Enable aggressive weighting toward multi-color cards. Multipliers: colorless=1x, mono=1x, dual=3x, triple=10x, four=20x, five=30x |

### Moxfield URL Format

- **Unlisted or public decks:** `https://moxfield.com/decks/DECK-ID`
- **Must be accessible via URL** (not private)
- **Commander is excluded** automatically from card pool
- **Basic lands excluded** automatically

### Moxfield Examples

#### Precon Upgrade Pool
```json
{
  "name": "Precon Upgrades",
  "source": "moxfield",
  "count": 3,
  "useCommanderColorIdentity": true,
  "slots": [
    {
      "deckUrl": "https://moxfield.com/decks/Ph3OYF_lLkuBhDpiP1qwuQ",
      "count": 15
    }
  ]
}
```

#### Mixed Deck Sources
```json
{
  "name": "Budget + Premium Mix",
  "source": "moxfield",
  "count": 2,
  "useCommanderColorIdentity": false,
  "slots": [
    {
      "deckUrl": "https://moxfield.com/decks/budget-deck-id",
      "count": 10
    },
    {
      "deckUrl": "https://moxfield.com/decks/premium-deck-id",
      "count": 5
    }
  ]
}
```

---

## Complete Field Reference

### Root Object

```typescript
{
  "packTypes": PackType[]  // Array of pack type definitions
}
```

### PackType Object

```typescript
{
  "name"?: string,                          // Optional: Custom pack name (auto-generated if omitted)
  "source"?: "edhrec" | "scryfall" | "moxfield",  // Default: "edhrec"
  "count": number,                          // Required: Number of packs to generate
  "useCommanderColorIdentity"?: boolean,    // Default: true for EDHRec, false for Moxfield
  "slots": Slot[]                           // Required: Array of slot definitions
}
```

### Slot Object (EDHRec)

```typescript
{
  "cardType": string,      // Required: See cardType table
  "count": number,         // Required: Number of cards
  "budget"?: "any" | "budget" | "expensive",  // Default: "any"
  "bracket"?: "any" | 2 | 3 | 4              // Default: "any"
}
```

### Slot Object (Scryfall)

```typescript
{
  "query": string,                        // Required: Scryfall search URL
  "count": number,                        // Required: Number of cards to select
  "useCommanderColorIdentity"?: boolean   // Optional: Override pack-level setting
}
```

### Slot Object (Moxfield)

```typescript
{
  "deckUrl": string,                      // Required: Moxfield deck URL
  "count": number,                        // Required: Number of cards to select
  "useCommanderColorIdentity"?: boolean   // Optional: Override pack-level setting
}
```

---

## Examples Library

### Mixed Sources Example

Combine EDHRec, Scryfall, and Moxfield in one config:

```json
{
  "packTypes": [
    {
      "name": "Commander Staples",
      "source": "edhrec",
      "count": 2,
      "slots": [
        { "cardType": "topcards", "count": 10, "bracket": 3 },
        { "cardType": "lands", "count": 5, "bracket": 2 }
      ]
    },
    {
      "name": "Banned Fun",
      "source": "scryfall",
      "count": 1,
      "useCommanderColorIdentity": false,
      "slots": [
        {
          "query": "https://scryfall.com/search?q=banned%3Acommander",
          "count": 15
        }
      ]
    },
    {
      "name": "Curated Upgrades",
      "source": "moxfield",
      "count": 2,
      "slots": [
        {
          "deckUrl": "https://moxfield.com/decks/YOUR-DECK-ID",
          "count": 12
        }
      ]
    }
  ]
}
```

### Progressive Power Levels

Different power brackets in separate packs:

```json
{
  "packTypes": [
    {
      "name": "Starter Pack - Bracket 2",
      "source": "edhrec",
      "count": 3,
      "slots": [
        { "cardType": "weighted", "count": 12, "budget": "budget", "bracket": 2 },
        { "cardType": "lands", "count": 3, "bracket": 2 }
      ]
    },
    {
      "name": "Mid Power - Bracket 3",
      "source": "edhrec",
      "count": 2,
      "slots": [
        { "cardType": "weighted", "count": 10, "bracket": 3 },
        { "cardType": "highsynergycards", "count": 5, "bracket": 3 }
      ]
    },
    {
      "name": "High Power - Bracket 4",
      "source": "edhrec",
      "count": 1,
      "slots": [
        { "cardType": "gamechangers", "count": 8, "bracket": 4 },
        { "cardType": "weighted", "count": 7, "budget": "expensive", "bracket": 4 }
      ]
    }
  ]
}
```

### Theme Packs

Create themed packs with Scryfall:

```json
{
  "packTypes": [
    {
      "name": "Draw Power",
      "source": "scryfall",
      "count": 3,
      "slots": [
        {
          "query": "https://scryfall.com/search?q=oracle%3A%22draw+a+card%22+type%3Acreature",
          "count": 8
        },
        {
          "query": "https://scryfall.com/search?q=oracle%3A%22draw+cards%22+type%3Ainstant",
          "count": 7
        }
      ]
    },
    {
      "name": "Artifact Synergy",
      "source": "scryfall",
      "count": 2,
      "slots": [
        {
          "query": "https://scryfall.com/search?q=type%3Aartifact+is%3Aspell",
          "count": 10
        },
        {
          "query": "https://scryfall.com/search?q=oracle%3A%22artifact+you+control%22",
          "count": 5
        }
      ]
    }
  ]
}
```

### Budget vs Premium

Separate budget and expensive packs:

```json
{
  "packTypes": [
    {
      "name": "Budget Pack",
      "source": "edhrec",
      "count": 5,
      "slots": [
        { "cardType": "weighted", "count": 15, "budget": "budget", "bracket": 2 }
      ]
    },
    {
      "name": "Premium Pack",
      "source": "edhrec",
      "count": 2,
      "slots": [
        { "cardType": "weighted", "count": 10, "budget": "expensive", "bracket": 4 },
        { "cardType": "gamechangers", "count": 5, "bracket": 4 }
      ]
    }
  ]
}
```

---

## Best Practices & Tips

### General Tips

1. **Start simple** - Test with 1-2 pack types first
2. **Use descriptive names** - Help players understand what's in the pack
3. **Test queries on Scryfall** before adding to config
4. **Consider pack size** - 15 cards is standard booster size
5. **Mix sources** for variety and replay value

### EDHRec Packs

- **Use `weighted` for balanced packs** - Mimics real deck distributions
- **Combine cardTypes** - Mix specific types with weighted/random
- **Match brackets to meta** - Use bracket 2-3 for casual, 4 for competitive
- **Use `gamechangers` sparingly** - These are high-impact, game-warping cards
- **Consider budget** - Mix budget/expensive for progression

### Scryfall Packs

- **Test queries** - Scryfall's syntax is powerful but specific
- **Use color filtering wisely** - `useCommanderColorIdentity: true` for on-theme packs
- **Exclude problematic cards** - Add `-t:conspiracy -o:ante` to avoid game-breaking cards
- **Check result counts** - Make sure query returns enough cards for your `count`
- **Combine multiple queries** - Use separate slots for different card types

### Moxfield Packs

- **Public decks only** - Ensure decks are publicly accessible
- **Curate deck contents** - Remove cards you don't want in the pool
- **Update decks dynamically** - Change Moxfield deck to change pack contents
- **Color filtering** - Set `false` to allow any cards from deck

### Pack Naming

- **Auto-generation works well** - Leave `name` field empty for smart names
- **Custom names add flair** - Use for theme packs or special events
- **Format:** `"Theme | Details"` - Example: `"Artifacts | Budget Mana Rocks"`
- **Keep it short** - Long names may wrap in TTS UI

### Performance

- **Limit total packs** - Keep total packs under 20 for reasonable generation time
- **Reasonable slot counts** - 1-20 cards per slot is ideal
- **Avoid duplicate slots** - Combine similar slots to reduce API calls
- **Cache queries** - API caches Scryfall results during request

---

## Troubleshooting

### Common Errors

#### "Missing commander_url parameter"

**Cause:** EDHRec packs require a commander URL  
**Fix:** 
- Enter commander URL in TTS mod before clicking Generate
- OR switch to Scryfall/Moxfield source

#### "No packs generated"

**Cause:** Config might be empty or invalid JSON  
**Fix:**
- Validate JSON syntax (use jsonlint.com)
- Ensure `packTypes` array is not empty
- Check that all required fields are present

#### "Scryfall query returned no cards"

**Cause:** Query too restrictive or syntax error  
**Fix:**
- Test query on scryfall.com first
- Check URL encoding (spaces = `%20`, etc.)
- Verify query returns results on Scryfall website

#### "Moxfield deck not found"

**Cause:** Deck is private or URL is incorrect  
**Fix:**
- Ensure deck is publicly accessible
- Double-check deck URL format: `https://moxfield.com/decks/DECK-ID`
- Try accessing deck in browser while logged out

#### "Config requires commander"

**Cause:** JSON config contains EDHRec pack types  
**Fix:**
- Enter commander URL in TTS mod
- OR change EDHRec packs to Scryfall/Moxfield

### Validation Checklist

Before using a config:

- [ ] Valid JSON syntax
- [ ] `packTypes` is an array with at least one pack type
- [ ] Each pack type has `count` and `slots`
- [ ] Each slot has required fields for its source:
  - EDHRec: `cardType`, `count`
  - Scryfall: `query`, `count`
  - Moxfield: `deckUrl`, `count`
- [ ] Total pack count is reasonable (< 20)
- [ ] Scryfall queries tested on scryfall.com
- [ ] Moxfield decks are public and accessible

### Testing Configs

1. **Validate JSON** - Use online validator (jsonlint.com)
2. **Host config** - Upload to GitHub, Vercel, or other public URL
3. **Test in TTS** - Paste URL into Pack Config field
4. **Check status** - Watch status text for errors
5. **Iterate** - Adjust and re-test as needed

### Getting Help

If you encounter issues:

1. **Check console logs** - TTS console shows detailed errors
2. **Validate JSON** - Ensure proper syntax
3. **Test components separately** - Try individual pack types
4. **Simplify config** - Start with minimal example and add complexity
5. **Check API status** - Ensure Vercel deployment is active

---

## Hosting Your Configs

### Option 1: GitHub Pages

1. Create GitHub repository
2. Add JSON file to `docs/` folder
3. Enable GitHub Pages
4. URL: `https://YOUR-USERNAME.github.io/REPO-NAME/config.json`

### Option 2: GitHub Raw

1. Push JSON to GitHub repository
2. Navigate to file in browser
3. Click "Raw" button
4. Copy URL
5. URL format: `https://raw.githubusercontent.com/USER/REPO/main/config.json`

### Option 3: Vercel

1. Create `/public/config.json` in project
2. Deploy to Vercel
3. URL: `https://YOUR-PROJECT.vercel.app/config.json`

### Option 4: Any Web Host

- Upload JSON to any web server
- Ensure file is publicly accessible
- Use full HTTPS URL

---

## Advanced Techniques

### Dynamic Pack Counts Based on Players

Create configs for different player counts:

```json
{
  "packTypes": [
    {
      "name": "3-Player Game Pack",
      "source": "edhrec",
      "count": 3,
      "slots": [
        { "cardType": "weighted", "count": 15, "bracket": 3 }
      ]
    }
  ]
}
```

Save as `3-player.json`, `4-player.json`, etc., and swap URLs based on game size.

### Seasonal/Event Packs

Create special configs for holidays or events:

```json
{
  "packTypes": [
    {
      "name": "Halloween Horror",
      "source": "scryfall",
      "count": 4,
      "slots": [
        {
          "query": "https://scryfall.com/search?q=type%3Azombie+OR+type%3Avampire+OR+type%3Awarewolf",
          "count": 15
        }
      ]
    }
  ]
}
```

### Progression Systems

Create configs that get progressively stronger:

- **Week 1:** `starter-packs.json` (bracket 2, budget)
- **Week 2:** `upgraded-packs.json` (bracket 3, mixed budget)
- **Week 3:** `premium-packs.json` (bracket 4, expensive)

Players upgrade over time by unlocking new pack tiers.

### Custom Draft Format

Create multiple pack types for draft:

```json
{
  "packTypes": [
    {
      "name": "Draft Pack A - Creatures",
      "source": "edhrec",
      "count": 8,
      "slots": [
        { "cardType": "creatures", "count": 10, "bracket": 2 },
        { "cardType": "lands", "count": 5, "bracket": 2 }
      ]
    },
    {
      "name": "Draft Pack B - Spells",
      "source": "edhrec",
      "count": 8,
      "slots": [
        { "cardType": "instants", "count": 5, "bracket": 2 },
        { "cardType": "sorceries", "count": 5, "bracket": 2 },
        { "cardType": "enchantments", "count": 5, "bracket": 2 }
      ]
    }
  ]
}
```

---

## Quick Reference Card

### EDHRec Slot Template
```json
{
  "cardType": "weighted",
  "count": 10,
  "budget": "any",
  "bracket": 2
}
```

### Scryfall Slot Template
```json
{
  "query": "https://scryfall.com/search?q=YOUR-QUERY",
  "count": 10,
  "useCommanderColorIdentity": true
}
```

### Moxfield Slot Template
```json
{
  "deckUrl": "https://moxfield.com/decks/DECK-ID",
  "count": 10,
  "useCommanderColorIdentity": false
}
```

### Full Pack Type Template
```json
{
  "name": "My Pack Name",
  "source": "edhrec",
  "count": 3,
  "useCommanderColorIdentity": true,
  "slots": [
    { /* slot config */ }
  ]
}
```

---

## Summary

This guide covers everything needed to create custom JSON pack configurations:

✅ **Three sources:** EDHRec, Scryfall, Moxfield  
✅ **Complete field reference:** All options documented  
✅ **Real examples:** Copy-paste ready configs  
✅ **Best practices:** Tips for great pack design  
✅ **Troubleshooting:** Common issues and solutions  

**Next Steps:**
1. Choose a pack concept
2. Pick your source(s)
3. Build JSON config
4. Host publicly
5. Test in TTS mod
6. Share with your playgroup!

**Happy pack building!** 🎉

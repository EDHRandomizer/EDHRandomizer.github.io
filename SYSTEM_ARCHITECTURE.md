# EDH Randomizer - Complete System Architecture

**Version:** 2.0  
**Last Updated:** November 2, 2025  
**Project:** EDH Commander Randomizer with Tabletop Simulator Integration

This document provides a comprehensive overview of the entire EDH Randomizer system architecture, covering all components, APIs, data flows, and integration points.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Breakdown](#component-breakdown)
4. [Data Pipeline](#data-pipeline)
5. [API Integrations](#api-integrations)
6. [Multiplayer Game Mode](#multiplayer-game-mode)
7. [Pack Generation System](#pack-generation-system)
8. [Powerup System](#powerup-system)
9. [Tabletop Simulator Integration](#tabletop-simulator-integration)
10. [Deployment & Infrastructure](#deployment--infrastructure)
11. [Testing & Validation](#testing--validation)
12. [Related Documentation](#related-documentation)

---

## System Overview

The EDH Randomizer is a comprehensive system that generates randomized Commander deck building challenges and integrates with Tabletop Simulator (TTS) for virtual gameplay. The system consists of three main components:

### Core Components

1. **Web Application** (GitHub Pages)
   - Static website hosted at `edhrandomizer.github.io`
   - Commander randomization UI
   - Multiplayer game mode interface
   - Pack code generation client

2. **Backend API** (Vercel Serverless)
   - Session management for multiplayer games
   - Pack code storage and retrieval
   - Powerup rolling and effect combination
   - Pack configuration generation

3. **TTS Mod** (Tabletop Simulator)
   - Pack code importer
   - Card spawning system
   - Deck loader integration
   - In-game UI

### Data Sources

- **EDHREC API** - Commander recommendations and card data
- **Scryfall API** - Card search and metadata
- **Moxfield API** - Decklist imports
- **Local CSV Data** - Cached commander rankings

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            User Flow                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  GitHub Pages Website (edhrandomizer.github.io)                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Single Player Mode                                           │      │
│  │  - Commander randomization                                    │      │
│  │  - Color/rank filtering                                       │      │
│  │  - Time period selection (week/month/2-year)                  │      │
│  │  - Direct commander selection                                 │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Multiplayer Game Mode                                        │      │
│  │  - Session creation/joining                                   │      │
│  │  - Powerup rolling                                            │      │
│  │  - Commander selection                                        │      │
│  │  - Pack code generation                                       │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
                │                                │
                │ (EDHREC URL)                   │ (Session API calls)
                ▼                                ▼
┌───────────────────────┐          ┌─────────────────────────────────────┐
│  EDHREC API           │          │  Vercel API (edhrandomizer-api)     │
│  - Commander data     │          │  Endpoint: /api/sessions/*          │
│  - Card recommendations│         │                                     │
│  - Synergy ratings    │          │  ┌──────────────────────────────┐  │
└───────────────────────┘          │  │  Session Management          │  │
                                   │  │  - Create/join sessions      │  │
                                   │  │  - Roll powerups             │  │
┌───────────────────────┐          │  │  - Lock commanders           │  │
│  Scryfall API         │          │  │  - Generate pack codes       │  │
│  - Card search        │◄─────────┤  └──────────────────────────────┘  │
│  - Metadata           │          │                                     │
│  - Image URLs         │          │  ┌──────────────────────────────┐  │
└───────────────────────┘          │  │  Pack Code Storage           │  │
                                   │  │  - Vercel KV (Redis)         │  │
┌───────────────────────┐          │  │  - 24-hour TTL               │  │
│  Moxfield API         │          │  │  - Pack config + powerups    │  │
│  - Decklist data      │◄─────────┤  └──────────────────────────────┘  │
│  - Card pools         │          │                                     │
└───────────────────────┘          │  ┌──────────────────────────────┐  │
                                   │  │  Powerup System              │  │
                                   │  │  - Load powerups.json        │  │
                                   │  │  - Rarity-weighted rolling   │  │
                                   │  │  - Type deduplication        │  │
                                   │  │  - Effect combination        │  │
                                   │  └──────────────────────────────┘  │
                                   └─────────────────────────────────────┘
                                                   │
                                                   │ (Pack Code)
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Tabletop Simulator Mod (EDH_Table)                                     │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Pack Code Import                                             │      │
│  │  1. User enters pack code (e.g., "U1LQSIWD")                  │      │
│  │  2. Mod calls Vercel API: /api/sessions/pack/{CODE}           │      │
│  │  3. Receives: commanderUrl, config, powerups                  │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Pack Generation                                              │      │
│  │  - Parse config.packTypes array                               │      │
│  │  - For each pack type:                                        │      │
│  │    • EDHRec source → API call with commander URL              │      │
│  │    • Scryfall source → API call with query                    │      │
│  │    • Moxfield source → API call with deck URL                 │      │
│  │  - Generate packs with custom names                           │      │
│  │  - Apply color filtering (if enabled)                         │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Card Spawning                                                │      │
│  │  - Create card objects in TTS                                 │      │
│  │  - Set deck names                                             │      │
│  │  - Position on table                                          │      │
│  │  - Display powerups in chat                                   │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Web Application (Frontend)

**Location:** `docs/` directory (deployed to GitHub Pages)  
**URL:** `https://edhrandomizer.github.io`

#### Key Files

| File | Purpose |
|------|---------|
| `index.html` | Main randomizer page (single player) |
| `random_commander_game.html` | Multiplayer game mode |
| `js/game-session/sessionManager.js` | Session API client |
| `js/game-session/gameModeController.js` | Commander generation with powerup effects |
| `js/game-session/packConfigGenerator.js` | Client-side pack config builder |
| `js/game-session/powerupLoader.js` | Loads and caches powerups.json |
| `js/commanderService.js` | Commander randomization logic |
| `js/dataLoader.js` | Loads CSV data files |
| `data/powerups.json` | Powerup definitions (deployed) |

#### Features

**Single Player Mode:**
- Commander randomization with filters (colors, rank range, time period)
- CSV data source (week/month/2-year rankings)
- Normal distribution centered at rank 1100 (σ=300)
- Direct integration with EDHREC

**Multiplayer Mode:**
- Session creation and joining (5-character codes)
- Real-time polling for updates (2-second interval)
- Powerup rolling (1-10 powerups per player)
- Commander selection with powerup effects
- Pack code generation

---

### 2. Backend API (Vercel Serverless)

**Location:** `api/sessions.py`  
**URL:** `https://edhrandomizer-api.vercel.app/api/sessions`  
**Runtime:** Python 3.x serverless function

#### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/create` | Create new session with host player |
| POST | `/join` | Join existing session by code |
| POST | `/update-name` | Update player name in session |
| POST | `/roll-powerups` | Roll powerups for all players (host only) |
| POST | `/lock-commander` | Lock in commander selection |
| POST | `/update-commanders` | Store generated commanders for player |
| POST | `/generate-pack-codes` | Generate pack codes for all players |
| GET | `/{sessionCode}` | Get current session data |
| GET | `/pack/{packCode}` | Get pack configuration by code |

#### Data Storage

**Vercel KV (Redis):**
- **Sessions:** 2-hour TTL, in-memory fallback
- **Pack Codes:** 24-hour TTL, LRU eviction policy
- **Key Format:** `session:{CODE}` and `pack:{CODE}`

**Session Data Structure:**
```python
{
    'sessionCode': str,           # 5-char uppercase code
    'hostId': str,                # 16-char player ID
    'state': str,                 # 'waiting', 'rolling', 'selecting', 'complete'
    'settings': {
        'powerupsCount': int      # 1-10 powerups per player
    },
    'players': [
        {
            'id': str,                    # Unique player ID
            'number': int,                # Player number (1-4)
            'name': str,                  # Display name
            'powerups': [],               # Rolled powerup objects
            'commanderUrl': str,          # Selected commander URL
            'commanderData': {},          # Commander metadata
            'commanderLocked': bool,      # Lock status
            'packCode': str,              # Generated pack code
            'packConfig': {},             # Full pack configuration
            'powerupsList': []            # Display list for TTS
        }
    ],
    'created_at': float,          # Unix timestamp
    'updated_at': float,
    'lastActivity': float
}
```

**Pack Code Data Structure:**
```python
{
    'commanderUrl': str,          # EDHREC commander URL
    'config': {                   # Pack configuration
        'packTypes': [            # Array of pack type definitions
            {
                'name': str,              # Pack display name
                'source': str,            # 'edhrec', 'scryfall', or 'moxfield'
                'count': int,             # Number of packs to generate
                'useCommanderColorIdentity': bool,
                'slots': [                # Slot definitions
                    {/* slot config */}
                ]
            }
        ]
    },
    'powerups': [                 # Array for TTS display
        {
            'name': str,
            'description': str,
            'rarity': str
        }
    ]
}
```

#### Pack Generation Logic

The API combines powerup effects and generates pack configurations:

1. **Load Powerups** - Read `data/powerups.json`
2. **Combine Effects** - Merge effects from all player powerups
3. **Apply to Config** - Generate pack types based on combined effects
4. **Store Pack Code** - Save to Vercel KV with 24-hour TTL

**Effect Combination Rules:**
- **Additive:** `packQuantity`, `budgetUpgradePacks`, `commanderQuantity`, `distributionShift`
- **Take Highest:** `bracketUpgrade`
- **Concatenate:** `specialPacks` (list of pack definitions)
- **Take First:** `colorFilterMode`, `allowedColors`

---

### 3. Data Pipeline (Commander Rankings)

**Location:** `scrape_edhrec_api.py` + GitHub Actions  
**Schedule:** Daily at 4:00 AM UTC

#### Scraping Process

```
GitHub Actions Workflow
  ├─ Job 1: Scrape Week Rankings
  │   └─ Run scrape_edhrec_api.py --period week
  │       └─ Output: docs/data/top_commanders_week.csv
  │
  ├─ Job 2: Scrape Month Rankings
  │   └─ Run scrape_edhrec_api.py --period month
  │       └─ Output: docs/data/top_commanders_month.csv
  │
  └─ Job 3: Scrape 2-Year Rankings
      └─ Run scrape_edhrec_api.py --period past-2-years
          └─ Output: docs/data/top_commanders_2year.csv
```

#### CSV Format

```csv
rank,name,url,color_identity,synergy_score
1,Atraxa Praetors Voice,https://edhrec.com/commanders/atraxa-praetors-voice,WUBG,100
2,Kinnan Bonder Prodigy,https://edhrec.com/commanders/kinnan-bonder-prodigy,GU,95
...
```

#### Data Flow

```
EDHREC API
  ↓ (Playwright automation)
Scraper Script
  ↓ (CSV files)
docs/data/*.csv
  ↓ (GitHub Pages deploy)
GitHub Pages CDN
  ↓ (fetch)
Web Application
  ↓ (dataLoader.js)
Commander Randomization
```

---

## API Integrations

### 1. EDHREC API

**Base URL:** `https://json.edhrec.com/pages/commanders/{slug}.json`

**Usage:**
- Commander data retrieval
- Card recommendations by category
- Synergy ratings
- Budget/bracket filtering

**Endpoints Used:**
- `/commanders/{slug}` - Base commander data
- `/commanders/{slug}/core` - Bracket 2 (budget)
- `/commanders/{slug}/upgraded` - Bracket 3 (mid-power)
- `/commanders/{slug}/optimized` - Bracket 4 (high-power)

**Card Categories:**
- `cardlists` → Card type distributions
- `newcards` → Recently released
- `highsynergycards` → High synergy rating
- `topcards` → Most popular
- `gamechangers` → High-impact cards (bracket 4 only)

**Budget Tiers:**
- `budget` - Cards under typical price threshold
- `expensive` - Premium cards above threshold
- Determined by EDHREC's internal pricing data

---

### 2. Scryfall API

**Base URL:** `https://api.scryfall.com`

**Usage:**
- Card search queries
- Custom pack generation
- Metadata retrieval
- Image URLs

**Search Syntax:**
- `banned:commander` - Banned cards
- `t:creature` - Type filtering
- `cmc<=3` - Mana value filtering
- `color:WU` - Color filtering
- `oracle:"text"` - Oracle text search
- `set:mh3` - Set filtering

**Color Filtering:**
When `useCommanderColorIdentity: true`, the system adds color restrictions:
```
+color<={commander_colors}
```

**Example Query:**
```
https://scryfall.com/search?q=t%3Aconspiracy+-is%3Aplaytest&unique=cards
```

---

### 3. Moxfield API

**Base URL:** Accessed via deck URLs  
**Format:** `https://moxfield.com/decks/{DECK_ID}`

**Usage:**
- Import decklists as card pools
- Curated card sets
- Custom pack sources

**Pack Configuration:**
```json
{
  "source": "moxfield",
  "slots": [{
    "deckUrl": "https://moxfield.com/decks/Ph3OYF_lLkuBhDpiP1qwuQ",
    "count": 15
  }]
}
```

**Automatic Exclusions:**
- Commander cards
- Basic lands
- Cards outside commander color identity (if filtering enabled)

---

## Multiplayer Game Mode

### Session Lifecycle

```
1. CREATE SESSION
   Host creates session
   └─ Generates 5-char code (e.g., "ABCD1")
   └─ Host becomes Player 1

2. JOIN SESSION
   Players 2-4 join by code
   └─ State: 'waiting'
   └─ Max 4 players

3. ROLL POWERUPS
   Host clicks "Roll Powerups"
   └─ API rolls powerups for all players
   └─ Rarity-weighted distribution
   └─ Type-based deduplication
   └─ State: 'selecting'

4. GENERATE COMMANDERS
   Each player generates commanders
   └─ Client-side randomization
   └─ Powerup effects applied:
       • distributionShift (popularity)
       • colorFilterMode (color restrictions)
       • commanderQuantity (extra choices)

5. LOCK COMMANDER
   Each player locks selection
   └─ Sends commanderUrl + commanderData
   └─ When all locked → auto-generate pack codes

6. PACK CODES READY
   Pack codes generated
   └─ Unique 8-char codes (e.g., "AB12CD34")
   └─ State: 'complete'
   └─ Players copy codes to TTS
```

### Real-Time Updates

**Polling System:**
- Client polls every 2 seconds
- Endpoint: `GET /api/sessions/{sessionCode}`
- Updates all UI elements
- Triggers state transitions

**Update Callbacks:**
```javascript
sessionManager.onUpdate((sessionData) => {
    // Update player list
    // Update powerup displays
    // Check for all-locked condition
    // Show pack codes when ready
});
```

---

## Pack Generation System

### Pack Configuration Schema

Full reference: [JSON_CONFIG_MASTER_GUIDE.md](docs/JSON_CONFIG_MASTER_GUIDE.md)

#### Pack Type Structure

```json
{
  "name": "Custom Pack Name",
  "source": "edhrec | scryfall | moxfield",
  "count": 3,
  "useCommanderColorIdentity": true,
  "slots": [/* slot definitions */]
}
```

#### Slot Types

**EDHRec Slots:**
```json
{
  "cardType": "weighted | creatures | instants | lands | ...",
  "budget": "any | budget | expensive",
  "bracket": "any | 2 | 3 | 4",
  "count": 10
}
```

**Scryfall Slots:**
```json
{
  "query": "https://scryfall.com/search?q=...",
  "count": 15,
  "useCommanderColorIdentity": true
}
```

**Moxfield Slots:**
```json
{
  "deckUrl": "https://moxfield.com/decks/DECK-ID",
  "count": 12
}
```

### Pack Generation Flow

```
Pack Code Import (TTS)
  ↓
API Call: GET /api/sessions/pack/{CODE}
  ↓
Receive: { commanderUrl, config, powerups }
  ↓
Parse config.packTypes
  ↓
For each pack type:
  ├─ EDHRec Source
  │   ├─ Build EDHREC API URL
  │   ├─ Fetch card data
  │   ├─ Filter by budget/bracket
  │   ├─ Apply color filtering
  │   └─ Random selection per slot
  │
  ├─ Scryfall Source
  │   ├─ Build Scryfall query
  │   ├─ Add color filters
  │   ├─ Execute search
  │   └─ Random selection
  │
  └─ Moxfield Source
      ├─ Fetch decklist
      ├─ Exclude commander/basics
      ├─ Apply color filtering
      └─ Random selection
  ↓
Generate Deck Objects
  ↓
Spawn Cards in TTS
  ↓
Display Powerups in Chat
```

---

## Powerup System

### Powerups Data Structure

**File:** `data/powerups.json` (v2.0 format)

```json
{
  "version": "2.0.0",
  "rarityWeights": {
    "common": 55,
    "uncommon": 30,
    "rare": 12,
    "mythic": 3
  },
  "powerupTypes": [
    {
      "type": "commander_popularity",
      "name": "Commander Popularity",
      "mutuallyExclusive": true,
      "powerups": [/* powerup objects */]
    }
  ]
}
```

### Powerup Types (14 Types, 32 Total Powerups)

| Type | Count | Mutually Exclusive | Effect |
|------|-------|-------------------|--------|
| Commander Popularity | 4 | ✅ Yes | `distributionShift: -100/-200/-300/-500` |
| Color Filter | 4 | ✅ Yes | `colorFilterMode`, `allowedColors` |
| Extra Choices | 3 | ✅ Yes | `commanderQuantity: +1/+3/+5` |
| Budget Upgrade | 2 | ❌ No | `budgetUpgradePacks: 1` with type |
| Bracket Upgrade | 2 | ❌ No | `bracketUpgrade: 3/4`, `bracketUpgradePacks: 1` |
| Extra Packs | 2 | ❌ No | `packQuantity: +1/+2` |
| Game Changer | 2 | ❌ No | `specialPack: 'gamechanger'`, `count: 1/3` |
| Conspiracy | 3 | ❌ No | `specialPack: 'conspiracy'`, `count: 1/2/3` |
| Test Cards | 2 | ❌ No | `specialPack: 'test_cards'`, Moxfield deck |
| Silly Cards | 2 | ❌ No | `specialPack: 'silly_cards'`, Moxfield deck |
| Banned Cards | 1 | ❌ No | `specialPack: 'banned'`, Moxfield deck |
| Manabase | 2 | ❌ No | `specialPack: 'any_cost_lands/expensive_lands'` |
| Manual Powerups | 3 | ❌ No | `manual: true` (not system-enforced) |

### Rolling Algorithm

```python
def roll_powerups(count, powerups_data):
    """Roll multiple powerups with type deduplication"""
    result = []
    used_types = set()
    
    for _ in range(count):
        # Rarity-weighted selection
        rarity = weighted_random(rarityWeights)
        
        # Get powerups of selected rarity
        candidates = [p for p in all_powerups if p['rarity'] == rarity]
        
        # Type deduplication
        while True:
            powerup = random.choice(candidates)
            powerup_type = get_powerup_type(powerup)
            
            # Check mutual exclusivity
            if type_is_mutually_exclusive(powerup_type):
                if powerup_type not in used_types:
                    used_types.add(powerup_type)
                    result.append(powerup)
                    break
            else:
                result.append(powerup)
                break
    
    return result
```

### Effect Application

**Client-Side (Commander Generation):**
```javascript
// gameModeController.js
const baseDistributionCenter = 1100;
const distributionShift = powerupEffects.distributionShift || 0;
const distributionCenter = baseDistributionCenter + distributionShift;

// Apply normal distribution
const probability = normalDistribution(rank, distributionCenter, 300);
```

**Server-Side (Pack Configuration):**
```python
# api/sessions.py
def apply_powerups_to_config(powerups, commander_url):
    combined_effects = combine_powerup_effects(powerups)
    
    # Base packs
    base_pack_count = 5 + combined_effects['packQuantity']
    
    # Modified packs
    normal_packs = base_pack_count - budget_packs - bracket_packs
    
    # Special packs (additional)
    for special_pack in combined_effects['specialPacks']:
        config['packTypes'].append(generate_special_pack(special_pack))
    
    return config
```

---

## Tabletop Simulator Integration

### TTS Mod Structure

**Location:** `EDH_Table/` repository  
**File:** `2296042369.json` (TTS save file)

#### Key Components

1. **Pack Code Input** - Text field for 8-char code
2. **Generate Button** - Triggers pack generation
3. **API Client** - Fetches pack config from Vercel
4. **Pack Generator** - Creates card decks
5. **Chat Display** - Shows powerup list

### Pack Code Import Flow

```lua
-- TTS Lua Script

function onPackCodeEntered(code)
    -- 1. Validate code format (8 uppercase alphanumeric)
    if not isValidPackCode(code) then
        showError("Invalid pack code format")
        return
    end
    
    -- 2. Call Vercel API
    local url = "https://edhrandomizer-api.vercel.app/api/sessions/pack/" .. code
    WebRequest.get(url, onPackDataReceived)
end

function onPackDataReceived(request)
    if request.is_error then
        showError("Pack code not found or expired")
        return
    end
    
    local data = JSON.decode(request.text)
    
    -- 3. Display powerups in chat
    displayPowerups(data.powerups)
    
    -- 4. Generate packs
    for _, packType in ipairs(data.config.packTypes) do
        generatePackType(packType, data.commanderUrl)
    end
end

function generatePackType(packType, commanderUrl)
    for i = 1, packType.count do
        local cards = {}
        
        -- Process each slot
        for _, slot in ipairs(packType.slots) do
            if packType.source == "edhrec" then
                cards = fetchEDHRecCards(commanderUrl, slot)
            elseif packType.source == "scryfall" then
                cards = fetchScryfallCards(slot.query, commanderUrl, packType.useCommanderColorIdentity)
            elseif packType.source == "moxfield" then
                cards = fetchMoxfieldCards(slot.deckUrl, commanderUrl, packType.useCommanderColorIdentity)
            end
        end
        
        -- Create deck in TTS
        spawnCardDeck(cards, packType.name or "Generated Pack")
    end
end
```

### Card Spawning

**Mystery Booster Pattern:**
- Uses TTS deck objects
- Custom deck state for card back
- Card data includes name, image URL, metadata
- Positioned on table grid

---

## Deployment & Infrastructure

### GitHub Pages (Frontend)

**Repository:** `EDHRandomizer/EDHRandomizer.github.io`  
**Branch:** `main`  
**Deploy Trigger:** Push to `main` branch  
**Build:** Automatic via GitHub Actions  
**URL:** `https://edhrandomizer.github.io`

**Deployment Process:**
```
1. Push to main branch
   ↓
2. GitHub Actions workflow
   ├─ Validate HTML/JS/CSS
   ├─ Build (if needed)
   └─ Deploy to GitHub Pages
   ↓
3. CDN propagation (~1 minute)
   ↓
4. Live at edhrandomizer.github.io
```

### Vercel API (Backend)

**Project:** `edhrandomizer-api`  
**Region:** Auto (edge functions)  
**Runtime:** Python 3.9+  
**Deploy Trigger:** Push to `main` branch

**Deployment Process:**
```
1. Push to main branch (GitHub)
   ↓
2. Vercel detects change
   ↓
3. Build serverless function
   ├─ Install dependencies (requirements.txt)
   ├─ Compile Python code
   └─ Package function
   ↓
4. Deploy to edge (~30 seconds)
   ↓
5. Live at edhrandomizer-api.vercel.app
```

**Environment Variables:**
- `KV_REST_API_URL` - Vercel KV endpoint
- `KV_REST_API_TOKEN` - Authentication token

### Data Scraper (GitHub Actions)

**Schedule:** `0 4 * * *` (4 AM UTC daily)  
**Timeout:** 30 minutes  
**Concurrency:** 3 parallel jobs

**Workflow File:** `.github/workflows/scrape_edhrec.yml`

```yaml
jobs:
  scrape-week:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python scrape_edhrec_api.py --period week
      - uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "Update week rankings"
```

---

## Testing & Validation

### Integration Tests

**File:** `tests/test_pack_code_integration.py`

**Test Coverage:**
- Session creation and joining
- Powerup rolling with proper effects
- Commander locking
- Pack code generation
- Pack configuration validation
- Powerup display list verification

**Run Tests:**
```bash
python tests/test_pack_code_integration.py
```

### Pack Config Tests

**File:** `tests/test_pack_config_logic.py`

**Test Cases:**
- Baseline pack generation
- Extra pack powerups
- Budget upgrade effects
- Bracket upgrade effects
- Special pack types
- Combined powerup effects
- Kitchen sink scenarios

### Validation Checklist

**Before Deployment:**
- [ ] `powerups.json` syntax valid
- [ ] All Moxfield deck IDs are public
- [ ] Scryfall queries return results
- [ ] API endpoints return 200
- [ ] Pack codes generate correctly
- [ ] TTS mod can import pack codes
- [ ] Powerups display in TTS chat
- [ ] Cards spawn in correct quantities

---

## Related Documentation

### Core Documentation

| File | Purpose |
|------|---------|
| [JSON_CONFIG_MASTER_GUIDE.md](docs/JSON_CONFIG_MASTER_GUIDE.md) | Complete pack configuration reference |
| [TTS_PACK_CODE_GUIDE.md](EDH_Table/TTS_PACK_CODE_GUIDE.md) | Pack code integration for TTS |
| [VERCEL_KV_SETUP.md](VERCEL_KV_SETUP.md) | Vercel KV configuration guide |

### Development Guides

| File | Purpose |
|------|---------|
| [DEVELOPMENT_METHODOLOGY.md](EDH_Table/DEVELOPMENT_METHODOLOGY.md) | Development practices |
| [TESTING_GUIDE.md](EDH_Table/TESTING_GUIDE.md) | Testing procedures |
| [DEPLOYMENT_WORKFLOW.md](EDH_Table/DEPLOYMENT_WORKFLOW.md) | Deployment steps |

### Component Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | EDHREC scraper documentation |
| [EDH_Table/README.md](EDH_Table/README.md) | TTS mod documentation |
| [EDHRandomizerPack/README.md](EDHRandomizerPack/README.md) | Pack system documentation |

---

## System Flow Summary

### End-to-End Flow (Multiplayer Game)

```
1. USER CREATES SESSION
   Web UI → POST /api/sessions/create → Vercel KV
   
2. PLAYERS JOIN
   Web UI → POST /api/sessions/join → Update session
   
3. HOST ROLLS POWERUPS
   Web UI → POST /api/sessions/roll-powerups
   API loads powerups.json → Weighted random selection
   → Type deduplication → Store in session
   
4. PLAYERS GENERATE COMMANDERS
   Client → Load CSV data → Apply powerup effects
   → Normal distribution (center = 1100 + distributionShift)
   → Color filtering → commanderQuantity choices
   
5. PLAYERS SELECT & LOCK
   Web UI → POST /api/sessions/lock-commander
   → When all locked → Auto-generate pack codes
   
6. PACK CODE GENERATION
   API → Combine powerup effects → Generate pack config
   → Create special packs → Store in Vercel KV
   → Generate 8-char code → Return to client
   
7. IMPORT TO TTS
   TTS Mod → User enters pack code
   → GET /api/sessions/pack/{CODE}
   → Receive commanderUrl, config, powerups
   
8. PACK GENERATION IN TTS
   For each packType:
     → If EDHRec: Fetch from EDHREC API
     → If Scryfall: Execute search query
     → If Moxfield: Fetch decklist
     → Apply color filtering
     → Random card selection
     → Create deck object
   
9. SPAWN CARDS
   TTS → Create card decks → Position on table
   → Display powerups in chat → Game ready!
```

---

## Performance Considerations

### Caching Strategy

- **CSV Data:** Loaded once, cached in browser
- **Powerups:** Loaded once per session
- **API Responses:** No client-side caching (real-time updates)
- **Vercel KV:** Redis cache with TTL
- **Scryfall:** Results cached during single request

### Rate Limiting

- **EDHREC:** No official limits, respectful delays
- **Scryfall:** 10 requests/second max
- **Moxfield:** No official limits
- **Vercel KV:** Plan-based limits

### Optimization

- **Parallel API calls** in TTS for faster pack generation
- **Batch card spawning** to reduce TTS lag
- **Compressed JSON** for pack configs
- **Edge functions** for low latency

---

## Troubleshooting

### Common Issues

**"Pack code not found"**
- Code expired (24-hour TTL)
- Invalid code format
- Vercel KV not configured

**"Empty packs in TTS"**
- Moxfield deck is private
- Scryfall query returns no results
- Color filtering too restrictive
- Check field names: `deckUrl` not `moxfieldDeck`

**"Powerups not working"**
- API not updated (check deployment)
- `powerups.json` syntax error
- Effect combination logic issue

**"Session not found"**
- Session expired (2-hour inactivity)
- Code typed incorrectly
- Vercel KV connection issue

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 2025 | Initial system launch |
| 2.0 | Nov 2025 | Powerups v2.0, Moxfield integration, improved pack generation |

---

## Contributing

See individual repository READMEs for contribution guidelines.

## License

MIT License - See LICENSE file in each repository.

---

**Maintained by:** Steven Scangas  
**Last Updated:** November 2, 2025  
**System Status:** ✅ Operational

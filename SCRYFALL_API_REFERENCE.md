# Scryfall API Reference

This document describes the data available from the Scryfall API `/cards/named` endpoint, which we use to fetch additional card information for commanders.

## API Endpoint

```
GET https://api.scryfall.com/cards/named?fuzzy={card_name}
```

**Rate Limiting:** Scryfall recommends 50-100ms between requests. Our scraper uses 75ms delays.

**Example:**
```
https://api.scryfall.com/cards/named?fuzzy=Atraxa%2C%20Praetors%27%20Voice
```

## Currently Used Fields

### Set Information
- **`set`** - Set code (e.g., `"2xm"`)
- **`set_name`** - Full set name (e.g., `"Double Masters"`)

These fields are currently included in our CSV exports under the columns `"Set Code"` and `"Set Name"`.

---

## Available Fields

### Basic Card Information

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Card name | `"Atraxa, Praetors' Voice"` |
| `mana_cost` | string | Mana cost with symbols | `"{G}{W}{U}{B}"` |
| `cmc` | number | Converted mana cost | `4.0` |
| `type_line` | string | Full type line | `"Legendary Creature — Phyrexian Angel Horror"` |
| `oracle_text` | string | Current rules text | `"Flying, vigilance, deathtouch..."` |
| `power` | string | Creature power | `"4"` |
| `toughness` | string | Creature toughness | `"4"` |
| `colors` | array | Card colors | `["B", "G", "U", "W"]` |
| `color_identity` | array | Commander color identity | `["B", "G", "U", "W"]` |
| `keywords` | array | Ability keywords | `["Deathtouch", "Flying", "Lifelink", "Vigilance", "Proliferate"]` |
| `rarity` | string | Card rarity | `"mythic"`, `"rare"`, `"uncommon"`, `"common"` |

### Artist & Flavor

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `artist` | string | Card artist name | `"Victor Adame Minguez"` |
| `artist_ids` | array | Scryfall artist IDs | `["..."...]` |
| `flavor_text` | string | Flavor text (if present) | `"..."` |
| `illustration_id` | string | Unique illustration ID | `"..."` |

### Set Information (Detailed)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `set` | string | Set code (3-4 chars) | `"2xm"` |
| `set_name` | string | Full set name | `"Double Masters"` |
| `set_type` | string | Type of set | `"masters"`, `"commander"`, `"expansion"`, `"core"`, `"draft_innovation"`, `"funny"` |
| `set_id` | string | Scryfall set UUID | `"..."` |
| `set_uri` | string | API link to set | `"https://api.scryfall.com/sets/..."` |
| `set_search_uri` | string | Search for all cards in set | `"https://api.scryfall.com/cards/search?..."` |
| `scryfall_set_uri` | string | Web link to set page | `"https://scryfall.com/sets/..."` |
| `released_at` | string | Release date (ISO 8601) | `"2020-08-07"` |
| `collector_number` | string | Card number in set | `"190"` |
| `reprint` | boolean | Is this a reprint? | `true` or `false` |

### Pricing Data

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `prices.usd` | string | USD paper price | `"22.53"` |
| `prices.usd_foil` | string | USD foil price | `"24.85"` |
| `prices.usd_etched` | string | USD etched price | `"17.50"` or `null` |
| `prices.eur` | string | EUR paper price | `"19.84"` |
| `prices.eur_foil` | string | EUR foil price | `"24.12"` |
| `prices.tix` | string | MTGO ticket price | `"0.91"` |

**Note:** All prices are strings (not numbers) and can be `null` if not available.

### Rankings & Popularity

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `edhrec_rank` | number | Overall EDHREC rank | `2190` |

### External IDs

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `tcgplayer_id` | number | TCGPlayer product ID | `214833` |
| `cardmarket_id` | number | Cardmarket product ID | `462559` |
| `mtgo_id` | number | MTGO catalog ID | `...` |
| `id` | string | Scryfall card UUID | `"..."` |
| `oracle_id` | string | Scryfall oracle ID (same across printings) | `"..."` |
| `multiverse_ids` | array | Gatherer multiverse IDs | `[...]` |

### Card Images

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `image_uris.small` | string | Small image (146x204) | `"https://cards.scryfall.io/small/..."` |
| `image_uris.normal` | string | Normal image (488x680) | `"https://cards.scryfall.io/normal/..."` |
| `image_uris.large` | string | Large image (672x936) | `"https://cards.scryfall.io/large/..."` |
| `image_uris.png` | string | High-res PNG | `"https://cards.scryfall.io/png/..."` |
| `image_uris.art_crop` | string | Cropped artwork only | `"https://cards.scryfall.io/art_crop/..."` |
| `image_uris.border_crop` | string | Card with minimal border | `"https://cards.scryfall.io/border_crop/..."` |

**Note:** For multi-faced cards, `image_uris` may not be present at the root level. Check `card_faces[].image_uris` instead.

### Legalities

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `legalities` | object | Format legality status | `{"commander": "legal", "standard": "not_legal", ...}` |

Format legality values: `"legal"`, `"not_legal"`, `"restricted"`, `"banned"`

Common formats: `commander`, `legacy`, `vintage`, `modern`, `standard`, `pioneer`, `pauper`, `historic`, `brawl`

### Card Layout & Printing Details

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `layout` | string | Card layout type | `"normal"`, `"transform"`, `"modal_dfc"`, `"adventure"`, `"split"` |
| `border_color` | string | Border color | `"black"`, `"white"`, `"silver"`, `"gold"` |
| `frame` | string | Card frame year | `"2015"`, `"2003"`, `"1997"` |
| `frame_effects` | array | Special frame effects | `["legendary"]`, `["showcase"]` |
| `full_art` | boolean | Is full-art? | `true` or `false` |
| `textless` | boolean | Is textless? | `true` or `false` |
| `foil` | boolean | Available in foil? | `true` or `false` |
| `nonfoil` | boolean | Available in nonfoil? | `true` or `false` |
| `finishes` | array | Available finishes | `["foil", "nonfoil"]`, `["etched"]` |
| `oversized` | boolean | Is oversized? | `true` or `false` |
| `promo` | boolean | Is promo card? | `true` or `false` |
| `security_stamp` | string | Security stamp type | `"oval"`, `"triangle"`, `"acorn"` |

### Links & URIs

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `scryfall_uri` | string | Scryfall card page | `"https://scryfall.com/card/2xm/190/..."` |
| `uri` | string | API URI for this card | `"https://api.scryfall.com/cards/..."` |
| `rulings_uri` | string | API URI for rulings | `"https://api.scryfall.com/cards/.../rulings"` |
| `prints_search_uri` | string | API search for all printings | `"https://api.scryfall.com/cards/search?..."` |
| `purchase_uris` | object | Links to purchase | `{"tcgplayer": "...", "cardmarket": "...", ...}` |
| `related_uris` | object | Related links | `{"gatherer": "...", "edhrec": "...", ...}` |

### Other Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `lang` | string | Language code | `"en"`, `"ja"`, `"es"` |
| `games` | array | Platforms available on | `["paper", "mtgo", "arena"]` |
| `reserved` | boolean | On Reserved List? | `true` or `false` |
| `digital` | boolean | Digital-only card? | `true` or `false` |
| `booster` | boolean | Available in boosters? | `true` or `false` |
| `story_spotlight` | boolean | Story spotlight card? | `true` or `false` |
| `preview` | object | Preview information | `{"source": "...", "source_uri": "...", ...}` |

---

## Potential Enhancements

### High-Value Additions

1. **`set_type`** - Filter by set category (exclude Secret Lair, promos, etc.)
   - Values: `"commander"`, `"masters"`, `"expansion"`, `"core"`, `"draft_innovation"`, `"funny"`

2. **`released_at`** - Filter by release date (e.g., "commanders from last year")
   - Format: `"YYYY-MM-DD"`

3. **`image_uris.normal`** - Display card images in the web UI
   - Direct hotlink-friendly URLs

4. **`oracle_text`** - Search/filter by card abilities
   - Example: Find commanders with "draw" or "proliferate"

5. **`keywords`** - Filter by mechanics
   - Example: "commanders with Flying and Vigilance"

6. **`edhrec_rank`** - Compare EDHREC's overall rank vs time-specific rank
   - Could show trending commanders

### Medium-Value Additions

7. **`type_line`** - More detailed filtering
   - Example: "Legendary Creature — Human Wizard" vs just "Creature"

8. **`collector_number`** - Sorting/organizing
   - Useful for set completionists

9. **`artist`** - Filter by favorite artists
   - Community favorite feature

10. **`prices`** - More accurate/up-to-date pricing
    - Scryfall aggregates from multiple sources
    - Update more frequently than EDHREC prices

### Low-Value Additions

11. **`legalities`** - Format legality checks
    - Though all commanders are legal in Commander by default

12. **`reprint`** - Filter first printings only
    - Niche use case

13. **`purchase_uris`** - Direct buy links
    - Affiliate revenue opportunity?

---

## Implementation Notes

### Rate Limiting
```python
# Scryfall recommends 50-100ms between requests
time.sleep(0.075)  # 75ms = 13.3 requests/second
```

### Error Handling
- `404` - Card not found (spelling variation, very new cards)
- `429` - Rate limit exceeded (retry with exponential backoff)
- `503` - Service temporarily unavailable (retry after delay)

### Caching Strategy
- Cache Scryfall responses to avoid repeated lookups
- Set data rarely changes for existing cards
- Only need to fetch for new commanders

### Multi-Faced Cards
For cards like `"Frodo // Sam"`:
```python
# Split on " // " and use first face name
search_name = card_name.split(' // ')[0]
```

Scryfall returns the full card object with both faces in `card_faces[]` array.

---

## Example Response

```json
{
  "name": "Atraxa, Praetors' Voice",
  "mana_cost": "{G}{W}{U}{B}",
  "cmc": 4.0,
  "type_line": "Legendary Creature — Phyrexian Angel Horror",
  "oracle_text": "Flying, vigilance, deathtouch, lifelink\nAt the beginning of your end step, proliferate.",
  "power": "4",
  "toughness": "4",
  "colors": ["B", "G", "U", "W"],
  "color_identity": ["B", "G", "U", "W"],
  "keywords": ["Deathtouch", "Flying", "Lifelink", "Vigilance", "Proliferate"],
  "set": "2xm",
  "set_name": "Double Masters",
  "set_type": "masters",
  "released_at": "2020-08-07",
  "rarity": "mythic",
  "artist": "Victor Adame Minguez",
  "edhrec_rank": 2190,
  "prices": {
    "usd": "22.53",
    "usd_foil": "24.85",
    "eur": "19.84",
    "eur_foil": "24.12",
    "tix": "0.91"
  },
  "image_uris": {
    "normal": "https://cards.scryfall.io/normal/front/d/0/d0d33d52-3d28-4635-b985-51e126289259.jpg",
    "png": "https://cards.scryfall.io/png/front/d/0/d0d33d52-3d28-4635-b985-51e126289259.png",
    "art_crop": "https://cards.scryfall.io/art_crop/front/d/0/d0d33d52-3d28-4635-b985-51e126289259.jpg"
  },
  "scryfall_uri": "https://scryfall.com/card/2xm/190/atraxa-praetors-voice",
  "tcgplayer_id": 214833,
  "cardmarket_id": 462559
}
```

---

## References

- **Official Documentation:** https://scryfall.com/docs/api/cards/named
- **Card Objects Schema:** https://scryfall.com/docs/api/cards
- **Rate Limits:** https://scryfall.com/docs/api#rate-limits-and-good-citizenship

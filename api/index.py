"""
EDH Randomizer Pack Generator API
Vercel Serverless Function (Combined Single File)

Endpoint: POST /api/index
"""

import json
import urllib.request
import urllib.parse
import re
import random
from typing import Dict, List, Any, Optional, Tuple
from http.server import BaseHTTPRequestHandler


# ==========================================
# COLOR IDENTITY MAPPING
# ==========================================

def get_color_identity_name(colors: Optional[List[str]]) -> Optional[str]:
    """
    Map color identity to guild/shard/wedge name
    
    Args:
        colors: List of color letters (e.g., ['W', 'U', 'B'])
    
    Returns:
        Color pairing name or None if colorless/no colors
    """
    if not colors or len(colors) == 0:
        return "Colorless"
    
    # Sort colors to normalize (order doesn't matter)
    color_set = frozenset(colors)
    
    # Mono-color
    if len(colors) == 1:
        color_names = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
        return f"Mono-{color_names.get(colors[0], 'Unknown')}"
    
    # Two colors (Guilds)
    two_color_names = {
        frozenset(['W', 'U']): 'Azorius',
        frozenset(['W', 'R']): 'Boros',
        frozenset(['U', 'B']): 'Dimir',
        frozenset(['B', 'G']): 'Golgari',
        frozenset(['R', 'G']): 'Gruul',
        frozenset(['U', 'R']): 'Izzet',
        frozenset(['B', 'W']): 'Orzhov',
        frozenset(['B', 'R']): 'Rakdos',
        frozenset(['G', 'W']): 'Selesnya',
        frozenset(['G', 'U']): 'Simic'
    }
    
    # Three colors (Shards/Wedges)
    three_color_names = {
        frozenset(['W', 'B', 'G']): 'Abzan',
        frozenset(['W', 'U', 'G']): 'Bant',
        frozenset(['W', 'U', 'B']): 'Esper',
        frozenset(['U', 'B', 'R']): 'Grixis',
        frozenset(['W', 'U', 'R']): 'Jeskai',
        frozenset(['B', 'R', 'G']): 'Jund',
        frozenset(['W', 'B', 'R']): 'Mardu',
        frozenset(['W', 'R', 'G']): 'Naya',
        frozenset(['U', 'B', 'G']): 'Sultai',
        frozenset(['U', 'R', 'G']): 'Temur'
    }
    
    if len(colors) == 2:
        return two_color_names.get(color_set)
    elif len(colors) == 3:
        return three_color_names.get(color_set)
    elif len(colors) == 4:
        return '4-Color'
    elif len(colors) == 5:
        return 'WUBRG'
    
    return None


# ==========================================
# SCRYFALL QUERIES
# ==========================================

# TODO: Convert to GitHub Action that runs nightly and caches results
# For now, we query Scryfall on every API call (fast enough for current usage)

def convert_to_scryfall_api_url(query_or_url: str) -> str:
    """
    Convert Scryfall search URL or raw query to API URL
    
    Args:
        query_or_url: Can be:
            - Full Scryfall URL: https://scryfall.com/search?q=...
            - API URL: https://api.scryfall.com/cards/search?q=...
            - Raw query: "t:creature cmc<=3"
    
    Returns:
        API URL ready to use
    """
    # Already an API URL
    if query_or_url.startswith("https://api.scryfall.com/cards/search"):
        return query_or_url
    
    # Scryfall search URL - replace domain/path
    if query_or_url.startswith("https://scryfall.com/search"):
        return query_or_url.replace("https://scryfall.com/search", "https://api.scryfall.com/cards/search")
    
    # Raw query - build API URL with URL encoding
    encoded_query = urllib.parse.quote(query_or_url)
    return f"https://api.scryfall.com/cards/search?q={encoded_query}"


def append_to_scryfall_query(url: str, additional_filters: str) -> str:
    """
    Append additional filters to a Scryfall API URL query string
    
    Args:
        url: Scryfall API URL
        additional_filters: Space-separated filters to append (e.g., "-banned:commander")
    
    Returns:
        Modified URL with appended filters
    """
    if not additional_filters:
        return url
    
    # Parse the URL
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    
    # Get existing query
    existing_query = query_params.get('q', [''])[0]
    
    # Append new filters
    new_query = f"{existing_query} {additional_filters}".strip()
    
    # Update query params
    query_params['q'] = [new_query]
    
    # Rebuild URL
    new_query_string = urllib.parse.urlencode(query_params, doseq=True)
    new_url = urllib.parse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query_string,
        parsed.fragment
    ))
    
    return new_url


def build_scryfall_query(
    query_or_url: str,
    commander_colors: Optional[List[str]] = None,
    use_commander_color_identity: bool = True
) -> str:
    """
    Build a Scryfall query with automatic filters for commander legality
    
    Args:
        query_or_url: Base query/URL from config
        commander_colors: Commander color identity (e.g., ['W', 'U', 'B'])
        use_commander_color_identity: Whether to filter by commander colors
    
    Returns:
        Complete Scryfall API URL with all filters applied
    """
    # Convert to API URL first
    url = convert_to_scryfall_api_url(query_or_url)
    
    # Parse existing query to check what's already there
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    existing_query = query_params.get('q', [''])[0].lower()
    
    # Build additional filters
    filters = []
    
    # Always exclude banned cards (unless explicitly included)
    if 'banned:commander' not in existing_query:
        filters.append('-banned:commander')
    
    # Add commander color identity filter
    if use_commander_color_identity and commander_colors:
        # Convert EDHRec format ['W', 'U', 'B'] to Scryfall format 'w,u,b'
        color_string = ','.join(c.lower() for c in commander_colors)
        if f'commander:{color_string}' not in existing_query:
            filters.append(f'commander:{color_string}')
    
    # Exclude basic lands (unless explicitly requested)
    if 't:basic' not in existing_query and 'type:basic' not in existing_query:
        filters.append('-t:basic')
    
    # Append all filters
    if filters:
        url = append_to_scryfall_query(url, ' '.join(filters))
    
    return url


def fetch_scryfall_cards(query_or_url: str) -> List[str]:
    """
    Fetch card names from Scryfall with given query or URL
    
    Args:
        query_or_url: Can be a Scryfall URL, API URL, or raw query string
    
    Returns:
        List of card names
    """
    cards = []
    url = convert_to_scryfall_api_url(query_or_url)
    
    while url:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Extract card names
            for card in data.get('data', []):
                name = card.get('name')
                if name:
                    cards.append(name)
            
            # Check for next page
            url = data.get('next_page')
            
        except Exception as e:
            print(f"Error fetching from Scryfall: {e}")
            break
    
    return cards


# Color complexity weighting multipliers
# Used to balance card selection when filtering by commander color identity
# Multi-color cards are rarer in pools, so we increase their selection weight
# More aggressive multipliers to really showcase multi-color cards
COLOR_COMPLEXITY_MULTIPLIERS = {
    0: 1,   # Colorless (artifacts, lands) - baseline like mono-color
    1: 1,   # Mono-color - baseline
    2: 3,   # Dual-color - increased from 2x to 3x
    3: 10,  # Triple-color - doubled from 5x to 10x
    4: 20,  # Four-color - more than doubled from 8x to 20x
    5: 30   # Five-color - more than doubled from 12x to 30x
}


def get_color_complexity_weight(color_identity: List[str]) -> int:
    """
    Get the selection weight multiplier for a card based on its color complexity
    
    Args:
        color_identity: List of color letters (e.g., ['W', 'U', 'B'])
    
    Returns:
        Weight multiplier (default 1 for mono-color)
    """
    color_count = len(color_identity)
    return COLOR_COMPLEXITY_MULTIPLIERS.get(color_count, 1)


def weighted_random_sample(cards_with_colors: List[Dict[str, Any]], count: int, use_quantity: bool = False) -> List[str]:
    """
    Select random cards with weighting based on color complexity
    
    Args:
        cards_with_colors: List of dicts with 'name', 'color_identity', and optionally 'quantity'
        count: Number of cards to select
        use_quantity: If True, multiply weight by card quantity (for Moxfield)
    
    Returns:
        List of selected card names
    """
    if not cards_with_colors:
        return []
    
    # Build weighted list
    weighted_pool = []
    for card in cards_with_colors:
        name = card['name']
        color_identity = card.get('color_identity', [])
        quantity = card.get('quantity', 1) if use_quantity else 1
        
        # Get color complexity weight
        color_weight = get_color_complexity_weight(color_identity)
        
        # Total weight = color_weight * quantity
        total_weight = color_weight * quantity
        
        # Add card to pool 'total_weight' times
        for _ in range(total_weight):
            weighted_pool.append(name)
    
    # Sample from weighted pool
    if not weighted_pool:
        return []
    
    selected_count = min(count, len(weighted_pool))
    return random.sample(weighted_pool, selected_count)


def fetch_scryfall_cards_with_colors(query_or_url: str) -> List[Dict[str, Any]]:
    """
    Fetch card data from Scryfall including color identity
    
    Args:
        query_or_url: Can be a Scryfall URL, API URL, or raw query string
    
    Returns:
        List of dicts with 'name' and 'color_identity' keys
        Example: [{'name': 'Sol Ring', 'color_identity': []}, {'name': 'Atraxa', 'color_identity': ['W','U','B','G']}]
    """
    cards = []
    url = convert_to_scryfall_api_url(query_or_url)
    
    while url:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Extract card names and color identity
            for card in data.get('data', []):
                name = card.get('name')
                if name:
                    cards.append({
                        'name': name,
                        'color_identity': card.get('color_identity', [])
                    })
            
            # Check for next page
            url = data.get('next_page')
            
        except Exception as e:
            print(f"Error fetching from Scryfall: {e}")
            break
    
    return cards


# Cards that should only appear in game changers packs, not in other EDHRec sections
# (Used to handle cases where Scryfall/EDHRec APIs haven't updated yet)
GAMECHANGER_ONLY_CARDS = {
    "Sol Ring",  # Doing what WotC should have done years ago
}


# Fetch lands with their color identities
# Only include in packs where ALL colors are in commander's color identity
FETCH_LANDS = {
    # Onslaught fetches (allied colors)
    'Flooded Strand': ['W', 'U'],
    'Polluted Delta': ['U', 'B'],
    'Bloodstained Mire': ['B', 'R'],
    'Wooded Foothills': ['R', 'G'],
    'Windswept Heath': ['G', 'W'],
    # Zendikar fetches (enemy colors)
    'Marsh Flats': ['W', 'B'],
    'Scalding Tarn': ['U', 'R'],
    'Verdant Catacombs': ['B', 'G'],
    'Arid Mesa': ['R', 'W'],
    'Misty Rainforest': ['G', 'U']
}


def get_game_changers() -> set:
    """Fetch game changer cards from Scryfall and add manually tracked cards"""
    gc_cards = fetch_scryfall_cards("is:gamechanger")
    
    # Add cards that should be game changers but might not be in Scryfall API yet
    gc_cards.extend(GAMECHANGER_ONLY_CARDS)
    
    return set(gc_cards)


def get_basic_lands() -> set:
    """Fetch basic lands from Scryfall (type:land type:basic)"""
    return set(fetch_scryfall_cards("type:land type:basic"))


# Cache for the current request (Vercel serverless functions are ephemeral)
_GAME_CHANGERS_CACHE = None
_BASIC_LANDS_CACHE = None


def get_cached_game_changers() -> set:
    """Get game changers with simple in-memory cache"""
    global _GAME_CHANGERS_CACHE
    if _GAME_CHANGERS_CACHE is None:
        _GAME_CHANGERS_CACHE = get_game_changers()
    return _GAME_CHANGERS_CACHE


def get_cached_basic_lands() -> set:
    """Get basic lands with simple in-memory cache"""
    global _BASIC_LANDS_CACHE
    if _BASIC_LANDS_CACHE is None:
        _BASIC_LANDS_CACHE = get_basic_lands()
    return _BASIC_LANDS_CACHE


# ==========================================
# MOXFIELD DECK IMPORT
# ==========================================

def fetch_moxfield_deck_name(deck_url_or_id: str) -> Optional[str]:
    """
    Fetch the deck name from a Moxfield decklist
    
    Args:
        deck_url_or_id: Either full Moxfield URL or just deck ID
    
    Returns:
        Deck name or None if unable to fetch
    """
    # Extract deck ID from URL if needed
    if 'moxfield.com' in deck_url_or_id:
        match = re.search(r'moxfield\.com/decks/([^/?]+)', deck_url_or_id)
        if match:
            deck_id = match.group(1)
        else:
            return None
    else:
        deck_id = deck_url_or_id
    
    # Moxfield API endpoint
    url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}/"
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        return data.get('name')
        
    except Exception as e:
        print(f"[Moxfield] Error fetching deck name: {e}")
        return None


def fetch_moxfield_cards(deck_url_or_id: str, commander_colors: Optional[List[str]] = None) -> List[str]:
    """
    Fetch card names from a Moxfield decklist
    
    Args:
        deck_url_or_id: Either full Moxfield URL or just deck ID
            - URL: https://moxfield.com/decks/abc123
            - ID: abc123
        commander_colors: Optional list of color identity letters to filter by (e.g., ['W', 'U', 'B'])
            If provided, only cards whose color identity is a subset will be included
    
    Returns:
        List of card names from mainboard (excludes commanders, companions, sideboard)
    """
    # Extract deck ID from URL if needed
    if 'moxfield.com' in deck_url_or_id:
        match = re.search(r'moxfield\.com/decks/([^/?]+)', deck_url_or_id)
        if match:
            deck_id = match.group(1)
        else:
            print(f"Could not extract Moxfield deck ID from: {deck_url_or_id}")
            return []
    else:
        deck_id = deck_url_or_id
    
    # Moxfield API endpoint
    url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}/"
    
    print(f"[Moxfield] Fetching deck from: {url}")
    if commander_colors:
        print(f"[Moxfield] Filtering by commander colors: {commander_colors}")
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        print(f"[Moxfield] Successfully fetched deck data")
        
        cards = []
        filtered_count = 0
        
        # Extract mainboard cards - they're in boards.mainboard.cards
        boards = data.get('boards', {})
        mainboard_data = boards.get('mainboard', {})
        mainboard = mainboard_data.get('cards', {})
        
        print(f"[Moxfield] Mainboard has {len(mainboard)} unique cards")
        
        for card_data in mainboard.values():
            if card_data.get('card'):
                card = card_data['card']
                card_name = card.get('name')
                card_color_identity = card.get('color_identity', [])
                quantity = card_data.get('quantity', 1)
                
                if card_name:
                    # Apply color identity filter if specified
                    if commander_colors is not None:
                        # Check if card's color identity is a subset of commander's
                        if all(color in commander_colors for color in card_color_identity):
                            # Add the card name 'quantity' times (for duplicates)
                            for _ in range(quantity):
                                cards.append(card_name)
                        else:
                            filtered_count += quantity
                    else:
                        # No filter - add all cards
                        for _ in range(quantity):
                            cards.append(card_name)
        
        if commander_colors:
            print(f"[Moxfield] Color filter excluded {filtered_count} cards")
        print(f"[Moxfield] Fetched {len(cards)} total cards from deck {deck_id}")
        return cards
        
    except urllib.error.HTTPError as e:
        print(f"[Moxfield] HTTP Error {e.code} fetching deck {deck_id}: {e.reason}")
        return []
    except urllib.error.URLError as e:
        print(f"[Moxfield] URL Error fetching deck {deck_id}: {e.reason}")
        return []
    except Exception as e:
        print(f"[Moxfield] Error fetching Moxfield deck {deck_id}: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []


def fetch_moxfield_cards_with_colors(deck_url_or_id: str, commander_colors: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch card data from Moxfield including color identity and quantities
    
    Args:
        deck_url_or_id: Either full Moxfield URL or just deck ID
        commander_colors: Optional list of color identity letters to filter by
    
    Returns:
        List of dicts with 'name', 'color_identity', and 'quantity' keys
        Each card appears once with its quantity (not duplicated in list)
        Example: [{'name': 'Sol Ring', 'color_identity': [], 'quantity': 1}, ...]
    """
    # Extract deck ID from URL if needed
    if 'moxfield.com' in deck_url_or_id:
        match = re.search(r'moxfield\.com/decks/([^/?]+)', deck_url_or_id)
        if match:
            deck_id = match.group(1)
        else:
            print(f"Could not extract Moxfield deck ID from: {deck_url_or_id}")
            return []
    else:
        deck_id = deck_url_or_id
    
    # Moxfield API endpoint
    url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}/"
    
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        cards = []
        
        # Extract mainboard cards
        boards = data.get('boards', {})
        mainboard_data = boards.get('mainboard', {})
        mainboard = mainboard_data.get('cards', {})
        
        for card_data in mainboard.values():
            if card_data.get('card'):
                card = card_data['card']
                card_name = card.get('name')
                card_color_identity = card.get('color_identity', [])
                quantity = card_data.get('quantity', 1)
                
                if card_name:
                    # Apply color identity filter if specified
                    if commander_colors is not None:
                        if all(color in commander_colors for color in card_color_identity):
                            cards.append({
                                'name': card_name,
                                'color_identity': card_color_identity,
                                'quantity': quantity
                            })
                    else:
                        cards.append({
                            'name': card_name,
                            'color_identity': card_color_identity,
                            'quantity': quantity
                        })
        
        return cards
        
    except Exception as e:
        print(f"[Moxfield] Error fetching deck {deck_id}: {e}")
        return []


# ==========================================
# PACK GENERATOR LOGIC
# ==========================================

# Bracket to URL path mapping
BRACKET_PATHS = {
    "any": "",  # Use default from TTS settings
    1: "/exhibition",
    2: "/core",
    3: "/upgraded", 
    4: "/optimized",
    5: "/cedh"
}

# Budget to URL suffix mapping
BUDGET_SUFFIXES = {
    "any": "",
    "budget": "/budget",
    "expensive": "/expensive"
}

# Cardlist tag to card type mapping
TAG_TO_TYPE = {
    "creatures": "Creature",
    "instants": "Instant",
    "sorceries": "Sorcery",
    "enchantments": "Enchantment",
    "planeswalkers": "Planeswalker",
    "battles": "Battle",
    "manaartifacts": "Artifact",
    "utilityartifacts": "Artifact"
}


def fetch_edhrec_data(commander_slug: str, bracket: int, budget: str) -> Optional[Dict]:
    """Fetch card data from EDHRec API"""
    bracket_path = BRACKET_PATHS.get(bracket, "")
    budget_suffix = BUDGET_SUFFIXES.get(budget, "")
    
    url = f"https://json.edhrec.com/pages/commanders/{commander_slug}{bracket_path}{budget_suffix}.json"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'container' in data and 'json_dict' in data['container']:
                return data['container']['json_dict']
            
            return None
            
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def get_commander_name_from_edhrec(edhrec_data: Optional[Dict]) -> Optional[str]:
    """
    Extract the pretty commander name from EDHRec data
    
    Args:
        edhrec_data: Data returned from fetch_edhrec_data
    
    Returns:
        Commander name (e.g., "Atraxa, Grand Unifier") or None
    """
    if not edhrec_data:
        return None
    
    card_data = edhrec_data.get('card', {})
    return card_data.get('name')


def fetch_average_deck(commander_slug: str, bracket: int) -> Optional[Dict[str, float]]:
    """Fetch average deck type distribution for weighted selection"""
    bracket_path = BRACKET_PATHS.get(bracket, "")
    
    url = f"https://edhrec.com/_next/data/hPTdkgKVPwypO51RvBDXB/average-decks/{commander_slug}{bracket_path}.json?commander={commander_slug}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'pageProps' in data and 'data' in data['pageProps']:
                deck_data = data['pageProps']['data']
                
                creature = deck_data.get('creature', 0)
                instant = deck_data.get('instant', 0)
                sorcery = deck_data.get('sorcery', 0)
                artifact = deck_data.get('artifact', 0)
                enchantment = deck_data.get('enchantment', 0)
                planeswalker = deck_data.get('planeswalker', 0)
                battle = deck_data.get('battle', 0)
                
                total = creature + instant + sorcery + artifact + enchantment + planeswalker + battle
                
                if total > 0:
                    return {
                        "Creature": creature / total,
                        "Instant": instant / total,
                        "Sorcery": sorcery / total,
                        "Artifact": artifact / total,
                        "Enchantment": enchantment / total,
                        "Planeswalker": planeswalker / total,
                        "Battle": battle / total
                    }
        
        return None
        
    except Exception as e:
        print(f"Error fetching average deck: {e}")
        return None


def process_cardlists(cardlists: List[Dict], include_game_changers: bool = True, collect_all_game_changers: bool = False) -> List[Dict[str, Any]]:
    """Process EDHRec cardlists into a flat list of cards with metadata
    
    Args:
        cardlists: List of cardlist dictionaries from EDHRec
        include_game_changers: Whether to include the dedicated game changers section
        collect_all_game_changers: If True, mark cards matching Scryfall's game changer list from all sections
    """
    cards = []
    
    # Get basic lands and game changers from Scryfall
    basic_lands = get_cached_basic_lands()
    game_changers = get_cached_game_changers() if collect_all_game_changers else set()
    
    for cardlist in cardlists:
        tag = cardlist.get('tag', '')
        
        # Skip game changers section if disabled (but only if we're not collecting all game changers)
        if tag == 'gamechangers' and not include_game_changers and not collect_all_game_changers:
            continue
        
        cardviews = cardlist.get('cardviews', [])
        
        for cardview in cardviews:
            name = cardview.get('name')
            
            if not name or name in basic_lands:
                continue
            
            # Filter cards that should only appear in game changers section
            # (Prevents duplicates when EDHRec data hasn't been updated yet)
            if name in GAMECHANGER_ONLY_CARDS and tag != 'gamechangers':
                continue
            
            # Determine if it's a land
            is_land = tag in ['lands', 'utilitylands']
            
            # Get card type from tag
            card_type = "Land" if is_land else TAG_TO_TYPE.get(tag, "Unknown")
            
            # If collecting all game changers, check if this card is in Scryfall's game changer list
            effective_tag = tag
            if collect_all_game_changers and name in game_changers:
                effective_tag = 'gamechangers'
            
            cards.append({
                "name": name,
                "category": "Land" if is_land else "NonLand",
                "cardType": card_type,
                "sourceList": effective_tag,
                "synergy": cardview.get('synergy'),
                "inclusion": cardview.get('inclusion')
            })
    
    return cards


def select_weighted_type(type_weights: Dict[str, float]) -> str:
    """Select a card type based on weighted distribution"""
    if not type_weights:
        return "Creature"
    
    types = []
    weights = []
    cumulative = 0
    
    for card_type, weight in type_weights.items():
        if weight > 0:
            types.append(card_type)
            cumulative += weight
            weights.append(cumulative)
    
    if not types:
        return "Creature"
    
    rand = random.random()
    
    for i, threshold in enumerate(weights):
        if rand <= threshold:
            return types[i]
    
    return types[-1]


def select_cards_by_type(cards: List[Dict], card_type: str, count: int, used_cards: set) -> List[str]:
    """Select random cards of a specific type"""
    available = [c['name'] for c in cards if c['cardType'] == card_type and c['name'] not in used_cards]
    
    if not available:
        return []
    
    selected_count = min(count, len(available))
    selected = random.sample(available, selected_count)
    
    return selected


def select_random_cards(cards: List[Dict], count: int, used_cards: set) -> List[str]:
    """Select random cards from all types with equal probability"""
    available = [c['name'] for c in cards if c['name'] not in used_cards]
    
    if not available:
        return []
    
    selected_count = min(count, len(available))
    selected = random.sample(available, selected_count)
    
    return selected


def select_weighted_cards(cards: List[Dict], count: int, type_weights: Dict[str, float], used_cards: set) -> List[str]:
    """Select cards using weighted type distribution from average deck"""
    selected = []
    
    for _ in range(count):
        card_type = select_weighted_type(type_weights)
        card_list = select_cards_by_type(cards, card_type, 1, used_cards)
        
        if card_list:
            selected.extend(card_list)
            used_cards.add(card_list[0])
        else:
            fallback = select_random_cards(cards, 1, used_cards)
            if fallback:
                selected.extend(fallback)
                used_cards.add(fallback[0])
    
    return selected


def select_cards_from_category(cards: List[Dict], category: str, count: int, used_cards: set, commander_colors: Optional[List[str]] = None) -> List[str]:
    """Select cards from a specific EDHRec category/tag
    
    Args:
        cards: List of card dictionaries with name, category, sourceList, etc.
        category: The EDHRec category/tag to select from
        count: Number of cards to select
        used_cards: Set of card names already used
        commander_colors: Optional commander color identity to filter off-color fetch lands
    
    Returns:
        List of selected card names
    """
    # When requesting 'lands', include both 'lands' and 'utilitylands'
    if category == 'lands':
        available = [c['name'] for c in cards if c['sourceList'] in ['lands', 'utilitylands'] and c['name'] not in used_cards]
    else:
        available = [c['name'] for c in cards if c['sourceList'] == category and c['name'] not in used_cards]
    
    # Filter out off-color fetch lands if commander colors are provided
    if commander_colors and category in ['lands', 'utilitylands']:
        commander_color_set = set(commander_colors)
        filtered = []
        for card_name in available:
            if card_name in FETCH_LANDS:
                # Only include fetch if ALL its colors are in commander's color identity
                fetch_colors = set(FETCH_LANDS[card_name])
                if fetch_colors.issubset(commander_color_set):
                    filtered.append(card_name)
            else:
                # Not a fetch land, include it
                filtered.append(card_name)
        available = filtered
    
    if not available:
        return []
    
    selected_count = min(count, len(available))
    selected = random.sample(available, selected_count)
    
    return selected


def process_scryfall_slots(
    slots: List[Dict],
    commander_colors: Optional[List[str]],
    pack_level_color_filter: bool,
    used_cards: set
) -> List[str]:
    """
    Process Scryfall slots to generate cards
    
    Args:
        slots: List of slot configurations for Scryfall packs
        commander_colors: Commander color identity from EDHRec
        pack_level_color_filter: Pack-level useCommanderColorIdentity setting
        used_cards: Set of cards already used
    
    Returns:
        List of selected card names
    """
    selected_cards = []
    
    for slot in slots:
        query = slot.get('query')
        count = slot.get('count', 1)
        
        # Slot-level override takes precedence over pack-level setting
        use_color_filter = slot.get('useCommanderColorIdentity', pack_level_color_filter)
        
        # Check if color complexity weighting is enabled (default: True for direct Scryfall URLs)
        use_weighting = slot.get('colorComplexityWeighting', True)
        
        if not query:
            continue
        
        # Build complete query with filters
        full_query = build_scryfall_query(query, commander_colors, use_color_filter)
        
        if use_weighting:
            # Fetch cards with color identity for weighted selection
            available_cards_data = fetch_scryfall_cards_with_colors(full_query)
            
            # Filter out already used cards
            available_cards_data = [c for c in available_cards_data if c['name'] not in used_cards]
            
            # Use weighted selection based on color complexity
            selected = weighted_random_sample(available_cards_data, count, use_quantity=False)
        else:
            # Simple unweighted selection (old behavior)
            available_cards = fetch_scryfall_cards(full_query)
            
            # Filter out already used cards
            available_cards = [c for c in available_cards if c not in used_cards]
            
            # Select random cards
            selected_count = min(count, len(available_cards))
            selected = random.sample(available_cards, selected_count) if selected_count > 0 else []
        
        selected_cards.extend(selected)
        used_cards.update(selected)
    
    return selected_cards


def process_moxfield_slots(
    slots: List[Dict],
    used_cards: set,
    commander_colors: Optional[List[str]] = None,
    pack_level_color_filter: bool = False
) -> List[str]:
    """
    Process Moxfield slots to generate cards from deck pools
    
    Args:
        slots: List of slot configurations for Moxfield packs
        used_cards: Set of cards already used
        commander_colors: Optional commander color identity for filtering
        pack_level_color_filter: Whether to apply color filtering (can be overridden per slot)
    
    Returns:
        List of selected card names
    """
    selected_cards = []
    
    for slot in slots:
        deck_url = slot.get('deckUrl')
        count = slot.get('count', 15)  # Default 15 cards per pack
        
        # Slot-level override takes precedence over pack-level setting
        use_color_filter = slot.get('useCommanderColorIdentity', pack_level_color_filter)
        
        # Check if color complexity weighting is enabled (default: True for direct Moxfield URLs)
        use_weighting = slot.get('colorComplexityWeighting', True)
        
        if not deck_url:
            print("[Moxfield] Warning: slot missing 'deckUrl'")
            continue
        
        # Fetch cards from Moxfield deck
        filter_colors = commander_colors if use_color_filter else None
        
        if use_weighting:
            # Fetch cards with color identity and quantities for weighted selection
            available_cards_data = fetch_moxfield_cards_with_colors(deck_url, filter_colors)
            
            # Filter out already used cards
            available_cards_data = [c for c in available_cards_data if c['name'] not in used_cards]
            
            # Use weighted selection (color complexity * quantity)
            selected = weighted_random_sample(available_cards_data, count, use_quantity=True)
        else:
            # Simple unweighted selection (old behavior)
            available_cards = fetch_moxfield_cards(deck_url, filter_colors)
            
            # Filter out already used cards
            available_cards = [c for c in available_cards if c not in used_cards]
            
            # Select random cards
            selected_count = min(count, len(available_cards))
            selected = random.sample(available_cards, selected_count) if selected_count > 0 else []
        
        if selected:
            selected_cards.extend(selected)
            used_cards.update(selected)
        else:
            print(f"[Moxfield] Warning: Not enough unique cards in deck (requested {count})")
    
    return selected_cards


def generate_packs(commander_slug: str, config: Dict[str, Any], bracket: int = 2) -> List[Dict[str, Any]]:
    """Main function to generate packs based on commander and configuration"""
    packs = []
    global_used_cards = set()
    
    # Fetch commander data from EDHRec (once for all packs)
    commander_colors = None
    commander_name = None
    if commander_slug:
        edhrec_data = fetch_edhrec_data(commander_slug, bracket, 'any')
        if edhrec_data:
            # Extract color identity and name from the card object
            card_data = edhrec_data.get('card', {})
            commander_colors = card_data.get('color_identity', [])
            commander_name = card_data.get('name')
    
    for pack_type in config.get('packTypes', []):
        pack_name = pack_type.get('name', 'Pack')
        pack_count = pack_type.get('count', 1)
        slots = pack_type.get('slots', [])
        source = pack_type.get('source', 'edhrec')  # Default to EDHRec for backward compatibility
        
        for pack_num in range(pack_count):
            pack_cards = []
            pack_used_cards = set()
            
            # Route to appropriate pack generation logic based on source
            if source == 'scryfall':
                # Scryfall pack generation
                pack_level_color_filter = pack_type.get('useCommanderColorIdentity', True)  # Default to true
                scryfall_cards = process_scryfall_slots(slots, commander_colors, pack_level_color_filter, pack_used_cards | global_used_cards)
                pack_cards.extend(scryfall_cards)
                pack_used_cards.update(scryfall_cards)
            
            elif source == 'moxfield':
                # Moxfield pack generation
                pack_level_color_filter = pack_type.get('useCommanderColorIdentity', False)  # Default to false for backward compatibility
                moxfield_cards = process_moxfield_slots(slots, pack_used_cards | global_used_cards, commander_colors, pack_level_color_filter)
                pack_cards.extend(moxfield_cards)
                pack_used_cards.update(moxfield_cards)
            
            else:
                # EDHRec pack generation (original logic)
                for slot in slots:
                    card_type = slot.get('cardType', 'weighted')
                    budget = slot.get('budget', 'any')
                    slot_bracket = slot.get('bracket', 'any')
                    card_count = slot.get('count', 1)
                    
                    # Use bracket 4 for gamechangers when "any" is specified (brackets 1-3 have few/no gamechangers)
                    if card_type == 'gamechangers' and slot_bracket == 'any':
                        effective_bracket = 4
                        print(f"[gamechangers] Using bracket 4 instead of 'any' (brackets 1-3 have minimal gamechangers)")
                    else:
                        # Use slot_bracket as-is, including "any" (which means no bracket filter)
                        effective_bracket = slot_bracket
                    
                    edhrec_data = fetch_edhrec_data(commander_slug, effective_bracket, budget)
                    
                    if not edhrec_data:
                        continue
                    
                    # When requesting gamechangers, collect from all sections using Scryfall's game changer list
                    collect_all = (card_type == 'gamechangers')
                    cards = process_cardlists(edhrec_data.get('cardlists', []), collect_all_game_changers=collect_all)
                    
                    selected = []
                    
                    if card_type == 'weighted':
                        type_weights = fetch_average_deck(commander_slug, effective_bracket)
                        if type_weights:
                            selected = select_weighted_cards(cards, card_count, type_weights, pack_used_cards | global_used_cards)
                        else:
                            selected = select_random_cards(cards, card_count, pack_used_cards | global_used_cards)
                    
                    elif card_type == 'random':
                        selected = select_random_cards(cards, card_count, pack_used_cards | global_used_cards)
                    
                    elif card_type in ['creatures', 'instants', 'sorceries', 'enchantments', 'planeswalkers', 
                                       'battles', 'lands', 'utilityartifacts', 'manaartifacts', 
                                       'newcards', 'highsynergycards', 'topcards', 'gamechangers']:
                        selected = select_cards_from_category(cards, card_type, card_count, pack_used_cards | global_used_cards, commander_colors)
                    
                    else:
                        selected = select_cards_from_category(cards, card_type, card_count, pack_used_cards | global_used_cards, commander_colors)
                    
                    pack_cards.extend(selected)
                    pack_used_cards.update(selected)
            
            global_used_cards.update(pack_used_cards)
            
            # Build intelligent pack name
            # Priority: 1. Config override (pack_name), 2. API-generated name, 3. Generic fallback
            
            # Check if config provided a custom name (not just the default "Pack")
            has_custom_name = pack_name != 'Pack'
            
            if has_custom_name:
                # Use config-provided name, but still add card count
                card_count = len(pack_cards)
                card_word = "Card" if card_count == 1 else "Cards"
                pack_display_name = f"{pack_name} | {card_count} {card_word}"
            else:
                # Generate intelligent name based on source
                # Format:
                #   EDHRec: "Commander Name | EDHRec | Color Identity"
                #   Scryfall: "Scryfall Query | Color Identity"
                #   Moxfield: "Deck Name Card Set | Color Identity"
                
                parts = []
                
                if source == 'moxfield':
                    # Try to fetch deck name from first slot
                    deck_name = None
                    if slots and len(slots) > 0:
                        first_deck_url = slots[0].get('deckUrl')
                        if first_deck_url:
                            deck_name = fetch_moxfield_deck_name(first_deck_url)
                    
                    if deck_name:
                        parts.append(f"{deck_name} Card Set")
                    else:
                        parts.append("Moxfield Card Set")
                
                elif source == 'scryfall':
                    parts.append("Scryfall Query")
                
                else:  # edhrec
                    if commander_name:
                        parts.append(commander_name)
                        parts.append("EDHRec")
                    else:
                        parts.append("EDHRec")
                
                # Add color identity suffix if filtering is active
                pack_level_color_filter = pack_type.get('useCommanderColorIdentity', False if source == 'moxfield' else True)
                
                if pack_level_color_filter and commander_colors:
                    color_name = get_color_identity_name(commander_colors)
                    if color_name:
                        parts.append(f"{color_name} Color Identity")
                
                # Add card count
                card_count = len(pack_cards)
                card_word = "Card" if card_count == 1 else "Cards"
                parts.append(f"{card_count} {card_word}")
                
                # Join with pipe separator
                pack_display_name = " | ".join(parts)
            
            packs.append({
                "name": pack_display_name,
                "cards": pack_cards
            })
    
    return packs


# ==========================================
# API HANDLER
# ==========================================

def extract_commander_slug(url: str) -> Optional[str]:
    """Extract commander slug from EDHRec URL"""
    match = re.search(r'/commanders/([^/]+)', url)
    return match.group(1) if match else None


def load_config(config_url: str) -> Dict[str, Any]:
    """Load pack configuration from URL"""
    try:
        with urllib.request.urlopen(config_url) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        raise Exception(f"Failed to load config from {config_url}: {str(e)}")


def get_default_config() -> Dict[str, Any]:
    """Return default pack configuration"""
    return {
        "packTypes": [
            {
                "name": "Standard Pack",
                "count": 1,
                "slots": [
                    {"cardType": "weighted", "budget": "expensive", "bracket": 0, "count": 1},
                    {"cardType": "weighted", "budget": "budget", "bracket": 0, "count": 11},
                    {"cardType": "lands", "budget": "any", "bracket": 0, "count": 3}
                ]
            }
        ]
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for pack generation"""
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            request_data = json.loads(body.decode('utf-8'))
            
            commander_url = request_data.get('commander_url')
            config_url = request_data.get('config_url')
            config_json = request_data.get('config')
            
            # Check if config is Scryfall-only (no EDHRec packs)
            if config_json:
                config = config_json
            elif config_url:
                config = load_config(config_url)
            else:
                config = get_default_config()
            
            is_scryfall_only = all(
                pack.get('source') in ['scryfall', 'moxfield']
                for pack in config.get('packTypes', [])
            )
            
            # Commander is optional for Scryfall/Moxfield-only configs
            if not commander_url and not is_scryfall_only:
                # Return a more helpful error with the flag
                self.send_json_response(400, {
                    "error": "Missing commander_url parameter (required for EDHRec packs)",
                    "commander_required": True,
                    "message": "This pack configuration contains EDHRec packs which require a commander URL. Please provide an EDHRec commander URL."
                })
                return
            
            commander_slug = None
            if commander_url:
                commander_slug = extract_commander_slug(commander_url)
                if not commander_slug:
                    self.send_error_response(400, "Invalid commander URL format")
                    return
            
            packs = generate_packs(commander_slug, config)
            
            self.send_json_response(200, {"packs": packs})
            
        except Exception as e:
            import traceback
            error_details = {
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            print(f"ERROR in do_POST: {error_details}")  # Log to Vercel logs
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests - return API documentation"""
        docs = {
            "endpoint": "/api/generate-packs",
            "method": "POST",
            "description": "Generate EDH randomizer packs based on commander and configuration",
            "input": {
                "commander_url": "https://edhrec.com/commanders/atraxa-grand-unifier",
                "config_url": "https://example.com/pack_config.json (optional)"
            },
            "output": {
                "packs": [
                    {
                        "name": "Standard Pack",
                        "cards": ["Card Name 1", "Card Name 2"]
                    }
                ]
            }
        }
        self.send_json_response(200, docs)
    
    def send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, status_code: int, message: str):
        """Send error response"""
        self.send_json_response(status_code, {"error": message})

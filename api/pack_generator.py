"""
EDHRec Pack Generator - Core Logic
Fetches and processes EDHRec data to generate card packs
Includes utility lands in land pool (fixed 2025-11-05)
"""

import json
import urllib.request
import random
from typing import Dict, List, Any, Optional, Tuple


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

# Basic lands to skip
BASIC_LANDS = {"Swamp", "Plains", "Forest", "Island", "Mountain"}

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
    """
    Fetch card data from EDHRec API
    
    Args:
        commander_slug: Commander name slug (e.g., 'atraxa-grand-unifier')
        bracket: Bracket level (1-5)
        budget: Budget tier ('any', 'budget', 'expensive')
    
    Returns:
        Dictionary with card lists or None on error
    """
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


def fetch_average_deck(commander_slug: str, bracket: int) -> Optional[Dict[str, float]]:
    """
    Fetch average deck type distribution for weighted selection
    
    Returns:
        Dictionary mapping card types to their weight percentages
    """
    bracket_path = BRACKET_PATHS.get(bracket, "")
    
    # Note: This URL format may need adjustment based on EDHRec's current API
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


def process_cardlists(cardlists: List[Dict], include_game_changers: bool = True) -> List[Dict[str, Any]]:
    """
    Process EDHRec cardlists into a flat list of cards with metadata
    
    Args:
        cardlists: List of cardlist objects from EDHRec API
        include_game_changers: Whether to include game-changing cards
    
    Returns:
        List of card dictionaries with name, type, category, etc.
    """
    cards = []
    
    for cardlist in cardlists:
        tag = cardlist.get('tag', '')
        
        # Skip game changers if disabled
        if tag == 'gamechangers' and not include_game_changers:
            continue
        
        cardviews = cardlist.get('cardviews', [])
        
        for cardview in cardviews:
            name = cardview.get('name')
            
            if not name or name in BASIC_LANDS:
                continue
            
            # Determine if it's a land
            is_land = tag in ['lands', 'utilitylands']
            
            # Get card type from tag
            card_type = "Land" if is_land else TAG_TO_TYPE.get(tag, "Unknown")
            
            cards.append({
                "name": name,
                "category": "Land" if is_land else "NonLand",
                "cardType": card_type,
                "sourceList": tag,
                "synergy": cardview.get('synergy'),
                "inclusion": cardview.get('inclusion')
            })
    
    return cards


def select_weighted_type(type_weights: Dict[str, float]) -> str:
    """
    Select a card type based on weighted distribution
    """
    if not type_weights:
        return "Creature"  # Default fallback
    
    # Create cumulative distribution
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
    
    # Random selection based on weights
    rand = random.random()
    
    for i, threshold in enumerate(weights):
        if rand <= threshold:
            return types[i]
    
    return types[-1]


def select_cards_by_type(cards: List[Dict], card_type: str, count: int, used_cards: set) -> List[str]:
    """
    Select random cards of a specific type
    """
    available = [c['name'] for c in cards if c['cardType'] == card_type and c['name'] not in used_cards]
    
    if not available:
        return []
    
    selected_count = min(count, len(available))
    selected = random.sample(available, selected_count)
    
    return selected


def select_random_cards(cards: List[Dict], count: int, used_cards: set) -> List[str]:
    """
    Select random cards from all types with equal probability
    """
    available = [c['name'] for c in cards if c['name'] not in used_cards]
    
    if not available:
        return []
    
    selected_count = min(count, len(available))
    selected = random.sample(available, selected_count)
    
    return selected


def select_weighted_cards(cards: List[Dict], count: int, type_weights: Dict[str, float], used_cards: set) -> List[str]:
    """
    Select cards using weighted type distribution from average deck
    """
    selected = []
    
    for _ in range(count):
        card_type = select_weighted_type(type_weights)
        card_list = select_cards_by_type(cards, card_type, 1, used_cards)
        
        if card_list:
            selected.extend(card_list)
            used_cards.add(card_list[0])
        else:
            # Try any type if preferred type unavailable
            fallback = select_random_cards(cards, 1, used_cards)
            if fallback:
                selected.extend(fallback)
                used_cards.add(fallback[0])
    
    return selected


def select_cards_from_category(cards: List[Dict], category: str, count: int, used_cards: set) -> List[str]:
    """
    Select cards from a specific EDHRec category/tag
    """
    # When requesting 'lands', include both 'lands' and 'utilitylands'
    if category == 'lands':
        available = [c['name'] for c in cards if c['sourceList'] in ['lands', 'utilitylands'] and c['name'] not in used_cards]
        print(f"[DEBUG] Selecting {count} lands from {len(available)} available (including utility lands)")
    else:
        available = [c['name'] for c in cards if c['sourceList'] == category and c['name'] not in used_cards]
    
    if not available:
        print(f"[DEBUG] No available cards for category: {category}")
        return []
    
    selected_count = min(count, len(available))
    selected = random.sample(available, selected_count)
    
    print(f"[DEBUG] Selected {len(selected)}/{count} cards from category: {category}")
    return selected


def generate_packs(commander_slug: str, config: Dict[str, Any], bracket: int = 2) -> List[Dict[str, Any]]:
    """
    Main function to generate packs based on commander and configuration
    
    Args:
        commander_slug: Commander name (e.g., 'atraxa-grand-unifier')
        config: Pack configuration with packTypes and slots
        bracket: Power bracket (1-6, default 2=core)
    
    Returns:
        List of packs, each with name and cards list
    """
    packs = []
    global_used_cards = set()  # Track duplicates across all packs
    
    # Process each pack type
    for pack_type in config.get('packTypes', []):
        pack_name = pack_type.get('name', 'Pack')
        pack_count = pack_type.get('count', 1)
        slots = pack_type.get('slots', [])
        
        # Generate multiple packs of this type
        for pack_num in range(pack_count):
            pack_cards = []
            pack_used_cards = set()  # Track within this pack
            
            # Process each slot in the pack
            for slot in slots:
                card_type = slot.get('cardType', 'weighted')
                budget = slot.get('budget', 'any')
                slot_bracket = slot.get('bracket', 'any')
                card_count = slot.get('count', 1)
                
                # Use provided bracket or default
                effective_bracket = slot_bracket if slot_bracket != "any" else bracket
                
                # Fetch EDHRec data for this slot
                edhrec_data = fetch_edhrec_data(commander_slug, effective_bracket, budget)
                
                if not edhrec_data:
                    # If fetch failed, skip this slot
                    continue
                
                # Process cardlists
                cards = process_cardlists(edhrec_data.get('cardlists', []))
                
                # Select cards based on cardType
                selected = []
                
                if card_type == 'weighted':
                    # Get type weights from average deck
                    type_weights = fetch_average_deck(commander_slug, effective_bracket)
                    if type_weights:
                        selected = select_weighted_cards(cards, card_count, type_weights, pack_used_cards | global_used_cards)
                    else:
                        # Fallback to random if no weights available
                        selected = select_random_cards(cards, card_count, pack_used_cards | global_used_cards)
                
                elif card_type == 'random':
                    selected = select_random_cards(cards, card_count, pack_used_cards | global_used_cards)
                
                elif card_type in ['creatures', 'instants', 'sorceries', 'enchantments', 'planeswalkers', 
                                   'battles', 'lands', 'utilityartifacts', 'manaartifacts', 
                                   'newcards', 'highsynergycards', 'topcards', 'gamechangers']:
                    # Specific category
                    selected = select_cards_from_category(cards, card_type, card_count, pack_used_cards | global_used_cards)
                
                else:
                    # Unknown type, try as category
                    selected = select_cards_from_category(cards, card_type, card_count, pack_used_cards | global_used_cards)
                
                # Add selected cards to pack
                pack_cards.extend(selected)
                pack_used_cards.update(selected)
            
            # Update global used cards
            global_used_cards.update(pack_used_cards)
            
            # Create pack
            pack_display_name = f"{pack_name} #{pack_num + 1}" if pack_count > 1 else pack_name
            packs.append({
                "name": pack_display_name,
                "cards": pack_cards
            })
    
    return packs

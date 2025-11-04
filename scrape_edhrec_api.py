#!/usr/bin/env python3
"""
EDHRec API Scraper - Fetches commander data from EDHRec's JSON API
Replaces complex Playwright-based scraping with simple HTTP requests
"""

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


# Next.js build ID will be fetched dynamically
NEXTJS_BUILD_ID = None


def get_nextjs_build_id() -> str:
    """
    Fetch the current Next.js build ID from EDHREC's HTML.
    The build ID is embedded in the HTML as buildId in a JSON script tag.
    """
    global NEXTJS_BUILD_ID
    
    if NEXTJS_BUILD_ID is not None:
        return NEXTJS_BUILD_ID
    
    try:
        print("Fetching current Next.js build ID from EDHREC...", flush=True)
        req = Request("https://edhrec.com/commanders", headers={'User-Agent': 'EDHRecScraper/1.0'})
        with urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        # Look for the buildId in the __NEXT_DATA__ script tag
        # Pattern: <script id="__NEXT_DATA__" type="application/json">{"props":...,"buildId":"xxx",...}</script>
        match = re.search(r'"buildId":"([^"]+)"', html)
        
        if match:
            build_id = match.group(1)
            NEXTJS_BUILD_ID = build_id
            print(f"  Found build ID: {build_id}")
            return build_id
        else:
            raise RuntimeError("Could not find Next.js build ID in HTML")
    
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Next.js build ID: {e}")


# API URL patterns for different timeframes
# First page (ranks 1-100): Next.js server-side data endpoints
# Subsequent pages (ranks 101+): json.edhrec.com pagination API
def get_api_patterns():
    """Get API patterns with current build ID."""
    build_id = get_nextjs_build_id()
    return {
        "2year": {
            "first": f"https://edhrec.com/_next/data/{build_id}/commanders.json",
            "paged": "https://json.edhrec.com/pages/commanders/year-past2years-{page}.json"
        },
        "month": {
            "first": f"https://edhrec.com/_next/data/{build_id}/commanders/month.json?slug=month",
            "paged": "https://json.edhrec.com/pages/commanders/month-pastmonth-{page}.json"
        },
        "week": {
            "first": f"https://edhrec.com/_next/data/{build_id}/commanders/week.json?slug=week",
            "paged": "https://json.edhrec.com/pages/commanders/week-pastweek-{page}.json"
        }
    }

# Output CSV filenames
CSV_FILENAMES = {
    "2year": "top_commanders_2year.csv",
    "month": "top_commanders_month.csv",
    "week": "top_commanders_week.csv"
}

# CSV column headers
CSV_HEADERS = [
    "Rank", "Colors", "CMC", "Name", "Rarity", "Type",
    "Card Kingdom", "TCGPlayer", "Face to Face", "Cardmarket",
    "Cardhoarder", "Salt", "Decks", "Set Code", "Set Name"
]


def fetch_scryfall_set_info(card_name: str) -> tuple[str, str]:
    """
    Fetch set information from Scryfall API for a given card name.
    Uses the /cards/named endpoint with fuzzy matching to get the default printing.
    
    Args:
        card_name: The name of the commander card
        
    Returns:
        Tuple of (set_code, set_name). Returns ("", "") if fetch fails.
    """
    try:
        # Handle double-faced cards (e.g., "Frodo // Sam" -> "Frodo")
        # Scryfall named search works with just the front face name
        search_name = card_name.split(' // ')[0]
        
        # URL encode the card name
        from urllib.parse import quote
        encoded_name = quote(search_name)
        
        # Use fuzzy search to be more forgiving of name variations
        url = f"https://api.scryfall.com/cards/named?fuzzy={encoded_name}"
        
        req = Request(url, headers={'User-Agent': 'EDHRecScraper/1.0'})
        
        # Scryfall recommends 50-100ms between requests
        time.sleep(0.075)
        
        with urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            set_code = data.get('set', '').upper()
            set_name = data.get('set_name', '')
            
            return (set_code, set_name)
            
    except HTTPError as e:
        if e.code == 404:
            print(f"    Warning: Card '{card_name}' not found on Scryfall", file=sys.stderr)
        else:
            print(f"    HTTP Error {e.code} fetching Scryfall data for '{card_name}': {e.reason}", file=sys.stderr)
        return ("", "")
    except Exception as e:
        print(f"    Error fetching Scryfall data for '{card_name}': {e}", file=sys.stderr)
        return ("", "")


def fetch_json_page(url: str) -> Optional[Dict[str, Any]]:
    """Fetch a single JSON page from the API."""
    try:
        req = Request(url, headers={'User-Agent': 'EDHRecScraper/1.0'})
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        if e.code == 403:
            # Page doesn't exist or access denied (likely means no more pages)
            return None
        print(f"HTTP Error {e.code} fetching {url}: {e.reason}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"URL Error fetching {url}: {e.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error for {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error fetching {url}: {e}", file=sys.stderr)
        return None


def get_color_identity(colors: List[str]) -> str:
    """Convert color array to comma-separated color identity string.
    
    Args:
        colors: List of color codes like ["W", "U", "B"] or empty list
        
    Returns:
        Comma-separated uppercase color codes like "W,U,B" or "Colorless"
    """
    if not colors or len(colors) == 0:
        return "Colorless"
    
    # Join with commas, uppercase (colors should already be uppercase from API)
    return ",".join(c.upper() for c in colors)


def extract_commander_data(card: Dict[str, Any], from_nextjs: bool = False) -> Dict[str, Any]:
    """Extract relevant data from a commander card object.
    
    Args:
        card: Card data dict from API
        from_nextjs: True if data is from Next.js endpoint (first page)
    
    Note: Next.js endpoints don't include prices, cmc, rarity, type, or salt.
          They only have: name, rank, color_identity, and inclusion (instead of num_decks)
    """
    # For Next.js responses, use simpler structure
    if from_nextjs:
        return {
            "rank": card.get("rank", ""),
            "colors": get_color_identity(card.get("color_identity", [])),
            "cmc": "",  # Not available in Next.js response
            "name": card.get("name", ""),
            "rarity": "",  # Not available in Next.js response
            "type": "",  # Not available in Next.js response
            "cardkingdom": "",
            "tcgplayer": "",
            "face2face": "",
            "cardmarket": "",
            "cardhoarder": "",
            "salt": "",  # Not available in Next.js response
            "num_decks": card.get("inclusion", ""),  # Next.js uses "inclusion" instead of "num_decks"
            "set_code": "",  # Will be fetched from Scryfall later
            "set_name": ""   # Will be fetched from Scryfall later
        }
    
    # For paginated API responses, use full data
    prices = card.get("prices", {}) or {}
    
    # Handle prices safely - some might be None
    def get_price(vendor: str) -> str:
        vendor_data = prices.get(vendor, {})
        if vendor_data is None:
            return ""
        return vendor_data.get("price", "")
    
    # Convert CMC from float to int (API returns 4.0, we want "4")
    cmc = card.get("cmc", "")
    if cmc and isinstance(cmc, (int, float)):
        cmc = int(cmc)
    
    return {
        "rank": card.get("rank", ""),
        "colors": get_color_identity(card.get("color_identity", [])),
        "cmc": cmc,
        "name": card.get("name", ""),
        "rarity": card.get("rarity", "").lower() if card.get("rarity") else "",
        "type": card.get("primary_type", ""),
        "cardkingdom": get_price("cardkingdom"),
        "tcgplayer": get_price("tcgplayer"),
        "face2face": get_price("face2face"),
        "cardmarket": get_price("cardmarket"),
        "cardhoarder": get_price("cardhoarder"),
        "salt": round(card.get("salt", 0), 2),
        "num_decks": card.get("num_decks", ""),
        "set_code": "",  # Will be fetched from Scryfall later
        "set_name": ""   # Will be fetched from Scryfall later
    }


def fetch_commander_detail(sanitized_name: str) -> Optional[Dict]:
    """
    Fetch detailed commander data from individual commander endpoint.
    
    Args:
        sanitized_name: The sanitized commander name (e.g., 'yshtola-nights-blessed')
        
    Returns:
        Commander data dictionary or None if fetch fails
    """
    url = f"https://json.edhrec.com/pages/commanders/{sanitized_name}.json"
    try:
        data = fetch_json_page(url)
        if data:
            container = data.get('container', {})
            json_dict = container.get('json_dict', {})
            card = json_dict.get('card', {})
            return card
    except Exception as e:
        print(f"    Error fetching detail for {sanitized_name}: {e}")
    return None


def fetch_all_commanders(timeframe: str, max_pages: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch all commander pages for a given timeframe.
    
    For the first 100 commanders, fetches individual detail pages to get complete metadata.
    For remaining commanders, uses pagination API which has full data.
    """
    url_config = get_api_patterns().get(timeframe)
    if not url_config:
        raise ValueError(f"Unknown timeframe: {timeframe}")
    
    all_commanders = []
    page = 0  # Start at 0 for the first page (ranks 1-100)
    
    print(f"Fetching {timeframe} commander data...")
    
    while page <= max_pages:
        # First page uses Next.js endpoint, subsequent pages use pagination API
        if page == 0:
            url = url_config["first"]
            is_nextjs = True
        else:
            url = url_config["paged"].format(page=page)
            is_nextjs = False
        
        print(f"  Fetching page {page}...", end=" ", flush=True)
        
        data = fetch_json_page(url)
        
        if data is None:
            print(f"No data (likely end of pages)")
            break
        
        # Extract cardviews from the response
        # Next.js endpoints wrap data differently: pageProps.data.container.json_dict.cardlists
        # Pagination API has direct: cardviews array
        if is_nextjs:
            try:
                cardlists = data["pageProps"]["data"]["container"]["json_dict"]["cardlists"]
                cardviews = cardlists[0].get("cardviews", [])
            except (KeyError, IndexError, TypeError):
                print(f"Invalid Next.js response structure")
                break
        else:
            cardviews = data.get("cardviews", [])
        
        if not cardviews:
            print(f"Empty cardviews (end of data)")
            break
        
        first_rank = cardviews[0].get('rank', '?')
        last_rank = cardviews[-1].get('rank', '?')
        print(f"Got {len(cardviews)} commanders (ranks {first_rank}-{last_rank})")
        
        # For first page (ranks 1-100), fetch individual detail pages for complete metadata
        if is_nextjs:
            print(f"  Fetching detailed data for top 100 commanders...")
            for i, card in enumerate(cardviews, 1):
                sanitized = card.get('sanitized', '')
                rank = card.get('rank', i)
                
                if sanitized:
                    print(f"    [{i}/100] Rank {rank}: {sanitized}", end=" ... ", flush=True)
                    detail = fetch_commander_detail(sanitized)
                    
                    if detail:
                        # Merge rank info from Next.js with detail data
                        detail['rank'] = rank
                        commander = extract_commander_data(detail, from_nextjs=False)
                        print("OK")
                    else:
                        # Fallback to limited Next.js data if detail fetch fails
                        print("FAILED (using limited data)")
                        commander = extract_commander_data(card, from_nextjs=True)
                    
                    all_commanders.append(commander)
                else:
                    print(f"    Warning: No sanitized name for rank {rank}")
        else:
            # For pagination pages (101+), use data directly (it has full metadata)
            for card in cardviews:
                all_commanders.append(extract_commander_data(card, from_nextjs=False))
        
        # Check if there are more pages
        # Both endpoint types include a "more" field
        if is_nextjs:
            # For Next.js, check inside cardlists
            more = cardlists[0].get("more") if cardlists else None
        else:
            # For pagination API, check at root level
            more = data.get("more")
        
        if not more:
            print(f"  Reached last page")
            break
        
        page += 1
    
    print(f"Total commanders fetched: {len(all_commanders)}")
    
    # Fetch set information from Scryfall for all commanders
    if all_commanders:
        print(f"\nFetching set information from Scryfall...")
        for i, commander in enumerate(all_commanders, 1):
            card_name = commander.get("name", "")
            if card_name:
                print(f"  [{i}/{len(all_commanders)}] {card_name}...", end=" ", flush=True)
                set_code, set_name = fetch_scryfall_set_info(card_name)
                commander["set_code"] = set_code
                commander["set_name"] = set_name
                if set_code:
                    print(f"{set_code} ({set_name})")
                else:
                    print("Not found")
            else:
                print(f"  [{i}/{len(all_commanders)}] Warning: Empty card name", file=sys.stderr)
    
    return all_commanders


def write_csv(commanders: List[Dict[str, Any]], output_path: Path) -> None:
    """Write commander data to CSV file with full quoting to match original format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(CSV_HEADERS)
        
        for cmd in commanders:
            writer.writerow([
                cmd["rank"],
                cmd["colors"],
                cmd["cmc"],
                cmd["name"],
                cmd["rarity"],
                cmd["type"],
                cmd["cardkingdom"],
                cmd["tcgplayer"],
                cmd["face2face"],
                cmd["cardmarket"],
                cmd["cardhoarder"],
                cmd["salt"],
                cmd["num_decks"],
                cmd["set_code"],
                cmd["set_name"]
            ])
    
    print(f"✅ Wrote {len(commanders)} commanders to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape EDHRec commander data via JSON API"
    )
    parser.add_argument(
        "--timeframe",
        choices=["2year", "month", "week"],
        required=True,
        help="Timeframe to scrape"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory for CSV files (default: data)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum pages to fetch (default: 100)"
    )
    
    args = parser.parse_args()
    
    try:
        # Fetch commanders from API
        commanders = fetch_all_commanders(args.timeframe, args.max_pages)
        
        if not commanders:
            print("❌ No commanders fetched!", file=sys.stderr)
            sys.exit(1)
        
        # Write to CSV
        output_file = args.output_dir / CSV_FILENAMES[args.timeframe]
        write_csv(commanders, output_file)
        
        print(f"✅ Successfully scraped {args.timeframe} data!")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

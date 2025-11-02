# Session Management API for EDH Randomizer Game Mode
# Vercel serverless function
# Updated: 2025-11-01

from http.server import BaseHTTPRequestHandler
import json
import time
import random
import string
from typing import Dict, List, Optional

# In-memory session storage (for MVP - replace with Redis/database for production)
SESSIONS: Dict[str, dict] = {}

# Session expiration time (24 hours)
SESSION_TTL = 24 * 60 * 60

def generate_session_code() -> str:
    """Generate a random 5-character session code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def generate_player_id() -> str:
    """Generate a unique player ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

def generate_pack_code() -> str:
    """Generate a unique pack code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def cleanup_expired_sessions():
    """Remove expired sessions"""
    current_time = time.time()
    expired = [code for code, session in SESSIONS.items() 
               if current_time - session['created_at'] > SESSION_TTL]
    for code in expired:
        del SESSIONS[code]

def cors_headers():
    """Return CORS headers for all responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        for key, value in cors_headers().items():
            self.send_header(key, value)
        self.end_headers()

    def do_POST(self):
        """Handle POST requests for session operations"""
        cleanup_expired_sessions()
        
        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_error_response(400, 'Invalid JSON')
            return

        # Route based on path - handle both with and without /api/sessions prefix
        path = self.path.split('?')[0]
        
        # Strip /api/sessions prefix if present (Vercel might include it or not)
        if path.startswith('/api/sessions'):
            path = path[13:]  # Remove '/api/sessions'
        
        if path == '/create' or path == '':
            self.handle_create_session(data)
        elif path == '/join':
            self.handle_join_session(data)
        elif path == '/update-name':
            self.handle_update_name(data)
        elif path == '/roll-powerups':
            self.handle_roll_powerups(data)
        elif path == '/lock-commander':
            self.handle_lock_commander(data)
        elif path == '/update-commanders':
            self.handle_update_commanders(data)
        elif path == '/generate-pack-codes':
            self.handle_generate_pack_codes(data)
        else:
            self.send_error_response(404, f'Endpoint not found: {self.path}')

    def do_GET(self):
        """Handle GET requests"""
        cleanup_expired_sessions()
        
        path = self.path.split('?')[0]
        
        # Strip /api/sessions prefix if present
        if path.startswith('/api/sessions'):
            path = path[13:]  # Remove '/api/sessions'
        
        # Get session by code: /sessions/{code} or /{code}
        if path.startswith('/pack/'):
            # Get pack by code: /pack/{code}
            pack_code = path.split('/')[-1].upper()
            self.handle_get_pack(pack_code)
        elif path and path != '/' and not '/' in path[1:]:
            # Single path segment = session code
            session_code = path.strip('/').upper()
            self.handle_get_session(session_code)
        else:
            self.send_error_response(404, f'Endpoint not found: {self.path}')

    def handle_create_session(self, data=None):
        """Create a new game session"""
        if data is None:
            data = {}
        
        player_name = data.get('playerName', '').strip()[:20]  # Max 20 chars
        if not player_name:
            player_name = 'Player 1'
        
        session_code = generate_session_code()
        while session_code in SESSIONS:
            session_code = generate_session_code()
        
        player_id = generate_player_id()
        
        session = {
            'sessionCode': session_code,
            'hostId': player_id,
            'state': 'waiting',  # waiting, rolling, selecting, complete
            'players': [
                {
                    'id': player_id,
                    'number': 1,
                    'name': player_name,
                    'powerup': None,
                    'commanderUrl': None,
                    'commanderData': None,
                    'commanderLocked': False,
                    'selectedCommanderIndex': None,
                    'packCode': None,
                    'packConfig': None
                }
            ],
            'created_at': time.time(),
            'updated_at': time.time()
        }
        
        SESSIONS[session_code] = session
        
        self.send_json_response(200, {
            'sessionCode': session_code,
            'playerId': player_id,
            'sessionData': session
        })

    def handle_join_session(self, data):
        """Join an existing session"""
        session_code = data.get('sessionCode', '').upper()
        player_name = data.get('playerName', '').strip()[:20]  # Max 20 chars
        
        if not session_code or session_code not in SESSIONS:
            self.send_error_response(404, 'Session not found')
            return
        
        session = SESSIONS[session_code]
        
        # Check if session is full (max 4 players)
        if len(session['players']) >= 4:
            self.send_error_response(400, 'Session is full')
            return
        
        # Check if session has already started rolling
        if session['state'] != 'waiting':
            self.send_error_response(400, 'Session has already started')
            return
        
        # Add new player
        player_id = generate_player_id()
        player_number = len(session['players']) + 1
        
        # Generate default name if not provided
        if not player_name:
            player_name = f'Player {player_number}'
        
        session['players'].append({
            'id': player_id,
            'number': player_number,
            'name': player_name,
            'powerup': None,
            'commanderUrl': None,
            'commanderData': None,
            'commanderLocked': False,
            'selectedCommanderIndex': None,
            'packCode': None,
            'packConfig': None
        })
        
        session['updated_at'] = time.time()
        
        self.send_json_response(200, {
            'playerId': player_id,
            'sessionData': session
        })

    def handle_update_name(self, data):
        """Update player name in session"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        player_name = data.get('playerName', '').strip()[:20]  # Max 20 chars
        
        if not session_code or session_code not in SESSIONS:
            self.send_error_response(404, 'Session not found')
            return
        
        session = SESSIONS[session_code]
        
        # Find player
        player = next((p for p in session['players'] if p['id'] == player_id), None)
        if not player:
            self.send_error_response(404, 'Player not found')
            return
        
        # Update player name
        if player_name:
            player['name'] = player_name
        
        session['updated_at'] = time.time()
        
        self.send_json_response(200, session)

    def handle_roll_powerups(self, data):
        """Roll powerups for all players (host only)"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        
        if not session_code or session_code not in SESSIONS:
            self.send_error_response(404, 'Session not found')
            return
        
        session = SESSIONS[session_code]
        
        # Verify player is host
        if session['hostId'] != player_id:
            self.send_error_response(403, 'Only host can roll powerups')
            return
        
        # Roll powerups for each player
        # Load powerups data
        import os
        import sys
        
        # Get powerups.json path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        powerups_path = os.path.join(current_dir, '..', 'data', 'powerups.json')
        
        try:
            with open(powerups_path, 'r') as f:
                powerups_data = json.load(f)
        except FileNotFoundError:
            # Fallback: use hardcoded powerup selection
            powerups_data = {
                'rarityWeights': {'common': 55, 'uncommon': 30, 'rare': 12, 'mythic': 3},
                'powerups': []  # Will be loaded from file in production
            }
        
        # Generate powerup for each player using weighted random
        for player in session['players']:
            powerup = self.get_random_powerup(powerups_data)
            player['powerup'] = {
                'id': powerup['id'],
                'name': powerup['name'],
                'rarity': powerup['rarity']
            }
        
        session['state'] = 'selecting'
        session['updated_at'] = time.time()
        
        self.send_json_response(200, session)

    def handle_lock_commander(self, data):
        """Lock in commander selection for a player"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        commander_url = data.get('commanderUrl', '')
        commander_data = data.get('commanderData', {})
        
        if not session_code or session_code not in SESSIONS:
            self.send_error_response(404, 'Session not found')
            return
        
        session = SESSIONS[session_code]
        
        # Find player
        player = next((p for p in session['players'] if p['id'] == player_id), None)
        if not player:
            self.send_error_response(404, 'Player not found')
            return
        
        # Lock in commander
        player['commanderUrl'] = commander_url
        player['commanderData'] = commander_data
        player['commanderLocked'] = True
        
        # Extract selectedCommanderIndex from commanderData and store at player level
        if 'selectedCommanderIndex' in commander_data:
            player['selectedCommanderIndex'] = commander_data['selectedCommanderIndex']
        
        # Check if all players locked in
        all_locked = all(p['commanderLocked'] for p in session['players'])
        if all_locked:
            # Auto-generate pack codes
            self.generate_pack_codes_internal(session)
            session['state'] = 'complete'
        
        session['updated_at'] = time.time()
        
        self.send_json_response(200, session)

    def handle_update_commanders(self, data):
        """Update generated commanders for a player"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        commanders = data.get('commanders', [])
        
        if not session_code or session_code not in SESSIONS:
            self.send_error_response(404, 'Session not found')
            return
        
        session = SESSIONS[session_code]
        
        # Find player
        player = next((p for p in session['players'] if p['id'] == player_id), None)
        if not player:
            self.send_error_response(404, 'Player not found')
            return
        
        # Store commanders in player data
        if 'commanders' not in player:
            player['commanders'] = []
        player['commanders'] = commanders[:10]  # Limit to 10 commanders max
        
        session['updated_at'] = time.time()
        
        self.send_json_response(200, session)

    def handle_generate_pack_codes(self, data):
        """Generate pack codes for all players (when all locked in)"""
        session_code = data.get('sessionCode', '').upper()
        
        if not session_code or session_code not in SESSIONS:
            self.send_error_response(404, 'Session not found')
            return
        
        session = SESSIONS[session_code]
        
        # Verify all players locked in
        all_locked = all(p['commanderLocked'] for p in session['players'])
        if not all_locked:
            self.send_error_response(400, 'Not all players have locked in')
            return
        
        # Generate pack codes
        self.generate_pack_codes_internal(session)
        session['state'] = 'complete'
        session['updated_at'] = time.time()
        
        self.send_json_response(200, session)

    def handle_get_session(self, session_code):
        """Get session data"""
        if session_code not in SESSIONS:
            self.send_error_response(404, 'Session not found')
            return
        
        self.send_json_response(200, SESSIONS[session_code])

    def handle_get_pack(self, pack_code):
        """Get pack configuration by pack code"""
        # Find session with this pack code
        for session in SESSIONS.values():
            for player in session['players']:
                if player.get('packCode') == pack_code:
                    pack_config = {
                        'commanderUrl': player['commanderUrl'],
                        'packQuantity': player['packConfig']['packQuantity'],
                        'config': player['packConfig']['config']
                    }
                    self.send_json_response(200, pack_config)
                    return
        
        self.send_error_response(404, 'Pack code not found')

    def generate_pack_codes_internal(self, session):
        """Internal helper to generate pack codes and configs"""
        # Load powerups to get effects
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        powerups_path = os.path.join(current_dir, '..', 'data', 'powerups.json')
        
        try:
            with open(powerups_path, 'r') as f:
                powerups_data = json.load(f)
        except:
            powerups_data = {'powerups': []}
        
        for player in session['players']:
            # Generate unique pack code
            pack_code = generate_pack_code()
            while any(p.get('packCode') == pack_code for s in SESSIONS.values() for p in s['players']):
                pack_code = generate_pack_code()
            
            # Get powerup effects
            powerup = next((p for p in powerups_data.get('powerups', []) 
                          if p['id'] == player['powerup']['id']), None)
            
            # Generate pack config
            pack_config = self.apply_powerup_to_config(powerup, player['commanderUrl'])
            
            player['packCode'] = pack_code
            player['packConfig'] = pack_config

    def apply_powerup_to_config(self, powerup, commander_url):
        """Generate bundle config from powerup effects (matches packConfigGenerator.js)"""
        bundle_config = {'packTypes': []}
        
        # Base standard pack (1 expensive, 11 budget, 3 lands)
        base_standard_pack = {
            'slots': [
                {'cardType': 'weighted', 'budget': 'expensive', 'bracket': 'any', 'count': 1},
                {'cardType': 'weighted', 'budget': 'budget', 'bracket': 'any', 'count': 11},
                {'cardType': 'lands', 'budget': 'any', 'bracket': 'any', 'count': 3}
            ]
        }
        
        # Special pack templates
        special_pack_templates = {
            'gamechanger': {
                'name': 'Game Changer',
                'count': 1,
                'slots': [{'cardType': 'gamechangers', 'budget': 'any', 'bracket': 'any', 'count': 1}]
            },
            'conspiracy': {
                'name': 'Conspiracy',
                'source': 'scryfall',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'query': 'https://scryfall.com/search?q=%28t%3Aconspiracy+-is%3Aplaytest%29+OR+%28set%3Amb2+name%3A%22Marchesa%27s+Surprise+Party%22%29+OR+%28set%3Amb2+name%3A%22Rule+with+an+Even+Hand%22%29&unique=cards&as=grid&order=name',
                    'count': 1
                }]
            },
            'banned': {
                'name': 'Banned Card',
                'source': 'scryfall',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'query': 'https://scryfall.com/search?q=banned%3Acommander+-f%3Aduel&unique=cards&as=grid&order=name',
                    'count': 1
                }]
            },
            'expensive_lands': {
                'name': 'Expensive Lands',
                'source': 'scryfall',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'query': 'https://scryfall.com/search?q=t%3Aland+%28o%3A%22add+%7B%22+OR+o%3A%22mana+of+any%22%29+usd%3E10&unique=cards&as=grid&order=usd',
                    'count': 1
                }]
            }
        }
        
        # Get effects or use defaults
        effects = powerup.get('effects', {}) if powerup else {}
        
        # Calculate base pack count
        base_pack_count = 5 + effects.get('packQuantity', 0)
        
        # Get modification counts
        budget_upgrade_packs = effects.get('budgetUpgradePacks', 0)
        full_expensive_packs = effects.get('fullExpensivePacks', 0)
        bracket_upgrade_packs = effects.get('bracketUpgradePacks', 0)
        bracket_upgrade = effects.get('bracketUpgrade')
        
        # Calculate pack distribution
        normal_packs = base_pack_count - budget_upgrade_packs - full_expensive_packs - bracket_upgrade_packs
        normal_packs = max(0, normal_packs)
        
        # Add normal packs
        if normal_packs > 0:
            pack = {'count': normal_packs, 'slots': base_standard_pack['slots'].copy()}
            bundle_config['packTypes'].append(pack)
        
        # Add budget upgraded packs
        if budget_upgrade_packs > 0:
            pack = {
                'name': 'Budget Upgraded',
                'count': budget_upgrade_packs,
                'slots': [
                    {'cardType': 'weighted', 'budget': 'expensive', 'bracket': 'any', 'count': 1},
                    {'cardType': 'weighted', 'budget': 'any', 'bracket': 'any', 'count': 11},
                    {'cardType': 'lands', 'budget': 'any', 'bracket': 'any', 'count': 3}
                ]
            }
            bundle_config['packTypes'].append(pack)
        
        # Add full expensive packs
        if full_expensive_packs > 0:
            pack = {
                'name': 'Full Expensive',
                'count': full_expensive_packs,
                'slots': [
                    {'cardType': 'weighted', 'budget': 'expensive', 'bracket': 'any', 'count': 12},
                    {'cardType': 'lands', 'budget': 'any', 'bracket': 'any', 'count': 3}
                ]
            }
            bundle_config['packTypes'].append(pack)
        
        # Add bracket upgraded packs
        if bracket_upgrade_packs > 0 and bracket_upgrade:
            pack = {
                'name': f'Bracket {bracket_upgrade}',
                'count': bracket_upgrade_packs,
                'slots': [
                    {'cardType': 'weighted', 'budget': 'expensive', 'bracket': str(bracket_upgrade), 'count': 1},
                    {'cardType': 'weighted', 'budget': 'budget', 'bracket': str(bracket_upgrade), 'count': 11},
                    {'cardType': 'lands', 'budget': 'any', 'bracket': 'any', 'count': 3}
                ]
            }
            bundle_config['packTypes'].append(pack)
        
        # Add special pack if specified
        special_pack = effects.get('specialPack')
        special_pack_count = effects.get('specialPackCount', 1)
        if special_pack and special_pack in special_pack_templates:
            pack = json.loads(json.dumps(special_pack_templates[special_pack]))
            pack['slots'][0]['count'] = special_pack_count
            bundle_config['packTypes'].append(pack)
        
        return bundle_config

    def get_random_powerup(self, powerups_data):
        """Get random powerup based on rarity weights"""
        weights = powerups_data.get('rarityWeights', {
            'common': 55, 'uncommon': 30, 'rare': 12, 'mythic': 3
        })
        powerups = powerups_data.get('powerups', [])
        
        if not powerups:
            # Fallback powerup
            return {
                'id': 'default',
                'name': 'Standard Pack',
                'rarity': 'common',
                'description': 'No special effects',
                'effects': {}
            }
        
        # Calculate total weight
        total = sum(weights.values())
        rand = random.random() * total
        
        # Determine rarity
        cumulative = 0
        selected_rarity = 'common'
        for rarity, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                selected_rarity = rarity
                break
        
        # Get powerups of that rarity
        rarity_powerups = [p for p in powerups if p['rarity'] == selected_rarity]
        if not rarity_powerups:
            rarity_powerups = [p for p in powerups if p['rarity'] == 'common']
        
        return random.choice(rarity_powerups)

    def send_json_response(self, status_code, data):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        for key, value in cors_headers().items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_json_response(status_code, {'error': True, 'message': message})

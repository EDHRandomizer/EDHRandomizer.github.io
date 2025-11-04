# Session Management API for EDH Randomizer Game Mode
# Vercel serverless function with Redis/Vercel KV support
# Updated: 2025-11-02

from http.server import BaseHTTPRequestHandler
import json
import time
import random
import string
import os
from typing import Dict, List, Optional

# Vercel KV (Redis) for pack code persistence
try:
    import redis
    
    # Try multiple possible environment variable names (Vercel uses different names)
    REDIS_URL = (
        os.environ.get('KV_REST_API_URL') or 
        os.environ.get('KV_URL') or 
        os.environ.get('REDIS_URL') or 
        ''
    )
    REDIS_TOKEN = os.environ.get('KV_REST_API_TOKEN', '')
    
    if REDIS_URL:
        # Vercel KV provides a complete URL, try to use it directly
        try:
            kv_client = redis.from_url(
                REDIS_URL,
                decode_responses=True
            )
            # Test connection
            kv_client.ping()
            KV_ENABLED = True
            print(f"✅ Redis/Vercel KV connected successfully!")
            print(f"   Using: {REDIS_URL[:30]}...")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            kv_client = None
            KV_ENABLED = False
    else:
        kv_client = None
        KV_ENABLED = False
        print("⚠️ Vercel KV not configured - using in-memory storage")
        print(f"   Checked: KV_REST_API_URL, KV_URL, REDIS_URL - all NOT SET")
except ImportError:
    kv_client = None
    KV_ENABLED = False
    print("⚠️ redis package not installed - using in-memory storage")

# In-memory session storage (sessions are temporary, pack codes use KV)
SESSIONS: Dict[str, dict] = {}

# In-memory pack code fallback (only used if KV is not available)
PACK_CODES: Dict[str, dict] = {}

# Session expiration time (12 hours - increased to prevent premature expiration during long game sessions)
# TTL is refreshed on every update, so active sessions stay alive indefinitely
SESSION_TTL = 12 * 60 * 60

# Pack code expiration time (24 hours - auto-removed when memory full via LRU eviction)
# Redis will automatically remove oldest pack codes if memory limit reached
PACK_CODE_TTL = 24 * 60 * 60  # 24 hours

def generate_session_code() -> str:
    """Generate a random 5-character session code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def generate_player_id() -> str:
    """Generate a unique player ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

def generate_pack_code() -> str:
    """Generate a unique pack code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def store_pack_code(pack_code: str, data: dict) -> bool:
    """
    Store pack code data with TTL
    Uses Vercel KV if available, falls back to in-memory
    """
    try:
        if KV_ENABLED and kv_client:
            # Store in Vercel KV with 2-hour TTL
            key = f"pack:{pack_code}"
            kv_client.setex(key, PACK_CODE_TTL, json.dumps(data))
            print(f"✅ Stored pack code {pack_code} in Vercel KV (TTL: {PACK_CODE_TTL}s)")
            return True
        else:
            # Fallback to in-memory storage
            PACK_CODES[pack_code] = {
                'data': data,
                'expires_at': time.time() + PACK_CODE_TTL
            }
            print(f"⚠️ Stored pack code {pack_code} in memory (will be lost on function restart)")
            return True
    except Exception as e:
        print(f"❌ Error storing pack code {pack_code}: {e}")
        # Fallback to in-memory
        PACK_CODES[pack_code] = {
            'data': data,
            'expires_at': time.time() + PACK_CODE_TTL
        }
        return False

def get_pack_code(pack_code: str) -> Optional[dict]:
    """
    Retrieve pack code data
    Checks Vercel KV first, then in-memory fallback
    """
    try:
        if KV_ENABLED and kv_client:
            # Try Vercel KV first
            key = f"pack:{pack_code}"
            data_str = kv_client.get(key)
            if data_str:
                print(f"✅ Retrieved pack code {pack_code} from Vercel KV")
                return json.loads(data_str)
            else:
                print(f"⚠️ Pack code {pack_code} not found in Vercel KV")
                return None
        else:
            # Use in-memory fallback
            if pack_code in PACK_CODES:
                entry = PACK_CODES[pack_code]
                # Check if expired
                if time.time() < entry['expires_at']:
                    print(f"✅ Retrieved pack code {pack_code} from memory")
                    return entry['data']
                else:
                    # Expired, remove it
                    del PACK_CODES[pack_code]
                    print(f"⚠️ Pack code {pack_code} expired and removed from memory")
                    return None
            else:
                print(f"⚠️ Pack code {pack_code} not found in memory")
                return None
    except Exception as e:
        print(f"❌ Error retrieving pack code {pack_code}: {e}")
        # Try in-memory fallback
        if pack_code in PACK_CODES:
            entry = PACK_CODES[pack_code]
            if time.time() < entry['expires_at']:
                return entry['data']
        return None

def store_session(session_code: str, session_data: dict) -> bool:
    """
    Store session data with TTL
    Uses Vercel KV if available, falls back to in-memory
    """
    print(f"💾 [STORE_SESSION] Storing session {session_code}, state: {session_data.get('state')}, players: {len(session_data.get('players', []))}")
    start_time = time.time()
    
    try:
        if KV_ENABLED and kv_client:
            # Store in Vercel KV with SESSION_TTL
            key = f"session:{session_code}"
            kv_client.setex(key, SESSION_TTL, json.dumps(session_data))
            elapsed = (time.time() - start_time) * 1000
            print(f"✅ [STORE_SESSION] Stored session {session_code} in Vercel KV (TTL: {SESSION_TTL}s, {elapsed:.1f}ms)")
            return True
        else:
            # Fallback to in-memory storage
            SESSIONS[session_code] = session_data
            print(f"⚠️ [STORE_SESSION] Stored session {session_code} in memory (will be lost on function restart)")
            return True
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"❌ [STORE_SESSION] Error storing session {session_code} ({elapsed:.1f}ms): {e}")
        import traceback
        traceback.print_exc()
        # Fallback to in-memory
        SESSIONS[session_code] = session_data
        print(f"⚠️ [STORE_SESSION] Fell back to in-memory storage")
        return False

def get_session(session_code: str) -> Optional[dict]:
    """
    Retrieve session data
    Checks Vercel KV first, then in-memory fallback
    """
    print(f"🔍 [GET_SESSION] Looking for session: {session_code}, KV_ENABLED={KV_ENABLED}")
    start_time = time.time()
    
    try:
        if KV_ENABLED and kv_client:
            # Try Vercel KV first
            key = f"session:{session_code}"
            print(f"📡 [GET_SESSION] Querying KV for key: {key}")
            
            data_str = kv_client.get(key)
            elapsed = (time.time() - start_time) * 1000
            
            if data_str:
                session_data = json.loads(data_str)
                print(f"✅ [GET_SESSION] Retrieved session {session_code} from Vercel KV ({elapsed:.1f}ms)")
                print(f"📊 [GET_SESSION] Session state: {session_data.get('state')}, players: {len(session_data.get('players', []))}")
                # Also cache in memory for this function instance
                SESSIONS[session_code] = session_data
                return session_data
            else:
                print(f"⚠️ [GET_SESSION] Session {session_code} not found in Vercel KV ({elapsed:.1f}ms)")
                print(f"🔍 [GET_SESSION] Checking in-memory fallback (have {len(SESSIONS)} cached sessions)")
                
                # Check in-memory as fallback
                if session_code in SESSIONS:
                    print(f"✅ [GET_SESSION] Found {session_code} in memory cache!")
                    return SESSIONS[session_code]
                    
                return None
        else:
            # Use in-memory fallback
            if session_code in SESSIONS:
                print(f"✅ [GET_SESSION] Retrieved session {session_code} from memory (have {len(SESSIONS)} sessions)")
                return SESSIONS[session_code]
            else:
                print(f"⚠️ [GET_SESSION] Session {session_code} not found in memory")
                print(f"📝 [GET_SESSION] Available sessions: {list(SESSIONS.keys())}")
                return None
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        print(f"❌ [GET_SESSION] Error retrieving session {session_code} ({elapsed:.1f}ms): {e}")
        import traceback
        traceback.print_exc()
        # Try in-memory fallback
        if session_code in SESSIONS:
            print(f"✅ [GET_SESSION] Fallback to memory cache successful")
            return SESSIONS[session_code]
        return None

def update_session(session_code: str, session_data: dict) -> bool:
    """
    Update existing session (updates both KV and memory)
    """
    # Update in memory
    SESSIONS[session_code] = session_data
    # Update in KV
    return store_session(session_code, session_data)

def delete_session(session_code: str) -> bool:
    """
    Delete a session from both KV and memory
    """
    try:
        if KV_ENABLED and kv_client:
            key = f"session:{session_code}"
            kv_client.delete(key)
            print(f"✅ Deleted session {session_code} from Vercel KV")
        
        if session_code in SESSIONS:
            del SESSIONS[session_code]
            print(f"✅ Deleted session {session_code} from memory")
        
        return True
    except Exception as e:
        print(f"❌ Error deleting session {session_code}: {e}")
        return False

def cleanup_expired_sessions():
    """
    Remove expired sessions from in-memory cache
    NOTE: Only used when KV is disabled. When KV is enabled, Redis handles TTL automatically.
    """
    if KV_ENABLED:
        # KV handles TTL automatically, no cleanup needed
        return
    
    current_time = time.time()
    expired = [code for code, session in SESSIONS.items() 
               if current_time - session.get('lastActivity', session['created_at']) > SESSION_TTL]
    for code in expired:
        del SESSIONS[code]
    
    # Also cleanup expired in-memory pack codes
    expired_packs = [code for code, entry in PACK_CODES.items()
                    if current_time > entry['expires_at']]
    for code in expired_packs:
        del PACK_CODES[code]

def touch_session(session_code: str):
    """Update session's last activity timestamp"""
    session = get_session(session_code)
    if session:
        session['lastActivity'] = time.time()
        session['updated_at'] = time.time()
        update_session(session_code, session)

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
        # Cache preflight response for 24 hours to reduce OPTIONS requests
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_POST(self):
        """Handle POST requests for session operations"""
        request_start = time.time()
        request_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        cleanup_expired_sessions()
        
        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        print(f"📥 [REQ-{request_id}] POST {self.path} (body: {len(body)} bytes)")
        
        try:
            data = json.loads(body) if body else {}
            print(f"📋 [REQ-{request_id}] Parsed data keys: {list(data.keys())}")
        except json.JSONDecodeError:
            print(f"❌ [REQ-{request_id}] Invalid JSON in request body")
            self.send_error_response(400, 'Invalid JSON')
            return

        # Route based on path - handle both with and without /api/sessions prefix
        path = self.path.split('?')[0]
        
        # Strip /api/sessions prefix if present (Vercel might include it or not)
        if path.startswith('/api/sessions'):
            path = path[13:]  # Remove '/api/sessions'
        
        print(f"🛤️ [REQ-{request_id}] Routing to: {path}")
        
        if path == '/create' or path == '':
            print(f"🎮 [REQ-{request_id}] Creating new session")
            self.handle_create_session(data)
        elif path == '/join':
            session_code = data.get('sessionCode', 'UNKNOWN')
            print(f"👥 [REQ-{request_id}] Joining session: {session_code}")
            self.handle_join_session(data)
        elif path == '/update-name':
            session_code = data.get('sessionCode', 'UNKNOWN')
            print(f"✏️ [REQ-{request_id}] Updating name in session: {session_code}")
            self.handle_update_name(data)
        elif path == '/roll-perks':
            session_code = data.get('sessionCode', 'UNKNOWN')
            print(f"🎲 [REQ-{request_id}] Rolling perks for session: {session_code}")
            self.handle_roll_perks(data)
        elif path == '/lock-commander':
            session_code = data.get('sessionCode', 'UNKNOWN')
            print(f"🔒 [REQ-{request_id}] Locking commander in session: {session_code}")
            self.handle_lock_commander(data)
        elif path == '/update-commanders':
            session_code = data.get('sessionCode', 'UNKNOWN')
            print(f"⚔️ [REQ-{request_id}] Updating commanders in session: {session_code}")
            self.handle_update_commanders(data)
        elif path == '/generate-pack-codes':
            session_code = data.get('sessionCode', 'UNKNOWN')
            print(f"📦 [REQ-{request_id}] Generating pack codes for session: {session_code}")
            self.handle_generate_pack_codes(data)
        else:
            print(f"❌ [REQ-{request_id}] Invalid endpoint: {self.path}")
            self.send_error_response(404, f'Endpoint not found: {self.path}')
            return
        
        elapsed = (time.time() - request_start) * 1000
        print(f"✅ [REQ-{request_id}] Completed in {elapsed:.1f}ms")

    def do_GET(self):
        """Handle GET requests"""
        request_start = time.time()
        request_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        cleanup_expired_sessions()
        
        path = self.path.split('?')[0]
        
        print(f"📥 [REQ-{request_id}] GET {path}")
        
        # Strip /api/sessions prefix if present
        if path.startswith('/api/sessions'):
            path = path[13:]  # Remove '/api/sessions'
        
        # Get session by code: /sessions/{code} or /{code}
        if path.startswith('/pack/'):
            # Get pack by code: /pack/{code}
            pack_code = path.split('/')[-1].upper()
            print(f"📦 [REQ-{request_id}] Getting pack code: {pack_code}")
            self.handle_get_pack(pack_code)
        elif path and path != '/' and not '/' in path[1:]:
            # Single path segment = session code
            session_code = path.strip('/').upper()
            print(f"🎮 [REQ-{request_id}] Getting session: {session_code}")
            self.handle_get_session(session_code)
        else:
            print(f"❌ [REQ-{request_id}] Invalid endpoint: {self.path}")
            self.send_error_response(404, f'Endpoint not found: {self.path}')
            
        elapsed = (time.time() - request_start) * 1000
        print(f"✅ [REQ-{request_id}] Completed in {elapsed:.1f}ms")

    def handle_create_session(self, data=None):
        """Create a new game session"""
        if data is None:
            data = {}
        
        player_name = data.get('playerName', '').strip()[:20]  # Max 20 chars
        if not player_name:
            player_name = 'Player 1'
        
        # Get perks count from host settings (default 3)
        perks_count = data.get('perksCount', 3)
        perks_count = max(1, min(10, int(perks_count)))  # Clamp between 1-10
        
        # Get Avatar Mode setting (default False)
        avatar_mode = data.get('avatarMode', False)
        
        session_code = generate_session_code()
        while session_code in SESSIONS:
            session_code = generate_session_code()
        
        player_id = generate_player_id()
        
        session = {
            'sessionCode': session_code,
            'hostId': player_id,
            'state': 'waiting',  # waiting, rolling, selecting, complete
            'settings': {
                'perksCount': perks_count,
                'avatarMode': avatar_mode
            },
            'players': [
                {
                    'id': player_id,
                    'number': 1,
                    'name': player_name,
                    'perks': [],
                    'commanderUrl': None,
                    'commanderData': None,
                    'commanderLocked': False,
                    'selectedCommanderIndex': None,
                    'packCode': None,
                    'packConfig': None
                }
            ],
            'created_at': time.time(),
            'updated_at': time.time(),
            'lastActivity': time.time()
        }
        
        store_session(session_code, session)
        
        self.send_json_response(200, {
            'sessionCode': session_code,
            'playerId': player_id,
            'sessionData': session
        })

    def handle_join_session(self, data):
        """Join an existing session"""
        session_code = data.get('sessionCode', '').upper()
        player_name = data.get('playerName', '').strip()[:20]  # Max 20 chars
        
        session = get_session(session_code)
        if not session_code or not session:
            self.send_error_response(404, 'Session not found')
            return
        
        touch_session(session_code)
        
        # Check if session is full (max 4 players)
        if len(session['players']) >= 4:
            self.send_error_response(400, 'Session is full')
            return
        
        # Check if session has already progressed beyond rolling
        # Allow joining during 'waiting' and 'rolling' phases
        if session['state'] not in ['waiting', 'rolling']:
            self.send_error_response(400, 'Session has already started commander selection')
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
            'perks': [],
            'commanderUrl': None,
            'commanderData': None,
            'commanderLocked': False,
            'selectedCommanderIndex': None,
            'packCode': None,
            'packConfig': None
        })
        
        session['updated_at'] = time.time()
        update_session(session_code, session)
        
        self.send_json_response(200, {
            'playerId': player_id,
            'sessionData': session
        })

    def handle_update_name(self, data):
        """Update player name in session"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        player_name = data.get('playerName', '').strip()[:20]  # Max 20 chars
        
        session = get_session(session_code)
        if not session_code or not session:
            self.send_error_response(404, 'Session not found')
            return
        
        touch_session(session_code)
        
        # Find the player
        player = next((p for p in session['players'] if p['id'] == player_id), None)
        if not player:
            self.send_error_response(404, 'Player not found')
            return
        
        # Update player name
        if player_name:
            player['name'] = player_name
        
        session['updated_at'] = time.time()
        update_session(session_code, session)
        
        self.send_json_response(200, session)

    def handle_roll_perks(self, data):
        """Roll perks for all players (host only)"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        
        session = get_session(session_code)
        if not session_code or not session:
            self.send_error_response(404, 'Session not found')
            return
        
        touch_session(session_code)
        
        # Verify host
        if session['hostId'] != player_id:
            self.send_error_response(403, 'Only host can Roll perks')
            return
        
        # Get perks count from session settings
        perks_count = session.get('settings', {}).get('perksCount', 3)
        
        # Roll perks for each player
        # Load perks data
        import os
        import sys
        
        # Get perks.json path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        perks_path = os.path.join(current_dir, '..', 'data', 'perks.json')
        
        try:
            with open(perks_path, 'r') as f:
                perks_data = json.load(f)
        except FileNotFoundError:
            # Fallback: use hardcoded perk selection
            perks_data = {
                'rarityWeights': {'common': 55, 'uncommon': 30, 'rare': 12, 'mythic': 3},
                'perks': []  # Will be loaded from file in production
            }
        
        # Generate multiple perks for each player with type-based deduplication
        for player in session['players']:
            player_perks = []
            used_types = set()  # Track perk types to prevent duplicates
            
            attempts = 0
            max_attempts = perks_count * 10  # Prevent infinite loop
            
            while len(player_perks) < perks_count and attempts < max_attempts:
                perk = self.get_random_perk(perks_data)
                perk_type = self.get_perk_type(perk, perks_data)
                
                # Check if this type is already used
                if perk_type not in used_types:
                    player_perks.append({
                        'id': perk['id'],
                        'name': perk['name'],
                        'rarity': perk['rarity'],
                        'description': perk.get('description', ''),
                        'perkPhase': perk.get('perkPhase', 'drafting'),
                        'effects': perk.get('effects', {})
                    })
                    used_types.add(perk_type)
                
                attempts += 1
            
            player['perks'] = player_perks
        
        session['state'] = 'selecting'
        session['updated_at'] = time.time()
        update_session(session_code, session)
        
        self.send_json_response(200, session)

    def handle_lock_commander(self, data):
        """Lock in commander selection for a player"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        commander_url = data.get('commanderUrl', '')
        commander_data = data.get('commanderData', {})
        
        session = get_session(session_code)
        if not session_code or not session:
            self.send_error_response(404, 'Session not found')
            return
        
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
        update_session(session_code, session)
        
        self.send_json_response(200, session)

    def handle_update_commanders(self, data):
        """Update generated commanders for current player"""
        session_code = data.get('sessionCode', '').upper()
        player_id = data.get('playerId', '')
        commanders = data.get('commanders', [])
        
        session = get_session(session_code)
        if not session_code or not session:
            self.send_error_response(404, 'Session not found')
            return
        
        touch_session(session_code)
        
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
        update_session(session_code, session)
        
        self.send_json_response(200, session)

    def handle_generate_pack_codes(self, data):
        """Generate pack codes for all players (when all locked in)"""
        session_code = data.get('sessionCode', '').upper()
        
        session = get_session(session_code)
        if not session_code or not session:
            self.send_error_response(404, 'Session not found')
            return
        
        touch_session(session_code)
        
        # Check if all players have locked
        all_locked = all(p['commanderLocked'] for p in session['players'])
        if not all_locked:
            self.send_error_response(400, 'Not all players have locked in')
            return
        
        # Generate pack codes
        self.generate_pack_codes_internal(session)
        session['state'] = 'complete'
        session['updated_at'] = time.time()
        update_session(session_code, session)
        
        self.send_json_response(200, session)

    def handle_get_session(self, session_code):
        """Get current session data"""
        session = get_session(session_code)
        if not session:
            self.send_error_response(404, 'Session not found')
            return
        
        touch_session(session_code)
        self.send_json_response(200, session)

    def handle_get_pack(self, pack_code):
        """Get pack configuration by pack code"""
        # Try to get from Vercel KV first (persistent storage)
        pack_data = get_pack_code(pack_code)
        
        if pack_data:
            # Found in KV storage
            self.send_json_response(200, pack_data)
            return
        
        # Fallback: search in active sessions (in-memory)
        for session in SESSIONS.values():
            for player in session['players']:
                if player.get('packCode') == pack_code:
                    # Return the pack config with commander URL and perks
                    response = {
                        'commanderUrl': player.get('commanderUrl', ''),
                        'config': player.get('packConfig', {}),
                        'perks': player.get('perksList', [])
                    }
                    self.send_json_response(200, response)
                    return
        
        self.send_error_response(404, 'Pack code not found or expired')

    def generate_pack_codes_internal(self, session):
        """Internal helper to generate pack codes and configs"""
        # Load perks to get effects
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        perks_path = os.path.join(current_dir, '..', 'data', 'perks.json')
        
        try:
            with open(perks_path, 'r') as f:
                perks_data = json.load(f)
        except:
            perks_data = {'perks': []}
        
        # Get all perks - support both formats
        if 'perkTypes' in perks_data:
            # V2 format - flatten perkTypes
            all_perks = []
            for ptype in perks_data.get('perkTypes', []):
                all_perks.extend(ptype.get('perks', []))
        else:
            # V1 format - direct perks array
            all_perks = perks_data.get('perks', [])
        
        for player in session['players']:
            # Generate unique pack code
            pack_code = generate_pack_code()
            while any(p.get('packCode') == pack_code for s in SESSIONS.values() for p in s['players']):
                pack_code = generate_pack_code()
            
            # Get all perk objects with full effects
            player_perks = []
            perk_display_list = []  # For TTS chat display (drafting perks only)
            for perk_ref in player.get('perks', []):
                perk_full = next((p for p in all_perks if p['id'] == perk_ref['id']), None)
                if perk_full:
                    player_perks.append(perk_full)
                    # Only add drafting perks to TTS display list
                    if perk_full.get('perkPhase') == 'drafting':
                        perk_display_list.append({
                            'name': perk_full.get('name', 'Unknown perk'),
                            'description': perk_full.get('description', ''),
                            'rarity': perk_full.get('rarity', 'common'),
                            'perkPhase': 'drafting'
                        })
            
            # Generate pack config by combining all perk effects
            pack_config = self.apply_perks_to_config(player_perks, player['commanderUrl'])
            
            # Store pack code data in Vercel KV (with fallback to in-memory)
            pack_data = {
                'commanderUrl': player['commanderUrl'],
                'config': pack_config,
                'perks': perk_display_list
            }
            store_pack_code(pack_code, pack_data)
            
            player['packCode'] = pack_code
            player['packConfig'] = pack_config
            player['perksList'] = perk_display_list  # Store for API retrieval
    
    def apply_perks_to_config(self, perks, commander_url):
        """Generate bundle config from multiple perk effects (combines all effects)"""
        # Combine all effects from perks
        combined_effects = {
            'packQuantity': 0,  # Additive
            'budgetUpgradePacks': 0,  # Additive
            'fullExpensivePacks': 0,  # Additive
            'bracketUpgrade': None,  # Take highest
            'bracketUpgradePacks': 0,  # Additive
            'specialPacks': [],  # Concatenate - list of {type, count, moxfieldDeck}
            'commanderQuantity': 0,  # Additive (affects commander selection, not pack config)
            'distributionShift': 0,  # Additive (affects commander selection, not pack config)
            'colorFilterMode': None,  # Take first non-None
            'allowedColors': None,  # Take first non-None
            'includeColorless': None  # Take first non-None
        }
        
        for perk in perks:
            if not perk:
                continue
            effects = perk.get('effects', {})
            
            # Additive effects
            combined_effects['packQuantity'] += effects.get('packQuantity', 0)
            combined_effects['budgetUpgradePacks'] += effects.get('budgetUpgradePacks', 0)
            combined_effects['fullExpensivePacks'] += effects.get('fullExpensivePacks', 0)
            combined_effects['bracketUpgradePacks'] += effects.get('bracketUpgradePacks', 0)
            combined_effects['commanderQuantity'] += effects.get('commanderQuantity', 0)
            combined_effects['distributionShift'] += effects.get('distributionShift', 0)
            
            # Bracket upgrade (take highest)
            if effects.get('bracketUpgrade'):
                current_bracket = combined_effects['bracketUpgrade']
                new_bracket = effects['bracketUpgrade']
                if current_bracket is None or new_bracket > current_bracket:
                    combined_effects['bracketUpgrade'] = new_bracket
            
            # Special packs (concatenate with moxfieldDeck)
            if effects.get('specialPack'):
                combined_effects['specialPacks'].append({
                    'type': effects['specialPack'],
                    'count': effects.get('specialPackCount', 1),
                    'moxfieldDeck': effects.get('moxfieldDeck')
                })
            
            # Color filters (take first)
            if combined_effects['colorFilterMode'] is None and effects.get('colorFilterMode'):
                combined_effects['colorFilterMode'] = effects['colorFilterMode']
                combined_effects['allowedColors'] = effects.get('allowedColors')
                combined_effects['includeColorless'] = effects.get('includeColorless', True)
        
        # Now apply combined effects to config
        return self.apply_perk_to_config_internal(combined_effects, commander_url)
    
    def apply_perk_to_config_internal(self, effects, commander_url):
        """Generate bundle config from combined perk effects"""
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
                'source': 'moxfield',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'deckUrl': None,  # Will be filled from perk effect
                    'count': 1
                }]
            },
            'test_cards': {
                'name': 'Test Cards',
                'source': 'moxfield',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'deckUrl': None,  # Will be filled from perk effect
                    'count': 1
                }]
            },
            'silly_cards': {
                'name': 'Silly Cards',
                'source': 'moxfield',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'deckUrl': None,  # Will be filled from perk effect
                    'count': 1
                }]
            },
            'scangtech': {
                'name': 'ScangTech Cards',
                'source': 'moxfield',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'deckUrl': None,  # Will be filled from perk effect
                    'count': 1
                }]
            },
            'jptech': {
                'name': 'JpTech Cards',
                'source': 'moxfield',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'deckUrl': None,  # Will be filled from perk effect
                    'count': 1
                }]
            },
            'any_cost_lands': {
                'name': 'Any Cost Lands',
                'source': 'edhrec',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'cardType': 'lands',
                    'budget': 'any',
                    'bracket': 'any',
                    'count': 1
                }]
            },
            'expensive_lands': {
                'name': 'Expensive Lands',
                'source': 'edhrec',
                'count': 1,
                'useCommanderColorIdentity': True,
                'slots': [{
                    'cardType': 'lands',
                    'budget': 'expensive',
                    'bracket': 'any',
                    'count': 1
                }]
            }
        }
        
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
        
        # Add special packs
        for special_pack_info in effects.get('specialPacks', []):
            special_pack_type = special_pack_info['type']
            special_pack_count = special_pack_info['count']
            moxfield_deck = special_pack_info.get('moxfieldDeck')
            
            if special_pack_type in special_pack_templates:
                pack = json.loads(json.dumps(special_pack_templates[special_pack_type]))
                
                # Set the count for the slot
                pack['slots'][0]['count'] = special_pack_count
                
                # If this pack needs a Moxfield deck URL, set it
                if moxfield_deck and 'deckUrl' in pack['slots'][0]:
                    # Convert deck ID to full URL
                    pack['slots'][0]['deckUrl'] = f"https://moxfield.com/decks/{moxfield_deck}"
                
                bundle_config['packTypes'].append(pack)
        
        return bundle_config

    def get_random_perk(self, perks_data):
        """Get random perk based on rarity weights - supports both v1 and v2 format"""
        weights = perks_data.get('rarityWeights', {
            'common': 55, 'uncommon': 30, 'rare': 12, 'mythic': 3
        })
        
        # Get all perks - support both formats
        if 'perkTypes' in perks_data:
            # V2 format - flatten perkTypes
            perks = []
            for ptype in perks_data.get('perkTypes', []):
                perks.extend(ptype.get('perks', []))
        else:
            # V1 format - direct perks array
            perks = perks_data.get('perks', [])
        
        if not perks:
            # Fallback perk
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
        
        # Get perks of that rarity
        rarity_perks = [p for p in perks if p['rarity'] == selected_rarity]
        if not rarity_perks:
            rarity_perks = [p for p in perks if p['rarity'] == 'common']
        
        return random.choice(rarity_perks)

    def get_perk_type(self, perk, perks_data):
        """Get the type category for a perk (for deduplication)"""
        # V2 format - explicit types
        if 'perkTypes' in perks_data:
            for ptype in perks_data.get('perkTypes', []):
                for p in ptype.get('perks', []):
                    if p['id'] == perk['id']:
                        return ptype['type']
        
        # V1 format - infer type from ID prefix
        perk_id = perk['id']
        if perk_id.startswith('commander_options_') or perk_id.startswith('reroll_'):
            return 'commander_quantity'
        elif perk_id.startswith('color_'):
            return 'color_filter'
        elif perk_id.startswith('budget_upgrade_'):
            return 'budget_upgrade'
        elif perk_id.startswith('budget_full_expensive_'):
            return 'expensive_packs'
        elif perk_id.startswith('extra_pack'):
            return 'extra_packs'
        elif perk_id.startswith('upgrade_bracket_'):
            return 'bracket_upgrade'
        elif 'gamechanger' in perk_id:
            return 'gamechanger_cards'
        elif 'conspiracy' in perk_id:
            return 'conspiracy_cards'
        elif 'banned' in perk_id:
            return 'banned_cards'
        elif 'manabase' in perk_id:
            return 'manabase'
        
        # Default: use the perk ID itself as the type (unique)
        return perk_id

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



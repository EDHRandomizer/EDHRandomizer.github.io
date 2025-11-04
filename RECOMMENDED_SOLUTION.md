# Recommended Solution: Serve Perks via API

## Why This Is Better

1. **Single Source of Truth** - Only `data/perks.json` exists
2. **No Manual Sync** - Frontend fetches from API automatically
3. **Versioning** - Can add version headers, caching, etc.
4. **Already Have Infrastructure** - Vercel API is already deployed

## Implementation

### 1. Add API Endpoint
```python
# api/perks.py
from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # CORS headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=3600')  # Cache for 1 hour
        self.end_headers()
        
        # Load perks.json
        current_dir = os.path.dirname(os.path.abspath(__file__))
        perks_path = os.path.join(current_dir, '..', 'data', 'perks.json')
        
        with open(perks_path, 'r', encoding='utf-8') as f:
            perks_data = f.read()
        
        self.wfile.write(perks_data.encode())
        return
```

### 2. Update Frontend
```javascript
// docs/js/game-session/perkLoader.js
async loadPerks() {
    if (this.perks) {
        return this.perks;
    }

    try {
        // Fetch from API instead of static file
        const response = await fetch('https://edhrandomizer-api.vercel.app/api/perks');
        if (!response.ok) {
            throw new Error(`Failed to load perks: ${response.statusText}`);
        }

        const data = await response.json();
        // ... rest of code
    }
}
```

### 3. Delete Duplicate File
```bash
rm docs/data/perks.json
```

### 4. Update vercel.json
```json
{
  "rewrites": [
    { "source": "/api/perks", "destination": "/api/perks.py" }
  ]
}
```

## Benefits

- ✅ No build step needed
- ✅ No sync scripts
- ✅ No duplicate files
- ✅ API can cache responses
- ✅ Can add authentication later if needed
- ✅ Can track usage/analytics
- ✅ Automatic deployment via Vercel

## Drawbacks

- Frontend requires API to be up (but it already does for sessions)
- Extra HTTP request (minimal, cached)

## Migration Plan

1. Create `api/perks.py` endpoint
2. Update `perkLoader.js` to use API
3. Test locally
4. Deploy to Vercel
5. Verify frontend works
6. Delete `docs/data/perks.json`
7. Delete `sync_perks.py`
8. Update tests

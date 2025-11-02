# Quick fix script to update all SESSIONS references
import re

with open('c:/Users/scangas/Desktop/edhrecscraper/api/sessions.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the pattern
replacements = [
    # Pattern 1: Check and get session
    (
        r'if not session_code or session_code not in SESSIONS:\s+self\.send_error_response\(404, \'Session not found\'\)\s+return\s+session = SESSIONS\[session_code\]',
        'session = get_session(session_code)\n        if not session_code or not session:\n            self.send_error_response(404, \'Session not found\')\n            return'
    ),
    # Pattern 2: Just get session (after error check)
    (
        r'session = SESSIONS\[session_code\]',
        'session = get_session(session_code) or SESSIONS.get(session_code, {})'
    ),
    # Pattern 3: Update session before sending response
    (
        r"session\['updated_at'\] = time\.time\(\)\s+self\.send_json_response\(200, session\)",
        "session['updated_at'] = time.time()\n        update_session(session_code, session)\n        self.send_json_response(200, session)"
    ),
    # Pattern 4: Get session from  SESSIONS (remaining)
    (
        r'if not session_code or session_code not in SESSIONS:',
        'session = get_session(session_code)\n        if not session_code or not session:'
    ),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('c:/Users/scangas/Desktop/edhrecscraper/api/sessions.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all SESSIONS references!")

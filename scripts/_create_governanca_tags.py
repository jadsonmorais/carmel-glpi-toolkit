from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

def req(method, endpoint, body=None, st=None):
    url = f"{creds['base_url']}/{endpoint}"
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header('App-Token', creds['app_token'])
    if st:
        r.add_header('Session-Token', st)
    else:
        r.add_header('Authorization', f"user_token {creds['user_token']}")
    if body:
        r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return {'error': f"HTTP {e.code}: {e.read().decode()}"}

TAGS = [
    {"name": "Break-Fix", "color": "#e67e22"},
    {"name": "Planejado", "color": "#2980b9"},
    {"name": "Blocked", "color": "#c0392b"},
]

sess = req('GET', 'initSession')
st = sess['session_token']

existing = req('GET', 'PluginTagTag?range=0-999', st=st)
existing = existing if isinstance(existing, list) else []
existing_by_name = {t.get('name', '').lower(): t for t in existing}

ids = {}
for tag in TAGS:
    found = existing_by_name.get(tag['name'].lower())
    if found:
        print(f"JA EXISTE: {tag['name']} -> id={found['id']}")
        ids[tag['name']] = found['id']
        continue
    body = {"input": {
        "name": tag['name'],
        "color": tag['color'],
        "entities_id": 1,
        "is_recursive": 1,
        "is_active": 1,
    }}
    r = req('POST', 'PluginTagTag', body=body, st=st)
    if r and 'id' in r:
        print(f"CRIADA: {tag['name']} -> id={r['id']}")
        ids[tag['name']] = r['id']
    else:
        print(f"ERRO ao criar {tag['name']}: {r}")

print()
print("IDs:", ids)

req('GET', 'killSession', st=st)

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
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
    if st: r.add_header('Session-Token', st)
    else: r.add_header('Authorization', f"user_token {creds['user_token']}")
    if body: r.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None

sess = req('GET', 'initSession')
st = sess['session_token']

# Listar categorias ITIL
cats = req('GET', 'ITILCategory?range=0-200', st=st)
for c in cats:
    print(f"#{c['id']} - {c.get('completename', c.get('name',''))}")

# Ver campos do Problem #260
print("\n=== Problem #260 ===")
p = req('GET', 'Problem/260', st=st)
for k, v in p.items():
    if v not in (None, '', 0, '0000-00-00 00:00:00'):
        print(f"  {k}: {v}")

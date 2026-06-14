import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os, html

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
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return {'error': f"HTTP {e.code}: {e.read().decode()}", 'code': e.code}

sess = req('GET', 'initSession')
st = sess['session_token']

# Inspecionar projeto 254 cru
p = req('GET', 'Project/254', st=st)
print("=== Project/254 keys ===")
for k, v in p.items():
    print(f"  {k}: {v}")

# Buscar ProjectTask via search com filtro projects_id
print("\n=== ProjectTask?searchText[projects_id]=254 ===")
r = req('GET', 'ProjectTask?searchText[projects_id]=254', st=st)
print(r if not isinstance(r, list) else f"{len(r)} itens")

# Listar todas ProjectTask e filtrar localmente
print("\n=== ProjectTask?range=0-50 (geral) ===")
r2 = req('GET', 'ProjectTask?range=0-2000', st=st)
if isinstance(r2, list):
    print(f"Total tasks: {len(r2)}")
    for t in r2:
        if t.get('projects_id') in (243,244,249,250,251,252,253,254):
            print(f"  proj={t.get('projects_id')} id={t.get('id')} status={t.get('status')} name={html.unescape(t.get('name',''))[:50]}")
else:
    print(r2)

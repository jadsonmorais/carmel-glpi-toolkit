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
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return {'error': f"HTTP {e.code}: {e.read().decode()}"}

sess = req('GET', 'initSession')
st = sess['session_token']

r = req('PUT', 'Problem/260', body={"input": {
    "id": 260,
    "itilcategories_id": 145,   # Serviços de Sistemas > CMFlex
    "status": 2,                # Em andamento (recorrente/aberto)
    "urgency": 3,               # Média
    "impact": 3,                # Médio
    "priority": 3,              # Média
    "actiontime": 0,
}}, st=st)

if isinstance(r, list) and r[0].get('260'):
    print("OK  Problem #260 atualizado com categoria e status")
else:
    print(f"ERR: {r}")

# Vincular o técnico responsável (Jadson = users_id do token atual)
# Tipo 2 = Assigned to
tech = req('POST', 'Problem_User', body={"input": {
    "problems_id": 260,
    "users_id": 316,
    "type": 2,
}}, st=st)
if tech and 'id' in tech:
    print(f"OK  Tecnico atribuido ao Problem #260")
else:
    print(f"WARN Tecnico: {tech}")

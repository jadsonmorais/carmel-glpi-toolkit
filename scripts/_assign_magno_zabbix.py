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

# Buscar users com forcedisplay correto
users = req('GET', "search/User?criteria[0][field]=1&criteria[0][searchtype]=contains&criteria[0][value]=magno&forcedisplay[0]=2&forcedisplay[1]=34&range=0-10", st=st)
print("Magno search:", json.dumps(users, ensure_ascii=False)[:500])

users2 = req('GET', "search/User?criteria[0][field]=1&criteria[0][searchtype]=contains&criteria[0][value]=davi&forcedisplay[0]=2&forcedisplay[1]=34&range=0-10", st=st)
print("Davi search:", json.dumps(users2, ensure_ascii=False)[:500])

# IDs confirmados pelo output anterior: magno.alves = login no campo '1', ID era o campo email
# Vamos buscar pelo endpoint direto
magno_raw = req('GET', "User?searchText[name]=magno&range=0-5", st=st)
print("Magno raw:", json.dumps(magno_raw, ensure_ascii=False)[:500] if magno_raw else None)

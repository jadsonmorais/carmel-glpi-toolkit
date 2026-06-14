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

sess = req('GET', 'initSession')
st = sess['session_token']

PROJECT_ID = 246

# 1. Renomeia Problem #255
new_name = "Adequacao Fiscal de Sistemas - Reforma Tributaria (NF-e / SEFAZ / IBS-CBS)"
r = req('PUT', 'Problem/255', body={"input": {"id": 255, "name": new_name}}, st=st)
print(f"Renomear #255: {r}")

# 2. Vincula Problems ao Projeto via Item_Project
for problem_id in [255, 243]:
    body = {"input": {"itemtype": "Problem", "items_id": problem_id, "projects_id": PROJECT_ID}}
    r = req('POST', 'Item_Project', body=body, st=st)
    if r and 'id' in r:
        print(f"Vinculado Problem #{problem_id} ao Projeto #{PROJECT_ID} (link {r['id']})")
    else:
        print(f"Erro ao vincular Problem #{problem_id}: {r}")

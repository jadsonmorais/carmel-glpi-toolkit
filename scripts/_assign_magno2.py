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

MAGNO = 320
DAVI = 155

# Atribuir Magno à tarefa Zabbix #2674
r = req('POST', 'ProjectTask_User', body={"input": {
    "projecttasks_id": 2674,
    "users_id": MAGNO,
    "type": 2,
}}, st=st)
print(f"Magno atribuido tarefa #2674: {'OK' if r and 'id' in r else r}")

# Adicionar Magno e Davi como membros do Projeto #244
for uid, nome in [(MAGNO, 'Magno'), (DAVI, 'Davi')]:
    r = req('POST', 'Project_User', body={"input": {
        "projects_id": 244,
        "users_id": uid,
        "type": 2,
    }}, st=st)
    print(f"{nome} no Projeto #244: {'OK' if r and 'id' in r else r}")

print("Magno ID: 320 | Davi ID: 155")

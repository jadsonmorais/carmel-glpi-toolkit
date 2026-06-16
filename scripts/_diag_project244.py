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

p = req('GET', 'Project/244', st=st)
print("=== PROJETO 244 ===")
print(f"Nome: {p.get('name')}")
print(f"Conteudo: {p.get('content')}")
print(f"Status (projectstates_id): {p.get('projectstates_id')}")
print(f"Inicio: {p.get('plan_start_date')} | Fim: {p.get('plan_end_date')}")
print()

tasks = req('GET', 'Project/244/ProjectTask', st=st)
print(f"=== TAREFAS ({len(tasks) if isinstance(tasks, list) else 0}) ===")
if isinstance(tasks, list):
    for t in tasks:
        print(f"- [{t.get('id')}] {t.get('name')} | status={t.get('projectstates_id')} | %={t.get('percent_done')} | inicio={t.get('plan_start_date')} fim={t.get('plan_end_date')}")
else:
    print(tasks)

req('GET', 'killSession', st=st)

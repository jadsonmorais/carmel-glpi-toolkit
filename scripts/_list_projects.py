import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os, html, re

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

STATUS = {1: "Novo", 2: "Em andamento", 3: "Concluído", 4: "Cancelado", 5: "Em espera"}
PRIORITY = {1: "Muito baixa", 2: "Baixa", 3: "Média", 4: "Alta", 5: "Muito alta", 6: "Importante", 7: "Maior"}

projects = req('GET', 'Project?range=0-300', st=st)
if isinstance(projects, dict) and 'error' in projects:
    print(projects)
    exit(1)

print(f"Total de projetos: {len(projects)}\n")
for p in projects:
    pid = p.get('id')
    name = html.unescape(p.get('name',''))
    status = str(STATUS.get(p.get('status'), p.get('status')))
    prio = str(PRIORITY.get(p.get('priority'), p.get('priority')))
    plan_start = p.get('plan_start_date') or '-'
    plan_end = p.get('plan_end_date') or '-'
    print(f"#{pid} | {status:12} | prio={prio:11} | {name[:70]} | {plan_start[:10]} -> {plan_end[:10]}")

# Para cada projeto, pegar tarefas
print("\n--- Tarefas por projeto ---")
for p in projects:
    pid = p.get('id')
    name = html.unescape(p.get('name',''))
    tasks = req('GET', f'Project/{pid}/ProjectTask', st=st)
    if not isinstance(tasks, list):
        continue
    if not tasks:
        print(f"\n#{pid} {name[:60]}: SEM TAREFAS")
        continue
    print(f"\n#{pid} {name[:60]} ({len(tasks)} tarefas):")
    for t in tasks:
        tname = html.unescape(t.get('name',''))
        tstatus = str(STATUS.get(t.get('status'), t.get('status')))
        print(f"   [{tstatus:12}] {tname[:65]}")

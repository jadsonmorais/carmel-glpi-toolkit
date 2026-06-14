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
        return None

sess = req('GET', 'initSession')
st = sess['session_token']

# ProjectState map
states_raw = req('GET', 'ProjectState?range=0-50', st=st)
STATES = {s['id']: html.unescape(s['name']) for s in states_raw} if isinstance(states_raw, list) else {}
print("ProjectStates:", STATES)

PRIORITY = {1: "Muito baixa", 2: "Baixa", 3: "Média", 4: "Alta", 5: "Muito alta", 6: "Importante", 7: "Maior"}

PROJECT_IDS = list(range(242, 255))

# Fetch all projects
projects = {}
for pid in PROJECT_IDS:
    p = req('GET', f'Project/{pid}', st=st)
    if p:
        projects[pid] = p

# Fetch project tasks by ID scan (known range created in this session + check via subitem too)
tasks_by_project = {pid: [] for pid in PROJECT_IDS}

# subitem endpoint
for pid in PROJECT_IDS:
    sub = req('GET', f'Project/{pid}/ProjectTask', st=st)
    if isinstance(sub, list):
        for t in sub:
            tasks_by_project[pid].append(t)

# direct ID scan to catch ones missing from subitem
seen_ids = {t['id'] for v in tasks_by_project.values() for t in v}
for tid in range(2650, 2720):
    if tid in seen_ids:
        continue
    t = req('GET', f'ProjectTask/{tid}', st=st)
    if t and t.get('projects_id') in PROJECT_IDS:
        tasks_by_project[t['projects_id']].append(t)

print("\n" + "="*100)
for pid in PROJECT_IDS:
    p = projects.get(pid)
    if not p:
        continue
    name = html.unescape(p.get('name',''))
    state = STATES.get(p.get('projectstates_id'), f"id={p.get('projectstates_id')}")
    prio = PRIORITY.get(p.get('priority'), p.get('priority'))
    pstart = (p.get('plan_start_date') or '-')[:10]
    pend = (p.get('plan_end_date') or '-')[:10]
    content = re.sub(r'<[^>]+>',' ', html.unescape(p.get('content','') or ''))[:200]
    print(f"\n#{pid} | {name}")
    print(f"   estado={state} | prioridade={prio} | periodo={pstart} -> {pend}")
    print(f"   resumo: {content.strip()[:180]}")
    tasks = tasks_by_project[pid]
    if tasks:
        for t in sorted(tasks, key=lambda x: x['id']):
            tname = html.unescape(t.get('name',''))
            tstate = STATES.get(t.get('projectstates_id'), f"id={t.get('projectstates_id')}")
            pdone = t.get('percent_done')
            print(f"     - [{tstate:15}] {pdone:>3}% {tname[:60]}")
    else:
        print("     (sem tarefas)")

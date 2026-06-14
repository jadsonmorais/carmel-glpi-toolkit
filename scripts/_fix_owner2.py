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

JADSON = 157   # correto
OLD    = 316   # token antigo — deve ser substituído
MAGNO  = 320

# TicketTasks criadas com users_id_tech=316
TICKETS_COM_TASK = [27956, 27814, 27832, 27866, 27936, 27812, 27899,
                    27898, 27910, 27948, 27953, 27848, 27896, 27897,
                    27839, 27886, 27895, 27919, 27892, 27903]

print("=== Corrigindo TicketTasks (316 -> 157) ===")
for tid in TICKETS_COM_TASK:
    tasks = req('GET', f"Ticket/{tid}/TicketTask?range=0-10", st=st)
    if not isinstance(tasks, list) or not tasks:
        continue
    for task in tasks:
        task_id = task['id']
        tech = task.get('users_id_tech', 0)
        creator = task.get('users_id', 0)
        patch = {}
        if tech == OLD: patch['users_id_tech'] = JADSON
        if creator == OLD: patch['users_id'] = JADSON
        if patch:
            patch['id'] = task_id
            r = req('PUT', f'TicketTask/{task_id}', body={"input": patch}, st=st)
            ok = isinstance(r, list) and r[0].get(str(task_id))
            print(f"  {'OK' if ok else 'ERR'}  Ticket #{tid} Task #{task_id} -> 157")
        else:
            print(f"  skip  Ticket #{tid} Task #{task_id} (tech={tech})")

print("\n=== Corrigindo ProjectTasks (316 -> 157) ===")
for pt_id in [2672, 2673]:
    task = req('GET', f'ProjectTask/{pt_id}', st=st)
    uid = task.get('users_id', 0) if task else 0
    if uid == OLD:
        r = req('PUT', f'ProjectTask/{pt_id}', body={"input": {"id": pt_id, "users_id": JADSON}}, st=st)
        ok = isinstance(r, list) and r[0].get(str(pt_id))
        print(f"  {'OK' if ok else 'ERR'}  ProjectTask #{pt_id} -> 157")
    else:
        print(f"  skip  ProjectTask #{pt_id} uid={uid}")

print("\n=== Corrigindo Problem_User (316 -> 157, revertendo fix anterior) ===")
PROBLEMS = [260, 261, 262, 263, 264, 265, 267]
for pid in PROBLEMS:
    pu = req('GET', f'Problem/{pid}/Problem_User?range=0-10', st=st)
    if not isinstance(pu, list): continue
    for entry in pu:
        uid = entry.get('users_id')
        ptype = entry.get('type')
        pu_id = entry.get('id')
        if ptype == 2 and uid == OLD:
            r = req('PUT', f'Problem_User/{pu_id}', body={"input": {"id": pu_id, "users_id": JADSON}}, st=st)
            print(f"  Problem #{pid} PU #{pu_id}: 316 -> 157")
        elif ptype == 2 and uid == JADSON:
            print(f"  OK  Problem #{pid} já está em 157")

print("\n=== CONCLUIDO ===")

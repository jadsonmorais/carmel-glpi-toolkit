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

JADSON = 316
MAGNO = 320

# Tickets que receberam tarefas nessa sessão
TICKETS_COM_TASK = [27956, 27814, 27832, 27866, 27936, 27812, 27899,
                    27898, 27910, 27948, 27953, 27848, 27896, 27897,
                    27839, 27886, 27895, 27919, 27892, 27903]

# ProjectTasks criadas nessa sessão (exceto #2674 que é do Magno)
PROJECT_TASKS = [2672, 2673]

print("=== Verificando e corrigindo TicketTasks ===")
for tid in TICKETS_COM_TASK:
    tasks = req('GET', f"Ticket/{tid}/TicketTask?range=0-10", st=st)
    if not isinstance(tasks, list) or not tasks:
        continue
    for task in tasks:
        task_id = task['id']
        tech = task.get('users_id_tech', 0)
        creator = task.get('users_id', 0)
        needs_fix = (tech != JADSON and tech != MAGNO) or (creator != JADSON and creator != MAGNO)
        status = f"tech={tech} creator={creator}"
        if needs_fix:
            body = {"input": {"id": task_id}}
            if tech != JADSON and tech != MAGNO:
                body["input"]["users_id_tech"] = JADSON
            if creator != JADSON and creator != MAGNO:
                body["input"]["users_id"] = JADSON
            r = req('PUT', f'TicketTask/{task_id}', body=body, st=st)
            ok = isinstance(r, list) and r[0].get(str(task_id))
            print(f"  {'OK' if ok else 'ERR'}  Ticket #{tid} Task #{task_id} ({status}) -> Jadson")
        else:
            print(f"  OK (já correto)  Ticket #{tid} Task #{task_id} ({status})")

print("\n=== Corrigindo ProjectTasks ===")
for pt_id in PROJECT_TASKS:
    task = req('GET', f'ProjectTask/{pt_id}', st=st)
    if not task or 'id' not in task:
        print(f"  ERR  ProjectTask #{pt_id} não encontrada: {task}")
        continue
    uid = task.get('users_id', 0)
    print(f"  ProjectTask #{pt_id} users_id atual: {uid}")
    if uid != JADSON:
        r = req('PUT', f'ProjectTask/{pt_id}', body={"input": {"id": pt_id, "users_id": JADSON}}, st=st)
        ok = isinstance(r, list) and r[0].get(str(pt_id))
        print(f"  {'OK' if ok else 'ERR'}  ProjectTask #{pt_id} -> Jadson (316)")
    else:
        print(f"  OK (já correto)")

print("\n=== Verificando Problems (atribuídos) ===")
# Problems criados nessa sessão
PROBLEMS = [260, 261, 262, 263, 264, 265, 266, 267]
for pid in PROBLEMS:
    pu = req('GET', f'Problem/{pid}/Problem_User?range=0-10', st=st)
    if isinstance(pu, list):
        for entry in pu:
            uid = entry.get('users_id')
            ptype = entry.get('type')
            pu_id = entry.get('id')
            if ptype == 2 and uid != JADSON:  # type 2 = atribuído
                r = req('PUT', f'Problem_User/{pu_id}', body={"input": {"id": pu_id, "users_id": JADSON}}, st=st)
                print(f"  Problem #{pid} Problem_User #{pu_id}: {uid} -> 316")
            elif ptype == 2:
                print(f"  OK  Problem #{pid} atribuído corretamente a {uid}")

print("\n=== CONCLUIDO ===")

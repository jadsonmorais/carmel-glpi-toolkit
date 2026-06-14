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

NOVO = 1
EM_ANDAMENTO = 2
CONCLUIDO = 4

# Projetos 249-254 -> estado "Novo" (251 e 252 ja tem trabalho iniciado/concluido -> Em Andamento)
project_states = {
    249: NOVO,
    250: NOVO,
    251: NOVO,
    252: EM_ANDAMENTO,  # FNRH ja tem a implantacao concluida
    253: NOVO,
    254: NOVO,
}

for pid, state in project_states.items():
    r = req('PUT', f'Project/{pid}', body={"input": {"id": pid, "projectstates_id": state}}, st=st)
    print(f"Project #{pid} -> projectstates_id={state}: {r}")

# Tarefas 2674-2693+ (criadas hoje) -> estado "Novo", exceto a 1a tarefa do FNRH (concluida)
task_ids_range = list(range(2675, 2710))  # vamos buscar quais existem e pertencem a 249-254

def get_task(tid):
    return req('GET', f'ProjectTask/{tid}', st=st)

PROJECT_IDS = {249,250,251,252,253,254}
fixed = 0
for tid in range(2670, 2710):
    t = get_task(tid)
    if not t or t.get('projects_id') not in PROJECT_IDS:
        continue
    if t.get('projectstates_id') != 0:
        continue
    name = t.get('name','')
    # Tarefa de implantacao FNRH ja feita -> Concluido
    state = CONCLUIDO if 'Implantação da integração OPERA Cloud' in name else NOVO
    pdone = 100 if state == CONCLUIDO else 0
    r = req('PUT', f'ProjectTask/{tid}', body={"input": {"id": tid, "projectstates_id": state, "percent_done": pdone}}, st=st)
    print(f"ProjectTask #{tid} (proj {t.get('projects_id')}) -> projectstates_id={state}: {'OK' if r else 'ERR'}")
    fixed += 1

print(f"\nTotal tarefas corrigidas: {fixed}")

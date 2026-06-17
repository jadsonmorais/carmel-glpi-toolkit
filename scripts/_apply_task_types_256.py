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

# 1. Criar os tipos
type_names = ["Marco", "Levantamento", "Alinhamento", "Execucao", "Documentacao", "Treinamento"]
types = {}
print("=== Criando ProjectTaskType ===")
for name in type_names:
    r = req('POST', 'ProjectTaskType', body={"input": {"name": name}}, st=st)
    if r and 'id' in r:
        types[name] = r['id']
        print(f"  [{r['id']}] {name}")
    else:
        print(f"  ERRO em '{name}': {r}")

# 2. Atribuir tipos a cada tarefa
assignments = {
    types['Marco']:        [2740, 2743, 2747, 2751, 2752],
    types['Levantamento']: [2744, 2745, 2746, 2766, 2768],
    types['Alinhamento']:  [2748, 2749, 2750, 2758, 2767, 2771, 2762, 2763],
    types['Execucao']:     [2741, 2742, 2759, 2760, 2761, 2764, 2765, 2769, 2770],
    types['Documentacao']: [2753, 2754, 2756, 2757],
    types['Treinamento']:  [2772, 2773, 2774, 2775, 2776],
}

print("\n=== Atribuindo tipos as tarefas ===")
for type_id, task_ids in assignments.items():
    type_name = [k for k, v in types.items() if v == type_id][0]
    print(f"\n{type_name} (type_id={type_id})")
    for tid in task_ids:
        r = req('PUT', f'ProjectTask/{tid}', body={"input": {"id": tid, "projecttasktypes_id": type_id}}, st=st)
        ok = r and str(tid) in str(r) and True in [v for v in (r[0] if isinstance(r, list) else r).values() if isinstance(v, bool)]
        print(f"  [{tid}] {'OK' if ok else r}")

# 3. Verificacao
print("\n=== Verificacao (1 tarefa por tipo) ===")
samples = {
    'Marco':        2740,
    'Levantamento': 2744,
    'Alinhamento':  2748,
    'Execucao':     2741,
    'Documentacao': 2753,
    'Treinamento':  2772,
}
for tipo, tid in samples.items():
    t = req('GET', f'ProjectTask/{tid}', st=st)
    print(f"  {tipo}: [{tid}] type={t.get('projecttasktypes_id')} ({t.get('name')})")

req('GET', 'killSession', st=st)

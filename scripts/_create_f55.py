from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}
BACKLOG = 11
F5 = 2752

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

def create_task(name, content, parent, st):
    body = {
        "input": {
            "projects_id": 256,
            "projecttasks_id": parent,
            "name": name,
            "content": content,
            "projectstates_id": BACKLOG,
            "is_milestone": 0,
            "percent_done": 0,
        }
    }
    r = req('POST', 'ProjectTask', body=body, st=st)
    if r and 'id' in r:
        print(f"  [{r['id']}] {name}")
    else:
        print(f"  ERRO em '{name}': {r}")

sess = req('GET', 'initSession')
st = sess['session_token']

f55 = None
body = {
    "input": {
        "projects_id": 256,
        "projecttasks_id": F5,
        "name": "F5.5 - Treinamentos",
        "content": "Trilhas de treinamento sobre o Simphony PDV direcionadas a diferentes "
                    "publicos, a serem aplicadas ao final do projeto.",
        "projectstates_id": BACKLOG,
        "is_milestone": 0,
        "percent_done": 0,
    }
}
r = req('POST', 'ProjectTask', body=body, st=st)
print(f"[{r['id']}] F5.5 - Treinamentos")
f55 = r['id']

create_task(
    "F5.5.1 - Trilha: Simphony para Suporte",
    "Trilha focada em EMC para suporte.",
    f55, st)

create_task(
    "F5.5.2 - Trilha: Simphony para Fiscal",
    "Trilha focada em cadastros fiscais no EMC.",
    f55, st)

create_task(
    "F5.5.3 - Trilha: Simphony para Controladoria",
    "Trilha com foco em cadastro de itens, print class, etc.",
    f55, st)

create_task(
    "F5.5.4 - Trilha: Simphony Avancado",
    "Conteudo mais completo sobre as configuracoes do Simphony.",
    f55, st)

req('GET', 'killSession', st=st)

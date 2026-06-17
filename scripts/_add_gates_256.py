from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

BACKLOG = 11
F4 = 2751
F5 = 2752

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

def create_milestone(name, content, parent, st):
    body = {
        "input": {
            "projects_id": 256,
            "projecttasks_id": parent,
            "name": name,
            "content": content,
            "projectstates_id": BACKLOG,
            "is_milestone": 1,
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

create_milestone(
    "[POS/Simphony] F4.G1 - Marco: Homologacao Concluida",
    "Portao de aprovacao: teste funcional do piloto (F4.3) validado e aprovado por TI e pela "
    "area de negocio do hotel piloto, com resultado registrado em F4.5, antes de liberar o rollout geral.",
    F4, st)

create_milestone(
    "[POS/Simphony] F4.G2 - Marco: Rollout Realizado",
    "Portao de aprovacao: GPO, rede/VLAN e Kaspersky aplicados e validados em todas as unidades "
    "(F4.6 concluida em 100% dos hoteis), com teste funcional confirmado por unidade.",
    F4, st)

create_milestone(
    "[POS/Simphony] F5.G1 - Marco: Operacao Assistida",
    "Portao de aprovacao: periodo de acompanhamento pos-rollout sem incidentes recorrentes "
    "de PDV/Simphony antes de encerrar o projeto e seguir para a documentacao final (KB) e treinamentos.",
    F5, st)

req('GET', 'killSession', st=st)

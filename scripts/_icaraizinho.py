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

# 1. Criar o Projeto
project = req('POST', 'Project', body={"input": {
    "name": "Icaraizinho - Abertura do Novo Hotel",
    "content": (
        "Projeto de acompanhamento de todas as demandas de TI relacionadas "
        "a abertura do Carmel Icaraizinho. Inclui implantacao de sistemas, "
        "infraestrutura de rede, inventario de ativos, configuracao de acessos "
        "e integracao com os demais sistemas da rede Carmel."
    ),
    "entities_id": 1,
    "is_recursive": 1,
    "projectstates_id": 1,   # Novo
    "projecttypes_id": 1,    # Estrategico
    "priority": 5,
    "plan_start_date": "2026-05-28",
    "plan_end_date": "2026-12-31",
    "percent_done": 0,
    "show_on_global_gantt": 1,
}}, st=st)

if not project or 'id' not in project:
    print(f"ERR Projeto: {project}")
    exit(1)

pid = project['id']
print(f"OK  Projeto #{pid} criado: Icaraizinho - Abertura do Novo Hotel")

# 2. Criar primeira tarefa ICZ-01
task = req('POST', 'ProjectTask', body={"input": {
    "projects_id": pid,
    "name": "ICZ-01 - Implantacao e Configuracao do CMFlex no Icaraizinho",
    "content": (
        "Configurar e implantar os modulos necessarios do CMFlex para o Carmel Icaraizinho. "
        "Inclui modulo de Ativo Fixo (CAF), parametrizacao de almoxarifado, integracao contabil "
        "e criacao de usuarios. Acompanhar chamados abertos junto ao suporte CMFlex/Sankhya."
    ),
    "plan_start_date": "2026-05-28",
    "plan_end_date": "2026-08-31",
    "projectstates_id": 1,
    "percent_done": 0,
}}, st=st)

if not task or 'id' not in task:
    print(f"ERR Tarefa: {task}")
    exit(1)

tid = task['id']
print(f"OK  Tarefa #{tid} criada: ICZ-01")

# 3. Associar chamado #27812 à tarefa
link = req('POST', 'ProjectTask_Ticket', body={"input": {
    "projecttasks_id": tid,
    "tickets_id": 27812,
}}, st=st)

if link and 'id' in link:
    print(f"OK  Chamado #27812 vinculado a tarefa #{tid} (link {link['id']})")
else:
    print(f"ERR Vinculo chamado: {link}")

print(f"\nProjeto disponivel em: {GLPI_BASE_URL}/front/project.form.php?id={pid}")

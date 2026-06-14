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

JADSON = 157

proj = req('POST', 'Project', body={"input": {
    "name": "Implantação PMWeb — Gestão de Projetos e Obras",
    "content": (
        "<p>Projeto de implantação do <strong>PMWeb</strong>, plataforma de gestão de "
        "projetos, contratos e obras (PMIS — Project Management Information System), "
        "voltada ao controle de empreendimentos, capex e construções da Carmel Hotéis.</p>"
        "<p>O PMWeb centraliza cronogramas, orçamentos, contratos com fornecedores, "
        "registros de campo e relatórios de progresso, substituindo controles "
        "fragmentados em planilhas e e-mails.</p>"
    ),
    "entities_id": 1,
    "status": 1,       # Novo
    "plan_start_date": "2026-06-09 00:00:00",
    "is_recursive": 0,
    "users_id": JADSON,
}}, st=st)

if not proj or 'id' not in proj:
    print(f"ERR ao criar projeto: {proj}")
    exit(1)

pid = proj['id']
print(f"OK  Project #{pid} criado: Implantação PMWeb")

tasks = [
    ("Kickoff e definição de escopo com o fornecedor PMWeb",            1, "2026-06-20 00:00:00"),
    ("Levantamento de processos: obras, contratos e capex Carmel",      1, "2026-06-30 00:00:00"),
    ("Configuração do ambiente e parametrização inicial",               1, "2026-07-15 00:00:00"),
    ("Migração / importação de projetos e contratos existentes",        1, "2026-07-31 00:00:00"),
    ("Treinamento dos usuários-chave (obras, financeiro, diretoria)",   1, "2026-08-15 00:00:00"),
    ("Piloto supervisionado com projeto real",                          1, "2026-08-31 00:00:00"),
    ("Go-live e suporte pós-implantação",                               1, "2026-09-15 00:00:00"),
]

for name, status, plan_end in tasks:
    t = req('POST', 'ProjectTask', body={"input": {
        "projects_id": pid,
        "name": name,
        "status": status,
        "plan_end_date": plan_end,
        "users_id": JADSON,
        "entities_id": 1,
    }}, st=st)
    print(f"  {'OK' if t and 'id' in t else 'ERR'}  {name[:65]}")

print(f"\nProjeto #{pid} pronto. Acesse: https://carmelhoteis.verdanadesk.com/front/project.form.php?id={pid}")

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
    "name": "Implantação Nonius — Taíba",
    "content": (
        "<p>Projeto de implantação da plataforma <strong>Nonius</strong> no hotel "
        "<strong>Carmel Taíba</strong>. A Nonius é uma solução de tecnologia para "
        "hospitalidade que engloba Wi-Fi gerenciado, IPTV/Chromecast, portal do hóspede "
        "e analytics de conectividade.</p>"
        "<p>Escopo inicial a ser definido junto ao fornecedor Nonius e à equipe de "
        "infraestrutura do hotel.</p>"
    ),
    "entities_id": 1,
    "status": 1,
    "plan_start_date": "2026-06-09 00:00:00",
    "is_recursive": 0,
    "users_id": JADSON,
}}, st=st)

if not proj or 'id' not in proj:
    print(f"ERR ao criar projeto: {proj}")
    exit(1)

pid = proj['id']
print(f"OK  Project #{pid} criado: Implantação Nonius — Taíba")

req('POST', 'Project_User', body={"input": {"projects_id": pid, "users_id": JADSON, "type": 2}}, st=st)
print(f"OK  Jadson vinculado como gestor")

tasks = [
    ("Levantamento de requisitos e escopo com a Nonius",   1, "2026-06-16 00:00:00"),
    ("Mapeamento de infraestrutura de rede — Taíba",       1, "2026-06-20 00:00:00"),
    ("Definição de cronograma e fases de implantação",     1, "2026-06-23 00:00:00"),
    ("Configuração e testes do ambiente Nonius",           1, "2026-07-07 00:00:00"),
    ("Treinamento da equipe do hotel",                     1, "2026-07-14 00:00:00"),
    ("Go-live e monitoramento pós-implantação",            1, "2026-07-21 00:00:00"),
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
    print(f"  {'OK' if t and 'id' in t else 'ERR'}  Tarefa: {name}")

print(f"\nProjeto #{pid} pronto. Acesse: https://carmelhoteis.verdanadesk.com/front/project.form.php?id={pid}")

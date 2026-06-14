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
    "name": "Compliance e Licenciamento de Software — Carmel Hotéis",
    "content": (
        "<p>Projeto de levantamento, regularização e renovação de licenças de software "
        "em todos os hotéis Carmel. Cobre sistemas operacionais Windows em versões "
        "desatualizadas (fora de suporte), pacote Office e licenças de Windows Server.</p>"
        "<p>Objetivo: eliminar riscos jurídicos e de segurança decorrentes do uso de "
        "software sem licença válida ou fora do ciclo de suporte do fabricante.</p>"
    ),
    "entities_id": 1,
    "status": 1,
    "plan_start_date": "2026-06-09 00:00:00",
    "is_recursive": 0,
    "users_id": JADSON,
}}, st=st)

if not proj or 'id' not in proj:
    print(f"ERR: {proj}")
    exit(1)

pid = proj['id']
print(f"OK  Project #{pid} criado: Compliance e Licenciamento")

tasks = [
    (
        "Windows — Inventário e atualização de versões fora de suporte",
        (
            "<p>Levantar todos os equipamentos com Windows 7, Windows 8.1 e Windows 10 "
            "(EOL em out/2025) em uso nos hotéis. Avaliar elegibilidade para upgrade "
            "para Windows 11, necessidade de substituição de hardware e aquisição de "
            "novas licenças. Regularizar máquinas sem licença válida.</p>"
        ),
    ),
    (
        "Microsoft Office — Levantamento e regularização de licenças",
        (
            "<p>Inventariar instalações do Office (2010, 2013, 2016, 2019 e Microsoft 365) "
            "em todos os hotéis. Identificar cópias não licenciadas ou ativações inválidas. "
            "Avaliar migração para Microsoft 365 Business (licença por usuário/mês) como "
            "modelo unificado para toda a rede Carmel.</p>"
        ),
    ),
    (
        "Windows Server — Auditoria de licenças e versões de servidor",
        (
            "<p>Auditar as licenças de Windows Server em uso (versões, edições e CALs de "
            "acesso). Verificar servidores com versões fora de suporte (2008, 2012). "
            "Planejar atualização ou migração para versões suportadas e regularizar "
            "licenciamento de CAL por usuário/dispositivo.</p>"
        ),
    ),
]

for name, content in tasks:
    t = req('POST', 'ProjectTask', body={"input": {
        "projects_id": pid,
        "name": name,
        "content": content,
        "status": 1,
        "users_id": JADSON,
        "entities_id": 1,
    }}, st=st)
    print(f"  {'OK' if t and 'id' in t else 'ERR'}  {name[:65]}")

print(f"\nProjeto #{pid} pronto. Acesse: https://carmelhoteis.verdanadesk.com/front/project.form.php?id={pid}")

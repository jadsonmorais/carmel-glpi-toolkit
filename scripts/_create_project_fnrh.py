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
    "name": "FNRH — Ficha Nacional de Registro de Hóspedes (Ministério do Turismo)",
    "content": (
        "<p>Projeto de implantação e melhoria contínua da integração OPERA Cloud com a "
        "<strong>FNRH</strong> (Ficha Nacional de Registro de Hóspedes), obrigação legal "
        "junto ao Ministério do Turismo para todos os meios de hospedagem.</p>"
        "<p>Escopo: envio automático dos dados cadastrais dos hóspedes no check-in, "
        "validação de campos obrigatórios e bloqueios operacionais para garantir "
        "conformidade com a legislação.</p>"
    ),
    "entities_id": 1,
    "status": 2,       # Em andamento
    "plan_start_date": "2026-06-09 00:00:00",
    "is_recursive": 0,
    "users_id": JADSON,
}}, st=st)

if not proj or 'id' not in proj:
    print(f"ERR ao criar projeto: {proj}")
    exit(1)

pid = proj['id']
print(f"OK  Project #{pid} criado: FNRH")

tasks = [
    {
        "name": "Implantação da integração OPERA Cloud → FNRH (Ministério do Turismo)",
        "content": (
            "<p>Configuração e ativação da integração OPERA Cloud com a FNRH para envio "
            "automático dos dados de hóspedes no check-in aos hotéis Carmel. "
            "Inclui mapeamento de campos obrigatórios, testes de envio e validação "
            "junto ao portal do Ministério do Turismo.</p>"
            "<p><strong>Status:</strong> Concluída.</p>"
        ),
        "status": 3,                        # Concluído
        "plan_end_date": "2026-06-09 00:00:00",
    },
    {
        "name": "Melhoria: bloquear check-in com campos obrigatórios da FNRH ausentes",
        "content": (
            "<p>Implementar bloqueio operacional no OPERA Cloud para impedir a efetivação "
            "do check-in quando campos obrigatórios da FNRH (como CPF, documento, "
            "nacionalidade, endereço) não estiverem preenchidos no perfil do hóspede.</p>"
            "<p>Objetivo: garantir conformidade legal e eliminar falhas de envio por "
            "dados incompletos, reduzindo retrabalho da recepção e da TI.</p>"
        ),
        "status": 1,                        # Em planejamento
        "plan_end_date": "2026-07-31 00:00:00",
    },
]

for task in tasks:
    t = req('POST', 'ProjectTask', body={"input": {
        "projects_id": pid,
        "name": task["name"],
        "content": task["content"],
        "status": task["status"],
        "plan_end_date": task["plan_end_date"],
        "users_id": JADSON,
        "entities_id": 1,
    }}, st=st)
    status_label = "Concluída" if task["status"] == 3 else "Planejada"
    print(f"  {'OK' if t and 'id' in t else 'ERR'}  [{status_label}] {task['name'][:60]}")

print(f"\nProjeto #{pid} pronto. Acesse: https://carmelhoteis.verdanadesk.com/front/project.form.php?id={pid}")

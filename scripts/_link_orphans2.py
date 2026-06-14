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

# 1. Vincular chamados a Problems
links = [
    (27232, 93,  "Movimentacao de produto -> Almoxarifado CMFlex"),
    (27809, 87,  "Erro baixa de cartao -> CAR Contas a Receber CMFlex"),
    (27814, 58,  "BI Almoxarifado -> BI do PDV desatualizado"),
]

print("=== Vinculos Problem_Ticket ===")
for ticket_id, problem_id, desc in links:
    r = req('POST', 'Problem_Ticket', body={"input": {
        "problems_id": problem_id,
        "tickets_id": ticket_id,
    }}, st=st)
    if r and 'id' in r:
        print(f"OK  #{ticket_id} -> Problem #{problem_id} ({desc})")
    else:
        print(f"ERR #{ticket_id} -> Problem #{problem_id}: {r}")

# 2. Atribuir etiqueta "Acessos" (ID 235) aos chamados de acesso
TAG_ID = 235
acessos = [
    (27572, "Criar Acesso EMC - Charme"),
    (27811, "Sem login Infraspeak - Taiba"),
    (27813, "Ajuste no acesso CMFlex Almoxarifado - Charme"),
]

print("\n=== Etiqueta Acessos ===")
for ticket_id, desc in acessos:
    r = req('POST', 'PluginTagTagItem', body={"input": {
        "plugin_tag_tags_id": TAG_ID,
        "itemtype": "Ticket",
        "items_id": ticket_id,
    }}, st=st)
    if r and 'id' in r:
        print(f"OK  #{ticket_id} -> tag Acessos ({desc})")
    else:
        print(f"ERR #{ticket_id} -> tag Acessos: {r}")

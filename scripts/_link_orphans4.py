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

def link_problem(tickets, problem_id, label):
    print(f"\n=== {label} -> Problem #{problem_id} ===")
    for tid in tickets:
        r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": problem_id, "tickets_id": tid}}, st=st)
        print(f"  {'OK' if r and 'id' in r else 'ERR'}  #{tid}")

def tag(tickets, tag_id, label):
    print(f"\n=== Etiqueta '{label}' (#{tag_id}) ===")
    for tid in tickets:
        r = req('POST', 'PluginTagTagItem', body={"input": {
            "plugin_tag_tags_id": tag_id,
            "itemtype": "Ticket",
            "items_id": tid,
        }}, st=st)
        ok = r and 'id' in r
        print(f"  {'OK' if ok else 'JA TEM/ERR'}  #{tid}")

# Problem #262 — Integração Simphony → CMFlex Fiscal
link_problem([27895, 27886], 262, "Integracao Simphony->Fiscal")

# Problem #261 — BPM múltiplas instâncias
link_problem([27919, 27892, 27903], 261, "BPM multiplas instancias")

# Problem #236 — Simphony instabilidade PDV
link_problem([27853], 236, "Simphony instabilidade PDV")

# Etiqueta Acessos (235)
tag([27909, 27863], 235, "Acessos")

from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}
BACKLOG = 11
F23 = 2746

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

body = {
    "input": {
        "projects_id": 256,
        "projecttasks_id": F23,
        "name": "F2.3.0 - Definir estrategia de protecao para tablets PDV (hardware restrito)",
        "content": "Os tablets do PDV tem hardware mais restrito que as workstations. Validar com "
                    "a gestao de TI se essas maquinas terao o Kaspersky instalado normalmente ou "
                    "se a estrategia sera apenas GPO especifica e restrita + firewall basico do "
                    "sistema operacional (sem antivirus completo). Decisao impacta o escopo de "
                    "F2.3 (parametrizacao Kaspersky) e F3.1 (GPO do PDV).",
        "projectstates_id": BACKLOG,
        "is_milestone": 0,
        "percent_done": 0,
    }
}
r = req('POST', 'ProjectTask', body=body, st=st)
print(r)
req('GET', 'killSession', st=st)

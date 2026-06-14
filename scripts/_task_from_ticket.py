import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os, html, re

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
PROJECT_ID = 243
TICKET_ID = 26582

# Buscar ticket
t = req('GET', f'Ticket/{TICKET_ID}', st=st)
raw_name = html.unescape(t.get('name', ''))
content_raw = html.unescape(t.get('content', ''))
no_tags = re.sub(r'<[^>]+>', ' ', content_raw)

# Tentar extrair título real do formulário
m = re.search(r'[Tt][íi]tulo\s+do\s+Chamado\s*:\s*(.+?)(?:\n|$|Descri)', no_tags)
real_title = re.sub(r'\s*\d+\)\s*$', '', m.group(1).strip().strip(':').strip())[:100] if m else raw_name[:100]

print(f"Ticket #{TICKET_ID}: {real_title}")
print(f"Nome GLPI: {raw_name[:80]}")

# Criar tarefa no projeto como concluída (status 3)
task = req('POST', 'ProjectTask', body={"input": {
    "projects_id": PROJECT_ID,
    "name": real_title,
    "content": (
        f"<p>Tarefa registrada com base no chamado fechado <strong>#{TICKET_ID}</strong>.</p>"
        f"<p>{no_tags[:500].strip()}</p>"
    ),
    "status": 3,  # 3 = Fechado / Concluído
    "users_id": JADSON,
    "entities_id": 1,
}}, st=st)

if task and 'id' in task:
    print(f"OK  ProjectTask #{task['id']} criada como concluída no Project #{PROJECT_ID}")
    print(f"    https://carmelhoteis.verdanadesk.com/front/project.form.php?id={PROJECT_ID}")
else:
    print(f"ERR: {task}")

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

print("=== ProjectTaskType existentes ===")
r = req('GET', 'ProjectTaskType?range=0-50', st=st)
print(json.dumps(r, indent=2, ensure_ascii=False))

print("\n=== Tarefas do projeto 256 com projecttasktypes_id ===")
tasks = req('GET', 'Project/256/ProjectTask', st=st)
if isinstance(tasks, list):
    for t in tasks:
        print(f"[{t['id']}] {t['name']} | type={t.get('projecttasktypes_id')} | milestone={t.get('is_milestone')}")

req('GET', 'killSession', st=st)

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os, html

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
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read().decode()
        print("Content-Range:", resp.headers.get('Content-Range'))
        return json.loads(raw) if raw else None

sess = req('GET', 'initSession')
st = sess['session_token']

r2 = req('GET', 'ProjectTask?range=0-2000', st=st)
print(f"len={len(r2)}")
for t in r2:
    print(f"  id={t.get('id')} proj={t.get('projects_id')} name={html.unescape(t.get('name',''))[:50]}")

# tentar Project/254/ProjectTask direto
print("\n--- Project/254/ProjectTask ---")
r3 = req('GET', 'Project/254/ProjectTask', st=st)
print(r3)

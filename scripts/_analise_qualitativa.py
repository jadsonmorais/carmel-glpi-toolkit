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

# Problems
print("=== PROBLEMS ===")
problems = req('GET', 'Problem?range=0-200&forcedisplay[0]=2&forcedisplay[1]=12&forcedisplay[2]=15', st=st)
for p in problems:
    print(f"#{p['id']}|{p.get('status')}|{p.get('name','')[:80]}")

# Changes
print("\n=== CHANGES ===")
changes = req('GET', 'Change?range=0-100&forcedisplay[0]=2&forcedisplay[1]=12', st=st)
if isinstance(changes, list):
    for c in changes:
        print(f"#{c['id']}|{c.get('status')}|{c.get('name','')[:80]}")
else:
    print(changes)

# Projects
print("\n=== PROJECTS ===")
projects = req('GET', 'Project?range=0-50', st=st)
if isinstance(projects, list):
    for p in projects:
        print(f"#{p['id']}|{p.get('projectstates_id')}|{p.get('percent_done')}%|{p.get('name','')[:70]}")
else:
    print(projects)

# Project Tasks
print("\n=== PROJECT TASKS ===")
tasks = req('GET', 'ProjectTask?range=0-100&forcedisplay[0]=2&forcedisplay[1]=3', st=st)
if isinstance(tasks, list):
    for t in tasks:
        print(f"#{t['id']}|proj:{t.get('projects_id')}|{t.get('projectstates_id')}|{t.get('percent_done')}%|{t.get('name','')[:60]}")
else:
    print(tasks)

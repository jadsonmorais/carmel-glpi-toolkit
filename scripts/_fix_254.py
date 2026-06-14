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
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return None

sess = req('GET', 'initSession')
st = sess['session_token']

for tid in range(2710, 2725):
    t = req('GET', f'ProjectTask/{tid}', st=st)
    if t and t.get('projects_id') == 254:
        name = html.unescape(t.get('name',''))
        if t.get('projectstates_id') == 0:
            r = req('PUT', f'ProjectTask/{tid}', body={"input": {"id": tid, "projectstates_id": 1}}, st=st)
            print(f"#{tid} -> projectstates_id=1: {'OK' if r else 'ERR'}  {name[:50]}")
        else:
            print(f"#{tid} ja ok: {name[:50]}")

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
        return {'error': f"HTTP {e.code}: {e.read().decode()}", 'code': e.code}

sess = req('GET', 'initSession')
st = sess['session_token']

for tid in [2693, 2674, 2672, 2673]:
    t = req('GET', f'ProjectTask/{tid}', st=st)
    if isinstance(t, dict) and 'id' in t:
        print(f"#{tid}: proj={t.get('projects_id')} status={t.get('status')} is_deleted={t.get('is_deleted')} entities_id={t.get('entities_id')} name={html.unescape(t.get('name',''))[:50]}")
    else:
        print(f"#{tid}: {t}")

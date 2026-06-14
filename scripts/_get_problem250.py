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
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode())

sess = req('GET', 'initSession')
st = sess['session_token']
p = req('GET', 'Problem/250', st=st)
content = re.sub(r'<[^>]+>', ' ', html.unescape(p.get('content', '')))
print('name   :', p.get('name'))
print('status :', p.get('status'))
print('content:', content[:400])

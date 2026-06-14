import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}
print("user_token:", creds['user_token'][:10] if creds['user_token'] else 'VAZIO')
print("app_token:", creds['app_token'][:10] if creds['app_token'] else 'VAZIO')

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
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {'error': f"HTTP {e.code}: {e.read().decode()}"}

sess = req('GET', 'initSession')
print("initSession:", sess)

if 'session_token' in sess:
    st = sess['session_token']
    r = req('GET', 'Ticket/27960', st=st)
    print("Ticket teste:", r)
    r2 = req('GET', 'search/Ticket?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]=2&range=0-3&forcedisplay[0]=1&forcedisplay[1]=2', st=st)
    print("Search teste:", json.dumps(r2, ensure_ascii=False)[:300] if r2 else None)

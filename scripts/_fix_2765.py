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
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None
sess = req('GET', 'initSession')
st = sess['session_token']
r = req('PUT', 'ProjectTask/2765', body={"input":{"id":2765,"name":"Reativar antivirus com excecoes e portas corretas"}}, st=st)
print(r)
r = req('GET', 'ProjectTask/2765', st=st)
print(repr(r['name']))
req('GET', 'killSession', st=st)

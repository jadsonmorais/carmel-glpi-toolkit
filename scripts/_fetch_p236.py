from _env import *
import json, urllib.request, os, sys

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
    if st:
        r.add_header('Session-Token', st)
    else:
        r.add_header('Authorization', f"user_token {creds['user_token']}")
    if body:
        r.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return {'error': e.read().decode()}

sess = req('GET', 'initSession')
st = sess['session_token']

p = req('GET', 'Problem/236', st=st)
print('TITULO:', p.get('name'))
print('STATUS:', p.get('status'))
print('CONTEUDO:', (p.get('content') or '')[:800])

# Busca sem forcedisplay para ver quais campos chegam
tickets = req('GET', 'search/Ticket?criteria[0][field]=201&criteria[0][searchtype]=equals&criteria[0][value]=236&range=0-200', st=st)
print('TOTAL CHAMADOS:', tickets.get('totalcount', 0))
# Mostra estrutura do primeiro item
data = tickets.get('data') or []
if data:
    print('CAMPOS DISPONIVEIS:', list(data[0].keys()))
    for t in data:
        fields = list(t.values())
        print(f"  {fields}")

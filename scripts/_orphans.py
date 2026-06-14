from _env import *
import json, urllib.request, os, sys, html

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
        return {'error': f"HTTP {e.code}: {e.read().decode()}"}

sess = req('GET', 'initSession')
st = sess['session_token']

STATUS = {1:'Novo', 2:'Atribuido', 3:'Planejado', 4:'Pendente'}

all_tickets = []
for s, label in STATUS.items():
    r = req('GET', (
        f"search/Ticket"
        f"?criteria[0][field]=200&criteria[0][searchtype]=equals&criteria[0][value]=0"
        f"&criteria[1][link]=AND&criteria[1][field]=12&criteria[1][searchtype]=equals&criteria[1][value]={s}"
        f"&forcedisplay[0]=2&forcedisplay[1]=1&forcedisplay[2]=12&forcedisplay[3]=15"
        f"&range=0-200"
    ), st=st)
    data = r.get('data') or []
    for t in data:
        all_tickets.append((t.get('2'), label, t.get('15',''), html.unescape(str(t.get('1','')))))

print(f"Total orfaos (Novo+Atribuido+Planejado+Pendente): {len(all_tickets)}\n")
print(f"{'#ID':<8} {'Status':<12} {'Local':<25} Titulo")
print("-" * 100)
for tid, status, entity, titulo in sorted(all_tickets, key=lambda x: x[0] or 0):
    print(f"#{tid:<7} {status:<12} {str(entity)[:25]:<25} {titulo[:65]}")

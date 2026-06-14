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

# Buscar órfãos: tickets sem Problem vinculado (problems_id=0), status 1,2,3,4
orphans = {}
for s in [1, 2, 3, 4]:
    r = req('GET',
        f"search/Ticket"
        f"?criteria[0][field]=200&criteria[0][searchtype]=equals&criteria[0][value]=0"
        f"&criteria[1][field]=12&criteria[1][searchtype]=equals&criteria[1][value]={s}"
        f"&forcedisplay[0]=1&forcedisplay[1]=2&forcedisplay[2]=12&forcedisplay[3]=80"
        f"&forcedisplay[4]=83&forcedisplay[5]=15"
        f"&range=0-200", st=st)
    if r and 'data' in r:
        for t in r['data']:
            tid = t.get('1')
            if not tid: continue
            try:
                tid = int(tid)
            except:
                continue
            orphans[tid] = {
                'id': tid,
                'name': t.get('2', ''),
                'status': s,
                'location': t.get('80', '') or t.get('83', ''),
                'category': t.get('15', ''),
            }

print(f"Total orfaos: {len(orphans)}")

# Mapear hotel pela localização/título
def hotel(t):
    loc = str(t.get('location', '')).lower()
    name = str(t.get('name', '')).lower()
    combined = loc + ' ' + name
    if 'cumbuco' in combined: return 'Cumbuco'
    if 'taib' in combined or 'taíba' in combined: return 'Taíba'
    if 'magna' in combined: return 'Magna Praia'
    if 'icaraiz' in combined: return 'Icaraizinho'
    if 'charme' in combined or 'beach' in combined: return 'Charme/Beach'
    if 'fortaleza' in combined: return 'Fortaleza'
    return 'Geral / Não identificado'

STATUS = {1: 'Novo', 2: 'Atribuído', 3: 'Planejado', 4: 'Pendente'}

by_hotel = {}
for tid, t in sorted(orphans.items()):
    h = hotel(t)
    by_hotel.setdefault(h, []).append(t)

for h in sorted(by_hotel.keys()):
    print(f"\n--- {h} ({len(by_hotel[h])}) ---")
    for t in sorted(by_hotel[h], key=lambda x: x['id']):
        print(f"  #{t['id']} [{STATUS.get(t['status'], t['status'])}] {t['name'][:80]}")

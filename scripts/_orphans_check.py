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

STATUS = {1: 'Novo', 2: 'Atribuído', 3: 'Planejado', 4: 'Pendente'}

# Buscar todos os tickets ativos e checar Problem_Ticket individualmente
# Estratégia: pegar todos status 1,2,3,4 e verificar quais não têm Problem
all_tickets = {}
for s in [1, 2, 3, 4]:
    r = req('GET',
        f"search/Ticket"
        f"?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]={s}"
        f"&forcedisplay[0]=1&forcedisplay[1]=2&forcedisplay[2]=80&forcedisplay[3]=15"
        f"&range=0-300", st=st)
    if r and 'data' in r:
        for t in r['data']:
            tid = t.get('1')
            try: tid = int(tid)
            except: continue
            all_tickets[tid] = {'id': tid, 'name': t.get('2',''), 'status': s,
                                'location': t.get('80',''), 'category': t.get('15','')}

print(f"Total tickets ativos: {len(all_tickets)}")

# Verificar quais têm Problem vinculado
orphans = {}
linked = 0
for i, (tid, t) in enumerate(sorted(all_tickets.items())):
    r = req('GET', f"Ticket/{tid}/Problem?range=0-5", st=st)
    has_problem = isinstance(r, list) and len(r) > 0
    if has_problem:
        linked += 1
    else:
        orphans[tid] = t
    if (i+1) % 20 == 0:
        print(f"  Verificados {i+1}/{len(all_tickets)}... ({len(orphans)} orfaos ate agora)")

print(f"\nOrfaos: {len(orphans)} | Com Problem: {linked}")

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

by_hotel = {}
for tid, t in orphans.items():
    h = hotel(t)
    by_hotel.setdefault(h, []).append(t)

for h in sorted(by_hotel.keys()):
    print(f"\n=== {h} ({len(by_hotel[h])}) ===")
    for t in sorted(by_hotel[h], key=lambda x: x['id']):
        print(f"  #{t['id']} [{STATUS.get(t['status'], t['status'])}] {t['name'][:80]}")

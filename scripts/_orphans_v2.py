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

# Campo 1 = nome, campo 2 = ID, campo 12 = status, campo 80 = localização, campo 15 = categoria
STATUS = {1: 'Novo', 2: 'Atribuído', 3: 'Planejado', 4: 'Pendente'}

all_tickets = {}
for s in [1, 2, 3, 4]:
    page = 0
    while True:
        start = page * 100
        r = req('GET',
            f"search/Ticket"
            f"?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]={s}"
            f"&forcedisplay[0]=1&forcedisplay[1]=2&forcedisplay[2]=80&forcedisplay[3]=15"
            f"&range={start}-{start+99}", st=st)
        if not r or 'data' not in r or not r['data']:
            break
        for t in r['data']:
            tid = t.get('2')   # campo 2 = ID numérico
            name = t.get('1', '')  # campo 1 = nome
            try: tid = int(tid)
            except: continue
            all_tickets[tid] = {
                'id': tid,
                'name': str(name),
                'status': s,
                'location': str(t.get('80', '')),
                'category': str(t.get('15', '')),
            }
        if len(r['data']) < 100:
            break
        page += 1

print(f"Total tickets ativos: {len(all_tickets)}")

# Verificar Problem_Ticket individualmente
orphans = {}
linked = 0
ids_sorted = sorted(all_tickets.keys())
for i, tid in enumerate(ids_sorted):
    r = req('GET', f"Ticket/{tid}/Problem_Ticket?range=0-5", st=st)
    has_problem = isinstance(r, list) and len(r) > 0
    if has_problem:
        linked += 1
    else:
        orphans[tid] = all_tickets[tid]
    if (i+1) % 30 == 0:
        print(f"  [{i+1}/{len(ids_sorted)}] orfaos={len(orphans)} vinculados={linked}")

print(f"\nTotal orfaos: {len(orphans)} | Com Problem: {linked}")

def hotel(t):
    loc = str(t.get('location', '')).lower()
    name = str(t.get('name', '')).lower()
    combined = loc + ' ' + name
    if 'cumbuco' in combined: return 'Cumbuco'
    if 'taib' in combined or 'taíba' in combined: return 'Taíba'
    if 'magna' in combined: return 'Magna Praia'
    if 'icaraiz' in combined: return 'Icaraizinho'
    if 'charme' in combined or 'beach' in combined: return 'Charme'
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

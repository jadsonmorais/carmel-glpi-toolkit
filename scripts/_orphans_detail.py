import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os, re

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

# Location IDs resolvidos do GLPI
locs = req('GET', 'Location?range=0-300', st=st)
loc_map = {}
if isinstance(locs, list):
    for l in locs:
        loc_map[l['id']] = l.get('completename', l.get('name', ''))

ORPHAN_IDS = [27832,27863,27866,27880,27884,27894,27898,27902,27910,27922,
              27931,27932,27936,27937,27938,27940,27941,27943,27945,27947,
              27949,27951,27956,27962,27965,27966,27969,27970,27971,27977,27979]

STATUS = {1:'Novo', 2:'Atribuído', 3:'Planejado', 4:'Pendente'}

def strip_html(s):
    return re.sub(r'<[^>]+>', '', s).replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&').replace('&#62;', '>').replace('&#38;', '&').strip()

def hotel_from_loc(loc_name):
    l = loc_name.lower()
    if 'cumbuco' in l: return 'Cumbuco'
    if 'taíba' in l or 'taiba' in l: return 'Taíba'
    if 'magna' in l: return 'Magna Praia'
    if 'icaraiz' in l: return 'Icaraizinho'
    if 'charme' in l or 'beach' in l: return 'Charme'
    if 'fortaleza' in l: return 'Fortaleza'
    return 'Geral'

def extract_title(content_html, fallback=''):
    # Tenta extrair "Título do Chamado" do formulário
    m = re.search(r'[Tt]ítulo[^:]*:\s*</b>\s*(.*?)(?:</div>|<br)', content_html)
    if m:
        t = strip_html(m.group(1)).strip()
        if t and len(t) > 3: return t
    return fallback

tickets = []
for tid in ORPHAN_IDS:
    t = req('GET', f'Ticket/{tid}', st=st)
    if not t or 'id' not in t: continue
    loc_id = t.get('locations_id', 0)
    loc_name = loc_map.get(loc_id, '')
    content = t.get('content', '')
    raw_name = strip_html(t.get('name', ''))
    title = extract_title(content, raw_name)
    hotel = hotel_from_loc(loc_name)
    status = STATUS.get(t.get('status', 0), str(t.get('status')))
    tickets.append({'id': tid, 'title': title[:80], 'hotel': hotel, 'loc': loc_name, 'status': status, 'category': strip_html(t.get('name',''))[:60]})
    print(f"#{tid} [{status}] hotel={hotel} | loc={loc_name[:40]} | {title[:60]}")

# Agrupado por hotel
by_hotel = {}
for t in tickets:
    by_hotel.setdefault(t['hotel'], []).append(t)

print("\n\n========== RESUMO POR HOTEL ==========")
for h in ['Charme','Cumbuco','Taíba','Magna Praia','Icaraizinho','Fortaleza','Geral']:
    if h not in by_hotel: continue
    print(f"\n### {h} ({len(by_hotel[h])})")
    for t in sorted(by_hotel[h], key=lambda x: x['id']):
        print(f"  #{t['id']} [{t['status']}] {t['title']}")

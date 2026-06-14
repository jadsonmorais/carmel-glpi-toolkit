import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os, re, html

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

ORPHAN_IDS = [27832,27863,27866,27880,27884,27894,27898,27902,27910,27922,
              27931,27932,27936,27937,27938,27940,27941,27943,27945,27947,
              27949,27951,27956,27962,27965,27966,27969,27970,27971,27977,27979]

def extract_title(content_raw):
    # Decodificar entidades HTML primeiro
    decoded = html.unescape(content_raw)
    # Remover tags HTML
    no_tags = re.sub(r'<[^>]+>', ' ', decoded)
    # Buscar "Título do Chamado"
    m = re.search(r'[Tt][íi]tulo\s+do\s+Chamado\s*:\s*(.+?)(?:\n|$|Descri)', no_tags)
    if m:
        t = m.group(1).strip().strip(':').strip()
        if t and len(t) > 2:
            return t[:80]
    return None

for tid in ORPHAN_IDS:
    t = req('GET', f'Ticket/{tid}', st=st)
    if not t: continue
    content = t.get('content', '')
    title = extract_title(content)
    raw_name = html.unescape(t.get('name', ''))
    print(f"#{tid}|{title or '---'}|{raw_name[:60]}")

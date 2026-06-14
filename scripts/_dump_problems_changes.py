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

STATUS_P = {1:'Novo', 2:'Em andamento', 3:'Aceito', 4:'Pendente', 5:'Planejado', 6:'Fechado', 7:'Cancelado', 8:'Em andamento (repetição)'}
STATUS_C = {1:'Novo', 2:'Aceito', 3:'Planejado', 4:'Em andamento', 5:'Aprovado', 6:'Fechado', 7:'Cancelado', 9:'Avaliação', 10:'Congelado', 11:'Em teste'}

# === PROBLEMS ativos (status != 6 e != 7) ===
print("=== PROBLEMS ATIVOS ===")
for s in [1,2,3,4,5,8]:
    r = req('GET',
        f"search/Problem"
        f"?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]={s}"
        f"&forcedisplay[0]=1&forcedisplay[1]=2&forcedisplay[2]=12&forcedisplay[3]=21&forcedisplay[4]=15"
        f"&range=0-200", st=st)
    if r and 'data' in r:
        for p in r['data']:
            pid = p.get('1') or p.get('id','?')
            nome = p.get('2') or p.get('name','')
            status = p.get('12') or s
            cat = p.get('21','')
            print(f"  #{pid}|S{s}:{STATUS_P.get(s,s)}|{cat}|{str(nome)[:90]}")

# === CHANGES ativas ===
print("\n=== CHANGES ATIVAS ===")
for s in [1,2,3,4,5,9,10,11]:
    r = req('GET',
        f"search/Change"
        f"?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]={s}"
        f"&forcedisplay[0]=1&forcedisplay[1]=2&forcedisplay[2]=12&forcedisplay[3]=21"
        f"&range=0-100", st=st)
    if r and 'data' in r:
        for c in r['data']:
            cid = c.get('1') or c.get('id','?')
            nome = c.get('2') or c.get('name','')
            cat = c.get('21','')
            print(f"  #{cid}|S{s}:{STATUS_C.get(s,s)}|{cat}|{str(nome)[:90]}")

# Detalhar cada Problem ativo para ver tickets vinculados
print("\n=== DETALHES PROBLEMS (tickets vinculados) ===")
# Buscar problem_tickets
for s in [1,2,3,4,5,8]:
    r = req('GET',
        f"search/Problem"
        f"?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]={s}"
        f"&forcedisplay[0]=1&range=0-200", st=st)
    if r and 'data' in r:
        for p in r['data']:
            pid = p.get('1')
            if not pid: continue
            # tickets vinculados
            linked = req('GET', f"Problem/{pid}/Ticket?range=0-20", st=st)
            count = len(linked) if isinstance(linked, list) else 0
            print(f"  Problem #{pid} -> {count} ticket(s) vinculado(s)")

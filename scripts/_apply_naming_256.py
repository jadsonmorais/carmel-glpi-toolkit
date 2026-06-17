from _env import *
import json, re, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

PREFIX = "[POS/Simphony]"
PATTERN = re.compile(r'^F\d+(\.\d+)*\s*-\s*.+')

# Lista obtida varrendo IDs e filtrando projects_id == 256 (endpoint
# Project/256/ProjectTask retorna apenas um subconjunto incompleto neste ambiente).
PROJECT_256_TASK_IDS = [
    2740, 2741, 2742, 2743, 2744, 2745, 2746, 2747, 2748, 2749, 2750,
    2751, 2752, 2753, 2754, 2756, 2757, 2759, 2760, 2761, 2762, 2763,
    2764, 2765, 2766, 2767, 2768, 2769, 2770, 2771, 2772, 2773, 2774,
    2775, 2776, 2777, 2778,
]

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

for tid in PROJECT_256_TASK_IDS:
    t = req('GET', f'ProjectTask/{tid}', st=st)
    if not isinstance(t, dict) or 'name' not in t:
        print(f"[{tid}] ERRO ao ler: {t}")
        continue
    name = t.get('name') or ''
    if name.startswith(PREFIX):
        print(f"[{tid}] ja com prefixo, pulando: {name}")
        continue
    if not PATTERN.match(name):
        print(f"[{tid}] nao segue padrao F{{n}}... - ..., pulando: {name}")
        continue
    new_name = f"{PREFIX} {name}"
    r = req('PUT', f'ProjectTask/{tid}', body={"input": {"id": tid, "name": new_name}}, st=st)
    print(f"[{tid}] -> {new_name}: {r}")

req('GET', 'killSession', st=st)

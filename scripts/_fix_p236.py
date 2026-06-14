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
        body_text = e.read().decode()
        return {'error': f"HTTP {e.code}: {body_text}"}

sess = req('GET', 'initSession')
st = sess['session_token']

# Tickets a desvincular do #236
tickets_desvincular = [22632, 26794, 27575, 27572, 27765]
# Tickets a vincular ao #252 (R&A Simphony)
tickets_p252 = [22632, 26794, 27575]

# 1. Busca todos os Problem_Ticket links do Problem #236
links = req('GET', 'Problem_Ticket?problems_id=236&range=0-999', st=st)
if isinstance(links, dict) and 'error' in links:
    print('ERRO ao buscar links:', links['error'])
    sys.exit(1)

print(f"Links encontrados no Problem #236: {len(links)}")
link_map = {item['tickets_id']: item['id'] for item in links}

# 2. Desvincula tickets do #236
for tid in tickets_desvincular:
    if tid in link_map:
        r = req('DELETE', f"Problem_Ticket/{link_map[tid]}", st=st)
        print(f"  Desvinculado #{tid} do #236 (link {link_map[tid]}): {r}")
    else:
        print(f"  #{tid} nao encontrado nos links do #236 (ja desvinculado?)")

# 3. Vincula tickets ao Problem #252
print("\nVinculando ao Problem #252...")
for tid in tickets_p252:
    body = {"input": {"problems_id": 252, "tickets_id": tid}}
    r = req('POST', 'Problem_Ticket', body=body, st=st)
    if r and 'id' in r:
        print(f"  Vinculado #{tid} ao #252 (link ID: {r['id']})")
    else:
        print(f"  ERRO ao vincular #{tid}: {r}")

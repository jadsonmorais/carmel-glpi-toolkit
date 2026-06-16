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

codes = {
    248: "PROJ-2026-OPERACIONAL-GERAL",
    249: "PROJ-2026-NONIUS-MAGNA",
    250: "PROJ-2026-NONIUS-TAIBA",
    251: "PROJ-2026-GOVERNANCA-SHADOWIT",
    252: "PROJ-2026-FISCAL-FNRH",
    253: "PROJ-2026-PMWEB-OBRAS",
    254: "PROJ-2026-COMPLIANCE-LICENCAS",
    256: "PROJ-2026-PDV-SIMPHONY",
}

sess = req('GET', 'initSession')
st = sess['session_token']

for pid, code in codes.items():
    r = req('PUT', f'Project/{pid}', body={"input": {"id": pid, "code": code}}, st=st)
    print(f"[{pid}] -> {code}: {r}")

req('GET', 'killSession', st=st)

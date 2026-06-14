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

tasks = [
    (2665, "RT-01 Adaptacao de Sistemas para Emissao de Documentos Fiscais 2026"),
    (2666, "RT-02 Mapeamento de Creditos na Cadeia Produtiva"),
    (2667, "RT-03 Preparacao Operacional e Estrategica"),
    (2668, "RT-04 Engajamento Multidisciplinar das Areas"),
    (2669, "RT-05 Acompanhamento da Regulamentacao e Novas Normas"),
]

for task_id, new_name in tasks:
    r = req('PUT', f'ProjectTask/{task_id}', body={"input": {"id": task_id, "name": new_name}}, st=st)
    ok = isinstance(r, list) and r[0].get(str(task_id))
    print(f"{'OK' if ok else 'ERR'} {task_id} -> {new_name}")

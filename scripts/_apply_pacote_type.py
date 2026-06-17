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

# Criar tipo Pacote
r = req('POST', 'ProjectTaskType', body={"input": {"name": "Pacote"}}, st=st)
pacote_id = r['id']
print(f"Tipo 'Pacote' criado: ID {pacote_id}")

# Fases F1-F5 + agrupadores intermediarios
pacotes = {
    2740: "F1 - Mitigacao",
    2743: "F2 - Preparo",
    2747: "F3 - Definicoes",
    2751: "F4 - Execucao",
    2752: "F5 - Conclusao",
    2745: "F2.2 - Requisitos Oracle",
    2746: "F2.3 - Configuracao Kaspersky",
    2772: "F5.5 - Treinamentos",
}

print("\nAplicando tipo Pacote:")
for tid, name in pacotes.items():
    r = req('PUT', f'ProjectTask/{tid}', body={"input": {"id": tid, "projecttasktypes_id": pacote_id}}, st=st)
    ok = isinstance(r, list) and r[0].get(str(tid)) is True
    print(f"  [{tid}] {name}: {'OK' if ok else r}")

req('GET', 'killSession', st=st)

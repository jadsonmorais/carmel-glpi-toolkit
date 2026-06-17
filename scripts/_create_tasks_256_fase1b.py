from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

BACKLOG = 11
FASE1   = 2740

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

def create_task(name, content, parent, st):
    body = {
        "input": {
            "projects_id": 256,
            "projecttasks_id": parent,
            "name": name,
            "content": content,
            "projectstates_id": BACKLOG,
            "is_milestone": 0,
            "percent_done": 0,
        }
    }
    r = req('POST', 'ProjectTask', body=body, st=st)
    if r and 'id' in r:
        print(f"  [{r['id']}] {name}")
    else:
        print(f"  ERRO em '{name}': {r}")

sess = req('GET', 'initSession')
st = sess['session_token']

print("Fase 1 - Mitigacao (novos itens DHCP)")

create_task(
    "Verificar se todas as maquinas PDV estao com DHCP ativo",
    "Checar em cada workstation do PDV se a interface de rede esta configurada para DHCP "
    "(e nao IP fixo). Registrar as que estiverem com IP estatico para correcao antes de "
    "enviar a lista para a 3WSI.",
    FASE1, st)

create_task(
    "Passar lista de IPs + MACs para a 3WSI fazer amarracao no DHCP Server",
    "Exportar do GLPI a lista de workstations PDV com IP atual e MAC address e enviar "
    "para a 3WSI realizar a amarracao (reserva DHCP) no servidor, garantindo IPs fixos "
    "por MAC sem necessidade de configuracao estatica nas maquinas.",
    FASE1, st)

req('GET', 'killSession', st=st)

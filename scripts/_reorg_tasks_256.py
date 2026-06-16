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

renames = {
    2741: ("Verificar TAG PDV nas Workstations no GLPI", None),
    2742: ("Mitigacao imediata: desativar antivirus nas workstations PDV", None),
    2744: ("Inventario GLPI (impressoras EMC + workstations PDV)",
        "[ ] a - Validar se as impressoras do EMC estao no GLPI com MAC informado.\n"
        "[ ] b - Validar se todas as workstations do PDV estao atualizadas no GLPI."),
    2745: ("Requisitos Oracle (hardware, portas de firewall, recomendacao de servidor CAPS)",
        "[ ] a - Qual o hardware necessario?\n"
        "[ ] b - Quais portas cada workstation precisa ter liberadas na regra de firewall do sistema operacional?\n"
        "[ ] c - Qual a recomendacao de servidor para a CAPS (Windows 10 ou Server)?"),
    2746: ("Configuracao Kaspersky (liberar portas necessarias)",
        "[ ] Configurar o Kaspersky para liberar as portas necessarias do Simphony PDV."),
    2748: ("Definir GPO do PDV (escopo + validacao com gestao de TI)", None),
    2749: ("Definir rede padrao do PDV (VLAN, rede por hotel)", None),
    2750: ("Validacao com 3WSI (MACs, DHCP, GPO, impressoras)", None),
    2753: ("KB MAN = Simphony BASE (manual pratico)", None),
    2754: ("Repassar regras de GPO do PDV (documentar resultado da Fase 3)", None),
    2756: ("Levantar erros conhecidos e criar SDV/SDT", None),
    2757: ("KB BEC = Erros Comuns Simphony (associando os SDV/SDT)", None),
}

for tid, (name, content) in renames.items():
    body = {"input": {"id": tid, "name": name}}
    if content is not None:
        body["input"]["content"] = content
    r = req('PUT', f'ProjectTask/{tid}', body=body, st=st)
    print(f"[{tid}] -> {name}: {r}")

# Remove item duplicado (93 - Kaspersky, agora absorvido em 2746)
r = req('DELETE', 'ProjectTask/2755', st=st)
print(f"DELETE 2755: {r}")

req('GET', 'killSession', st=st)

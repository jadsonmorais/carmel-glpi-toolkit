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

renames = {
    2740: "F1 - Mitigacao",
    2741: "F1.1 - Verificar TAG PDV nas Workstations no GLPI",
    2742: "F1.2 - Mitigacao imediata: desativar antivirus nas workstations PDV",
    2758: "F1.3 - Definir prazo limite e compensacao para antivirus desativado",

    2743: "F2 - Preparo",
    2744: "F2.1 - Inventario GLPI (impressoras EMC + workstations PDV)",
    2745: "F2.2 - Requisitos Oracle (hardware, portas de firewall, recomendacao de servidor CAPS)",
    2746: "F2.3 - Configuracao Kaspersky (liberar portas necessarias)",

    2747: "F3 - Definicoes",
    2748: "F3.1 - Definir GPO do PDV (escopo + validacao com gestao de TI)",
    2749: "F3.2 - Definir rede padrao do PDV (VLAN, rede por hotel)",
    2750: "F3.3 - Validacao com 3WSI (MACs, DHCP, GPO, impressoras)",

    2751: "F4 - Execucao",
    2759: "F4.1 - Selecionar hotel piloto e agendar janela de manutencao",
    2760: "F4.2 - Aplicar GPO, rede/VLAN e Kaspersky no hotel piloto",
    2761: "F4.3 - Teste funcional pos-mudanca no piloto",
    2762: "F4.4 - Plano de rollback (piloto)",
    2763: "F4.5 - Validar resultado do piloto e ajustar antes do rollout",
    2764: "F4.6 - Rollout para demais hoteis",
    2765: "F4.7 - Reativar antivirus com excecoes e portas corretas",

    2752: "F5 - Conclusao",
    2753: "F5.1 - KB MAN = Simphony BASE (manual pratico)",
    2754: "F5.2 - Repassar regras de GPO do PDV (documentar resultado da Fase 3)",
    2756: "F5.3 - Levantar erros conhecidos e criar SDV/SDT",
    2757: "F5.4 - KB BEC = Erros Comuns Simphony (associando os SDV/SDT)",
}

sess = req('GET', 'initSession')
st = sess['session_token']

for tid, name in renames.items():
    r = req('PUT', f'ProjectTask/{tid}', body={"input": {"id": tid, "name": name}}, st=st)
    print(f"[{tid}] -> {name}: {r}")

req('GET', 'killSession', st=st)

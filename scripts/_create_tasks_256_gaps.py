from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

BACKLOG = 11
FASE1 = 2740
FASE4 = 2751

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

print("Fase 1 - Mitigacao (novo item)")
create_task(
    "Definir prazo limite e compensacao para antivirus desativado",
    "Definir ate quando o antivirus pode ficar desativado nas workstations PDV e qual a "
    "compensacao temporaria nesse periodo (isolamento de VLAN, bloqueio de trafego externo "
    "nessas maquinas). Este prazo e a referencia para a tarefa 'Reativar antivirus' na Fase 4.",
    FASE1, st)

print("Fase 4 - Execucao (novos itens)")
create_task(
    "Selecionar hotel piloto e agendar janela de manutencao",
    "Escolher 1 hotel como piloto para aplicar GPO, rede/VLAN e Kaspersky antes do rollout "
    "geral. Agendar janela de manutencao com a unidade.",
    FASE4, st)

create_task(
    "Aplicar GPO, rede/VLAN e Kaspersky no hotel piloto",
    "Executar, no hotel piloto, as configuracoes definidas na Fase 3: GPO do PDV, rede/VLAN "
    "padrao e regras do Kaspersky (portas liberadas).",
    FASE4, st)

create_task(
    "Teste funcional pos-mudanca no piloto",
    "Validar no hotel piloto, apos a aplicacao das mudancas: transacao de teste no PDV, "
    "impressao em cupom/EMC, conectividade das workstations e do CAPS.",
    FASE4, st)

create_task(
    "Plano de rollback (piloto)",
    "Definir como revertar GPO, rede/VLAN e Kaspersky no hotel piloto caso o teste funcional "
    "falhe, antes de prosseguir para o rollout geral.",
    FASE4, st)

create_task(
    "Validar resultado do piloto e ajustar antes do rollout",
    "Revisar os resultados do teste funcional do piloto, ajustar GPO/rede/Kaspersky se "
    "necessario e so entao liberar o rollout para as demais unidades.",
    FASE4, st)

create_task(
    "Rollout para demais hoteis",
    "Aplicar GPO, rede/VLAN e Kaspersky nas demais unidades, com janela de manutencao e "
    "teste funcional por hotel (mesmo checklist do piloto).",
    FASE4, st)

create_task(
    "Reativar antivirus com exceções e portas corretas",
    "Reativar o antivirus (Kaspersky) nas workstations PDV de cada hotel, ja com as "
    "exceções/portas definidas na Fase 2/3, encerrando a mitigacao da Fase 1.",
    FASE4, st)

req('GET', 'killSession', st=st)

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

NOVO       = 1
EM_AND     = 2
CONCLUIDO  = 4
BACKLOG    = 11
PROJECT_ID = 247

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

def create_task(name, content, parent, state, percent, st):
    body = {
        "input": {
            "projects_id": PROJECT_ID,
            "projecttasks_id": parent,
            "name": name,
            "content": content,
            "projectstates_id": state,
            "is_milestone": 0,
            "percent_done": percent,
        }
    }
    r = req('POST', 'ProjectTask', body=body, st=st)
    if r and 'id' in r:
        print(f"  [{r['id']}] {name}")
        return r['id']
    print(f"  ERRO em '{name}': {r}")
    return None

sess = req('GET', 'initSession')
st = sess['session_token']

# ── CONCLUIDAS ───────────────────────────────────────────────────────────────
print("\n=== Concluidas ===")

create_task(
    "Levantamento de dados (historico de reservas + UHs por hotel)",
    "Coleta e envio para a Oracle do historico de reservas e numero de UHs dos hoteis "
    "Taiba, Charme e Cumbuco, necessarios para a contratacao da licenca OCD.",
    0, CONCLUIDO, 100, st)

create_task(
    "Negociacao comercial com a Oracle",
    "Alinhamento de valores e propostas com a Oracle para a licenca Opera Cloud Distribution (OCD).",
    0, CONCLUIDO, 100, st)

create_task(
    "Assinatura dos contratos (todas as unidades)",
    "Formalizacao: assinatura dos contratos OCD de todas as unidades. Concluida em 12/06/2026.",
    0, CONCLUIDO, 100, st)

create_task(
    "Ativacao da Cloud Account - Icaraizinho (Carmel Wind Esporte Ceara)",
    "Criacao da Cloud Account no portal Oracle para a unidade Icaraizinho, seguindo o fluxo "
    "'Create New Cloud Account'. Concluida com sucesso.",
    0, CONCLUIDO, 100, st)

# ── EM ANDAMENTO / BLOQUEADO ─────────────────────────────────────────────────
print("\n=== Em Andamento ===")

create_task(
    "Ativacao das Cloud Accounts - Taiba, Charme e Cumbuco",
    "Criar as Cloud Accounts no portal Oracle para as tres unidades restantes.\n\n"
    "INSTRUCAO (Roberto/Oracle): selecionar 'Create New Cloud Account' — NAO 'Add to existing'.\n"
    "Nomenclatura: nome unico do hotel, apenas letras minusculas, sem simbolos ou espacos.\n\n"
    "STATUS: Bloqueado. A opcao 'Create New Cloud Account' nao esta aparecendo para essas "
    "unidades. Se persistir, documentar print do erro e solicitar intervencao tecnica da Oracle "
    "(possivel falta de permissao na conta).",
    0, EM_AND, 0, st)

# ── A FAZER ──────────────────────────────────────────────────────────────────
print("\n=== A Fazer ===")

create_task(
    "Confirmar ativacao das contas ao Roberto (Oracle)",
    "Apos criar as contas de Taiba, Charme e Cumbuco, enviar ao Roberto os nomes das contas "
    "criadas para que o time de implantacao OCD possa dar andamento ao processo.",
    0, NOVO, 0, st)

create_task(
    "Setup e provisionamento OCD - Icaraizinho",
    "Iniciar a configuracao do Opera Cloud Distribution para a unidade Icaraizinho apos "
    "o handoff do Roberto para o time de implantacao OCD.",
    0, NOVO, 0, st)

create_task(
    "Setup e provisionamento OCD - Taiba, Charme e Cumbuco",
    "Apos ativacao das Cloud Accounts, iniciar a implantacao OCD em producao nas tres "
    "unidades restantes, com acompanhamento do time de implantacao Oracle.",
    0, NOVO, 0, st)

create_task(
    "Acompanhar transicao: Roberto -> time de implantacao OCD",
    "Acompanhar a transferencia de responsabilidade do Roberto para o time de implantacao OCD. "
    "Tratar questoes de billing e cronograma tecnico com o novo ponto de contato.",
    0, NOVO, 0, st)

req('GET', 'killSession', st=st)

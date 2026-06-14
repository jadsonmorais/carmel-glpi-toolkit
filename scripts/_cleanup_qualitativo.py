import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
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

JADSON = 316

# ============================================================
# Buscar ID do Magno Alves
# ============================================================
print("=== Buscando Magno Alves e Davi Tavares ===")
users = req('GET', "search/User?criteria[0][field]=1&criteria[0][searchtype]=contains&criteria[0][value]=magno&forcedisplay[0]=1&forcedisplay[1]=2&forcedisplay[2]=34&range=0-10", st=st)
magno_id = None
if users and 'data' in users:
    for u in users['data']:
        nome = u.get('2') or u.get('34') or ''
        uid = u.get('1') or u.get('id')
        print(f"  Encontrado: #{uid} — {nome}")
        if 'magno' in str(nome).lower():
            magno_id = int(uid)
else:
    print(f"  Nenhum resultado: {users}")

users2 = req('GET', "search/User?criteria[0][field]=1&criteria[0][searchtype]=contains&criteria[0][value]=davi&forcedisplay[0]=1&forcedisplay[1]=2&forcedisplay[2]=34&range=0-10", st=st)
davi_id = None
if users2 and 'data' in users2:
    for u in users2['data']:
        nome = u.get('2') or u.get('34') or ''
        uid = u.get('1') or u.get('id')
        print(f"  Encontrado: #{uid} — {nome}")
        if 'davi' in str(nome).lower():
            davi_id = int(uid)
else:
    print(f"  Nenhum resultado: {users2}")

print(f"  Magno ID: {magno_id} | Davi ID: {davi_id}")

# ============================================================
# 1. Criar tarefa Zabbix no Projeto #244 (Infraestrutura)
# ============================================================
print("\n=== Tarefa Zabbix — Projeto #244 Infraestrutura ===")
zabbix_task = req('POST', 'ProjectTask', body={"input": {
    "projects_id": 244,
    "name": "INF-Zabbix — Configuração do Zabbix no Servidor Linux do Magna Praia",
    "content": (
        "Instalar e configurar o Zabbix no servidor Linux do Magna Praia para monitoramento "
        "de infraestrutura. Responsável: Magno Alves. "
        "Escopo: instalação do Zabbix Server/Agent, configuração de hosts e alertas básicos "
        "de disponibilidade (CPU, memória, disco, rede)."
    ),
    "plan_start_date": "2026-06-09",
    "plan_end_date": "2026-06-20",
    "projectstates_id": 2,  # Em andamento
    "percent_done": 0,
    **({"users_id": magno_id} if magno_id else {}),
}}, st=st)
if zabbix_task and 'id' in zabbix_task:
    print(f"  OK  Tarefa #{zabbix_task['id']} criada — Zabbix no Projeto #244")
    if magno_id:
        req('POST', 'ProjectTask_User', body={"input": {
            "projecttasks_id": zabbix_task['id'],
            "users_id": magno_id,
            "type": 2,
        }}, st=st)
        print(f"  OK  Magno (#{magno_id}) atribuído à tarefa")
else:
    print(f"  ERR: {zabbix_task}")

# ============================================================
# 2. Fechar Problems que são filas/tarefas disfarçadas
# ============================================================
print("\n=== Fechando Problems sem causa raiz real ===")

FECHAMENTOS = [
    (237, "Problem encerrado: demanda de aquisição de tablets não configura Problema ITIL — sem causa raiz técnica recorrente. Tickets vinculados mantidos para registro histórico."),
    (230, "Problem encerrado: sem plano de ação definido após 5 meses. Ticket #24888 permanece aberto para acompanhamento individual."),
    (236, "Problem encerrado: funcionava como fila de suporte Simphony, não como Problem com causa raiz identificada. Tickets específicos vinculados a Problems temáticos (#262 integração fiscal, #265 XML Sefaz)."),
]

for pid, nota in FECHAMENTOS:
    r = req('PUT', f'Problem/{pid}', body={"input": {"id": pid, "status": 6}}, st=st)
    ok = isinstance(r, list) and r[0].get(str(pid))
    print(f"  {'OK' if ok else 'ERR'}  Problem #{pid} -> status 6 (Fechado)")
    req('POST', 'ITILFollowup', body={"input": {
        "itemtype": "Problem", "items_id": pid,
        "content": nota, "is_private": 0,
    }}, st=st)

# ============================================================
# 3. Incorporar #266 ao #259 via followup e fechar #266
# ============================================================
print("\n=== Incorporando #266 ao #259 e fechando ===")
# Adicionar nota no #259
req('POST', 'ITILFollowup', body={"input": {
    "itemtype": "Problem", "items_id": 259,
    "content": (
        "Incorporado: Problem #266 (CMFlex Almoxarifado - Ordem de Produção) foi consolidado aqui. "
        "A falha/restrição na geração de Ordem de Produção é uma manifestação dentro do escopo "
        "deste Problem. Tickets vinculados ao #266 passam a ser acompanhados por este Problem."
    ),
    "is_private": 0,
}}, st=st)
# Migrar tickets do #266 para #259 (ticket #27899)
r_migrate = req('POST', 'Problem_Ticket', body={"input": {"problems_id": 259, "tickets_id": 27899}}, st=st)
print(f"  {'OK' if r_migrate and 'id' in r_migrate else 'ERR/duplicado'}  #27899 vinculado ao #259")
# Fechar #266
r = req('PUT', 'Problem/266', body={"input": {"id": 266, "status": 6}}, st=st)
ok = isinstance(r, list) and r[0].get('266')
print(f"  {'OK' if ok else 'ERR'}  Problem #266 -> Fechado (incorporado ao #259)")
req('POST', 'ITILFollowup', body={"input": {
    "itemtype": "Problem", "items_id": 266,
    "content": "Problem encerrado e incorporado ao #259 (CMFlex Almoxarifado - Inventário, Requisições e Divergências de Estoque).",
    "is_private": 0,
}}, st=st)

# ============================================================
# 4. Corrigir escopo do #258 — remover "BPM" do nome
# ============================================================
print("\n=== Corrigindo escopo do Problem #258 ===")
r = req('PUT', 'Problem/258', body={"input": {
    "id": 258,
    "name": "CMFlex Financeiro - Contas a Pagar, Aprovacoes e Lancamentos",
}}, st=st)
ok = isinstance(r, list) and r[0].get('258')
print(f"  {'OK' if ok else 'ERR'}  Problem #258 renomeado (BPM removido do escopo)")

# ============================================================
# 5. Subordinar Change #54 (FlexDFE NFCe) ao Problem #255
# ============================================================
print("\n=== Vinculando Change #54 ao Problem #255 (Reforma Tributaria) ===")
r = req('POST', 'Change_Problem', body={"input": {"changes_id": 54, "problems_id": 255}}, st=st)
print(f"  {'OK' if r and 'id' in r else 'ERR/duplicado'}  Change #54 -> Problem #255")

# ============================================================
# 6. Atualizar Projeto #244 status para Em andamento
# ============================================================
print("\n=== Atualizando Projeto #244 para Em andamento ===")
r = req('PUT', 'Project/244', body={"input": {
    "id": 244,
    "projectstates_id": 2,  # Em andamento
}}, st=st)
ok = isinstance(r, list) and r[0].get('244')
print(f"  {'OK' if ok else 'ERR'}  Projeto #244 -> Em andamento")

print("\n=== CONCLUIDO ===")

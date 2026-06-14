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
AMANHA = "2026-06-09"
PLANEJADO = 3  # status Atendimento Planejado

def set_planned(tid, begin="2026-06-09 08:00:00", note=None):
    r = req('PUT', f'Ticket/{tid}', body={"input": {"id": tid, "status": PLANEJADO}}, st=st)
    ok = isinstance(r, list) and r[0].get(str(tid))
    print(f"  {'OK' if ok else 'ERR'}  #{tid} -> status Planejado")
    if note:
        req('POST', 'ITILFollowup', body={"input": {
            "itemtype": "Ticket", "items_id": tid,
            "content": note, "is_private": 0,
        }}, st=st)
    return ok

def add_task(tid, content, begin, end=None):
    if not end:
        end = begin[:10] + " 09:00:00"
    r = req('POST', 'TicketTask', body={"input": {
        "tickets_id": tid,
        "content": content,
        "begin": begin,
        "end": end,
        "state": 1,
        "users_id_tech": JADSON,
    }}, st=st)
    ok = r and 'id' in r
    print(f"  {'OK' if ok else 'ERR'}  Task em #{tid}: {content[:60]}")
    return ok

# ============================================================
# 1. #27899 — Criar Problem: Ordem de Produção CMFlex
# ============================================================
print("=== #27899 — Problem: Ordem de Producao CMFlex ===")
p27899 = req('POST', 'Problem', body={"input": {
    "name": "CMFlex Almoxarifado - Falha ou restricao na geracao de Ordem de Producao",
    "itilcategories_id": 146,  # CMFlex > Almoxarifado
    "status": 2,
    "urgency": 3, "impact": 3, "priority": 3,
    "entities_id": 1,
    "content": (
        "Usuarios relatam dificuldade ou erro ao tentar gerar Ordem de Producao no modulo "
        "Almoxarifado do CMFlex. Necessita investigacao para identificar se e restricao de "
        "parametrizacao, permissao de usuario ou bug no sistema."
    ),
    "symptomcontent": "<p>Erro ou bloqueio ao tentar criar/salvar Ordem de Producao no CMFlex Almoxarifado.</p>",
    "causecontent": "<p>A investigar: pode ser restricao de parametrizacao, perfil de acesso insuficiente ou bug no modulo.</p>",
    "impactcontent": "<p>Operacao de producao/almoxarifado bloqueada, impactando controle de estoque e insumos.</p>",
}}, st=st)
if p27899 and 'id' in p27899:
    pid = p27899['id']
    print(f"  OK  Problem #{pid} criado")
    req('POST', 'Problem_User', body={"input": {"problems_id": pid, "users_id": JADSON, "type": 2}}, st=st)
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": pid, "tickets_id": 27899}}, st=st)
    print(f"  {'OK' if r and 'id' in r else 'ERR'}  #27899 -> Problem #{pid}")
set_planned(27899, note="Planejado para analise — aguarda investigacao de parametrizacao e permissoes no CMFlex.")

# ============================================================
# 2. #27910 — Criar projeto "Melhorias Operacionais" + tarefa
# ============================================================
print("\n=== #27910 — Projeto Melhorias Operacionais ===")
proj = req('POST', 'Project', body={"input": {
    "name": "Melhorias Operacionais",
    "content": (
        "Projeto para centralizar demandas de melhoria operacional da rede Carmel que nao se encaixam "
        "em projetos especificos de sistema ou infraestrutura. Inclui automacoes, facilitadores de "
        "processos e pequenas melhorias de produtividade das equipes."
    ),
    "entities_id": 1,
    "is_recursive": 1,
    "projectstates_id": 2,   # Em andamento
    "projecttypes_id": 4,    # Melhorias
    "priority": 3,
    "plan_start_date": "2026-06-09",
    "plan_end_date": "2026-12-31",
    "percent_done": 0,
}}, st=st)
if proj and 'id' in proj:
    proj_id = proj['id']
    print(f"  OK  Projeto #{proj_id} criado: Melhorias Operacionais")
    task = req('POST', 'ProjectTask', body={"input": {
        "projects_id": proj_id,
        "name": "MOP-01 - Criacao de QR Code para acesso rapido",
        "content": (
            "Solicitacao de criacao de QR Code para facilitar acesso a recurso interno. "
            "Verificar ferramenta (Google Forms, link direto ou outro) e gerar o QR Code para o requerente."
        ),
        "plan_start_date": "2026-06-09",
        "plan_end_date": "2026-06-09",
        "projectstates_id": 1,
        "percent_done": 0,
    }}, st=st)
    if task and 'id' in task:
        tid_task = task['id']
        print(f"  OK  Tarefa MOP-01 #{tid_task} criada")
        r = req('POST', 'ProjectTask_Ticket', body={"input": {"projecttasks_id": tid_task, "tickets_id": 27910}}, st=st)
        print(f"  {'OK' if r and 'id' in r else 'ERR'}  #27910 -> Tarefa MOP-01")
    else:
        print(f"  ERR Tarefa: {task}")
else:
    print(f"  ERR Projeto: {proj}")

# ============================================================
# 3. Tickets planejados para amanha cedo (slots 1-4)
# ============================================================
print("\n=== Planejamento amanha 09/06 ===")

# Slot 1 — 08:00 — #27956 Inventario fisico
set_planned(27956)
add_task(27956, "Investigar e corrigir inventario fisico e financeiro que nao atualizou no CMFlex.", "2026-06-09 08:00:00", "2026-06-09 09:00:00")

# Slot 2 — 09:00 — #27814 BI Almoxarifado
set_planned(27814)
add_task(27814, "Analisar BI Almoxarifado — identificar causa do erro no dashboard.", "2026-06-09 09:00:00", "2026-06-09 10:00:00")

# Slot 3 — 10:00 — #27832 KDS Simphony (verificar com Kevin)
set_planned(27832, note="Verificar com Kevin sobre a configuracao do cardapio KDS para a cozinha Cipo.")
add_task(27832, "Verificar com Kevin: reconfigurar cardapio KDS Simphony para sair nas comandeiras da cozinha Cipo.", "2026-06-09 10:00:00", "2026-06-09 11:00:00")

# Slot 4 — 11:00 — #27866 SCI centro de custo (possivel bug CMFlex)
set_planned(27866, note="Possivel bug no CMFlex: sistema aceitando SCI de centro de custo que nao deveria. Abriu falso precedente — verificar parametrizacao e reportar ao suporte Sankhya se confirmado.")
add_task(27866, "Investigar bug CMFlex: SCI sendo aceita por centro de custo nao autorizado. Verificar parametrizacao e abrir chamado Sankhya se confirmado.", "2026-06-09 11:00:00", "2026-06-09 12:00:00")

# ============================================================
# 4. #27898 — Tarefa no projeto 242 (Melhorias de Infraestrutura)
# ============================================================
print("\n=== #27898 — Tarefa no Projeto 242 ===")
task242 = req('POST', 'ProjectTask', body={"input": {
    "projects_id": 242,
    "name": "Opera Cloud — Replicar motivo de estada entre reservas",
    "content": (
        "Investigar como configurar ou habilitar a replicacao automatica do motivo de estada "
        "entre reservas no Opera Cloud PMS — Carmel Taiba."
    ),
    "plan_start_date": "2026-06-10",
    "plan_end_date": "2026-06-10",
    "projectstates_id": 1,
    "percent_done": 0,
}}, st=st)
if task242 and 'id' in task242:
    t242_id = task242['id']
    print(f"  OK  Tarefa #{t242_id} criada no Projeto 242")
    r = req('POST', 'ProjectTask_Ticket', body={"input": {"projecttasks_id": t242_id, "tickets_id": 27898}}, st=st)
    print(f"  {'OK' if r and 'id' in r else 'ERR'}  #27898 -> Tarefa #{t242_id}")
else:
    print(f"  ERR: {task242}")

# ============================================================
# 5. #27936 — Planejado + task com data do Meet (09/06 10:00)
# ============================================================
print("\n=== #27936 — Treinamento Meet 09/06 10:00 ===")
set_planned(27936, note="Reuniao agendada no Google Meet para 09/06 as 10:00 — gravar treinamento.")
add_task(27936, "Gravar treinamento conforme agendado no Meet.", "2026-06-09 10:00:00", "2026-06-09 12:00:00")

# ============================================================
# 6. #27812 — Criar Problem + vincular + planejado amanha
# ============================================================
print("\n=== #27812 — Problem: Template de cadastro de localizacao Icaraizinho ===")
p27812 = req('POST', 'Problem', body={"input": {
    "name": "CMFlex CAF - Ausencia de template padrao para cadastro de localizacoes no Icaraizinho",
    "itilcategories_id": 147,  # CMFlex > Ativo Fixo (CAF)
    "status": 2,
    "urgency": 3, "impact": 3, "priority": 3,
    "entities_id": 1,
    "content": (
        "O modulo de Ativo Fixo (CAF) do CMFlex nao possui template padronizado para cadastro "
        "de localizacoes no Carmel Icaraizinho. Sem o template, os cadastros ficam inconsistentes "
        "e fora do padrao da rede Carmel, impactando rastreabilidade de ativos e inventario."
    ),
    "symptomcontent": "<p>Cadastros de localizacao no CAF do Icaraizinho sendo realizados sem padrao — campo testado manualmente sem template definido.</p>",
    "causecontent": "<p>Ausencia de template de localizacao configurado para a unidade Carmel Icaraizinho no CMFlex CAF. Unidade nova, sem parametrizacao inicial concluida.</p>",
    "impactcontent": "<p>Inventario de ativos do Icaraizinho com localizacoes inconsistentes, dificultando rastreabilidade e futuras auditorias de patrimonio.</p>",
}}, st=st)
if p27812 and 'id' in p27812:
    pid812 = p27812['id']
    print(f"  OK  Problem #{pid812} criado")
    req('POST', 'Problem_User', body={"input": {"problems_id": pid812, "users_id": JADSON, "type": 2}}, st=st)
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": pid812, "tickets_id": 27812}}, st=st)
    print(f"  {'OK' if r and 'id' in r else 'ERR'}  #27812 -> Problem #{pid812}")
set_planned(27812)
add_task(27812, "Criar e parametrizar template de cadastro de localizacoes no CMFlex CAF para o Carmel Icaraizinho.", "2026-06-09 08:30:00", "2026-06-09 09:30:00")

# ============================================================
# 7. Redistribuicao dos demais tickets em Planejado (status=3)
#    a partir de 10/06, um por dia as 08:00
# ============================================================
print("\n=== Redistribuicao dos demais Planejados a partir de 10/06 ===")
# Buscar todos status=3 excluindo os que ja tratamos hoje
JA_TRATADOS = {27956, 27814, 27832, 27866, 27936, 27812, 27899, 27910, 27898}

planned = []
for s in [3]:
    r = req('GET',
        f"search/Ticket"
        f"?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]=3"
        f"&forcedisplay[0]=1&forcedisplay[1]=3&forcedisplay[2]=80"
        f"&range=0-100", st=st)
    if r and 'data' in r:
        for t in r['data']:
            tid = t.get('1') or t.get('id')
            if tid and int(tid) not in JA_TRATADOS:
                planned.append(int(tid))

print(f"  Encontrados {len(planned)} tickets planejados para redistribuir: {planned}")

from datetime import date, timedelta
dia = date(2026, 6, 10)
for tid in sorted(planned):
    data_str = dia.strftime("%Y-%m-%d")
    r = req('POST', 'TicketTask', body={"input": {
        "tickets_id": tid,
        "content": f"Atendimento planejado para {data_str}.",
        "begin": f"{data_str} 08:00:00",
        "end":   f"{data_str} 09:00:00",
        "state": 1,
        "users_id_tech": JADSON,
    }}, st=st)
    ok = r and 'id' in r
    print(f"  {'OK' if ok else 'ERR'}  #{tid} -> tarefa {data_str}")
    dia += timedelta(days=1)

print("\n=== CONCLUIDO ===")

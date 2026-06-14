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

# ============================================================
# #27948 — Problem: Migração de Servidores dos Resorts
# ============================================================
print("=== Problem: Migracao de Servidores dos Resorts ===")
p1 = req('POST', 'Problem', body={"input": {
    "name": "Infraestrutura - Necessidade de migracao e reconfiguracao dos servidores de aplicacao dos Resorts",
    "itilcategories_id": 210,  # Infraestrutura > Servidor
    "status": 2,               # Em andamento
    "urgency": 4,
    "impact": 4,
    "priority": 4,
    "entities_id": 1,

    "content": (
        "Os servidores de aplicacao dos resorts da rede Carmel necessitam de migracao e reconfiguracao. "
        "Carmel Taiba ja foi executado (concluido). Wind e Charme estao programados — "
        "Jadson e Italo estao conduzindo o planejamento e execucao em conjunto. "
        "Cada migracao envolve downtime planejado, reconfiguracoes de servicos e validacao pos-migracao."
    ),

    "symptomcontent": (
        "<p>Servidores de aplicacao dos resorts operam em configuracao desatualizada ou inadequada, "
        "gerando instabilidade, lentidao e dificuldade de manutencao. Servidores antigos apresentam "
        "limitacoes de performance e risco de indisponibilidade por falta de suporte.</p>"
    ),

    "causecontent": (
        "<p>Necessidade de modernizacao da infraestrutura de servidores de aplicacao dos resorts. "
        "A causa raiz e a obsolescencia ou subdimensionamento dos servidores atuais, exigindo "
        "migracao planejada resort a resort para minimizar impacto operacional.</p>"
        "<p><strong>Status por unidade:</strong></p>"
        "<ul>"
        "<li>Carmel Taiba: <strong>Concluido</strong></li>"
        "<li>Carmel Wind: <strong>Programado</strong> — Jadson + Italo</li>"
        "<li>Carmel Charme: <strong>Programado</strong> — Jadson + Italo (apos Wind)</li>"
        "</ul>"
    ),

    "impactcontent": (
        "<p>Durante a janela de migracao de cada resort, os sistemas de aplicacao ficam indisponiveis "
        "(downtime planejado). Pos-migracao, espera-se melhora de performance, estabilidade e "
        "facilidade de manutencao. Risco de regressao em servicos dependentes se a migracao "
        "nao for validada corretamente.</p>"
    ),
}}, st=st)

if p1 and 'id' in p1:
    pid1 = p1['id']
    print(f"OK  Problem #{pid1} criado")
    req('POST', 'Problem_User', body={"input": {"problems_id": pid1, "users_id": 316, "type": 2}}, st=st)
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": pid1, "tickets_id": 27948}}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR'}  #27948 -> Problem #{pid1}")
else:
    print(f"ERR Problem: {p1}")
    pid1 = None

# ============================================================
# #27948 — Change (Mudança): Migração de Servidores dos Resorts
# ============================================================
print("\n=== Change: Migracao de Servidores dos Resorts ===")
c1 = req('POST', 'Change', body={"input": {
    "name": "Migracao e reconfiguracao dos servidores de aplicacao dos Resorts (Wind e Charme)",
    "itilcategories_id": 210,  # Infraestrutura > Servidor
    "status": 2,               # Em avaliacao / Em andamento
    "urgency": 3,
    "impact": 4,
    "priority": 3,
    "entities_id": 1,
    "content": (
        "Mudanca planejada de migracao e reconfiguracao dos servidores de aplicacao dos resorts "
        "Carmel Wind e Carmel Charme. Execucao conduzida por Jadson Morais e Italo. "
        "Carmel Taiba ja foi concluido. Wind e Charme serao executados em sequencia "
        "com janelas de manutencao programadas para minimizar impacto operacional."
    ),
}}, st=st)

if c1 and 'id' in c1:
    cid1 = c1['id']
    print(f"OK  Change #{cid1} criado")
    # Vincular chamado à mudança
    r = req('POST', 'Change_Ticket', body={"input": {"changes_id": cid1, "tickets_id": 27948}}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR'}  #27948 -> Change #{cid1}")
    # Vincular problem à mudança
    if pid1:
        r = req('POST', 'Change_Problem', body={"input": {"changes_id": cid1, "problems_id": pid1}}, st=st)
        print(f"{'OK' if r and 'id' in r else 'ERR'}  Problem #{pid1} -> Change #{cid1}")
    # Atribuir tecnico
    req('POST', 'Change_User', body={"input": {"changes_id": cid1, "users_id": 316, "type": 2}}, st=st)
    print(f"OK  Tecnico atribuido a Change #{cid1}")
else:
    print(f"ERR Change: {c1}")

# ============================================================
# #27953 — Problem: Simphony XML Sefaz via Harmonized
# ============================================================
print("\n=== Problem: Simphony - Payload XML invalido para Sefaz via Harmonized ===")
p2 = req('POST', 'Problem', body={"input": {
    "name": "Simphony - Inconsistencia no Payload XML enviado a Sefaz via Harmonized ao encerrar mesa",
    "itilcategories_id": 171,  # Serviços de Sistemas > Simphony
    "status": 2,
    "urgency": 4,
    "impact": 4,
    "priority": 4,
    "entities_id": 1,

    "content": (
        "Durante o encerramento de mesa no Simphony, um erro gera inconsistencia no Payload XML "
        "enviado a Sefaz via Harmonized. Problema identificado por Jadson em chamado com N1 Simphony (Aline). "
        "Suporte N2 solicitou logs da CAPS para investigacao — consultas passadas no chamado interno 260601-002347. "
        "Kevin Almeida atribuido como responsavel tecnico."
    ),

    "symptomcontent": (
        "<p>Ao encerrar uma mesa no Simphony, o sistema gera um erro que resulta em Payload XML "
        "invalido ou inconsistente enviado a Sefaz via integracao Harmonized. Sintomas:</p>"
        "<ul>"
        "<li>Erro durante o fluxo de encerramento de mesa no Simphony.</li>"
        "<li>Rejeicao ou falha silenciosa na transmissao fiscal para a Sefaz.</li>"
        "<li>Possivel geracao de NFC-e/NF-e com dados incorretos ou nao transmitidas.</li>"
        "<li>Logs da CAPS indicam inconsistencia no XML gerado pelo Simphony antes do envio.</li>"
        "</ul>"
    ),

    "causecontent": (
        "<p>Bug no Simphony durante o processo de encerramento de mesa que gera um Payload XML "
        "mal-formado ou com dados inconsistentes antes do envio a Sefaz via Harmonized. "
        "Causa raiz em investigacao pelo N2 do suporte Simphony (Oracle), que solicitou "
        "logs especificos da CAPS para identificar o ponto exato da inconsistencia. "
        "Chamado de suporte interno: <strong>260601-002347</strong>.</p>"
    ),

    "impactcontent": (
        "<p>Impacto direto na operacao fiscal e de F&amp;B:</p>"
        "<ul>"
        "<li><strong>Fiscal:</strong> Documentos fiscais (NFC-e/NF-e) podem nao ser transmitidos "
        "corretamente a Sefaz, gerando risco de irregularidade fiscal e necessidade de contingencia.</li>"
        "<li><strong>Operacao:</strong> Encerramento de mesas bloqueado ou com erro, impactando "
        "o fluxo de caixa do restaurante e a experiencia do hospede no checkout.</li>"
        "<li><strong>Auditoria:</strong> Divergencia entre vendas registradas no Simphony e "
        "documentos fiscais emitidos.</li>"
        "</ul>"
    ),
}}, st=st)

if p2 and 'id' in p2:
    pid2 = p2['id']
    print(f"OK  Problem #{pid2} criado")
    # Atribuir Kevin (precisamos do users_id do Kevin — buscando)
    req('POST', 'Problem_User', body={"input": {"problems_id": pid2, "users_id": 316, "type": 1}}, st=st)  # Jadson como observador
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": pid2, "tickets_id": 27953}}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR'}  #27953 -> Problem #{pid2}")
else:
    print(f"ERR Problem: {p2}")

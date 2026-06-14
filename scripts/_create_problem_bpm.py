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

# 1. Criar Problem
problem = req('POST', 'Problem', body={"input": {
    "name": "CMFlex BPM - Multiplas instancias de aprovacao geradas para o mesmo objeto",
    "itilcategories_id": 149,  # Serviços de Sistemas > CMFlex > BPM
    "status": 2,               # Em andamento
    "urgency": 3,
    "impact": 4,               # Grande — bloqueia fluxos de aprovacao
    "priority": 3,
    "entities_id": 1,

    "content": (
        "Ao salvar uma requisicao, pedido de compra ou qualquer documento que dispara fluxo de aprovacao "
        "no modulo BPM do CMFlex, o sistema gera uma nova instancia de aprovacao sem cancelar a anterior. "
        "O resultado sao multiplas instancias ativas para o mesmo objeto, causando duplicidade de "
        "notificacoes, aprovacoes concorrentes e inconsistencia no status do documento."
    ),

    "symptomcontent": (
        "<p>Ao salvar ou reeditar uma requisicao/documento que ja possui fluxo de aprovacao ativo, "
        "o CMFlex BPM dispara uma nova instancia de aprovacao sem encerrar a anterior. "
        "Sintomas observados:</p>"
        "<ul>"
        "<li>Aprovadores recebem multiplas notificacoes para o mesmo documento.</li>"
        "<li>O documento aparece em estado inconsistente (pendente e aprovado simultaneamente).</li>"
        "<li>Aprovacoes realizadas na instancia errada nao refletem no status real do documento.</li>"
        "<li>Historico de BPM mostra instancias duplicadas ou sobrepostas para o mesmo objeto.</li>"
        "</ul>"
    ),

    "causecontent": (
        "<p>Bug no motor de BPM do CMFlex (Sankhya): ao acionar o gatilho de salvamento em um documento "
        "ja com fluxo ativo, o sistema nao verifica a existencia de instancia em andamento antes de "
        "criar uma nova. A instancia anterior permanece ativa em paralelo em vez de ser cancelada ou "
        "arquivada automaticamente. Causa raiz e de responsabilidade do fornecedor (Sankhya/CMFlex) "
        "e exige correcao no codigo do produto.</p>"
    ),

    "impactcontent": (
        "<p>Impacto direto nos fluxos de aprovacao das areas de Suprimentos, Controladoria e Financeiro:</p>"
        "<ul>"
        "<li><strong>Suprimentos:</strong> Requisicoes e ordens de compra ficam presas em aprovacao "
        "duplicada, atrasando aquisicoes e gerando retrabalho manual para cancelar instancias incorretas.</li>"
        "<li><strong>Controladoria/Financeiro:</strong> Documentos financeiros com multiplas aprovacoes "
        "ativas geram risco de pagamento ou comprometimento de verba duplicado.</li>"
        "<li><strong>Gestao:</strong> Aprovadores perdem rastreabilidade do fluxo real do documento, "
        "comprometendo a governanca do processo de compras e pagamentos.</li>"
        "</ul>"
    ),
}}, st=st)

if not problem or 'id' not in problem:
    print(f"ERR Problem: {problem}")
    exit(1)

pid = problem['id']
print(f"OK  Problem #{pid} criado: CMFlex BPM - Multiplas instancias de aprovacao")

# 2. Atribuir tecnico
tech = req('POST', 'Problem_User', body={"input": {
    "problems_id": pid,
    "users_id": 316,
    "type": 2,
}}, st=st)
print(f"{'OK' if tech and 'id' in tech else 'ERR'}  Tecnico atribuido")

# 3. Vincular chamado #27848
link = req('POST', 'Problem_Ticket', body={"input": {
    "problems_id": pid,
    "tickets_id": 27848,
}}, st=st)
print(f"{'OK' if link and 'id' in link else 'ERR'}  Chamado #27848 vinculado ao Problem #{pid}: {'' if link and 'id' in link else link}")

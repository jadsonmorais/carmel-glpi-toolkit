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

problem = req('POST', 'Problem', body={"input": {
    "name": "RHID - Falha de conectividade impactando ponto eletronico e operacoes de DP/RH",
    "itilcategories_id": 170,  # Serviços de Sistemas > RHID
    "status": 2,
    "urgency": 4,
    "impact": 4,
    "priority": 4,
    "entities_id": 1,

    "content": (
        "O sistema RHID apresenta falhas de conectividade intermitentes que impactam o registro "
        "de ponto eletronico e demais operacoes do DP/RH. O problema se manifesta como "
        "indisponibilidade do sistema ou lentidao critica em horarios de pico de batida de ponto, "
        "gerando registros ausentes ou incorretos que precisam de correcao manual pelo RH."
    ),

    "symptomcontent": (
        "<p>Sistema RHID inacessivel ou extremamente lento durante o uso:</p>"
        "<ul>"
        "<li>Colaboradores nao conseguem bater ponto — sistema nao responde no terminal ou app.</li>"
        "<li>Batidas de ponto de dias anteriores ausentes no historico, exigindo ajuste manual.</li>"
        "<li>Relatorios de frequencia e espelho de ponto com dados incompletos.</li>"
        "<li>Ocorrencias em multiplos hoteis simultaneamente, indicando causa na camada de conectividade "
        "com o SaaS e nao em equipamento local especifico.</li>"
        "</ul>"
    ),

    "causecontent": (
        "<p>Instabilidade na conectividade entre a rede dos hoteis e a infraestrutura SaaS do RHID. "
        "Possiveis causas:</p>"
        "<ul>"
        "<li>Degradacao ou interrupcao temporaria no servico de nuvem do fornecedor RHID.</li>"
        "<li>Saturacao de banda em horarios de pico (entrada/saida de turnos) quando multiplos "
        "dispositivos tentam sincronizar simultaneamente.</li>"
        "<li>Timeout de sessao nao tratado pelo cliente, resultando em perda silenciosa de registros.</li>"
        "</ul>"
        "<p>A causa raiz precisa ser investigada em conjunto com o suporte do fornecedor RHID.</p>"
    ),

    "impactcontent": (
        "<p>Impacto direto na area de Departamento Pessoal e RH:</p>"
        "<ul>"
        "<li><strong>Ponto eletronico:</strong> Registros ausentes geram inconsistencias na folha de "
        "pagamento, horas extras nao computadas e necessidade de ajuste manual com autorizacao de gestor.</li>"
        "<li><strong>Compliance trabalhista:</strong> Falhas sistematicas no registro de ponto podem "
        "configurar irregularidade perante fiscalizacao do MTE.</li>"
        "<li><strong>Produtividade do RH:</strong> Cada ocorrencia gera demanda de correcao retroativa, "
        "consumindo tempo da equipe de DP em retrabalho operacional.</li>"
        "</ul>"
    ),
}}, st=st)

if not problem or 'id' not in problem:
    print(f"ERR Problem: {problem}")
    exit(1)

pid = problem['id']
print(f"OK  Problem #{pid} criado: RHID - Falha de conectividade DP/RH")

req('POST', 'Problem_User', body={"input": {"problems_id": pid, "users_id": 316, "type": 2}}, st=st)
print(f"OK  Tecnico atribuido")

for tid in [27896, 27897]:
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": pid, "tickets_id": tid}}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR'}  #{tid} -> Problem #{pid}")

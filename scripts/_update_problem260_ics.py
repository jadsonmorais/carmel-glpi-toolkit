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

r = req('PUT', 'Problem/260', body={"input": {
    "id": 260,

    "symptomcontent": (
        "<p>Modulo do CMFlex (Almoxarifado, Contas a Pagar, Fiscal, Contabilidade, entre outros) "
        "apresenta lentidao extrema ou nao responde durante o uso normal. O comportamento e "
        "intermitente e afeta modulos aleatorios, podendo variar entre hoteis e usuarios. "
        "Em alguns casos a pagina trava ou expira a sessao sem acao do usuario.</p>"
    ),

    "causecontent": (
        "<p>Instabilidade ou degradacao de desempenho na infraestrutura SaaS do CMFlex (Sankhya). "
        "Descartado problema de conectividade local apos validacao da internet em cada ocorrencia. "
        "A causa raiz e externa: sobrecarga, manutencao nao comunicada ou falha nos servidores do "
        "fornecedor. Nao ha acesso direto aos logs ou infraestrutura do CMFlex pela equipe de TI Carmel.</p>"
    ),

    "impactcontent": (
        "<p>Operacoes de backoffice ficam bloqueadas ou lentas: lancamentos de almoxarifado, "
        "fechamentos financeiros, emissao fiscal e consultas de contas a pagar/receber. "
        "Impacto direto na produtividade das equipes de Suprimentos, Controladoria e Fiscal. "
        "Em episodios prolongados pode atrasar fechamentos contabeis e apuracao fiscal do periodo.</p>"
    ),
}}, st=st)

if isinstance(r, list) and r[0].get('260'):
    print("OK  Sintomas, Causas e Impactos preenchidos no Problem #260")
else:
    print(f"ERR: {r}")

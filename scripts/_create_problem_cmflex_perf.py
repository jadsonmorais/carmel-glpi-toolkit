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

# 1. Criar o Problem
problem = req('POST', 'Problem', body={"input": {
    "name": "CMFlex - Baixo desempenho intermitente em modulos (SaaS)",
    "content": (
        "O sistema CMFlex apresenta baixo desempenho de forma intermitente e em modulos aleatorios "
        "(Almoxarifado, Contas a Pagar, Fiscal, etc.). O padrao identificado e: o sistema fica lento "
        "ou nao responde, a equipe verifica a conectividade com a internet (que se confirma estavel), "
        "descartando problema local. Confirmado que a causa raiz e na infraestrutura SaaS do CMFlex, "
        "sendo necessario abrir chamado diretamente com o suporte CMFlex/Sankhya para investigacao "
        "no lado do fornecedor. Problema recorrente sem solucao definitiva ate o momento."
    ),
    "status": 1,
    "urgency": 3,
    "impact": 3,
    "priority": 3,
}}, st=st)

if not problem or 'id' not in problem:
    print(f"ERR Problem: {problem}")
    exit(1)

pid = problem['id']
print(f"OK  Problem #{pid} criado: CMFlex - Baixo desempenho intermitente em modulos (SaaS)")

# 2. Vincular chamado #27828
link = req('POST', 'Problem_Ticket', body={"input": {
    "problems_id": pid,
    "tickets_id": 27828,
}}, st=st)

if link and 'id' in link:
    print(f"OK  Chamado #27828 vinculado ao Problem #{pid}")
else:
    print(f"ERR Vinculo: {link}")

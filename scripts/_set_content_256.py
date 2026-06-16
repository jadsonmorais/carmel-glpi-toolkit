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

content = """PROBLEMA: As workstations e tablets do PDV (Simphony) operam hoje sem padronizacao de inventario no GLPI, sem regras de firewall/antivirus alinhadas com os requisitos da Oracle, e sem rede/GPO padronizada entre as unidades - gerando risco de indisponibilidade do PDV, retrabalho de suporte e falta de documentacao para a equipe.

SOLUCAO PROPOSTA: Padronizar o inventario (GLPI), levantar e aplicar os requisitos de rede/firewall/antivirus exigidos pela Oracle para o Simphony, definir GPO e padrao de rede por hotel (com apoio da 3WSI), validar tudo em um hotel piloto antes do rollout geral, e encerrar com documentacao (KB) e trilhas de treinamento para Suporte, Fiscal, Controladoria e configuracao avancada.

CRITERIO DE SUCESSO:
- 100% das workstations/tablets PDV identificados no GLPI com TAG PDV
- GPO e regras de firewall/Kaspersky aplicadas e validadas no piloto, depois replicadas em todas as unidades
- Antivirus reativado em todas as maquinas com excecoes corretas (sem ficar "temporariamente" desativado)
- KB "Simphony BASE" e "Erros Comuns Simphony" publicadas
- Trilhas de treinamento (Suporte, Fiscal, Controladoria, Avancado) entregues

ESCOPO:
- Esta dentro: inventario GLPI, rede/GPO/firewall/antivirus do PDV, documentacao e treinamentos
- Esta fora: mudancas no sistema Simphony em si (configuracoes de negocio do EMC fora do escopo de infraestrutura)
- Pode entrar depois (fase 2): expansao das trilhas de treinamento para outras areas, automacao de inventario"""

sess = req('GET', 'initSession')
st = sess['session_token']
r = req('PUT', 'Project/256', body={"input": {"id": 256, "content": content}}, st=st)
print(r)
req('GET', 'killSession', st=st)

from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

BACKLOG = 11
F22 = 2745
F23 = 2746

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

print("F2.2 filhas")
create_task(
    "F2.2.1 - Validar se as workstations precisam ser dedicadas ao uso exclusivo de PDV",
    "Verificar com a Oracle se as workstations do PDV precisam ser de uso exclusivo "
    "(sem outros aplicativos/usos) ou se podem ser compartilhadas com outras funcoes.",
    F22, st)

create_task(
    "F2.2.2 - Validar com a gestao a tratativa sobre o uso exclusivo do PDV",
    "Com base na resposta da Oracle, alinhar com a gestao se o uso exclusivo das "
    "workstations PDV e viavel operacionalmente e como sera tratado (politica, comunicacao).",
    F22, st)

print("F2.3 filhas")
create_task(
    "F2.3.1 - Levantamento de informacoes com fornecedor e manuais",
    "Levantar com o fornecedor do Kaspersky (e manuais oficiais) as configuracoes "
    "necessarias para liberar as portas exigidas pelo Simphony PDV.",
    F23, st)

create_task(
    "F2.3.2 - Parametrizacao do console",
    "Parametrizar no console do Kaspersky as regras/excecoes levantadas em F2.3.1 "
    "para as workstations do PDV.",
    F23, st)

create_task(
    "F2.3.3 - Testes e POC",
    "Executar prova de conceito validando que as regras parametrizadas no Kaspersky "
    "liberam as portas necessarias sem comprometer a protecao das workstations PDV.",
    F23, st)

req('GET', 'killSession', st=st)

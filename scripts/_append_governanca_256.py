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

GOVERNANCA = """

GOVERNANCA:
- Nomenclatura: todas as tarefas usam o padrao "[POS/Simphony] F{fase}.{item} - Acao", facilitando busca e relatorios.
- Tags: tarefas deste projeto devem usar a etiqueta "Planejado" (trabalho de engenharia/evolucao), em contraste com "Break-Fix" (usada em chamados/incidentes pontuais do PDV, fora deste projeto). Tarefas travadas por dependencia externa (Oracle, Kaspersky, 3WSI) devem receber a etiqueta "Blocked".
- Marcos de aprovacao (is_milestone=1) na Fase 4/5: "F4.G1 - Homologacao Concluida" (pos-validacao do piloto), "F4.G2 - Rollout Realizado" (pos-rollout em todas as unidades) e "F5.G1 - Operacao Assistida" (acompanhamento pos-rollout antes do encerramento).
- Definition of Done: tarefas-folha so devem ser fechadas com evidencia anexada no checklist do "content" (print/log/documento conforme o tipo da tarefa), nao apenas marcadas como concluidas."""

sess = req('GET', 'initSession')
st = sess['session_token']

p = req('GET', 'Project/256', st=st)
content = p.get('content') or ''
if 'GOVERNANCA:' in content:
    print("Secao GOVERNANCA ja existe, nada a fazer.")
else:
    new_content = content + GOVERNANCA
    r = req('PUT', 'Project/256', body={"input": {"id": 256, "content": new_content}}, st=st)
    print(r)

req('GET', 'killSession', st=st)

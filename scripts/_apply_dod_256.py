from _env import *
import json, re, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

PROJECT_256_TASK_IDS = [
    2740, 2741, 2742, 2743, 2744, 2745, 2746, 2747, 2748, 2749, 2750,
    2751, 2752, 2753, 2754, 2756, 2757, 2759, 2760, 2761, 2762, 2763,
    2764, 2765, 2766, 2767, 2768, 2769, 2770, 2771, 2772, 2773, 2774,
    2775, 2776, 2777, 2778,
]

PHASE_RE = re.compile(r'F(\d+)')

DOD_BY_PHASE = {
    '1': "[ ] Anexar evidencia (print/export do GLPI ou log) confirmando a execucao\n[ ] Responsavel e data registrados",
    '2': "[ ] Anexar evidencia (print/export do GLPI ou log) confirmando a execucao\n[ ] Responsavel e data registrados",
    '3': "[ ] Documento de definicao aprovado anexado\n[ ] Validacao registrada com o responsavel",
    '4': "[ ] Log/print do teste funcional anexado\n[ ] Horario e responsavel da execucao registrados",
    '5': "[ ] Artigo de KB publicado / trilha disponibilizada\n[ ] Link do artigo/trilha anexado",
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

sess = req('GET', 'initSession')
st = sess['session_token']

tasks = {}
for tid in PROJECT_256_TASK_IDS:
    t = req('GET', f'ProjectTask/{tid}', st=st)
    if isinstance(t, dict) and 'id' in t:
        tasks[tid] = t

parent_ids = {t.get('projecttasks_id') for t in tasks.values() if t.get('projecttasks_id')}

for tid, t in tasks.items():
    if t.get('is_milestone') == 1:
        continue
    if tid in parent_ids:
        continue  # tarefa-container (tem filhos), nao e folha
    content = t.get('content') or ''
    if '[ ]' in content or '[x]' in content.lower():
        print(f"[{tid}] ja tem checklist, pulando")
        continue
    m = PHASE_RE.search(t.get('name') or '')
    phase = m.group(1) if m else None
    dod = DOD_BY_PHASE.get(phase)
    if not dod:
        print(f"[{tid}] fase nao identificada, pulando: {t.get('name')}")
        continue
    new_content = f"{content}\n\nDEFINITION OF DONE:\n{dod}" if content else f"DEFINITION OF DONE:\n{dod}"
    r = req('PUT', f'ProjectTask/{tid}', body={"input": {"id": tid, "content": new_content}}, st=st)
    print(f"[{tid}] DoD adicionado: {r}")

req('GET', 'killSession', st=st)

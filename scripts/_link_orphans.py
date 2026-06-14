from _env import *
import json, urllib.request, os, sys

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

sess = req('GET', 'initSession')
st = sess['session_token']

assignments = {
    258: [20150, 27253, 27514, 27679, 27714, 27754, 27701],   # CMFlex Financeiro
    257: [27516, 27534, 27567, 27594, 27643, 27671, 27676,     # CMFlex BI & Dados
          24873, 26319, 26320, 26602, 27060, 27771],
    245: [27786, 27787, 27788, 27800, 27004],                  # Infraestrutura
    239: [27803, 27804],                                        # Impressoras
    237: [27802],                                               # Tablets
    236: [27778, 27780],                                        # Simphony Micros
    252: [27798],                                               # Opera R&A
}

PROBLEM_NAMES = {
    258: "CMFlex Financeiro",
    257: "CMFlex BI & Dados",
    245: "Infraestrutura de Rede",
    239: "Impressoras",
    237: "Tablets",
    236: "Simphony Micros",
    252: "Opera/Simphony R&A",
}

total_ok = 0
total_err = 0

for problem_id, tickets in assignments.items():
    print(f"\n--- Problem #{problem_id} ({PROBLEM_NAMES[problem_id]}) ---")
    for tid in tickets:
        body = {"input": {"problems_id": problem_id, "tickets_id": tid}}
        r = req('POST', 'Problem_Ticket', body=body, st=st)
        if r and 'id' in r:
            print(f"  OK  #{tid} -> #{problem_id} (link {r['id']})")
            total_ok += 1
        else:
            print(f"  ERR #{tid} -> #{problem_id}: {r}")
            total_err += 1

print(f"\nResultado: {total_ok} vinculados, {total_err} erros")
print("Orfaos por design (nao vinculados): #27572 (Acesso EMC), #27801 (Falha Acesso Windows)")

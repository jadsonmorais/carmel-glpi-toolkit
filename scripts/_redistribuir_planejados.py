import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from _env import *
import json, urllib.request, os
from datetime import date, timedelta

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

JADSON = 316
JA_TRATADOS = {27956, 27814, 27832, 27866, 27936, 27812, 27899, 27910, 27898}

# Buscar tickets com status=3 (Planejado)
r = req('GET',
    "search/Ticket"
    "?criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]=3"
    "&forcedisplay[0]=1&forcedisplay[1]=3"
    "&range=0-100", st=st)

planned = []
if r and 'data' in r:
    for t in r['data']:
        # campo 1 = ID do ticket
        tid_raw = t.get('1')
        try:
            tid = int(tid_raw)
            if tid not in JA_TRATADOS:
                planned.append(tid)
        except (TypeError, ValueError):
            pass

print(f"Tickets planejados para redistribuir ({len(planned)}): {planned}")

dia = date(2026, 6, 10)
for tid in sorted(planned):
    data_str = dia.strftime("%Y-%m-%d")
    r = req('POST', 'TicketTask', body={"input": {
        "tickets_id": tid,
        "content": f"Atendimento planejado para {data_str}.",
        "begin": f"{data_str} 08:00:00",
        "end":   f"{data_str} 09:00:00",
        "state": 1,
        "users_id_tech": JADSON,
    }}, st=st)
    ok = r and 'id' in r
    print(f"{'OK' if ok else 'ERR'}  #{tid} -> {data_str}")
    dia += timedelta(days=1)

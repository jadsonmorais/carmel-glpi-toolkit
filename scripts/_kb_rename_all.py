import sys, io, re, html
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

KCS_CATS = {50: 'BEC', 51: 'IDT', 52: 'SDC', 53: 'SDV', 54: 'MAN', 55: 'DTS'}

# Busca todos os vinculos
all_links = req('GET', 'KnowbaseItem_KnowbaseItemCategory?range=0-9999', st=st)

# Agrupa artigos por categoria KCS
by_cat = {}
for l in all_links:
    cat_id = l['knowbaseitemcategories_id']
    if cat_id in KCS_CATS:
        prefix = KCS_CATS[cat_id]
        by_cat.setdefault(prefix, set()).add(l['knowbaseitems_id'])

# Padrão correto: PREFIX-XXXX (com ou sem " - Titulo")
PATTERN = re.compile(r'^(BEC|DTS|IDT|MAN|SDC|SDV)-\d{4}(\s+-\s+|\s+|$)')

# Próximos números disponíveis (baseado na padronização anterior)
next_num = {'BEC': 15, 'DTS': 11, 'IDT': 46, 'MAN': 42, 'SDC': 4, 'SDV': 5}

ok = err = 0

for prefix in ['BEC', 'DTS', 'IDT', 'MAN', 'SDC', 'SDV']:
    article_ids = sorted(by_cat.get(prefix, []))
    out_of_pattern = []

    for aid in article_ids:
        a = req('GET', f'KnowbaseItem/{aid}', st=st)
        name = html.unescape(a.get('name', '') if isinstance(a, dict) else '')
        if not PATTERN.match(name):
            out_of_pattern.append((aid, name))

    if not out_of_pattern:
        print(f"[{prefix}] todos OK")
        continue

    print(f"\n[{prefix}] {len(out_of_pattern)} para renomear:")
    for aid, name in out_of_pattern:
        new_name = f"{prefix}-{next_num[prefix]:04d} - {name.strip()}"
        r = req('PUT', f'KnowbaseItem/{aid}', body={"input": {"id": aid, "name": new_name}}, st=st)
        success = isinstance(r, list) and r[0].get(str(aid))
        if success: ok += 1
        else: err += 1
        print(f"  {'OK ' if success else 'ERR'} #{aid} -> {new_name[:85]}")
        if success:
            next_num[prefix] += 1

print(f"\n=== RESULTADO: {ok} OK | {err} erros ===")
print(f"Proximos numeros: { {k: f'{k}-{v:04d}' for k, v in next_num.items()} }")

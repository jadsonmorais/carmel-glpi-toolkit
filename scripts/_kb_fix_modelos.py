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

ok = err = 0

def rename(aid, new_name):
    global ok, err
    r = req('PUT', f'KnowbaseItem/{aid}', body={"input": {"id": aid, "name": new_name}}, st=st)
    success = isinstance(r, list) and r[0].get(str(aid))
    if success: ok += 1
    else: err += 1
    print(f"  {'OK ' if success else 'ERR'} RENAME #{aid} -> {new_name}")

def remove_cat(aid, cat_id, label):
    global ok, err
    all_links = req('GET', 'KnowbaseItem_KnowbaseItemCategory?range=0-9999', st=st)
    link_id = next((l['id'] for l in all_links
                    if l['knowbaseitems_id'] == aid and l['knowbaseitemcategories_id'] == cat_id), None)
    if not link_id:
        print(f"  --- SKIP remove #{aid} de {label} (link nao encontrado)")
        return
    r = req('DELETE', f'KnowbaseItem_KnowbaseItemCategory/{link_id}', st=st)
    success = isinstance(r, list) and r[0].get(str(link_id))
    if success: ok += 1
    else: err += 1
    print(f"  {'OK ' if success else 'ERR'} REMOVE_CAT #{aid} de {label} (link {link_id})")

# #90: renomear MAN-0002 → MAN-0000 (template de estrutura)
print("=== #90 — Template HTML MAN ===")
rename(90, "MAN-0000 - Modelo de Estrutura de Artigo")

# #94: já é BEC-0000, mas está vinculado também à MAN — remover de MAN
print("\n=== #94 — Modelo BEC (remover de MAN) ===")
rename(94, "BEC-0000 - Modelo BEC")
remove_cat(94, 54, 'MAN')  # cat_id 54 = MAN

# #181: corrigir título duplicado "MAN-0089 - MAN - 0023 - Credenciais..."
print("\n=== #181 — Corrigir titulo duplicado ===")
rename(181, "MAN-0089 - Credenciais de acesso ao banco Qualyteam")

# #256: limpar colchetes do título
print("\n=== #256 — Limpar colchetes ===")
rename(256, "BEC-0017 - Modelo - Problema Opera Check-in Resolvido")

print(f"\n=== RESULTADO: {ok} OK | {err} erros ===")

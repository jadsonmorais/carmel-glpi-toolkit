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

CAT_IDS = {'BEC': 50, 'IDT': 51, 'SDC': 52, 'SDV': 53, 'MAN': 54, 'DTS': 55}
ok = 0
err = 0

def rename(article_id, new_name):
    global ok, err
    r = req('PUT', f'KnowbaseItem/{article_id}', body={"input": {"id": article_id, "name": new_name}}, st=st)
    success = isinstance(r, list) and r[0].get(str(article_id))
    if success: ok += 1
    else: err += 1
    print(f"  {'OK ' if success else 'ERR'} RENAME #{article_id} -> {new_name[:75]}")

def add_cat(article_id, cat):
    global ok, err
    body = {"input": {"knowbaseitems_id": article_id, "knowbaseitemcategories_id": CAT_IDS[cat]}}
    r = req('POST', 'KnowbaseItem_KnowbaseItemCategory', body=body, st=st)
    success = r and 'id' in r
    if success: ok += 1
    else: err += 1
    print(f"  {'OK ' if success else 'ERR'} CAT #{article_id} -> {cat}  {r if not success else ''}")

# =============================================================
# ETAPA 1 — Renumerar duplicados antes de vincular
# =============================================================
print("=== ETAPA 1: Renumerar duplicados ===")
rename(17,  "IDT-0044 - Liberando acesso de usuário a outras empresas no Simphony")
rename(40,  "MAN-0039 - Manual de Funcionamento Micros Simphony R&A")
rename(59,  "MAN-0040 - Operadora Net2Phone - Charme")
rename(80,  "IDT-0045 - Mapeamento de pastas do servidor")
rename(219, "MAN-0041 - Familias de MACs de Babas Eletronicas - Liberadas na Zoox")

# =============================================================
# ETAPA 2 — Vincular à categoria MAN
# =============================================================
print("\n=== ETAPA 2: MAN ===")
man_ids = [
    2, 7, 11, 16, 19, 22, 23, 34, 37, 38, 39, 40, 52, 56, 57, 59, 67, 73, 74,
    75, 76, 83, 84, 86, 87, 88, 89, 95, 116, 120, 123, 127, 128, 131, 132, 134,
    135, 137, 140, 143, 149, 159, 170, 171, 172, 175, 176, 177, 178, 185, 187,
    188, 189, 195, 201, 202, 209, 212, 214, 219, 220, 223, 224, 225, 226, 229,
    230, 231, 234, 236, 239, 240, 241, 242, 251, 252, 255
]
for aid in man_ids:
    add_cat(aid, 'MAN')

# =============================================================
# ETAPA 3 — Vincular à categoria IDT
# =============================================================
print("\n=== ETAPA 3: IDT ===")
idt_ids = [
    9, 17, 21, 47, 48, 49, 53, 55, 69, 77, 80, 82, 109, 112, 130, 186,
    192, 196, 198, 215, 217, 218, 235, 250, 253, 258
]
for aid in idt_ids:
    add_cat(aid, 'IDT')

# =============================================================
# ETAPA 4 — Vincular à categoria DTS
# =============================================================
print("\n=== ETAPA 4: DTS ===")
dts_ids = [12, 14, 60, 228, 232, 245, 246, 247, 248]
for aid in dts_ids:
    add_cat(aid, 'DTS')

# =============================================================
# ETAPA 5 — Vincular à categoria BEC
# =============================================================
print("\n=== ETAPA 5: BEC ===")
bec_ids = [20, 29, 256]
for aid in bec_ids:
    add_cat(aid, 'BEC')

print(f"\n=== RESULTADO FINAL: {ok} OK | {err} erros ===")

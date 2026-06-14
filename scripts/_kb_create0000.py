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
ok = err = 0

def rename(aid, new_name):
    global ok, err
    r = req('PUT', f'KnowbaseItem/{aid}', body={"input": {"id": aid, "name": new_name}}, st=st)
    success = isinstance(r, list) and r[0].get(str(aid))
    if success: ok += 1
    else: err += 1
    print(f"  {'OK ' if success else 'ERR'} RENAME #{aid} -> {new_name}")

def create_and_link(name, content, cat):
    global ok, err
    r = req('POST', 'KnowbaseItem', body={"input": {"name": name, "answer": content, "is_faq": 0}}, st=st)
    if not r or 'id' not in r:
        err += 1
        print(f"  ERR CREATE {name}: {r}")
        return
    aid = r['id']
    ok += 1
    print(f"  OK  CREATE #{aid} -> {name}")
    link = req('POST', 'KnowbaseItem_KnowbaseItemCategory',
               body={"input": {"knowbaseitems_id": aid, "knowbaseitemcategories_id": CAT_IDS[cat]}}, st=st)
    if link and 'id' in link:
        ok += 1
        print(f"  OK  LINK #{aid} -> {cat}")
    else:
        err += 1
        print(f"  ERR LINK #{aid} -> {cat}: {link}")

# ============================================================
# 1. Renumerar IDT-0000 real (#41) para IDT-0070
# ============================================================
print("=== Renumerar IDT-0000 real (#41) -> IDT-0070 ===")
rename(41, "IDT-0070 - Ativacao de conta do Ambiente e-learning Opera Cloud")

# ============================================================
# 2. Criar templates 0000 para IDT, DTS, SDC, SDV
# ============================================================
templates = {
    'IDT': (
        "IDT-0000 - Modelo IDT",
        "<h2>Objetivo</h2><p>[Descreva o objetivo da instrucao de trabalho]</p>"
        "<h2>Pre-requisitos</h2><p>[Liste o que e necessario antes de iniciar]</p>"
        "<h2>Passo a Passo</h2><ol><li>[Passo 1]</li><li>[Passo 2]</li><li>[Passo N]</li></ol>"
        "<h2>Resultado Esperado</h2><p>[Descreva o resultado apos seguir os passos]</p>"
        "<h2>Observacoes</h2><p>[Informacoes adicionais, atencao, cuidados]</p>"
    ),
    'DTS': (
        "DTS-0000 - Modelo DTS",
        "<h2>Descricao do Servico</h2><p>[Descreva o servico ou sistema documentado]</p>"
        "<h2>Arquitetura / Topologia</h2><p>[Diagrama ou descricao da arquitetura]</p>"
        "<h2>Configuracoes e Parametros</h2><p>[Detalhe as configuracoes relevantes]</p>"
        "<h2>Procedimentos de Manutencao</h2><p>[Rotinas, backups, atualizacoes]</p>"
        "<h2>Referencias</h2><p>[Links, documentos, contatos do fornecedor]</p>"
    ),
    'SDC': (
        "SDC-0000 - Modelo SDC",
        "<h2>Erro / Sintoma</h2><p>[Descreva o erro ou sintoma observado]</p>"
        "<h2>Causa Identificada</h2><p>[Explique a causa do problema, se conhecida]</p>"
        "<h2>Saida de Contorno</h2><p>[Passos para contornar o problema temporariamente]</p>"
        "<h2>Impacto e Limitacoes</h2><p>[Descreva o impacto desta solucao de contorno]</p>"
        "<h2>BEC Relacionado</h2><p>[Referencia ao BEC correspondente, se houver]</p>"
    ),
    'SDV': (
        "SDV-0000 - Modelo SDV",
        "<h2>Erro / Sintoma</h2><p>[Descreva o erro ou sintoma observado]</p>"
        "<h2>Causa Raiz</h2><p>[Explique a causa raiz identificada]</p>"
        "<h2>Solucao Definitiva</h2><p>[Passos para resolver o problema de forma definitiva]</p>"
        "<h2>Validacao</h2><p>[Como confirmar que o problema foi resolvido]</p>"
        "<h2>BEC / SDC Relacionado</h2><p>[Referencia ao BEC ou SDC correspondente, se houver]</p>"
    ),
}

print("\n=== Criar templates 0000 ===")
for cat, (name, content) in templates.items():
    create_and_link(name, content, cat)

print(f"\n=== RESULTADO: {ok} OK | {err} erros ===")

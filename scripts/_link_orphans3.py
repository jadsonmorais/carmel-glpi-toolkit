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

# ============================================================
# 1. Criar Problem: Integração Simphony → CMFlex Fiscal
# ============================================================
print("=== Criar Problem: Integracao Simphony -> CMFlex Fiscal ===")
p_integ = req('POST', 'Problem', body={"input": {
    "name": "Simphony x CMFlex - Falha na integracao de comandas com o modulo Fiscal",
    "itilcategories_id": 156,  # CMFlex > Fiscal
    "status": 2,
    "urgency": 4,
    "impact": 4,
    "priority": 4,
    "entities_id": 1,
    "content": (
        "Comandas geradas no Simphony (PDV) nao sao integralizadas corretamente no modulo Fiscal "
        "do CMFlex. O problema ocorre de forma intermitente e resulta em lancamentos fiscais ausentes "
        "ou incompletos, exigindo correcao manual e impactando a apuracao de impostos e o fechamento fiscal."
    ),
    "symptomcontent": (
        "<p>Comandas fechadas no Simphony nao aparecem ou aparecem parcialmente no CMFlex Fiscal. "
        "Sintomas:</p><ul>"
        "<li>Comandas com status 'nao integralizada' no painel de integracao.</li>"
        "<li>Divergencia entre o faturamento do PDV (Simphony) e os lancamentos fiscais (CMFlex).</li>"
        "<li>Necessidade de conciliacao manual periodica entre os dois sistemas.</li>"
        "</ul>"
    ),
    "causecontent": (
        "<p>Falha na camada de integracao entre Simphony e CMFlex (Integra Front). "
        "Possiveis causas: timeout na comunicacao entre os sistemas, rejeicao de registros por "
        "inconsistencia de parametros fiscais, ou falha silenciosa no servico de integracao sem "
        "reprocessamento automatico. A causa raiz envolve tanto configuracao local quanto comportamento "
        "do fornecedor (Sankhya/Oracle).</p>"
    ),
    "impactcontent": (
        "<p>Impacto direto na area Fiscal e Controladoria:</p><ul>"
        "<li>Lancamentos fiscais incompletos aumentam risco de inconsistencia na apuracao de impostos.</li>"
        "<li>Fechamento fiscal do periodo requer conciliacao manual, gerando retrabalho.</li>"
        "<li>Em casos criticos, pode haver subnotificacao de receita no SPED Fiscal.</li>"
        "</ul>"
    ),
}}, st=st)

if p_integ and 'id' in p_integ:
    pid_integ = p_integ['id']
    print(f"OK  Problem #{pid_integ} criado")
    req('POST', 'Problem_User', body={"input": {"problems_id": pid_integ, "users_id": 316, "type": 2}}, st=st)
    # Vincular #27839
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": pid_integ, "tickets_id": 27839}}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR'}  #27839 -> Problem #{pid_integ}")
else:
    print(f"ERR Problem integracao: {p_integ}")

# ============================================================
# 2. Vincular Simphony instabilidade -> Problem #236
# ============================================================
print("\n=== Vincular Simphony instabilidade -> Problem #236 ===")
for tid in [27836, 27837, 27846]:
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": 236, "tickets_id": tid}}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR'}  #{tid} -> Problem #236")

# ============================================================
# 3. Etiqueta Acessos (ID 235) para chamados de acesso/senha Opera
# ============================================================
print("\n=== Etiqueta Acessos -> Opera ===")
for tid in [27830, 27833, 27835, 27844]:
    r = req('POST', 'PluginTagTagItem', body={"input": {
        "plugin_tag_tags_id": 235,
        "itemtype": "Ticket",
        "items_id": tid,
    }}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR (já tem ou erro)'}  #{tid} -> tag Acessos: {'' if r and 'id' in r else r}")

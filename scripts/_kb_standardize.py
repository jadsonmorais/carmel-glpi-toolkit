import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from _env import *
import json, urllib.request, os, html

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
CAT_IDS  = {v: k for k, v in KCS_CATS.items()}

# Busca todos os vinculos para ter os IDs de link
all_links = req('GET', 'KnowbaseItem_KnowbaseItemCategory?range=0-9999', st=st)
# link_map: (article_id, cat_id) -> link_id
link_map = {(l['knowbaseitems_id'], l['knowbaseitemcategories_id']): l['id'] for l in all_links}

ok = 0
err = 0

def rename(article_id, new_name):
    global ok, err
    r = req('PUT', f'KnowbaseItem/{article_id}', body={"input": {"id": article_id, "name": new_name}}, st=st)
    success = isinstance(r, list) and r[0].get(str(article_id))
    status = "OK " if success else "ERR"
    if success: ok += 1
    else: err += 1
    print(f"  {status} RENAME #{article_id} -> {new_name[:80]}")

def remove_cat_link(article_id, cat_prefix):
    global ok, err
    cat_id = CAT_IDS[cat_prefix]
    link_id = link_map.get((article_id, cat_id))
    if not link_id:
        print(f"  --- SKIP remove_link #{article_id} de {cat_prefix} (link nao encontrado)")
        return
    r = req('DELETE', f'KnowbaseItem_KnowbaseItemCategory/{link_id}', st=st)
    success = isinstance(r, list) and r[0].get(str(link_id))
    status = "OK " if success else "ERR"
    if success: ok += 1
    else: err += 1
    print(f"  {status} REMOVE_CAT #{article_id} de {cat_prefix} (link {link_id})")

def add_cat_link(article_id, cat_prefix):
    global ok, err
    cat_id = CAT_IDS[cat_prefix]
    body = {"input": {"knowbaseitems_id": article_id, "knowbaseitemcategories_id": cat_id}}
    r = req('POST', 'KnowbaseItem_KnowbaseItemCategory', body=body, st=st)
    success = r and 'id' in r
    status = "OK " if success else "ERR"
    if success: ok += 1
    else: err += 1
    print(f"  {status} ADD_CAT #{article_id} em {cat_prefix}")

# =========================================================
# BEC — correcoes
# =========================================================
print("\n=== BEC ===")
rename(105, "BEC-0006 - Erro de banco de dados de segurança no servidor")  # remover espaço inicial
rename(210, "BEC-0014 - Remoção de Limite de Credito para Faturamento")

# =========================================================
# SDC — remover espaços iniciais
# =========================================================
print("\n=== SDC ===")
rename(106, "SDC-0002 - Saída contorno - Erro de banco de dados de segurança no servidor")
rename(151, "SDC-0003 - Saída contorno - Erro Saldo da conta excede o limite de créditos da conta")

# =========================================================
# DTS — remover vínculos errados e numerar sem prefixo
# =========================================================
print("\n=== DTS — remover vinculos errados ===")
remove_cat_link(156, 'DTS')   # é IDT, remove de DTS
remove_cat_link(160, 'DTS')   # é MAN, remove de DTS
remove_cat_link(181, 'DTS')   # é MAN, remove de DTS
remove_cat_link(182, 'MAN')   # é DTS, remove de MAN

print("\n=== DTS — numerar artigos sem prefixo ===")
rename(161, "DTS-0001 - Credencial admin Software VisionLine - Taiba")
rename(166, "DTS-0005 - Links do AppSheet Resorts")
rename(182, "DTS-0006 - Telefonia Taiba - Documentação")
rename(221, "DTS-0007 - Termo de descarte e doação de dispositivos eletrônicos")
rename(238, "DTS-0008 - Documentação de Configuração: Centralização de Numeração NFC-e (Harmony)")
rename(244, "DTS-0009 - Habilitar VNC para acesso remoto dos Raspberries")
rename(259, "DTS-0010 - Fortigate - Monitoramento de Link de Internet")

# =========================================================
# IDT — numerar artigos sem prefixo
# =========================================================
print("\n=== IDT — numerar artigos sem prefixo ===")
rename(156, "IDT-0039 - Atualização da senha Opera na interface")
rename(227, "IDT-0040 - Hack da OI para canais")
rename(237, "IDT-0041 - Ajuste de Sequence no Postgres")
rename(243, "IDT-0042 - Onity Onportal - Manual de Instalação")
rename(254, "IDT-0043 - Como cadastrar o Caixa para novo usuario no Opera Cloud")

# =========================================================
# MAN — corrigir duplicatas e numerar sem prefixo
# =========================================================
print("\n=== MAN — corrigir duplicatas de numero ===")
# MAN-0010 duplicado: #111 (original) fica, #138 recebe novo numero
rename(138, "MAN-0029 - Transição Opera Cloud Native")
# MAN-0022 duplicado: #157 (original) fica, #160 recebe novo numero
rename(160, "MAN-0031 - Como verificar gravações nas câmeras do hotel")
# MAN-0023 duplicado: #181 (original) fica, #183 recebe novo numero
rename(183, "MAN-0034 - Software de gerenciamento do Nobreak APC")

print("\n=== MAN — numerar artigos sem prefixo ===")
rename(103, "MAN-0027 - Credenciais de acesso ao VSphere - VMs dos Tablets (Taiba, Charme, Wind, Magna)")
rename(133, "MAN-0028 - E-mail de acesso aos aplicativos AppSheet e Power BI Qualidade")
rename(141, "MAN-0030 - Senhas do Applock dos tablets")
rename(163, "MAN-0032 - Manual de definições das tabelas - Opera R&A")
rename(174, "MAN-0033 - Acesso ao GoDaddy - Contrato do domínio carmelhoteis.com")
rename(193, "MAN-0035 - Planilha de Controle de Licenças do E-mail Google")
rename(203, "MAN-0036 - Instalação Questor")
rename(222, "MAN-0037 - Script para reiniciar o PDV do Simphony")
rename(249, "MAN-0038 - Documentação do Script de conversão de cupons NFC-e para PDF")

print(f"\n=== RESULTADO: {ok} OK | {err} erros ===")

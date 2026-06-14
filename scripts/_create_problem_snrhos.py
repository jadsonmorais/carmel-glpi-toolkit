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

JADSON = 157

p = req('POST', 'Problem', body={"input": {
    "name": "OFIS/FLIP - Falha na geracao do payload JSON para a API SNRHOS no checkout",
    "itilcategories_id": 156,  # Fiscal
    "status": 2,  # Em andamento
    "urgency": 4, "impact": 4, "priority": 4,
    "entities_id": 1,
    "content": (
        "O template XSLT FLIPTemplateSNRHOS_v2.xslt, responsavel por transformar o Business Event "
        "de CHECK OUT do OPERA Cloud em payload JSON para a API SNRHOS (sistema fiscal), nao esta "
        "gerando o JSON no formato esperado pela API. Como consequencia, o SNRHOS responde em ~115ms "
        "sem retornar um numero de documento fiscal valido, o OFIS chama UpdateFiscalBEStatusRQ com "
        "TransactionIdentifiers vazio e o OPERA retorna OPERAWS-CPI01010. Impacto imediato: ~5 "
        "reservas com checkout realizado nao tiveram o registro fiscal emitido."
    ),
    "symptomcontent": (
        "<p>Fluxo afetado: <strong>OPERA Cloud → OFIS (FLIP) → Saxon (XSLT) → JSON → SNRHOS → UpdateFiscalBEStatusRQ → OPERA</strong></p>"
        "<ul>"
        "<li>SNRHOS responde em ~115ms (rapido demais para processar emissao fiscal real)</li>"
        "<li>OFIS nao recebe numero de documento fiscal valido do SNRHOS</li>"
        "<li>UpdateFiscalBEStatusRQ chamado com TransactionIdentifiers nulo/vazio</li>"
        "<li>OPERA retorna: <code>OPERAWS-CPI01010: Invalid request, Transaction Identifiers is null or empty.</code></li>"
        "<li>OFIS tenta retry e recebe o mesmo erro</li>"
        "</ul>"
        "<p>Hotel afetado: Magna Praia (MAGNA). Aproximadamente 5 reservas com checkout nao registradas fiscalmente.</p>"
    ),
    "causecontent": (
        "<p>O template XSLT gera um JSON com estrutura incorreta ou com campos obrigatorios ausentes para a API SNRHOS. "
        "Causas identificadas na analise do XSLT:</p>"
        "<ol>"
        "<li><strong>Campo <code>tipo_nacionalidade_id</code> ausente no JSON de saida</strong>: "
        "a variavel <code>$tipoNacionalidadeId</code> e calculada no XSLT mas nunca emitida no "
        "<code>&lt;map&gt;</code> do hospede principal. Se o campo e obrigatorio na API SNRHOS, "
        "a requisicao falha silenciosamente.</li>"
        "<li><strong>Fallback de documento incorreto</strong>: "
        "<code>fn:exists($cpf)</code> retorna <code>true</code> mesmo para string vazia. "
        "Se CPF nao preenchido, <code>numero_documento</code> fica vazio em vez de usar <code>ID NUMBER</code>.</li>"
        "<li><strong>Campo <code>PaisNacionalidade_id</code> com fonte diferente</strong> entre hospede principal "
        "(usa <code>NATIONALITY CODE</code>) e acompanhantes (usa <code>COUNTRY</code>).</li>"
        "</ol>"
        "<p>Contexto: o template foi alterado recentemente para corrigir o campo <code>numero_reserva</code> "
        "(de RESV NAME ID para CONFIRMATION NO) e duas falhas silenciosas do Saxon foram corrigidas "
        "(xsl:catch com namespace errado e xs:date() sem null guard). "
        "Porem o JSON gerado ainda nao atende o contrato da API SNRHOS.</p>"
    ),
    "impactcontent": (
        "<ul>"
        "<li><strong>Fiscal</strong>: checkouts nao geram registro fiscal no SNRHOS — risco de irregularidade na FNRH/SEFAZ para o hotel Magna Praia.</li>"
        "<li><strong>Operacional</strong>: ~5 reservas acumuladas com FAILURE. Precisam ser reprocessadas apos a correcao do XSLT.</li>"
        "<li><strong>OPERA</strong>: status fiscal das reservas nao atualizado — pode gerar inconsistencia em relatorios e auditorias.</li>"
        "<li><strong>Abrangencia potencial</strong>: todos os checkouts do Magna Praia estao afetados enquanto o problema nao for corrigido.</li>"
        "</ul>"
    ),
}}, st=st)

if p and 'id' in p:
    pid = p['id']
    print(f"OK  Problem #{pid} criado")
    # Atribuir Jadson
    req('POST', 'Problem_User', body={"input": {"problems_id": pid, "users_id": JADSON, "type": 2}}, st=st)
    # Vincular ticket #27937
    r = req('POST', 'Problem_Ticket', body={"input": {"problems_id": pid, "tickets_id": 27937}}, st=st)
    print(f"{'OK' if r and 'id' in r else 'ERR/dup'}  #27937 -> Problem #{pid}")
    print(f"\nProblem #{pid}: OFIS/FLIP SNRHOS payload — Magna Praia, ~5 reservas impactadas")
else:
    print(f"ERR: {p}")

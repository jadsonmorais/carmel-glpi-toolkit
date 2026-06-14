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

name = "IDT-0071 - Checklist de Inventario de Impressoras no GLPI"

content = """
<h2>Objetivo</h2>
<p>Registrar e padronizar todas as impressoras da rede (locadas ou pr&oacute;prias) no GLPI para controle de chamados, localiza&ccedil;&atilde;o e insumos.</p>

<h2>Pr&eacute;-requisitos</h2>
<ul>
  <li>Acesso ao GLPI com permiss&atilde;o de cadastro em Ativos &gt; Impressoras</li>
  <li>Etiquetas f&iacute;sicas de identifica&ccedil;&atilde;o dispon&iacute;veis</li>
  <li>Acesso f&iacute;sico ao equipamento</li>
  <li>Padr&atilde;o de nomenclatura definido (ex: MAGNA-IMP-01)</li>
</ul>

<h2>Passo a Passo</h2>

<h3>&#128295; Fase 1: Verifica&ccedil;&atilde;o F&iacute;sica e Conectividade</h3>
<ol>
  <li><strong>Coleta de Dados F&iacute;sicos:</strong> Identifique a marca, modelo e o N&uacute;mero de S&eacute;rie (S/N) real do equipamento.</li>
  <li><strong>Endere&ccedil;amento IP:</strong> Verifique se a impressora est&aacute; com IP est&aacute;tico (fixo) na rede e anote-o para o cadastro.</li>
  <li><strong>Etiquetagem F&iacute;sica:</strong> Cole a etiqueta com o nome padronizado do dispositivo em local de f&aacute;cil visualiza&ccedil;&atilde;o na impressora.</li>
  <li><strong>Valida&ccedil;&atilde;o de Setor (UH):</strong> Confirme fisicamente em qual UH/Setor a impressora est&aacute; instalada.</li>
</ol>

<h3>&#128187; Fase 2: Cadastro e Ajustes no GLPI</h3>
<p>Abra a aba <strong>Ativos &gt; Impressoras</strong> no GLPI.</p>
<ol start="5">
  <li><strong>Nome da Impressora:</strong> Siga o padr&atilde;o de nomenclatura definido.<br/>
      <em>Sugest&atilde;o: MAGNA-IMP-01, WIND-IMP-02, TAIBA-IMP-01</em></li>
  <li><strong>Tipo e Fabricante:</strong> Preencha os campos Fabricante (HP, Brother, Kyocera, etc.) e Modelo corretamente.</li>
  <li><strong>Localiza&ccedil;&atilde;o:</strong> Vincule &agrave; &aacute;rvore correta: <em>Hoteis &gt; Nome do Hotel</em> (Ex: Hoteis &gt; Carmel Cumbuco).</li>
  <li><strong>Campo UH (Setor) e Patrim&ocirc;nio:</strong> Preencha o setor f&iacute;sico e o n&uacute;mero do patrim&ocirc;nio nos campos correspondentes.</li>
  <li><strong>V&iacute;nculo de Rede:</strong> Adicione a porta de rede e o endere&ccedil;o IP correto para permitir testes de ping e acesso &agrave; p&aacute;gina web do equipamento.</li>
</ol>

<h3>&#128196; Fase 3: Suprimentos, Hist&oacute;rico e Fotos</h3>
<ol start="10">
  <li><strong>Contador Inicial (Notas):</strong> Tire um relat&oacute;rio de p&aacute;ginas da impressora e grave o contador atual no campo <strong>Notas</strong> como marco zero do invent&aacute;rio.</li>
  <li><strong>Associa&ccedil;&atilde;o de Consum&iacute;veis (Se aplic&aacute;vel):</strong> Vincule os cartuchos/toners corretos ao modelo da impressora no GLPI, se volumetria estiver ativa.</li>
  <li><strong>Imagem do Item:</strong> Tire uma foto da impressora no local de opera&ccedil;&atilde;o e anexe na aba <strong>Documentos</strong> do GLPI.</li>
  <li><strong>Termo / Contrato:</strong> Se locada (outsourcing): verifique se o contrato ou termo de responsabilidade est&aacute; associado. Se pr&oacute;pria: use a etiqueta <em>"Sem documento"</em>.</li>
</ol>

<h2>Resultado Esperado</h2>
<p>Impressora totalmente cadastrada no GLPI com: nome padronizado, localiza&ccedil;&atilde;o correta, IP vinculado, contador zero registrado em Notas, foto anexada e contrato/termo associado quando aplic&aacute;vel.</p>

<h2>Observa&ccedil;&otilde;es</h2>
<ul>
  <li>Confirmar com a equipe o padr&atilde;o final de nomenclatura (IMP ou PRNT no identificador) antes de iniciar o cadastro em massa.</li>
  <li>Este checklist pode ser mesclado com o fluxo de invent&aacute;rio de outros ativos (desktops, tablets) para gerar um documento unificado de onboarding de equipamentos.</li>
</ul>
""".strip()

r = req('POST', 'KnowbaseItem', body={"input": {"name": name, "answer": content, "is_faq": 0}}, st=st)
if r and 'id' in r:
    aid = r['id']
    print(f"OK  CREATE #{aid} -> {name}")
    link = req('POST', 'KnowbaseItem_KnowbaseItemCategory',
               body={"input": {"knowbaseitems_id": aid, "knowbaseitemcategories_id": 51}}, st=st)
    if link and 'id' in link:
        print(f"OK  LINK #{aid} -> IDT (cat 51)")
    else:
        print(f"ERR LINK: {link}")
else:
    print(f"ERR CREATE: {r}")

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

name = "IDT-0072 - Checklist de Inventario de Computadores no GLPI"

content = """
<h2>Objetivo</h2>
<p>Padronizar o cadastro e a verifica&ccedil;&atilde;o f&iacute;sica de computadores (desktops e notebooks) no GLPI, garantindo rastreabilidade, conformidade de seguran&ccedil;a e qualidade das informa&ccedil;&otilde;es de inventário.</p>

<h2>Pr&eacute;-requisitos</h2>
<ul>
  <li>Acesso ao GLPI com permiss&atilde;o de edi&ccedil;&atilde;o em Ativos &gt; Computadores</li>
  <li>Etiquetas f&iacute;sicas de identifica&ccedil;&atilde;o dispon&iacute;veis</li>
  <li>Acesso f&iacute;sico ao equipamento</li>
  <li>Termos de responsabilidade dispon&iacute;veis para associa&ccedil;&atilde;o</li>
  <li>Agent GLPI instalado no equipamento (para invent&aacute;rio autom&aacute;tico)</li>
</ul>

<h2>Passo a Passo</h2>

<h3>&#128272; Seguran&ccedil;a e Conformidade</h3>
<ol>
  <li>
    <strong>Antiv&iacute;rus:</strong> Verifique se o Kaspersky est&aacute; instalado e ativo.<br/>
    <ul>
      <li>Se sim: confirmar licen&ccedil;a ativa no painel Kaspersky Cloud.</li>
      <li>Se n&atilde;o h&aacute; licen&ccedil;as dispon&iacute;veis: instalar sem licen&ccedil;a e aplicar a etiqueta <strong>"Sem licen&ccedil;as - Kaspersky"</strong>.</li>
    </ul>
  </li>
  <li>
    <strong>Dom&iacute;nio:</strong> Verifique se a m&aacute;quina est&aacute; ingressada no dom&iacute;nio Active Directory do hotel correspondente.<br/>
    <em>Caminho: Painel de Controle &gt; Sistema &gt; Nome do Computador / Dom&iacute;nio.</em>
  </li>
</ol>

<h3>&#128204; Identifica&ccedil;&atilde;o e Localiza&ccedil;&atilde;o</h3>
<ol start="3">
  <li>
    <strong>Nome do Dispositivo:</strong> Confirme se o nome segue o padr&atilde;o definido:<br/>
    <ul>
      <li>MAGNA-COMERC-01 &mdash; uso departamental espec&iacute;fico</li>
      <li>WIND-55 / TAIBA-22 / CHARME-22 &mdash; identifica&ccedil;&atilde;o sequencial por hotel</li>
      <li>MAGNA-BACKUP-01 &mdash; equipamentos de reserva/backup</li>
    </ul>
    Se o nome estiver incorreto, renomear o computador e atualizar o cadastro no GLPI.
  </li>
  <li>
    <strong>Localiza&ccedil;&atilde;o no GLPI:</strong> Verifique se a localiza&ccedil;&atilde;o est&aacute; vinculada &agrave; &aacute;rvore correta:<br/>
    <em>Hoteis &gt; Nome do Hotel</em> (Ex: Hoteis &gt; Carmel Cumbuco).<br/>
    Confirmar f&iacute;sicamente o local onde o equipamento opera.
  </li>
  <li>
    <strong>Campo UH (Setor):</strong> Preencha o campo UH/Setor no GLPI com o setor f&iacute;sico real do equipamento.<br/>
    <em>Bater fisicamente para garantir a informa&ccedil;&atilde;o correta &mdash; n&atilde;o confiar apenas no cadastro anterior.</em>
  </li>
</ol>

<h3>&#127991;&#65039; Etiquetagem F&iacute;sica</h3>
<ol start="6">
  <li>
    <strong>Etiquetar o equipamento:</strong> Cole a etiqueta com o nome padronizado do dispositivo no gabinete (desktop) ou na tampa (notebook).<br/>
    Em caso de <strong>notebook</strong>: etiquetar tamb&eacute;m o <strong>carregador/fonte</strong> com o mesmo nome.
  </li>
</ol>

<h3>&#128196; Documenta&ccedil;&atilde;o e Patrim&ocirc;nio</h3>
<ol start="7">
  <li>
    <strong>Termo de Responsabilidade:</strong> Verifique se o termo est&aacute; associado ao item no GLPI (aba Documentos).<br/>
    <ul>
      <li>Se associado: confirmar que o usu&aacute;rio respons&aacute;vel est&aacute; correto.</li>
      <li>Se n&atilde;o associado: aplicar a etiqueta <strong>"Sem documento"</strong>.</li>
    </ul>
    Preencha o campo <strong>Patrim&ocirc;nio</strong> com o n&uacute;mero patrimonial do equipamento.
  </li>
  <li>
    <strong>Imagem do Item:</strong> Tire uma foto do equipamento no local de opera&ccedil;&atilde;o e anexe na aba <strong>Documentos</strong> do GLPI.
  </li>
</ol>

<h3>&#128221; Preenchimento de Campos no GLPI</h3>
<ol start="9">
  <li>
    <strong>Etiquetas (Tags):</strong> Utilize as etiquetas pr&eacute;-definidas para sinalizar situa&ccedil;&otilde;es especiais, sempre aliadas ao Status do item.<br/>
    Exemplos:
    <ul>
      <li><strong>"N&atilde;o localizado"</strong> &mdash; equipamento n&atilde;o encontrado fisicamente.</li>
      <li><strong>"Sem documento"</strong> &mdash; sem termo de responsabilidade.</li>
      <li><strong>"Sem licen&ccedil;as - Kaspersky"</strong> &mdash; antiv&iacute;rus sem licen&ccedil;a ativa.</li>
    </ul>
  </li>
  <li>
    <strong>Notas:</strong> Use o campo Notas para registrar informa&ccedil;&otilde;es que devem ficar gravadas historicamente (marcos de invent&aacute;rio, data da &uacute;ltima verifica&ccedil;&atilde;o, contador, etc.).<br/>
    Sempre incluir a data no registro: <em>[AAAA-MM-DD] Descri&ccedil;&atilde;o da ocorr&ecirc;ncia.</em>
  </li>
  <li>
    <strong>Coment&aacute;rio:</strong> Preencher <strong>somente em casos excepcionais</strong> que exijam detalhamento da situa&ccedil;&atilde;o do equipamento. N&atilde;o usar para informa&ccedil;&otilde;es rotineiras.
  </li>
  <li>
    <strong>Tipo do Computador:</strong> Ao realizar o primeiro invent&aacute;rio via Agent GLPI, altere o campo <strong>Tipo</strong> do valor padr&atilde;o "Computador" para o tipo correto (Desktop, Notebook, All-in-One, etc.).
  </li>
</ol>

<h2>Resultado Esperado</h2>
<p>Computador totalmente cadastrado no GLPI com: nome padronizado, localiza&ccedil;&atilde;o e setor corretos, dom&iacute;nio verificado, antiv&iacute;rus ativo (ou etiquetado), etiqueta f&iacute;sica aplicada, patrim&ocirc;nio preenchido, termo associado (ou etiquetado), foto anexada, notas de hist&oacute;rico iniciadas e tipo correto definido.</p>

<h2>Observa&ccedil;&otilde;es</h2>
<ul>
  <li>Este checklist deve ser executado no primeiro cadastro do equipamento e revisado a cada ciclo de invent&aacute;rio.</li>
  <li>Para impressoras, consultar <strong>IDT-0071</strong>. Para tablets, consultar o checklist espec&iacute;fico quando dispon&iacute;vel.</li>
  <li>Etiquetas f&iacute;sicas danificadas ou ausentes devem ser repostas imediatamente durante a visita.</li>
</ul>
""".strip()

r = req('POST', 'KnowbaseItem', body={"input": {"name": name, "answer": content, "is_faq": 0}}, st=st)
if r and 'id' in r:
    aid = r['id']
    print(f"OK  CREATE #{aid} -> {name}")
    link = req('POST', 'KnowbaseItem_KnowbaseItemCategory',
               body={"input": {"knowbaseitems_id": aid, "knowbaseitemcategories_id": 51}}, st=st)
    print(f"{'OK' if link and 'id' in link else 'ERR'}  LINK #{aid} -> IDT")
else:
    print(f"ERR CREATE: {r}")

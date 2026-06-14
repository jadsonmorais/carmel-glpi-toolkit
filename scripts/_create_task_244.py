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

# Verifica projeto 244
p = req('GET', 'Project/244', st=st)
print(f"Projeto #244: {p.get('name')} | Status: {p.get('projectstates_id')}")

content = """OBJETIVO: Registrar e padronizar todas as impressoras da rede (locadas ou proprias) no GLPI para controle de chamados, localizacao e insumos.

=== FASE 1: VERIFICACAO FISICA E CONECTIVIDADE ===

[ ] 1. Coleta de Dados Fisicos
Identifique a marca, modelo e o Numero de Serie (S/N) real do equipamento.

[ ] 2. Enderecamento IP
Verifique se a impressora esta com IP estatico (fixo) na rede e anote-o para o cadastro.

[ ] 3. Etiquetagem Fisica
Cole a etiqueta com o nome padronizado do dispositivo em um local de facil visualizacao na impressora.

[ ] 4. Validacao de Setor (UH)
Confirme fisicamente em qual UH/Setor a impressora esta instalada.

=== FASE 2: CADASTRO E AJUSTES NO GLPI ===
Abra: Ativos > Impressoras no GLPI.

[ ] 5. Nome da Impressora
Siga a padronizacao: MAGNA-IMP-01, WIND-IMP-02, TAIBA-IMP-01 (confirmar padrao com a equipe).

[ ] 6. Tipo e Fabricante
Garanta que os campos Fabricante (HP, Brother, Kyocera, etc.) e Modelo estejam preenchidos corretamente.

[ ] 7. Localizacao
Vincule a arvore correta: Hoteis > Nome do Hotel (Ex: Hoteis > Carmel Cumbuco).

[ ] 8. Campo UH (Setor) e Patrimonio
Preencha o setor fisico e o numero do patrimonio nos campos correspondentes.

[ ] 9. Vinculo de Rede
Adicione a porta de rede e o endereco IP correto para permitir testes de ping e acesso a pagina web do equipamento.

=== FASE 3: SUPRIMENTOS, HISTORICO E FOTOS ===

[ ] 10. Contador Inicial (Notas)
Tire relatorio de paginas da impressora e grave o contador atual no campo Notas como marco zero do inventario.

[ ] 11. Associacao de Consumiveis
Vincule os cartuchos/toners corretos ao modelo no GLPI, se volumetria estiver ativa.

[ ] 12. Imagem do Item
Tire uma foto da impressora no local de operacao e anexe na aba Documentos do GLPI.

[ ] 13. Termo / Contrato
Se locada (outsourcing): verifique se contrato ou termo de responsabilidade esta associado.
Se propria: use a etiqueta "Sem documento"."""

task_body = {
    "input": {
        "projects_id": 244,
        "name": "INV-01 Checklist de Inventario e Padronizacao de Impressoras no GLPI",
        "content": content,
        "plan_start_date": "2026-05-28",
        "plan_end_date": "2026-07-31",
        "projectstates_id": 1,
        "percent_done": 0,
    }
}

r = req('POST', 'ProjectTask', body=task_body, st=st)
if r and 'id' in r:
    print(f"Tarefa criada: ID {r['id']}")
    print(f"Acesse: {GLPI_BASE_URL}/front/project.form.php?id=244")
else:
    print(f"Erro: {r}")

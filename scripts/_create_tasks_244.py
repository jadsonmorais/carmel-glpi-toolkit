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

inv01_content = """OBJETIVO: Registrar e padronizar todas as impressoras da rede (locadas ou proprias) no GLPI para controle de chamados, localizacao e insumos.

CRITERIO DE SUCESSO: 100% das impressoras cadastradas no GLPI com IP, localizacao, setor e patrimonio preenchidos.

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

net_content = """OBJETIVO: Reduzir o volume recorrente de chamados de rede (Problem #245) por meio de manutencao preventiva e padronizacao da infraestrutura de rede fisica e logica nas unidades.

CRITERIO DE SUCESSO: Reducao mensuravel de chamados de conectividade/AP/switch por unidade apos a manutencao.

=== SUBTAREFA: Levantamento de Access Points e Switches ===
[ ] 1. Mapear todos os APs e switches por unidade (modelo, firmware, localizacao)
[ ] 2. Identificar equipamentos com falhas recorrentes (cruzar com chamados do Problem #245)
[ ] 3. Documentar topologia atual de cada unidade

=== SUBTAREFA: Reconfiguracao e Atualizacao de APs ===
[ ] 4. Atualizar firmware dos APs identificados
[ ] 5. Revisar configuracao de canais/SSID para evitar interferencia
[ ] 6. Validar cobertura de sinal nas areas com mais reclamacoes

=== SUBTAREFA: Manutencao de Switches e Cabeamento Estruturado ===
[ ] 7. Inspecionar e organizar racks (cabeamento, identificacao de portas)
[ ] 8. Substituir cabos/conectores danificados
[ ] 9. Revisar VLANs e portas com erro/loop

=== SUBTAREFA: Documentacao e Encerramento ===
[ ] 10. Atualizar diagramas de rede por unidade
[ ] 11. Vincular chamados orfaos do Problem #245 resolvidos a esta tarefa
[ ] 12. Reportar reducao de chamados ao requerente"""

mig_content = """OBJETIVO: Concluir a migracao e reconfiguracao dos servidores de aplicacao dos resorts da rede Carmel (Problem #264).

CONTEXTO: Carmel Taiba ja foi migrado (concluido). Wind e Charme estao programados. Jadson e Italo conduzem o planejamento e execucao.

CRITERIO DE SUCESSO: Wind e Charme migrados e validados sem regressao de servicos.

=== SUBTAREFA: Migracao Carmel Wind ===
Responsavel: Jadson / Italo
[ ] 1. Planejar janela de downtime com a unidade
[ ] 2. Preparar novo servidor/ambiente de destino
[ ] 3. Executar migracao dos servicos
[ ] 4. Reconfigurar integracoes e dependencias
[ ] 5. Validar servicos pos-migracao (checklist funcional)
[ ] 6. Comunicar conclusao a unidade

=== SUBTAREFA: Migracao Carmel Charme ===
Responsavel: Jadson / Italo
[ ] 7. Planejar janela de downtime com a unidade
[ ] 8. Preparar novo servidor/ambiente de destino
[ ] 9. Executar migracao dos servicos
[ ] 10. Reconfigurar integracoes e dependencias
[ ] 11. Validar servicos pos-migracao (checklist funcional)
[ ] 12. Comunicar conclusao a unidade

=== SUBTAREFA: Documentacao Final ===
[ ] 13. Atualizar runbook de migracao com licoes aprendidas (referencia para futuras unidades)
[ ] 14. Encerrar/atualizar chamados orfaos vinculados ao Problem #264"""

rhid_content = """OBJETIVO: Estabilizar a conectividade do sistema RHID para eliminar falhas no registro de ponto eletronico e operacoes de DP/RH (Problem #263).

CRITERIO DE SUCESSO: Ausencia de registros de ponto ausentes/incorretos por falha de conectividade nos horarios de pico.

=== SUBTAREFA: Diagnostico de Conectividade ===
[ ] 1. Mapear topologia de rede dos relogios de ponto RHID por unidade
[ ] 2. Monitorar latencia/queda de conexao nos horarios de pico (entrada/saida de turno)
[ ] 3. Identificar pontos de falha (link, switch, servidor RHID)

=== SUBTAREFA: Correcao de Infraestrutura ===
[ ] 4. Ajustar QoS/priorizacao de trafego do RHID nos horarios criticos
[ ] 5. Substituir/realocar equipamentos de rede com falha identificada
[ ] 6. Validar redundancia de link onde aplicavel

=== SUBTAREFA: Validacao com DP/RH ===
[ ] 7. Acompanhar 2 ciclos de batida de ponto em horario de pico pos-correcao
[ ] 8. Confirmar com DP/RH ausencia de registros incorretos/ausentes
[ ] 9. Vincular chamados orfaos do Problem #263 resolvidos a esta tarefa"""

tasks = [
    {
        "name": "INV-01 Checklist de Inventario e Padronizacao de Impressoras no GLPI",
        "content": inv01_content,
        "plan_start_date": "2026-06-15",
        "plan_end_date": "2026-08-31",
    },
    {
        "name": "NET-01 Manutencao e Padronizacao de Infraestrutura de Rede (Problem #245)",
        "content": net_content,
        "plan_start_date": "2026-06-15",
        "plan_end_date": "2026-09-30",
    },
    {
        "name": "MIG-01 Migracao de Servidores dos Resorts Wind e Charme (Problem #264)",
        "content": mig_content,
        "plan_start_date": "2026-06-15",
        "plan_end_date": "2026-10-31",
    },
    {
        "name": "RHID-01 Estabilizacao de Conectividade do Ponto Eletronico (Problem #263)",
        "content": rhid_content,
        "plan_start_date": "2026-06-15",
        "plan_end_date": "2026-08-31",
    },
]

for t in tasks:
    body = {
        "input": {
            "projects_id": 244,
            "name": t["name"],
            "content": t["content"],
            "plan_start_date": t["plan_start_date"],
            "plan_end_date": t["plan_end_date"],
            "projectstates_id": 1,
            "percent_done": 0,
        }
    }
    r = req('POST', 'ProjectTask', body=body, st=st)
    if r and 'id' in r:
        print(f"Criada: [{r['id']}] {t['name']}")
    else:
        print(f"Erro em '{t['name']}': {r}")

req('GET', 'killSession', st=st)

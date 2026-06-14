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

# Cria o projeto principal
project_body = {
    "input": {
        "name": "Reforma Tributaria - Adequacao de Sistemas e Processos",
        "content": (
            "Projeto de adequacao dos sistemas, processos e areas da Carmel Hoteis "
            "as novas regras da Reforma Tributaria (IBS/CBS/IS), com vigencia a partir de 2026. "
            "Envolve adaptacao fiscal de sistemas (CMFlex, Opera, Simphony, PDV), "
            "mapeamento de creditos na cadeia produtiva, revisao de contratos e precos, "
            "engajamento multidisciplinar e acompanhamento continuo da regulamentacao."
        ),
        "entities_id": 1,
        "is_recursive": 1,
        "projectstates_id": 1,   # Novo
        "projecttypes_id": 1,    # Estrategico
        "priority": 5,           # Muito urgente
        "plan_start_date": "2026-05-28",
        "plan_end_date": "2026-12-31",
        "percent_done": 0,
        "show_on_global_gantt": 1,
    }
}

project = req('POST', 'Project', body=project_body, st=st)
print(f"Projeto criado: {project}")

if not project or 'id' not in project:
    print("ERRO: projeto nao criado, abortando.")
    exit(1)

project_id = project['id']
print(f"ID do projeto: {project_id}")

# Tarefas do projeto
tasks = [
    {
        "name": "Adaptacao de Sistemas para Emissao de Documentos Fiscais 2026",
        "content": (
            "Levantar roadmap de adequacao de CMFlex/Sankhya, Oracle Opera e Simphony para "
            "os novos documentos fiscais (IBS/CBS/IS). Pressionar fornecedores por versao e data "
            "de entrega. Preparar ambiente de homologacao para testes antes da virada. "
            "Vincular aos problemas abertos #255 (CMFlex Fiscal) e #243 (PDV Harmony/SEFAZ)."
        ),
        "plan_start_date": "2026-05-28",
        "plan_end_date": "2026-09-30",
        "projectstates_id": 1,
        "percent_done": 0,
    },
    {
        "name": "Mapeamento de Creditos na Cadeia Produtiva",
        "content": (
            "Mapear quais insumos e servicos adquiridos pelos hoteis gerarao credito aproveitavel "
            "sob o regime IBS/CBS. Avaliar se os sistemas financeiros/fiscais (CMFlex) suportam "
            "classificacao por CNAE e regime tributario do fornecedor. Definir ajustes necessarios."
        ),
        "plan_start_date": "2026-06-01",
        "plan_end_date": "2026-08-31",
        "projectstates_id": 1,
        "percent_done": 0,
    },
    {
        "name": "Preparacao Operacional e Estrategica",
        "content": (
            "Analisar impactos da reforma em precos de diarias e pacotes, contratos com fornecedores "
            "e SLAs de servico. Revisar parametros de precificacao no Opera. Garantir que relatorios "
            "gerenciais (Power BI, CMFlex BI) reflitam a nova carga tributaria corretamente."
        ),
        "plan_start_date": "2026-06-01",
        "plan_end_date": "2026-10-31",
        "projectstates_id": 1,
        "percent_done": 0,
    },
    {
        "name": "Engajamento Multidisciplinar das Areas",
        "content": (
            "Constituir grupo de trabalho com pontos focais de: Contabil, Fiscal, Juridico, "
            "Financeiro, TI, Suprimentos, Operacoes, RH e Comercial. Definir responsaveis por "
            "sistema critico. Realizar reunioes periodicas de alinhamento e status."
        ),
        "plan_start_date": "2026-05-28",
        "plan_end_date": "2026-12-31",
        "projectstates_id": 1,
        "percent_done": 0,
    },
    {
        "name": "Acompanhamento da Regulamentacao e Novas Normas",
        "content": (
            "Monitorar publicacao de decretos, instrucoes normativas e regulamentacoes do IBS/CBS/IS. "
            "Avaliar impacto de cada nova norma nos sistemas e processos em andamento. "
            "Manter tabelas fiscais e configuracoes de sistema com flexibilidade para ajustes."
        ),
        "plan_start_date": "2026-05-28",
        "plan_end_date": "2026-12-31",
        "projectstates_id": 1,
        "percent_done": 0,
    },
]

print(f"\nCriando {len(tasks)} tarefas...")
for task in tasks:
    task_body = {"input": {**task, "projects_id": project_id}}
    r = req('POST', 'ProjectTask', body=task_body, st=st)
    if r and 'id' in r:
        print(f"  OK  Tarefa '{task['name'][:60]}' (ID {r['id']})")
    else:
        print(f"  ERR Tarefa '{task['name'][:60]}': {r}")

print(f"\nProjeto disponivel em: {GLPI_BASE_URL}/front/project.form.php?id={project_id}")

from _env import *
import json, urllib.request, os

creds = {
    'app_token': os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url': (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
}

BACKLOG = 11

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

def create_task(name, content="", parent=0, milestone=False, st=None):
    body = {
        "input": {
            "projects_id": 256,
            "projecttasks_id": parent,
            "name": name,
            "content": content,
            "projectstates_id": BACKLOG,
            "is_milestone": 1 if milestone else 0,
            "percent_done": 0,
        }
    }
    r = req('POST', 'ProjectTask', body=body, st=st)
    if r and 'id' in r:
        print(f"  [{r['id']}] {name}")
        return r['id']
    print(f"  ERRO em '{name}': {r}")
    return None

sess = req('GET', 'initSession')
st = sess['session_token']

# ============ FASE 1 - MITIGACAO ============
print("Fase 1 - Mitigacao")
f1 = create_task("Fase 1 - Mitigacao",
    "Coletar informacoes e determinar os padroes iniciais antes de qualquer mudanca estrutural.",
    milestone=True, st=st)

create_task(
    "1 - Verificar TAG PDV nas Workstations no GLPI",
    "Verificar se todas as Workstations do PDV estao cadastradas no GLPI e identificadas com a TAG PDV.",
    parent=f1, st=st)

create_task(
    "2 - Mitigacao rapida: desativar antivirus nas maquinas PDV",
    "Executar uma mitigacao rapida desativando o antivirus em todas as maquinas do PDV.",
    parent=f1, st=st)

# ============ FASE 2 - PREPARO ============
print("Fase 2 - Preparo")
f2 = create_task("Fase 2 - Preparo",
    "Levantamentos internos e junto a Oracle/Kaspersky necessarios antes da execucao.",
    milestone=True, st=st)

create_task(
    "1 - Internamente",
    "[ ] a - Validar se as impressoras do EMC estao no GLPI com MAC informado.\n"
    "[ ] b - Validar se todas as workstations do PDV estao atualizadas no GLPI.",
    parent=f2, st=st)

create_task(
    "2 - Oracle",
    "[ ] a - Qual o hardware necessario?\n"
    "[ ] b - Quais portas cada workstation precisa ter liberadas na regra de firewall do sistema operacional?\n"
    "[ ] c - Qual a recomendacao de servidor para a CAPS (Windows 10 ou Server)?",
    parent=f2, st=st)

create_task(
    "3 - Kaspersky",
    "[ ] a - Configurar o Kaspersky para liberar as portas necessarias.",
    parent=f2, st=st)

# ============ FASE 3 - DEFINICOES ============
print("Fase 3 - Definicoes")
f3 = create_task("Fase 3 - Definicoes",
    "Definir GPO, rede padrao do PDV e itens a alinhar com a 3WSI.",
    milestone=True, st=st)

create_task(
    "GPO do PDV",
    "[ ] a - Definir o que sera feito via GPO.\n"
    "[ ] b - Validacao da GPO com a gestao da TI.",
    parent=f3, st=st)

create_task(
    "Rede padrao do PDV",
    "[ ] Tera VLAN padrao? Verificar a viabilidade com a 3WSI e registrar.\n"
    "[ ] Qual a rede correta em cada hotel? Verificar com a 3WSI e registrar.",
    parent=f3, st=st)

create_task(
    "3WSI",
    "[ ] Solicitar a criacao da GPO com a 3WSI.\n"
    "[ ] Baixar a lista de MACs dos PDVs no GLPI.\n"
    "[ ] Enviar para a 3WSI a lista de MACs para validar cadastro correto no DHCP (IP) e liberacao na rede WiFi correta.\n"
    "[ ] Passar a lista de impressoras com MACs para verificacao no DHCP.",
    parent=f3, st=st)

# ============ FASE 4 - EXECUCAO ============
print("Fase 4 - Execucao")
f4 = create_task("Fase 4 - Execucao",
    "Execucao das mudancas definidas nas fases anteriores. Detalhamento pendente.",
    milestone=True, st=st)

# ============ FASE 5 - CONCLUSAO ============
print("Fase 5 - Conclusao")
f5 = create_task("Fase 5 - Conclusao",
    "Documentacao, base de conhecimento e padronizacao de erros conhecidos do Simphony.",
    milestone=True, st=st)

create_task(
    "91 - Criar KB MAN = Simphony BASE",
    "Criacao de um artigo de Base de Conhecimento tipo MAN = Simphony BASE (manual pratico do sistema e configuracao).",
    parent=f5, st=st)

create_task(
    "92 - Passar as regras de GPO do PDV",
    "Repassar/documentar as regras de GPO definidas para o PDV.",
    parent=f5, st=st)

create_task(
    "93 - Configuracao do Kaspersky para liberar portas necessarias",
    "Descobrir e documentar como configurar o Kaspersky para liberar as portas necessarias do Simphony PDV.",
    parent=f5, st=st)

create_task(
    "94 - Listar erros conhecidos e criar SDV/SDT",
    "Listar os erros mais conhecidos do Simphony e criar, para cada um, um artigo SDV ou SDT conforme padrao da base de conhecimento.",
    parent=f5, st=st)

create_task(
    "95 - Criar KB BEC = Erros Comuns Simphony",
    "Criacao de um artigo de Base de Conhecimento tipo BEC = Erros Comuns Simphony, associando todos os artigos SDV/SDT criados no item 94.",
    parent=f5, st=st)

req('GET', 'killSession', st=st)

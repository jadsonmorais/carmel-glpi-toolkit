"""
task-tag.py — Adiciona ou remove uma etiqueta em uma lista de ProjectTasks.

Uso:
    py task-tag.py add   --tag 217 --ids 2740 2743 2747
    py task-tag.py remove --tag 217 --ids 2740 2743 2747

Argumentos:
    action      "add" ou "remove"
    --tag       ID da etiqueta (PluginTagTag)
    --ids       Um ou mais IDs de ProjectTask

Exemplo com lista longa via arquivo (um ID por linha):
    py task-tag.py add --tag 217 --ids $(cat ids.txt | tr '\n' ' ')
"""

import argparse, json, os, sys
from urllib import request, error
from _env import *

creds = {
    'app_token':  os.environ.get('GLPI_APP_TOKEN'),
    'user_token': os.environ.get('GLPI_USER_TOKEN'),
    'base_url':   (os.environ.get('GLPI_URL') or 'https://carmelhoteis.verdanadesk.com').rstrip('/') + '/apirest.php'
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
        with request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except error.HTTPError as e:
        return {'error': f"HTTP {e.code}: {e.read().decode()}"}

def get_tag_item_id(task_id, tag_id, st):
    """Retorna o id da associacao PluginTagTagItem para remocao."""
    r = req('GET',
        f'PluginTagTagItem?searchText[itemtype]=ProjectTask'
        f'&searchText[items_id]={task_id}'
        f'&searchText[plugin_tag_tags_id]={tag_id}',
        st=st)
    if isinstance(r, list) and r:
        return r[0].get('id')
    return None

def add_tag(task_id, tag_id, st):
    body = {"input": {
        "plugin_tag_tags_id": tag_id,
        "itemtype": "ProjectTask",
        "items_id": task_id
    }}
    r = req('POST', 'PluginTagTagItem', body=body, st=st)
    if r and 'id' in r:
        return f"OK (assoc id={r['id']})"
    if r and 'error' in r and 'Duplicate' in str(r):
        return "JA EXISTE"
    return f"ERRO: {r}"

def remove_tag(task_id, tag_id, st):
    assoc_id = get_tag_item_id(task_id, tag_id, st)
    if not assoc_id:
        return "NAO ENCONTRADA"
    r = req('DELETE', f'PluginTagTagItem/{assoc_id}', st=st)
    if isinstance(r, list) and r and r[0].get(str(assoc_id)) is True:
        return f"OK (assoc id={assoc_id} removida)"
    return f"ERRO: {r}"

# --- CLI ---
parser = argparse.ArgumentParser(description="Adiciona ou remove etiqueta em ProjectTasks")
parser.add_argument('action', choices=['add', 'remove'], help='"add" ou "remove"')
parser.add_argument('--tag', type=int, required=True, help='ID da etiqueta (PluginTagTag)')
parser.add_argument('--ids', type=int, nargs='+', required=True, help='IDs das tarefas')
args = parser.parse_args()

sess = req('GET', 'initSession')
if not isinstance(sess, dict) or 'session_token' not in sess:
    print(f"ERRO ao iniciar sessao: {sess}")
    sys.exit(1)
st = sess['session_token']

# Mostra nome da etiqueta para confirmacao
tag_info = req('GET', f'PluginTagTag/{args.tag}', st=st)
tag_name = tag_info.get('name', '???') if isinstance(tag_info, dict) else '???'
print(f"Acao: {args.action.upper()} | Etiqueta: [{args.tag}] {tag_name} | Tasks: {args.ids}\n")

for task_id in args.ids:
    if args.action == 'add':
        result = add_tag(task_id, args.tag, st)
    else:
        result = remove_tag(task_id, args.tag, st)
    print(f"  [{task_id}] {result}")

req('GET', 'killSession', st=st)

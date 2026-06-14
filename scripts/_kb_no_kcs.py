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

KCS_CAT_IDS = {50, 51, 52, 53, 54, 55}

# Todos os vinculos categoria-artigo
all_links = req('GET', 'KnowbaseItem_KnowbaseItemCategory?range=0-9999', st=st)
# Artigos que já têm vínculo KCS
kcs_article_ids = {l['knowbaseitems_id'] for l in all_links if l['knowbaseitemcategories_id'] in KCS_CAT_IDS}

# Todos os artigos
all_articles = req('GET', 'KnowbaseItem?range=0-9999', st=st)
print(f"Total artigos: {len(all_articles)} | Com KCS: {len(kcs_article_ids)}")
print(f"Sem KCS: {len([a for a in all_articles if a['id'] not in kcs_article_ids])}\n")

print(f"{'#ID':<6} {'Título'}")
print("-" * 100)
for a in sorted(all_articles, key=lambda x: x['id']):
    if a['id'] not in kcs_article_ids:
        title = html.unescape(a.get('name', ''))
        print(f"#{a['id']:<5} {title}")

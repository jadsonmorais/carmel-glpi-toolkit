import sys, io, re, html
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

KCS_CATS = {50: 'BEC', 51: 'IDT', 52: 'SDC', 53: 'SDV', 54: 'MAN', 55: 'DTS'}
all_links = req('GET', 'KnowbaseItem_KnowbaseItemCategory?range=0-9999', st=st)

by_cat = {}
for l in all_links:
    if l['knowbaseitemcategories_id'] in KCS_CATS:
        prefix = KCS_CATS[l['knowbaseitemcategories_id']]
        by_cat.setdefault(prefix, set()).add(l['knowbaseitems_id'])

all_articles = req('GET', 'KnowbaseItem?range=0-9999', st=st)
name_map = {a['id']: html.unescape(a.get('name','')) for a in all_articles}

for prefix in ['BEC','DTS','IDT','MAN','SDC','SDV']:
    ids = by_cat.get(prefix, set())
    found = [(aid, name_map[aid]) for aid in ids if re.match(rf'^{prefix}-0000', name_map.get(aid,''))]
    wrong = [(aid, name_map[aid]) for aid in ids if re.match(r'^[A-Z]+-0000', name_map.get(aid,'')) and not re.match(rf'^{prefix}-0000', name_map.get(aid,''))]
    print(f"[{prefix}] 0000: {'EXISTE -> ' + str(found) if found else 'NAO EXISTE'}")
    if wrong:
        print(f"       ATENCAO artigo com 0000 errado: {wrong}")

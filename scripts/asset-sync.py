"""
asset-sync.py — Sincroniza inventário de ativos do GLPI para arquivos .md locais.
Alertas são específicos por tipo de ativo (rádio, smartphone, servidor, etc.).
Lê etiquetas existentes do GLPI e sugere novas com base nos alertas detectados.

Uso:
    py scripts/asset-sync.py              # fetch + index + alertas + .md individuais
    py scripts/asset-sync.py --report     # só index + alertas (sem .md por ativo)
    py scripts/asset-sync.py --id 42      # processa ativo específico
    py scripts/asset-sync.py --tags       # aplica etiquetas sugeridas no GLPI (requer REST)
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
from _env import URL_ASSETS, BASE_DIR, fetch_json

ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ──────────────────────────────────────────────────────────────────────────────
# Classificação de tipos
# ──────────────────────────────────────────────────────────────────────────────

# Grupos semânticos de tipos de máquina
_TIPO_RADIO    = {"Rádios"}
_TIPO_MOBILE   = {"Smartphone"}
_TIPO_TABLET   = {"Tablet Físico", "Tablet Virtual"}
_TIPO_PC       = {"Desktop", "Notebook", "Mini PC", "Docking Station"}
_TIPO_SERVER   = {"Servidor Físico", "Servidor VM", "Rack Mount Chassis"}
_TIPO_IOT      = {"IOT"}

def _grupo(tipo: str | None) -> str:
    t = (tipo or "").strip()
    if t in _TIPO_RADIO:    return "radio"
    if t in _TIPO_MOBILE:   return "mobile"
    if t in _TIPO_TABLET:   return "tablet"
    if t in _TIPO_PC:       return "pc"
    if t in _TIPO_SERVER:   return "server"
    if t in _TIPO_IOT:      return "iot"
    return "outro"

# ──────────────────────────────────────────────────────────────────────────────
# Helpers de data
# ──────────────────────────────────────────────────────────────────────────────

def _idle_days(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace(" ", "T"))
        dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except ValueError:
        return None

def _fmt_idle(days: int | None) -> str:
    if days is None:
        return "—"
    return "hoje" if days == 0 else f"{days}d atrás"

def _mem_total(mem_str: str | None) -> str:
    if not mem_str or mem_str == "Não Identificado":
        return mem_str or "—"
    try:
        total = sum(float(x.replace("GB", "").strip()) for x in mem_str.split(";"))
        return f"{total:.2f} GB"
    except (ValueError, AttributeError):
        return mem_str

def _so_curto(so: str | None) -> str:
    if not so or so == "Não Identificado":
        return "—"
    # Retorna só o primeiro SO (pode ter múltiplos separados por ;)
    return so.split(";")[0].strip()[:35]

# ──────────────────────────────────────────────────────────────────────────────
# Etiquetas de Computer no GLPI
# ──────────────────────────────────────────────────────────────────────────────

# Mapeamento: alerta_code → (tag_id, nome_tag)
ALERTA_PARA_TAG = {
    "NAO_LOCALIZADO":  (215, "Não localizado"),
    "MANUTENCAO":      (214, "Alerta de Manutenção"),
    "SEM_PATRIMONIO":  (247, "Sem Patrimônio"),
    "FORA_DOMINIO":    (239, "Fora do Domínio"),
    "PROBLEMA":        (233, "Problema"),
}

def _buscar_tags_glpi(ids: list[int]) -> dict[int, list[dict]]:
    """Busca etiquetas atribuídas a uma lista de IDs de Computer via REST."""
    try:
        from tag_manager_lib import GLPIApiClient, load_credentials  # type: ignore
    except ImportError:
        pass
    # Tenta carregar tag-manager como módulo
    import importlib.util
    tm_path = os.path.join(_SCRIPT_DIR, "tag-manager.py")
    spec = importlib.util.spec_from_file_location("tag_manager", tm_path)
    tm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tm)

    try:
        creds = tm.load_credentials()
        client = tm.GLPIApiClient(creds)
    except Exception:
        return {}

    result = {}
    for cid in ids:
        try:
            tags = client.get(
                f"PluginTagTagItem",
                params={"searchText[itemtype]": "Computer", "searchText[items_id]": str(cid), "range": "0-50"}
            )
            if isinstance(tags, list):
                result[cid] = tags
        except Exception:
            pass
    return result

# ──────────────────────────────────────────────────────────────────────────────
# Lógica de alertas por tipo
# ──────────────────────────────────────────────────────────────────────────────

def _alertas(ativo: dict) -> list[tuple[str, str]]:
    """
    Retorna lista de (codigo, descricao) com alertas relevantes para o tipo do ativo.
    Evita falsos positivos: rádios não precisam de antivírus, servidores têm limiares
    diferentes de boot, etc.
    """
    grupo = _grupo(ativo.get("Tipo de Máquina"))
    situacao = ativo.get("Situação do Equipamento") or ""
    cadastro = ativo.get("Situação do Cadastro") or ""
    av = ativo.get("Antivírus") or "Nenhum"
    anydesk = ativo.get("AnyDesk") or "Não instalado"
    dominio = ativo.get("Domínios") or "Não Identificado"
    serial = ativo.get("Número de Série") or ""
    boot_idle = _idle_days(ativo.get("Último Boot"))
    inv_idle  = _idle_days(ativo.get("Última Execução do GLPI"))

    alerts: list[tuple[str, str]] = []

    # ── Alerta universal: cadastro removido mas aparece como ativo ──
    if cadastro == "Removido" and situacao not in {"(SU) Sucata", "(DS) Desativado", "(DE) Defeito"}:
        alerts.append(("CADASTRO_REMOVIDO", "Cadastro marcado como removido"))

    # ── Alerta universal: situações problemáticas ──
    if "(NL) Não localizado" in situacao:
        alerts.append(("NAO_LOCALIZADO", "Equipamento não localizado"))
    if "(DE) Defeito" in situacao:
        alerts.append(("DEFEITO", "Em situação de defeito"))
    if "(SU) Sucata" in situacao:
        alerts.append(("SUCATA", "Marcado como sucata"))

    # ── Rádios: só patrimônio e localização importam ──
    if grupo == "radio":
        if not serial:
            alerts.append(("SEM_PATRIMONIO", "Sem número de série/patrimônio"))
        return alerts

    # ── IoT: mínimo de validações ──
    if grupo == "iot":
        return alerts

    # ── Mobile (smartphones): sem serial é crítico ──
    if grupo == "mobile":
        if not serial:
            alerts.append(("SEM_PATRIMONIO", "Sem número de série/IMEI"))
        return alerts

    # ── Tablets (físico e virtual): Windows, precisa de AV e AnyDesk ──
    if grupo == "tablet":
        so = ativo.get("Sistema Operacional") or ""
        if "Windows" in so:
            if av == "Nenhum":
                alerts.append(("SEM_AV", "Sem antivírus (Windows)"))
            if anydesk == "Não instalado":
                alerts.append(("SEM_ANYDESK", "AnyDesk não instalado"))
            if dominio == "Não Identificado":
                alerts.append(("FORA_DOMINIO", "Sem domínio identificado"))
        if not serial:
            alerts.append(("SEM_PATRIMONIO", "Sem número de série"))
        if boot_idle is not None and boot_idle > 60:
            alerts.append(("BOOT_ANTIGO", f"Último boot há {boot_idle} dias"))
        return alerts

    # ── PC (Desktop/Notebook/Mini PC) ──
    if grupo == "pc":
        if av == "Nenhum":
            alerts.append(("SEM_AV", "Sem antivírus"))
        if anydesk == "Não instalado":
            alerts.append(("SEM_ANYDESK", "AnyDesk não instalado"))
        if dominio == "Não Identificado":
            alerts.append(("FORA_DOMINIO", "Sem domínio identificado"))
        if not serial:
            alerts.append(("SEM_PATRIMONIO", "Sem número de série"))
        if boot_idle is not None and boot_idle > 60:
            alerts.append(("BOOT_ANTIGO", f"Último boot há {boot_idle} dias"))
        if inv_idle is not None and inv_idle > 45:
            alerts.append(("INV_ANTIGO", f"Inventário GLPI desatualizado há {inv_idle} dias"))
        return alerts

    # ── Servidores (físicos e VMs): criticidade alta ──
    if grupo == "server":
        if av == "Nenhum":
            alerts.append(("SEM_AV", "CRÍTICO: Servidor sem antivírus"))
        if boot_idle is not None and boot_idle > 30:
            alerts.append(("BOOT_ANTIGO", f"CRÍTICO: Servidor sem boot há {boot_idle} dias"))
        if inv_idle is not None and inv_idle > 14:
            alerts.append(("INV_ANTIGO", f"Inventário GLPI desatualizado há {inv_idle} dias"))
        if not serial and "Físico" in (ativo.get("Tipo de Máquina") or ""):
            alerts.append(("SEM_PATRIMONIO", "Servidor físico sem número de série"))
        return alerts

    # ── Outros tipos não mapeados ──
    return alerts


def _tags_sugeridas(alertas: list[tuple[str, str]]) -> list[tuple[int, str]]:
    """Retorna lista de (tag_id, nome) sugeridas com base nos alertas."""
    codigos = {a[0] for a in alertas}
    sugestoes = []
    if "NAO_LOCALIZADO" in codigos:
        sugestoes.append(ALERTA_PARA_TAG["NAO_LOCALIZADO"])
    if "DEFEITO" in codigos or "BOOT_ANTIGO" in codigos or "SEM_AV" in codigos:
        sugestoes.append(ALERTA_PARA_TAG["MANUTENCAO"])
    if "SEM_PATRIMONIO" in codigos:
        sugestoes.append(ALERTA_PARA_TAG["SEM_PATRIMONIO"])
    if "FORA_DOMINIO" in codigos:
        sugestoes.append(ALERTA_PARA_TAG["FORA_DOMINIO"])
    if len(codigos) >= 3:
        sugestoes.append(ALERTA_PARA_TAG["PROBLEMA"])
    # Deduplica mantendo ordem
    seen = set()
    return [(tid, tnm) for tid, tnm in sugestoes if not (tid in seen or seen.add(tid))]


# ──────────────────────────────────────────────────────────────────────────────
# Renderização de .md por ativo
# ──────────────────────────────────────────────────────────────────────────────

def _render_md(ativo: dict, tags_glpi: list[dict] | None = None) -> str:
    mem = _mem_total(ativo.get("Quantidade de Memória"))
    grupo = _grupo(ativo.get("Tipo de Máquina"))
    alertas = _alertas(ativo)
    sugeridas = _tags_sugeridas(alertas)

    alerta_bloco = ""
    if alertas:
        itens = "\n".join(f"- [{a[0]}] {a[1]}" for a in alertas)
        alerta_bloco = f"\n## Alertas\n{itens}\n"

    tags_bloco = ""
    if tags_glpi:
        nomes = [t.get("name") or str(t.get("plugin_tag_tags_id")) for t in tags_glpi]
        tags_bloco = f"\n## Etiquetas GLPI\n" + "\n".join(f"- {n}" for n in nomes) + "\n"
    if sugeridas:
        sg = "\n".join(f"- [{tid}] {tnm}" for tid, tnm in sugeridas)
        tags_bloco += f"\n## Etiquetas Sugeridas\n{sg}\n"

    # Blocos condicionais por grupo
    software_bloco = ""
    if grupo in ("pc", "tablet", "server"):
        software_bloco = f"""
## Software
| Campo | Valor |
|---|---|
| Sistema Operacional | {_so_curto(ativo.get('Sistema Operacional'))} |
| Domínio | {ativo.get('Domínios', '—')} |
| Antivírus | {ativo.get('Antivírus', '—')} |
"""

    acesso_bloco = ""
    if grupo in ("pc", "tablet", "server"):
        acesso_bloco = f"""
## Acesso Remoto
| Campo | Valor |
|---|---|
| AnyDesk | {ativo.get('AnyDesk', '—')} |
| TeamViewer | {ativo.get('TeamViewer', '—')} |
"""

    hw_bloco = ""
    if grupo in ("pc", "tablet", "server"):
        hw_bloco = f"""
## Hardware
| Campo | Valor |
|---|---|
| Armazenamento | {ativo.get('Armazenamento', '—')} |
| Tipo de Disco | {ativo.get('Tipo de Disco Rígido', '—')} |
| Memória Total | {mem} |
| Tipo de Memória | {ativo.get('Tipo de Memória', '—')} |
| MAC Wi-Fi | {ativo.get('Endereço MAC (Wi-fi)', '—')} |
"""

    return f"""# Ativo #{ativo['id']} — {ativo.get('Máquina', '?')}

## Identificação
| Campo | Valor |
|---|---|
| Grupo | {grupo.upper()} |
| Tipo | {ativo.get('Tipo de Máquina', '—')} |
| Situação Cadastro | {ativo.get('Situação do Cadastro', '—')} |
| Situação Equipamento | {ativo.get('Situação do Equipamento', '—')} |
| Fabricante | {ativo.get('Fabricante', '—')} |
| Modelo | {ativo.get('Modelo', '—')} |
| Número de Série | {ativo.get('Número de Série') or '—'} |
| Entidade | {ativo.get('Entidade', '—')} |
| Localização | {ativo.get('Localização', '—')} |
| Local/UH | {ativo.get('Local', '—')} |
| Grupo GLPI | {ativo.get('Grupo') or '—'} |
| Usuário | {ativo.get('Usuário') or '—'} |
| Conta | {ativo.get('Conta do Usuário') or '—'} |
{alerta_bloco}{tags_bloco}{software_bloco}{acesso_bloco}{hw_bloco}
## Histórico
| Campo | Valor |
|---|---|
| Criado em | {ativo.get('Criado Em', '—')} |
| Última Atualização | {ativo.get('Última Atualização', '—')} |
| Último Boot | {ativo.get('Último Boot', '—')} ({_fmt_idle(_idle_days(ativo.get('Último Boot')))}) |
| Último Inventário | {ativo.get('Última Execução do GLPI', '—')} ({_fmt_idle(_idle_days(ativo.get('Última Execução do GLPI')))}) |
| Dinâmico | {'Sim' if ativo.get('Dinamico') else 'Não'} |
| Documentos | {ativo.get('Quantidade de Documentos', 0)} |

## Comentário
{ativo.get('Comentário') or '*(sem comentário)*'}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Index
# ──────────────────────────────────────────────────────────────────────────────

def _render_index(ativos: list[dict], gerado_em: str) -> str:
    total = len(ativos)
    por_grupo: dict[str, int] = {}
    por_situacao: dict[str, int] = {}
    for a in ativos:
        g = _grupo(a.get("Tipo de Máquina"))
        por_grupo[g] = por_grupo.get(g, 0) + 1
        s = a.get("Situação do Equipamento") or "null"
        por_situacao[s] = por_situacao.get(s, 0) + 1

    resumo_grupo = " | ".join(f"{g.upper()}: {n}" for g, n in sorted(por_grupo.items(), key=lambda x: -x[1]))
    resumo_sit = " | ".join(f"{s}: {n}" for s, n in sorted(por_situacao.items(), key=lambda x: -x[1]))

    linhas = [
        "# Inventário de Ativos de TI",
        f"\nGerado em: {gerado_em}",
        f"Total: **{total}** ativos",
        f"\n**Por grupo:** {resumo_grupo}",
        f"**Por situação:** {resumo_sit}\n",
        "---\n",
        "| ID | Máquina | Grupo | Tipo | Situação | Fabricante | Local | UH | SO | Memória | Disco | AnyDesk | Antivírus | Último Boot | Alertas |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for a in sorted(ativos, key=lambda x: (x.get("Localização") or "", x.get("Tipo de Máquina") or "")):
        mem = _mem_total(a.get("Quantidade de Memória"))
        boot_idle = _idle_days(a.get("Último Boot"))
        boot_str = f"{(a.get('Último Boot') or '')[:10]} ({_fmt_idle(boot_idle)})" if a.get("Último Boot") else "—"
        av = a.get("Antivírus") or "Nenhum"
        grupo = _grupo(a.get("Tipo de Máquina"))
        alertas = _alertas(a)

        # Ícone de antivírus só relevante para PC/tablet/server
        if grupo in ("pc", "tablet", "server"):
            av_str = "✓" if av != "Nenhum" else "**NENHUM**"
        else:
            av_str = "N/A"

        al_str = str(len(alertas)) if alertas else "—"

        linhas.append(
            f"| {a['id']} | {a.get('Máquina','?')} | {grupo.upper()} | {a.get('Tipo de Máquina','?')} "
            f"| {a.get('Situação do Equipamento','?')} | {a.get('Fabricante','?')} "
            f"| {a.get('Localização','?')} | {a.get('Local','?')} "
            f"| {_so_curto(a.get('Sistema Operacional'))} "
            f"| {mem} | {a.get('Armazenamento','—')} "
            f"| {a.get('AnyDesk','—')} | {av_str} | {boot_str} | {al_str} |"
        )
    return "\n".join(linhas) + "\n"


# ──────────────────────────────────────────────────────────────────────────────
# Alertas consolidados
# ──────────────────────────────────────────────────────────────────────────────

def _render_alertas(ativos: list[dict], gerado_em: str) -> str:
    criticos = [(a, _alertas(a)) for a in ativos if _alertas(a)]
    # Ordenar: mais alertas primeiro, depois por grupo (server primeiro)
    ordem_grupo = {"server": 0, "pc": 1, "tablet": 2, "mobile": 3, "radio": 4, "iot": 5, "outro": 6}
    criticos.sort(key=lambda x: (ordem_grupo.get(_grupo(x[0].get("Tipo de Máquina")), 9), -len(x[1])))

    por_codigo: dict[str, int] = {}
    for _, als in criticos:
        for cod, _ in als:
            por_codigo[cod] = por_codigo.get(cod, 0) + 1

    resumo = " | ".join(f"{c}: {n}" for c, n in sorted(por_codigo.items(), key=lambda x: -x[1]))

    linhas = [
        "# Alertas de Ativos",
        f"\nGerado em: {gerado_em}",
        f"Total com alertas: **{len(criticos)}** de {len(ativos)} ativos\n",
        f"**Por tipo de alerta:** {resumo}\n",
        "---\n",
    ]

    grupo_atual = None
    for ativo, alerts in criticos:
        grupo = _grupo(ativo.get("Tipo de Máquina"))
        if grupo != grupo_atual:
            grupo_atual = grupo
            linhas.append(f"\n## {grupo.upper()}\n")
        sugeridas = _tags_sugeridas(alerts)
        tag_str = ", ".join(f"[{tid}] {tnm}" for tid, tnm in sugeridas) if sugeridas else "—"
        linhas.append(
            f"### [{ativo['id']}] {ativo.get('Máquina','?')} "
            f"— {ativo.get('Localização','?')} / {ativo.get('Local','?')}"
        )
        linhas.append(f"Tipo: {ativo.get('Tipo de Máquina','?')} | Situação: {ativo.get('Situação do Equipamento','?')}")
        linhas.append(f"Etiquetas sugeridas: {tag_str}")
        for cod, desc in alerts:
            linhas.append(f"- [{cod}] {desc}")
        linhas.append("")

    return "\n".join(linhas)


# ──────────────────────────────────────────────────────────────────────────────
# Aplicação de etiquetas sugeridas no GLPI
# ──────────────────────────────────────────────────────────────────────────────

def _aplicar_tags(ativos: list[dict]) -> None:
    import importlib.util
    tm_path = os.path.join(_SCRIPT_DIR, "tag-manager.py")
    spec = importlib.util.spec_from_file_location("tag_manager", tm_path)
    tm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tm)

    try:
        creds = tm.load_credentials()
        client = tm.GLPIApiClient(creds)
    except Exception as e:
        print(f"[tags] Falha ao conectar na API REST: {e}")
        return

    aplicados = 0
    erros = 0
    for ativo in ativos:
        alerts = _alertas(ativo)
        if not alerts:
            continue
        sugeridas = _tags_sugeridas(alerts)
        for tag_id, tag_nome in sugeridas:
            payload = {"itemtype": "Computer", "items_id": ativo["id"], "plugin_tag_tags_id": tag_id}
            try:
                result = client.post("PluginTagTagItem", payload)
                if isinstance(result, list):  # duplicata — benigno
                    pass
                elif isinstance(result, dict) and result.get("id"):
                    aplicados += 1
                    print(f"  [+] #{ativo['id']} {ativo.get('Máquina')} ← [{tag_id}] {tag_nome}")
            except Exception as e:
                erros += 1
                print(f"  [!] #{ativo['id']} tag {tag_id}: {e}")

    print(f"[tags] {aplicados} atribuições aplicadas, {erros} erros.")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sincroniza ativos do GLPI com análise por tipo")
    parser.add_argument("--report", action="store_true", help="Só index + alertas, sem .md por ativo")
    parser.add_argument("--id", type=int, help="Processa somente o ativo com este ID")
    parser.add_argument("--tags", action="store_true", help="Aplica etiquetas sugeridas no GLPI via REST")
    args = parser.parse_args()

    print("[asset-sync] Buscando dados...")
    payload = fetch_json(URL_ASSETS)
    ativos = payload.get("data", [])
    if not ativos:
        print("[ERRO] Nenhum ativo retornado. Verifique VERDANADESK_URL_ASSETS / token.")
        sys.exit(1)

    print(f"[asset-sync] {len(ativos)} ativos recebidos.")

    os.makedirs(ASSETS_DIR, exist_ok=True)
    gerado_em = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Snapshot JSON
    raw_path = os.path.join(ASSETS_DIR, "snapshot.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(ativos, f, ensure_ascii=False, indent=2)

    # Index
    index_path = os.path.join(ASSETS_DIR, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(_render_index(ativos, gerado_em))
    print(f"[asset-sync] index.md gerado ({len(ativos)} ativos)")

    # Alertas
    alertas_path = os.path.join(ASSETS_DIR, "alertas.md")
    with open(alertas_path, "w", encoding="utf-8") as f:
        f.write(_render_alertas(ativos, gerado_em))
    n_alertas = sum(1 for a in ativos if _alertas(a))
    print(f"[asset-sync] alertas.md gerado ({n_alertas} ativos com alertas)")

    # Aplicar tags no GLPI
    if args.tags:
        print("[asset-sync] Aplicando etiquetas sugeridas no GLPI...")
        _aplicar_tags(ativos)

    if args.report:
        return

    # .md individuais
    filtro = [a for a in ativos if a["id"] == args.id] if args.id else ativos
    for ativo in filtro:
        nome = "".join(c if c.isalnum() or c in "-_" else "_" for c in (ativo.get("Máquina") or str(ativo["id"])))
        md_path = os.path.join(ASSETS_DIR, f"{ativo['id']}-{nome}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(_render_md(ativo))

    print(f"[asset-sync] {len(filtro)} fichas individuais geradas em {ASSETS_DIR}/")


if __name__ == "__main__":
    main()

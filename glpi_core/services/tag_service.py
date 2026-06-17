from __future__ import annotations

from glpi_core.connection.client import GLPIClient
from glpi_core.schemas.governance import GovernanceTag
from glpi_core.schemas.tag import TagAssignSchema, TaggableItemType


class TagService:
    def __init__(self, client: GLPIClient):
        self._client = client

    def resolve_tag_id(self, name: str) -> int:
        """Busca o id de uma tag existente no GLPI pelo nome exato.

        Nao cria tags novas — a criacao de PluginTagTag e feita pela interface
        do GLPI (ou via tag-manager.py); aqui so resolvemos o id determinístico.
        """
        matches = [t for t in self.list_tags() if t.get("name") == name]
        if not matches:
            raise ValueError(f"tag '{name}' nao existe no GLPI — crie-a antes de usar esta macro")
        return matches[0]["id"]

    def assign_governance_tag(self, itemtype: TaggableItemType, items_id: int, tag: GovernanceTag) -> dict:
        """Atribui uma das tags de governanca (Break-Fix/Planejado/Projeto/Blocked) a um item."""
        tag_id = self.resolve_tag_id(tag.value)
        schema = TagAssignSchema(itemtype=itemtype, items_id=items_id, tag_id=tag_id)
        return self.assign(schema)

    def list_tags(self, name_filter: str | None = None) -> list[dict]:
        result = self._client.request("GET", "PluginTagTag?range=0-999")
        if not isinstance(result, list):
            return []
        if name_filter:
            name_lower = name_filter.lower()
            result = [t for t in result if name_lower in t.get("name", "").lower()]
        return result

    def list_item_tags(self, itemtype: str, items_id: int) -> list[dict]:
        result = self._client.request("GET", f"{itemtype}/{items_id}/PluginTagTagItem")
        return result if isinstance(result, list) else []

    def assign(self, schema: TagAssignSchema) -> dict:
        body = {
            "input": {
                "itemtype": schema.itemtype.value,
                "items_id": schema.items_id,
                "plugin_tag_tags_id": schema.tag_id,
            }
        }
        return self._client.request("POST", "PluginTagTagItem", body)

    def remove(self, tag_item_id: int) -> dict:
        return self._client.request("DELETE", f"PluginTagTagItem/{tag_item_id}")

    def bulk_assign_governance_tag(
        self, itemtype: TaggableItemType, items_ids: list[int], tag: GovernanceTag
    ) -> list[dict]:
        """Atribui uma tag de governanca a varios itens de uma vez.

        Resolve o id da tag uma unica vez (nao a cada item). Equivalente a
        scripts/task-tag.py add --tag <id> --ids <...>, mas reaproveitando os
        schemas validados deste pacote.
        """
        tag_id = self.resolve_tag_id(tag.value)
        results = []
        for items_id in items_ids:
            schema = TagAssignSchema(itemtype=itemtype, items_id=items_id, tag_id=tag_id)
            results.append(self.assign(schema))
        return results

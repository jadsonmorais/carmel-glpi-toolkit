# VerdanaDesk / GLPI Field Redaction (Hidden Columns)

## The `[` Token

In the VerdanaDesk dashboard, column headers that start with a bracket—e.g. `[Numero]`, `[Aberto Por]`, `[Categoria]`—indicate **hidden / redacted columns**.

These fields are present in the database but are **not exposed through the JSON endpoints** unless the user explicitly enables them in the GLPI / VerdanaDesk web UI. The bracket is a visual hint in the front-end grid, not part of the actual database schema.

## Impact on API consumption

When calling the bulk endpoint (`graphic.json.php`), the returned JSON only contains columns that are **visible** in the user's current dashboard view. If a column is hidden (shown with `[...]`), its data will be missing from the `data` array.

Example: if `[Numero]` is hidden, the ticket ID must be parsed from other fields (e.g. the `Ticket` grouping key in the bulk response) rather than read directly from a flat `numero` key.

## How to make hidden columns visible

1. Log into VerdanaDesk as an admin or the service-account user that owns the API token.
2. Open the dashboard grid that lists tickets.
3. Use the **column picker / field selector** (usually a gear icon or "Show / hide columns" dropdown).
4. Check the boxes for the columns currently shown as `[...]`.
5. Save the layout.

After this, the next `curl` to the JSON endpoint will include those newly-visible fields.

## Pitfall: "missing field" errors in scripts

Scripts that assume a fixed schema (e.g. always expecting `numero`) will break when the dashboard layout changes. Defensive parsing is recommended:

```python
numero = item.get("Numero") or item.get("Ticket") or "unknown"
```

## Related

- `references/endpoint-types.md` — how the bulk endpoint structures its response.
- `references/incremental-processing-recipe.md` — compares `Ticket` (always present) against metadata fields that may be hidden.

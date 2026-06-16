"""Schema cache with recursive $ref resolution for OpenAPI documents."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

MAX_SCHEMA_DEPTH = 2


def _split_ref(ref: Any) -> Optional[str]:
    """Return the schema name from '#/components/schemas/Name' or None."""
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        return None
    return ref.split("/")[-1]


class SchemaCache:
    """Index components/schemas and resolve references recursively."""

    def __init__(self, document: Dict[str, Any]) -> None:
        self._schemas: Dict[str, Any] = {}
        # Support both OpenAPI 3.x components/schemas and Swagger 2.0 definitions.
        if "components" in document and isinstance(document["components"], dict):
            self._schemas.update(document["components"].get("schemas", {}) or {})
        if "definitions" in document and isinstance(document["definitions"], dict):
            self._schemas.update(document["definitions"] or {})
        # Cache resolved schema objects keyed by name.
        self._cache: Dict[str, Dict[str, Any]] = {}

    def resolve(
        self,
        name: str,
        depth: int = 0,
        seen: Optional[set] = None,
    ) -> Dict[str, Any]:
        """Resolve a schema by name.

        Returns a dict with keys:
        - name
        - description
        - fields: list[Field]
        - nestedSchemas: dict[str, ResolvedSchema]
        """
        if seen is None:
            seen = set()

        if name in self._cache:
            return self._cache[name]

        raw = self._schemas.get(name, {})
        if not raw:
            # Schema referenced but not defined in components/schemas.
            return {
                "name": name,
                "description": "（未找到该 Schema 定义）",
                "fields": [],
                "nestedSchemas": {},
            }

        description = raw.get("description") or "(无描述)"

        fields: List[Dict[str, Any]] = []
        nested: Dict[str, Any] = {}

        # If the schema is an array wrapper, resolve its items.
        if raw.get("type") == "array":
            items = raw.get("items") or {}
            item_ref = _split_ref(items.get("$ref"))
            if item_ref and depth < MAX_SCHEMA_DEPTH and item_ref not in seen:
                seen.add(item_ref)
                nested[item_ref] = self.resolve(item_ref, depth + 1, seen)
            fields.append(
                {
                    "name": "items",
                    "type": f"array<{item_ref}>" if item_ref else "array",
                    "format": items.get("format"),
                    "description": items.get("description") or "(无描述)",
                    "required": False,
                    "default": None,
                    "nestedSchema": item_ref,
                }
            )
            result = {
                "name": name,
                "description": description,
                "fields": fields,
                "nestedSchemas": nested,
            }
            self._cache[name] = result
            return result

        required_set = set(raw.get("required", []))
        properties = raw.get("properties", {})
        if not properties and raw.get("type") == "object":
            # Empty object schema.
            pass

        for fname, fschema in properties.items():
            ref_name = _split_ref(fschema.get("$ref"))
            item_ref_name: Optional[str] = None
            field_type = fschema.get("type") or "object"
            field_format = fschema.get("format")

            if ref_name:
                field_type = "object"
                if depth < MAX_SCHEMA_DEPTH and ref_name not in seen:
                    seen.add(ref_name)
                    nested[ref_name] = self.resolve(ref_name, depth + 1, seen)
            elif field_type == "array":
                item_ref_name = _split_ref((fschema.get("items") or {}).get("$ref"))
                if item_ref_name:
                    field_type = f"array<{item_ref_name}>"
                    if depth < MAX_SCHEMA_DEPTH and item_ref_name not in seen:
                        seen.add(item_ref_name)
                        nested[item_ref_name] = self.resolve(
                            item_ref_name, depth + 1, seen
                        )
                else:
                    item_type = (fschema.get("items") or {}).get("type")
                    if item_type:
                        field_type = f"array<{item_type}>"

            fields.append(
                {
                    "name": fname,
                    "type": field_type,
                    "format": field_format,
                    "description": fschema.get("description") or "(无描述)",
                    "required": fname in required_set,
                    "default": fschema.get("default"),
                    "nestedSchema": ref_name or item_ref_name,
                }
            )

        result = {
            "name": name,
            "description": description,
            "fields": fields,
            "nestedSchemas": nested,
        }
        self._cache[name] = result
        return result

    def resolve_schema_object(self, schema: Dict[str, Any], depth: int = 0) -> Optional[Dict[str, Any]]:
        """Resolve an inline schema object that may contain $ref or items.$ref."""
        ref_name = _split_ref(schema.get("$ref"))
        if ref_name:
            return self.resolve(ref_name, depth)
        if schema.get("type") == "array":
            item_ref = _split_ref((schema.get("items") or {}).get("$ref"))
            if item_ref:
                return self.resolve(item_ref, depth)
        return None

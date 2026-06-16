"""Markdown and JSON formatters for api-doc-parser."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def sanitize_filename(name: str) -> str:
    """Replace filesystem-unsafe characters with underscore."""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def _schema_table(schema: Dict[str, Any], required_header: bool = True) -> str:
    """Render a single schema field table in Chinese columns."""
    lines: List[str] = []
    if required_header:
        lines.extend(
            [
                "| 字段 | 类型 | 必填 | 描述 |",
                "|------|------|------|------|",
            ]
        )
    else:
        lines.extend(
            [
                "| 字段 | 类型 | 描述 |",
                "|------|------|------|",
            ]
        )
    for field in schema.get("fields", []):
        ftype = field.get("type") or "object"
        fmt = field.get("format")
        if fmt:
            ftype = f"{ftype}({fmt})"
        desc = field.get("description") or "(无描述)"
        if field.get("deprecated"):
            desc = f"~~{desc}~~ (已废弃)"
        nested = field.get("nestedSchema")
        if nested and nested not in schema.get("nestedSchemas", {}):
            # Referenced but not expanded (depth limit / circular).
            desc = f"{desc} → {nested}"
        if required_header:
            req = "Yes" if field.get("required") else "No"
            lines.append(f"| {field.get('name', '')} | {ftype} | {req} | {desc} |")
        else:
            lines.append(f"| {field.get('name', '')} | {ftype} | {desc} |")
    return "\n".join(lines)


def _render_nested(
    schema: Dict[str, Any],
    required_header: bool = True,
    rendered: Optional[set] = None,
) -> List[str]:
    """Render nested schema sub-tables recursively."""
    if rendered is None:
        rendered = set()
    lines: List[str] = []
    for name, nested in schema.get("nestedSchemas", {}).items():
        if name in rendered:
            continue
        rendered.add(name)
        lines.append(f"\n#### {name}\n")
        lines.append(_schema_table(nested, required_header=required_header))
        lines.extend(_render_nested(nested, required_header=required_header, rendered=rendered))
    return lines


def to_markdown(
    module_name: str,
    module_description: Optional[str],
    endpoints: List[Dict[str, Any]],
) -> str:
    """Generate Markdown document for a module."""
    lines: List[str] = []
    lines.append(f"# {module_name}\n")
    desc = module_description or "(no description)"
    lines.append(f"> {desc}\n")
    lines.append(f"**Endpoints:** {len(endpoints)}\n")

    method_order = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3, "PATCH": 4}
    endpoints = sorted(
        endpoints,
        key=lambda e: (method_order.get(e.get("method", "").upper(), 99), e.get("path", "")),
    )

    for ep in endpoints:
        lines.append("---\n")
        lines.append(f"## {ep.get('method', '').upper()} {ep.get('path', '')} — {ep.get('summary', '')}\n")
        lines.append(f"**Description:** {ep.get('description') or '(no description)'}\n")
        lines.append(f"**Operation ID:** `{ep.get('operationId') or '(no operationId)'}`\n")

        params = ep.get("parameters") or []
        lines.append("### Request Parameters\n")
        if not params:
            lines.append("无参数\n")
        else:
            lines.extend(
                [
                    "| Name | In | Type | Required | Default | Description |",
                    "|------|----|------|----------|---------|-------------|",
                ]
            )
            for p in params:
                pschema = p.get("schema", {})
                ptype = pschema.get("type") or "object"
                fmt = pschema.get("format")
                if fmt:
                    ptype = f"{ptype}({fmt})"
                req = "Yes" if p.get("required") else "No"
                default = pschema.get("default")
                default_str = "—" if default is None else str(default)
                lines.append(
                    f"| {p.get('name', '')} | {p.get('in', '')} | {ptype} | {req} | {default_str} | {p.get('description') or '(无描述)'} |"
                )
            lines.append("")

        body = ep.get("requestBody")
        if body:
            lines.append(f"### Request Body ({body.get('contentType', 'application/json')}, {'required' if body.get('required') else 'optional'})\n")
            schema = body.get("schema")
            if schema:
                lines.append(f"#### {schema.get('name', 'RequestBody')}\n")
                lines.append(_schema_table(schema, required_header=True))
                lines.extend(_render_nested(schema, required_header=True))

        lines.append("### Responses\n")
        responses = ep.get("responses") or []
        if not responses:
            lines.append("无响应定义\n")
        else:
            lines.extend(
                [
                    "| Status | Description | Schema |",
                    "|--------|-------------|--------|",
                ]
            )
            for r in responses:
                schema = r.get("schema")
                schema_name = schema.get("name") if schema else "—"
                lines.append(
                    f"| {r.get('status', '')} | {r.get('description') or '(无描述)'} | {schema_name} |"
                )
            lines.append("")

            # Deduplicate shared schemas.
            rendered: set = set()
            for r in responses:
                schema = r.get("schema")
                if not schema or schema.get("name") in rendered:
                    continue
                rendered.add(schema.get("name"))
                lines.append(f"#### {r.get('status')} {r.get('description') or ''} — {schema.get('name')}\n")
                lines.append(_schema_table(schema, required_header=False))
                lines.extend(_render_nested(schema, required_header=False, rendered=rendered))

    return "\n".join(lines)


def to_json(
    module_name: str,
    module_description: Optional[str],
    endpoints: List[Dict[str, Any]],
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate structured JSON document for a module."""
    return {
        "meta": {
            "sourceUrl": meta.get("sourceUrl", ""),
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "openapiVersion": meta.get("openapiVersion", ""),
        },
        "module": {
            "name": module_name,
            "description": module_description or "(no description)",
        },
        "endpointCount": len(endpoints),
        "endpoints": endpoints,
    }


def save_outputs(
    module_name: str,
    module_description: Optional[str],
    endpoints: List[Dict[str, Any]],
    meta: Dict[str, Any],
    output_dir: Path,
    skip_json: bool = False,
    skip_md: bool = False,
) -> Tuple[Optional[Path], Optional[Path]]:
    """Write Markdown and JSON files and return their paths.

    Returns (md_path|None, json_path|None) depending on skip flags.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    base = sanitize_filename(module_name)
    md_path: Optional[Path] = None
    json_path: Optional[Path] = None

    if not skip_md:
        md_path = output_dir / f"{base}.md"
        md_content = to_markdown(module_name, module_description, endpoints)
        md_path.write_text(md_content, encoding="utf-8")

    if not skip_json:
        json_path = output_dir / f"{base}.json"
        json_content = to_json(module_name, module_description, endpoints, meta)
        json_path.write_text(
            json.dumps(json_content, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return md_path, json_path

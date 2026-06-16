#!/usr/bin/env python3
"""Unified OpenAPI parser for api-doc-parser.

Reads state.json, extracts endpoints for selected tags, recursively resolves
$ref schemas, and emits Markdown and/or JSON output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.formatter import save_outputs, to_markdown
from lib.schema_cache import SchemaCache

# Fast JSON loading: use orjson if available (3-5x faster on large files).
try:
    import orjson
    def _load_json(path: Path) -> Dict[str, Any]:
        with open(path, "rb") as f:
            return orjson.loads(f.read())
except ImportError:
    def _load_json(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


def _ensure_utf8_stdio() -> None:
    """Reconfigure stdio streams to UTF-8 on Windows and other platforms."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def _build_tag_index(
    document: Dict[str, Any],
) -> Tuple[Dict[str, List[Tuple[str, str, Dict[str, Any]]]], Dict[str, Optional[str]]]:
    """Build a pre-indexed mapping: tag -> [(path, method, operation), ...].

    Returns (tag_index, tag_descriptions).
    """
    tag_index: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}
    tag_descriptions: Dict[str, Optional[str]] = {}

    # Index descriptions from top-level tags array.
    for t in document.get("tags", []) or []:
        name = t.get("name", "")
        if name:
            tag_descriptions[name] = t.get("description")

    # Build operation index — single pass over all paths.
    paths = document.get("paths")
    if paths:
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op in path_item.items():
                if method == "parameters" or not isinstance(op, dict):
                    continue
                op_tags = op.get("tags")
                if not op_tags:
                    continue
                for tag in op_tags:
                    tag_index.setdefault(tag, []).append((path, method, op))

    return tag_index, tag_descriptions


def _resolve_content_schema(
    content: Dict[str, Any], cache: SchemaCache
) -> Optional[Dict[str, Any]]:
    """Resolve the first content type schema found in a content dict."""
    for media_type, media_obj in (content or {}).items():
        if not isinstance(media_obj, dict):
            continue
        schema = media_obj.get("schema")
        if not isinstance(schema, dict):
            continue
        resolved = cache.resolve_schema_object(schema)
        if resolved:
            return resolved
    return None


def _extract_parameters(
    op: Dict[str, Any],
    document: Dict[str, Any],
    _param_cache: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Extract parameters, resolving '#/components/parameters/<name>' refs.

    _param_cache: pre-built {ref_name: param_dict} for component parameters.
    """
    if _param_cache is None:
        _param_cache = document.get("components", {}).get("parameters", {})
    params: List[Dict[str, Any]] = []
    for p in op.get("parameters", []):
        if not isinstance(p, dict):
            continue
        ref = p.get("$ref", "")
        if ref and ref.startswith("#/components/parameters/"):
            ref_name = ref.split("/")[-1]
            p = _param_cache.get(ref_name, {})
            if not p:
                continue
        schema = p.get("schema", {})
        params.append(
            {
                "name": p.get("name", ""),
                "in": p.get("in", ""),
                "description": p.get("description") or "(无描述)",
                "required": bool(p.get("required", False)),
                "schema": {
                    "type": schema.get("type") or "object",
                    "format": schema.get("format"),
                    "default": schema.get("default"),
                },
            }
        )
    return params


def _extract_request_body(op: Dict[str, Any], cache: SchemaCache) -> Optional[Dict[str, Any]]:
    body = op.get("requestBody")
    if not isinstance(body, dict):
        return None
    content = body.get("content", {})
    if not content:
        return None
    schema = _resolve_content_schema(content, cache)
    if not schema:
        return None
    return {
        "required": bool(body.get("required", False)),
        "contentType": next(iter(content.keys()), "application/json"),
        "schema": schema,
    }


def _extract_responses(op: Dict[str, Any], cache: SchemaCache) -> List[Dict[str, Any]]:
    responses: List[Dict[str, Any]] = []
    for status, resp in (op.get("responses", {}) or {}).items():
        if not isinstance(resp, dict):
            continue
        schema = _resolve_content_schema(resp.get("content", {}), cache)
        responses.append(
            {
                "status": str(status),
                "description": resp.get("description") or "(无描述)",
                "schema": schema,
            }
        )
    return responses


def _extract_endpoints(
    document: Dict[str, Any],
    selected_tags: List[str],
    tag_index: Dict[str, List[Tuple[str, str, Dict[str, Any]]]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Return mapping tag_name -> endpoints using pre-built tag index."""
    cache = SchemaCache(document)
    param_cache = document.get("components", {}).get("parameters", {})
    result: Dict[str, List[Dict[str, Any]]] = {tag: [] for tag in selected_tags}

    for tag in selected_tags:
        for path, method, op in tag_index.get(tag, []):
            endpoint = {
                "path": path,
                "method": method.upper(),
                "summary": op.get("summary") or "(no summary)",
                "description": op.get("description") or "(no description)",
                "operationId": op.get("operationId") or "(no operationId)",
                "parameters": _extract_parameters(op, document, param_cache),
                "requestBody": _extract_request_body(op, cache),
                "responses": _extract_responses(op, cache),
            }
            result[tag].append(endpoint)
    return result


def _detect_openapi_version(document: Dict[str, Any]) -> str:
    return document.get("openapi") or document.get("swagger") or "unknown"


def main() -> int:
    _ensure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Parse OpenAPI docs by tag.")
    parser.add_argument("--state", required=True, help="Path to state.json")
    parser.add_argument("--output-dir", default="api-doc-parser/.output", help="Output directory")
    parser.add_argument("--mode", choices=["A", "B"], default="B", help="A=stdout, B=files")
    parser.add_argument("--auto", action="store_true", help="Skip large module confirmation")
    parser.add_argument("--no-json", action="store_true", help="Skip JSON output (Mode B only)")
    parser.add_argument("--no-md", action="store_true", help="Skip Markdown output (Mode B only)")
    args = parser.parse_args()

    state_path = Path(args.state)
    state = _load_json(state_path)

    source_path = Path(state.get("sourcePath", ""))
    if not source_path.is_absolute():
        source_path = state_path.parent / source_path
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}", file=sys.stderr)
        return 1

    selected_tags = state.get("selectedTags", [])
    if not selected_tags:
        print("ERROR: No selectedTags in state.", file=sys.stderr)
        return 1

    document = _load_json(source_path)
    version = _detect_openapi_version(document)
    meta = {
        "sourceUrl": state.get("sourceUrl", str(source_path)),
        "openapiVersion": version,
    }

    tag_index, tag_descriptions = _build_tag_index(document)
    endpoints_by_tag = _extract_endpoints(document, selected_tags, tag_index)

    output_dir = Path(args.output_dir)
    results: List[Tuple[str, int, Optional[Path], Optional[Path]]] = []

    for tag in selected_tags:
        endpoints = endpoints_by_tag.get(tag, [])
        if not endpoints:
            results.append((tag, 0, None, None))
            continue

        if len(endpoints) > 30 and not args.auto:
            print(f"LARGE_MODULE:{tag}:{len(endpoints)}", file=sys.stderr)

        desc = tag_descriptions.get(tag)

        if args.mode == "A":
            md = to_markdown(tag, desc, endpoints)
            print(f"\n## Module: {tag}\n")
            print(md)
            results.append((tag, len(endpoints), None, None))
        else:
            md_path, json_path = save_outputs(
                tag, desc, endpoints, meta, output_dir,
                skip_json=args.no_json, skip_md=args.no_md,
            )
            results.append((tag, len(endpoints), md_path, json_path))

    print("PARSE_COMPLETE")
    for tag, count, md_path, json_path in results:
        md_str = str(md_path) if md_path else ""
        json_str = str(json_path) if json_path else ""
        print(f"{tag}\t{count}\t{md_str}\t{json_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CLI entrypoint for table_generator."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import subprocess
from typing import Any, Dict, List

from .api import render_table
from .schema import SchemaError, validate_spec
from .templates import DEFAULT_RECORDS, DEFAULT_SPEC
from .pipeline import build_table, compute_highlights, compute_significance
from .render_html import render_html


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_records(path: str) -> List[Dict[str, Any]]:
    if path.endswith(".jsonl"):
        records = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError("Records JSON must be a list")
    return data


def cmd_render(args: argparse.Namespace) -> int:
    try:
        records = _load_records(args.records)
        spec = _load_json(args.spec)
        validated = validate_spec(spec)
        if args.preview:
            table = build_table(records, validated)
            highlights = compute_highlights(table, validated)
            markers = compute_significance(table, validated)
            text = render_html(table, highlights, validated, markers)
            result = {"text": text}
        else:
            result = render_table(records, validated)
    except (SchemaError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    text = result["text"]
    out_path = args.out
    if args.preview and args.open and not out_path:
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        out_path = temp.name
        temp.close()

    if out_path:
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text)

    if args.preview and args.open:
        target = out_path
        if target:
            subprocess.run(["open", target], check=False)
    return 0


def cmd_template(args: argparse.Namespace) -> int:
    payload = {"spec": DEFAULT_SPEC, "records": DEFAULT_RECORDS}
    text = json.dumps(payload, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tablegen")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="Render a table")
    render.add_argument("--records", required=True, help="Path to records JSON/JSONL")
    render.add_argument("--spec", required=True, help="Path to spec JSON")
    render.add_argument("--out", required=False, help="Optional output path")
    render.add_argument(
        "--preview",
        action="store_true",
        help="Render an HTML preview instead of the main output",
    )
    render.add_argument(
        "--open",
        action="store_true",
        help="Open the HTML preview in the default browser (macOS only)",
    )
    render.set_defaults(func=cmd_render)

    template = subparsers.add_parser("template", help="Emit a default spec + records example")
    template.add_argument("--out", required=False, help="Optional output path")
    template.set_defaults(func=cmd_template)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

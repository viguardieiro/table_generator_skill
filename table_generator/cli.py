"""CLI entrypoint for table_generator."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

from .api import render_table
from .schema import SchemaError
from .templates import DEFAULT_RECORDS, DEFAULT_SPEC


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
        result = render_table(records, spec)
    except (SchemaError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    text = result["text"]
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
    print(text)
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

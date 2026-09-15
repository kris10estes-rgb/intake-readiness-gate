"""Command line entry point.

    python -m intake_gate examples/clean_deal.json
    python -m intake_gate examples/custom_sla.json --format json
    python -m intake_gate --name ATL01 --screen 2 --type promo --date 2026-07-29
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .brief import render
from .gate import evaluate
from .naming import build_name


def _load(path: str) -> dict:
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("intake file must contain a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="intake_gate", description="Run a deal through the nine-stage readiness gate.")
    parser.add_argument("intake", nargs="?", help="path to an intake JSON file")
    parser.add_argument("--format", choices=("brief", "json"), default="brief")
    parser.add_argument("--name", help="build a filename: location code")
    parser.add_argument("--screen", type=int, default=1)
    parser.add_argument("--type", dest="ctype", default="promo")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)

    if args.name:
        try:
            print(build_name(args.name, args.screen, args.ctype, date.fromisoformat(args.date)))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

    if not args.intake:
        parser.print_help()
        return 2

    try:
        intake = _load(args.intake)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    decision = evaluate(intake)
    if args.format == "json":
        print(json.dumps(decision.to_dict(), indent=2))
    else:
        print(render(intake, decision), end="")
    return 0 if decision.cleared else 1


if __name__ == "__main__":
    sys.exit(main())

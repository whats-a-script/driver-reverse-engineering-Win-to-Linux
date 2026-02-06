#!/usr/bin/env python3
"""AstraForge CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from modules import list_canonicals, summarize_capabilities, validator


REPO_ROOT = SCRIPT_DIR.parents[1]


def _handle_validate(args: argparse.Namespace) -> int:
    raw_root = Path(args.raw_root).resolve()
    report = validator.validate_raw_datasets(
        raw_root, platform=args.platform, device_id=args.device_id
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _handle_list_canonicals(args: argparse.Namespace) -> int:
    output_dir = Path(args.path).resolve() if args.path else None
    files = list_canonicals.list_canonical_files(output_dir)
    if not files:
        print("No canonical files found.")
        return 0
    for file_path in files:
        print(file_path)
    return 0


def _handle_summarize(args: argparse.Namespace) -> int:
    canonical_path = args.canonical_file
    if canonical_path is None:
        prompt_value = input("Enter canonical JSON file path: ").strip()
        if not prompt_value:
            print("ERROR: canonical JSON path is required.")
            return 1
        canonical_path = prompt_value
    summary = summarize_capabilities.summarize_capabilities(Path(canonical_path))
    print(summary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AstraForge driver analysis toolkit.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate", help="Validate raw dataset files."
    )
    validate_parser.add_argument(
        "--raw-root",
        default=str(REPO_ROOT / "data" / "raw"),
        help="Root directory for raw datasets.",
    )
    validate_parser.add_argument(
        "--platform",
        choices=["windows", "linux"],
        help="Limit validation to a specific platform.",
    )
    validate_parser.add_argument(
        "--device-id",
        help="Validate a single device directory under the raw root.",
    )
    validate_parser.set_defaults(func=_handle_validate)

    list_parser = subparsers.add_parser(
        "list-canonicals", help="List canonical files under an output folder."
    )
    list_parser.add_argument(
        "--path", help="Directory to scan for canonical output files."
    )
    list_parser.set_defaults(func=_handle_list_canonicals)

    summarize_parser = subparsers.add_parser(
        "summarize", help="Summarize capabilities from canonical JSON."
    )
    summarize_parser.add_argument(
        "canonical_file", nargs="?", help="Path to canonical JSON file."
    )
    summarize_parser.set_defaults(func=_handle_summarize)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

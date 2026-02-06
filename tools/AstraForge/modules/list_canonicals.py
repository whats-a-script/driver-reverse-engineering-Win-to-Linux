"""Locate canonical files in AstraForge output folders."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional


def list_canonical_files(output_dir: Optional[Path] = None) -> List[Path]:
    if output_dir is None:
        output_value = input("Enter output directory to scan for canonical files: ").strip()
        output_dir = Path(output_value) if output_value else Path.cwd()

    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    return sorted(
        path
        for path in output_dir.rglob("canonical_*")
        if path.is_file() and path.suffix == ".json"
    )

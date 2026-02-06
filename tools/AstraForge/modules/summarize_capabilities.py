"""Capability summarizer for canonical JSON output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str):
        return [value] if value else []
    return [str(value)]


def _format_section(label: str, values: Iterable[str]) -> str:
    entries = [value for value in values if value]
    if not entries:
        return f"{label}: (none)"
    return f"{label}: {', '.join(entries)}"


def summarize_capabilities(canonical_path: Path) -> str:
    with canonical_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    capabilities = data.get("capabilities", {})
    bands = _normalize_list(capabilities.get("bands") or data.get("bands"))
    modes = _normalize_list(capabilities.get("modes") or data.get("modes"))
    features = _normalize_list(capabilities.get("features") or data.get("features"))

    header = f"Capabilities Summary: {data.get('device_id', canonical_path.stem)}"
    if data.get("platform"):
        header += f" ({data['platform']})"

    summary_lines = [
        header,
        _format_section("Bands", bands),
        _format_section("Modes", modes),
        _format_section("Features", features),
    ]
    return "\n".join(summary_lines)

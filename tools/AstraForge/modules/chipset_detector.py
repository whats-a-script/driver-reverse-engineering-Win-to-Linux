"""Chipset auto-detection helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Optional, Tuple


CHIPSET_MAP = {
    "14c3:7927": "mt7927",
    "14c3:0616": "mt7921",
    "8086:2725": "ax210",
}


def _normalize_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if cleaned.startswith("0x"):
        cleaned = cleaned[2:]
    cleaned = cleaned.strip()
    if not cleaned:
        return None
    if len(cleaned) < 4:
        cleaned = cleaned.zfill(4)
    return cleaned


def _search_value(data: object, keys: Iterable[str]) -> Optional[str]:
    if isinstance(data, dict):
        lower_map = {str(k).lower(): v for k, v in data.items()}
        for key in keys:
            if key.lower() in lower_map:
                value = lower_map[key.lower()]
                return str(value) if value is not None else None
        for value in lower_map.values():
            found = _search_value(value, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _search_value(item, keys)
            if found is not None:
                return found
    return None


def _combine_subsystem(vendor: Optional[str], device: Optional[str]) -> Optional[str]:
    if vendor and device:
        return f"{vendor}:{device}"
    return vendor or device


def _parse_pci_device_json(path: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None, None

    vendor_id = _normalize_id(
        _search_value(data, ["vendor_id", "vendorid", "pci_vendor_id"])
    )
    device_id = _normalize_id(
        _search_value(data, ["device_id", "deviceid", "pci_device_id"])
    )
    subsystem_id = _normalize_id(
        _search_value(data, ["subsystem_id", "subsystemid"])
    )
    subsystem_vendor = _normalize_id(
        _search_value(data, ["subsystem_vendor_id", "subsystemvendorid"])
    )
    subsystem_device = _normalize_id(
        _search_value(data, ["subsystem_device_id", "subsystemdeviceid"])
    )
    subsystem = subsystem_id or _combine_subsystem(subsystem_vendor, subsystem_device)
    return vendor_id, device_id, subsystem


def _parse_lspci(path: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None, None, None

    vendor_id = None
    device_id = None
    subsystem = None
    id_pattern = re.compile(r"\[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\]")

    for line in lines:
        match = id_pattern.search(line)
        if match and vendor_id is None and device_id is None:
            vendor_id = _normalize_id(match.group(1))
            device_id = _normalize_id(match.group(2))
        if "subsystem" in line.lower():
            sub_match = id_pattern.search(line)
            if sub_match:
                subsystem_vendor = _normalize_id(sub_match.group(1))
                subsystem_device = _normalize_id(sub_match.group(2))
                subsystem = _combine_subsystem(subsystem_vendor, subsystem_device)
    return vendor_id, device_id, subsystem


def _extract_pci_ids(raw_path: Path, platform: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if platform == "windows":
        return _parse_pci_device_json(raw_path / "pci_device.json")
    if platform == "linux":
        return _parse_lspci(raw_path / "lspci.txt")
    return None, None, None


def detect_chipset(pci_vendor: str, pci_device: str, subsystem: str | None) -> str:
    """Return chipset name or 'unknown'."""
    vendor_id = _normalize_id(pci_vendor)
    device_id = _normalize_id(pci_device)
    if not vendor_id or not device_id:
        return "unknown"
    key = f"{vendor_id}:{device_id}"
    return CHIPSET_MAP.get(key, "unknown")


def _detect_from_raw(raw_path: Path, platform: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    vendor_id, device_id, subsystem = _extract_pci_ids(raw_path, platform)
    chipset = detect_chipset(vendor_id or "", device_id or "", subsystem)
    return chipset, vendor_id, device_id, subsystem

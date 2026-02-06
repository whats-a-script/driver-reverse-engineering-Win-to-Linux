"""Raw dataset validator for AstraForge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional


WINDOWS_REQUIRED = ("pci_device.json", "driver_package.json", "driver_files.json")
WINDOWS_OPTIONAL = ("registry.json", "systeminfo.txt", "netsh_wlan_drivers.txt")
LINUX_REQUIRED = ("lspci.txt",)
LINUX_OPTIONAL = ("uname.txt", "iw_list.txt", "iw_dev.txt", "dmesg.txt", "rfkill.txt")

WINDOWS_JSON = {
    "pci_device.json",
    "driver_package.json",
    "driver_files.json",
    "registry.json",
}


def _check_readable(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            handle.read(1)
        return True
    except OSError:
        return False


def _validate_file(path: Path, required: bool, report: Dict[str, List[str]]) -> None:
    if not path.exists():
        key = "missing_required" if required else "missing_optional"
        report[key].append(str(path))
        return

    if path.name in WINDOWS_JSON:
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except (OSError, json.JSONDecodeError):
            report["invalid_json"].append(str(path))
            return
    else:
        if not _check_readable(path):
            key = "missing_required" if required else "missing_optional"
            report[key].append(str(path))
            return

    report["ok"].append(str(path))


def _iter_device_dirs(base_path: Path) -> Iterable[Path]:
    if not base_path.exists():
        return iter(())
    return (entry for entry in base_path.iterdir() if entry.is_dir())


def validate_raw_datasets(
    raw_root: Path,
    platform: Optional[str] = None,
    device_id: Optional[str] = None,
) -> Dict[str, List[str]]:
    report = {
        "missing_required": [],
        "missing_optional": [],
        "invalid_json": [],
        "ok": [],
    }

    platforms = [platform] if platform else ["windows", "linux"]
    for platform_name in platforms:
        if platform_name not in {"windows", "linux"}:
            continue
        platform_root = raw_root / platform_name
        device_dirs = (
            [platform_root / device_id]
            if device_id
            else list(_iter_device_dirs(platform_root))
        )

        required = WINDOWS_REQUIRED if platform_name == "windows" else LINUX_REQUIRED
        optional = WINDOWS_OPTIONAL if platform_name == "windows" else LINUX_OPTIONAL

        for device_dir in device_dirs:
            for filename in required:
                _validate_file(device_dir / filename, True, report)
            for filename in optional:
                _validate_file(device_dir / filename, False, report)

    return report

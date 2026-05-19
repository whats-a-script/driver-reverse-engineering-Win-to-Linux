# SPDX-License-Identifier: LicenseRef-AstraForge-Proprietary
# Copyright (C) 2026 linuxwifi7 (Charles Ellison). All Rights Reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or
# modification of this file, via any medium, is strictly prohibited.
# See LICENSE at the repository root for full terms.
#
# AstraForge — Windows-to-Linux Driver Reverse Engineering Toolkit
# Version: 1.2.0

import json
import argparse
import textwrap
import os
import threading
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
import re

# Serialises oversized-file prompts so parallel scan workers don't interleave input
_OVERSIZE_PROMPT_LOCK = threading.Lock()


# ============================================================
# CONFIG SYSTEM
# ============================================================

CONFIG_PATH = Path(__file__).parent / "AstraForge.config.json"


def load_config():
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def prompt_for_path(label, saved_value=None, must_exist=True):
    print(f"\n--- {label} ---")
    if saved_value:
        print(f"Last used path:\n{saved_value}")
        confirm = input("Use this path? (Y/n): ").strip().lower()
        if confirm in ("", "y", "yes"):
            if not must_exist or Path(saved_value).exists():
                return saved_value
            print("Saved path does not exist anymore. Please enter a new one.")
    while True:
        new_path = input("Enter folder path: ").strip().strip('"')
        if not must_exist or Path(new_path).exists():
            return new_path
        print("Invalid path. Folder does not exist. Try again.")


def get_paths_for_mode(mode):
    cfg = load_config()

    if mode == "windows":
        raw = prompt_for_path("Windows RAW driver folder", cfg.get("windows_raw"))
        out = prompt_for_path("Windows OUTPUT folder", cfg.get("windows_out"), must_exist=False)
        cfg["windows_raw"] = raw
        cfg["windows_out"] = out
        save_config(cfg)
        return raw, out

    if mode == "linux":
        raw = prompt_for_path("Linux RAW driver folder", cfg.get("linux_raw"))
        out = prompt_for_path("Linux OUTPUT folder", cfg.get("linux_out"), must_exist=False)
        cfg["linux_raw"] = raw
        cfg["linux_out"] = out
        save_config(cfg)
        return raw, out

    if mode == "diff":
        win_json = prompt_for_path("Windows canonical JSON folder", cfg.get("windows_out"))
        lin_json = prompt_for_path("Linux canonical JSON folder", cfg.get("linux_out"))
        diff_out = prompt_for_path("Diff OUTPUT folder", cfg.get("diff_out"), must_exist=False)
        cfg["diff_out"] = diff_out
        save_config(cfg)
        return win_json, lin_json, diff_out

    if mode == "generate":
        canonical_dir = prompt_for_path("Canonical JSON folder", cfg.get("windows_out"))
        out = prompt_for_path("Linux driver OUTPUT folder", cfg.get("driver_out"), must_exist=False)
        cfg["driver_out"] = out
        save_config(cfg)
        return canonical_dir, out

    raise ValueError(f"Unknown mode: {mode}")


# ============================================================
# LOGGING + HELPERS
# ============================================================

VERBOSE = True


def log(msg: str):
    if VERBOSE:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")


def ensure_dir(path: Path):
    if not path.exists():
        log(f"Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    log(f"Loading JSON: {path}")
    if not path.exists():
        log(f"WARNING: JSON file not found: {path}")
        return {}
    for enc in ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"]:
        try:
            with path.open("r", encoding=enc) as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    log(f"ERROR: Could not decode JSON: {path}")
    return {}


def load_text(path: Path):
    log(f"Loading text: {path}")
    if not path.exists():
        log(f"WARNING: text file not found: {path}")
        return ""
    for enc in ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"]:
        try:
            with path.open("r", encoding=enc) as f:
                content = f.read()
            if "\x00" not in content:
                return content
        except (UnicodeDecodeError, UnicodeError):
            continue
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _norm_id(hex_str: str) -> str:
    """'0x14C3' or '14C3' -> '14C3' (upper, no prefix)."""
    return hex_str.upper().replace("0X", "").lstrip("0") or "0"


def _c_ident(name: str) -> str:
    """Convert any string to a valid lowercase C identifier."""
    ident = re.sub(r"[^a-zA-Z0-9]", "_", name).lower().strip("_")
    ident = re.sub(r"_+", "_", ident)          # collapse repeated underscores
    if ident and ident[0].isdigit():
        ident = "drv_" + ident
    return ident or "unknown"


def _derive_chipset_name(canonical: dict, fallback: str = "unknown") -> str:
    """
    Derive a clean driver/module name from canonical device data.

    Priority:
      1. original_filename from PE resources → e.g. "mt7927-linux"
      2. vendor_id + device_id              → e.g. "mt7927", "rtl8125"
      3. Sanitised device description
      4. fallback (folder name)
    """
    dev = canonical.get("device", {})

    # Priority 1: manufacturer's original filename embedded in PE binary
    orig = dev.get("original_filename", "")
    if orig and len(orig) >= 3:
        stem = _c_ident(orig)
        if stem and stem not in ("unknown", "driver", "bin"):
            return f"{stem}-linux"
    vid = dev.get("vendor_id", "")
    did = dev.get("device_id", "")

    # Known vendor prefixes for friendly names
    _VENDOR_PREFIX = {
        "14C3": "mt",    # MediaTek
        "10EC": "rtl",   # Realtek (PCI)
        "0BDA": "rtl",   # Realtek (USB)
        "8086": "iwl",   # Intel
        "168C": "ath",   # Atheros/Qualcomm
        "0CF3": "ath",   # Atheros (USB)
        "0B05": "asus",  # ASUS
        "14E4": "brcm",  # Broadcom
        "0A5C": "brcm",  # Broadcom (USB BT)
        "1969": "atl",   # Atheros/Attansic LAN
        "1B4B": "mv",    # Marvell
        "1AF4": "virt",  # VirtIO
        "1022": "amd",   # AMD
        "1002": "amd",   # AMD GPU
        "10DE": "nv",    # NVIDIA
        "8087": "iwl",   # Intel (USB BT)
        "0846": "netgear",
        "0B4B": "tp",    # TP-Link (USB)
        "2357": "tp",    # TP-Link (USB alt)
        "046D": "logi",  # Logitech
        "045E": "ms",    # Microsoft
        "04F2": "chic",  # Chicony
        "0458": "kye",   # KYE/Genius
        "1532": "razer", # Razer
        "1B1C": "cors",  # Corsair
        "3938": "wooting",
        "0D8C": "cmedia",# C-Media audio
        "1043": "asus",  # ASUS (PCI)
        "10B9": "ali",   # ALi
    }

    if vid and did:
        raw_vid = vid.upper().replace("0X", "")
        raw_did = did.upper().replace("0X", "")
        prefix  = _VENDOR_PREFIX.get(raw_vid, "")
        if prefix:
            return f"{prefix}{raw_did.lower()}"        # e.g. "mt7927", "rtl8125"
        return f"v{raw_vid.lower()}_{raw_did.lower()}" # e.g. "v046d_c07c"

    # Fallback: sanitise description
    desc = dev.get("description") or ""
    if desc:
        # Strip common noise words
        noise = r"\b(pcie|pci|usb|adapter|controller|device|family|series|"  \
                r"wireless|network|wi-fi|wifi|wlan|ethernet|gigabit|"          \
                r"windows|linux|driver|express|express root|root|port)\b"
        cleaned = re.sub(noise, "", desc, flags=re.I)
        cleaned = re.sub(r"\s+", "_", cleaned.strip())
        ident   = _c_ident(cleaned)
        if len(ident) >= 3:
            return ident

    return _c_ident(fallback)


# PCI infrastructure class names/fragments to skip during auto-detect
_PCI_INFRA = frozenset([
    "host bridge", "pci bridge", "isa bridge", "root port", "pcie port",
    "acpi", "smbios", "dma", "timer", "pic", "processor", "system board",
    "pci standard", "generic bus", "amd psp",
])


def _is_infrastructure(name: str) -> bool:
    low = name.lower()
    return any(frag in low for frag in _PCI_INFRA)


# ============================================================
# DEVICE TYPE DETECTION
# ============================================================

# Maps device type tag -> Linux subsystem description
DEVICE_TYPES = {
    "wifi":         "WiFi (mac80211 / PCI)",
    "ethernet_pci": "Ethernet (net_device / PCI)",
    "ethernet_usb": "Ethernet (usbnet / USB)",
    "bluetooth":    "Bluetooth (HCI)",
    "audio":        "Audio (ALSA / HDA)",
    "hid":          "HID (human interface)",
    "display":      "Display / GPU (DRM/KMS)",
    "storage":      "Storage (SCSI/NVMe)",
    "usb_generic":  "USB (generic)",
    "generic_pci":  "Generic PCI",
}


def detect_device_type(canonical: dict) -> str:
    """
    Infer the Linux driver subsystem from canonical device metadata.
    Returns one of the keys in DEVICE_TYPES.
    """
    desc  = (canonical["device"].get("description") or
             canonical["device"].get("name") or "").lower()
    cls   = (canonical["device"].get("class") or "").lower()
    bus   = (canonical["device"].get("bus") or "pci").lower()
    modes = canonical["driver"]["capabilities"].get("modes") or []

    # --- Bluetooth (before WiFi: "Intel Wireless Bluetooth" must not match wifi) ---
    if "bluetooth" in desc or "bluetooth" in cls:
        return "bluetooth"

    # --- WiFi ---
    wifi_kw = {"wi-fi", "wifi", "wireless", "wlan", "802.11", "pcie adapter"}
    if any(w in desc or w in cls for w in wifi_kw) or \
       any("802.11" in m for m in modes):
        return "wifi"

    # --- Ethernet ---
    eth_kw = {"ethernet", "gigabit", "gbe", "lan controller", "network controller",
              "realtek pcie", "realtek usb", "intel i2", "aqtion", "killer"}
    if any(w in desc or w in cls for w in eth_kw):
        return "ethernet_usb" if bus == "usb" else "ethernet_pci"

    # --- Audio ---
    audio_kw = {"audio", "sound", "hda", "high definition", "codec",
                "headset", "speaker", "microphone", "ac97"}
    if any(w in desc or w in cls for w in audio_kw):
        return "audio"

    # --- HID ---
    hid_kw = {"hid", "human interface", "mouse", "keyboard",
              "gamepad", "joystick", "touchpad", "digitizer"}
    if any(w in desc or w in cls for w in hid_kw):
        return "hid"

    # --- Display / GPU ---
    gpu_kw = {"display", "graphics", "vga", "gpu", "radeon", "geforce",
              "intel hd", "intel uhd", "iris", "rx 6", "rtx", "gtx"}
    if any(w in desc or w in cls for w in gpu_kw):
        return "display"

    # --- Storage ---
    stor_kw = {"nvme", "sata", "ahci", "storage", "scsi", "raid", "ssd",
               "hard disk", "disk drive"}
    if any(w in desc or w in cls for w in stor_kw):
        return "storage"

    # --- Generic USB ---
    if bus == "usb":
        return "usb_generic"

    return "generic_pci"


# ============================================================
# CANONICAL STRUCTURE
# ============================================================

def empty_canonical(os_name: str, chipset: str):
    return {
        "device": {
            "name":        chipset,
            "description": None,   # friendly name from Windows/lspci
            "class":       None,   # Windows device class (Net, Media, HIDClass, …)
            "bus":         "pci",  # "pci" or "usb"
            "vendor_id":   None,   # PCI VEN or USB VID  (0x-prefixed)
            "device_id":   None,   # PCI DEV or USB PID  (0x-prefixed)
            "subsystem_id": None,
            "revision":    None,
        },
        "driver": {
            "version":  None,
            "date":     None,
            "provider": None,
            "files":    [],
            "firmware": [],
            "registry_keys": [],
            "capabilities": {
                "bands":    [],
                "modes":    [],
                "features": [],
            },
        },
        "system": {
            "os":             os_name,
            "kernel_or_build": None,
            "architecture":   None,
            "notes":          [],
        },
    }


# ============================================================
# WINDOWS NORMALIZATION — any peripheral
# ============================================================

def extract_device_from_windows(pci_json, canonical,
                                 vendor_id=None, device_id=None):
    """
    Extract device IDs from Windows pci_device.json.
    Handles both PCI (VEN_/DEV_) and USB (VID_/PID_) instance IDs.
    If vendor_id/device_id given, matches exactly.
    Otherwise auto-selects the first non-infrastructure peripheral.
    """
    if not pci_json:
        log("No device JSON; skipping device extraction.")
        return
    log("Extracting device info (Windows).")

    devices = pci_json if isinstance(pci_json, list) else [pci_json]
    target_ven = _norm_id(vendor_id) if vendor_id else None
    target_dev = _norm_id(device_id) if device_id else None

    for device in devices:
        if not isinstance(device, dict):
            continue

        inst = (device.get("InstanceId") or device.get("DeviceID") or
                device.get("PNPDeviceID") or "").upper()
        friendly = (device.get("FriendlyName") or device.get("Name") or "")
        dev_class = (device.get("Class") or device.get("PNPClass") or "")

        if not inst or not friendly:
            continue

        # Skip PCI infrastructure (bridges, root ports, ACPI, …)
        if _is_infrastructure(friendly):
            continue

        # Determine bus type
        is_usb = inst.startswith("USB\\")
        is_pci = inst.startswith("PCI\\")

        if not is_pci and not is_usb:
            continue

        # Parse IDs
        if is_pci:
            if "VEN_" not in inst:
                continue
            ven = inst.split("VEN_")[1].split("&")[0]
            dev = inst.split("DEV_")[1].split("&")[0] if "DEV_" in inst else ""
        else:  # USB
            if "VID_" not in inst:
                continue
            ven = inst.split("VID_")[1].split("&")[0]
            dev = inst.split("PID_")[1].split("&")[0] if "PID_" in inst else ""

        # Apply explicit ID filter
        if target_ven and ven != target_ven:
            continue
        if target_dev and dev != target_dev:
            continue

        # Auto-detect: if no filter, skip infrastructure-class devices
        if not target_ven and not target_dev:
            skip_classes = {"system", "computer", "processor", "printqueue",
                            "volume", "diskdrive"}
            if dev_class.lower() in skip_classes:
                continue

        # Populate canonical
        canonical["device"]["bus"]       = "usb" if is_usb else "pci"
        canonical["device"]["vendor_id"] = f"0x{ven}"
        if dev:
            canonical["device"]["device_id"] = f"0x{dev}"
        if is_pci:
            if "SUBSYS_" in inst:
                subsys = inst.split("SUBSYS_")[1].split("&")[0]
                canonical["device"]["subsystem_id"] = f"0x{subsys}"
            if "REV_" in inst:
                rev = inst.split("REV_")[1].split("\\")[0]
                canonical["device"]["revision"] = f"0x{rev}"
        canonical["device"]["description"] = friendly
        canonical["device"]["class"]       = dev_class

        log(f"Device match [{canonical['device']['bus'].upper()}]: "
            f"VEN/VID={ven} DEV/PID={dev} | {friendly} [{dev_class}]")
        break


def extract_driver_package_windows(pkg_json, canonical,
                                    vendor_id=None, device_id=None):
    """
    Extract version/date/provider from driver_package.json.
    Accepts any driver package; skips PCI infrastructure entries.
    Prefers packages whose DeviceName matches the already-known description.
    """
    if not pkg_json:
        log("No driver_package JSON; skipping.")
        return
    log("Extracting driver package info (Windows).")

    packages = pkg_json if isinstance(pkg_json, list) else [pkg_json]
    known_desc = (canonical["device"].get("description") or "").lower()

    best = None
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        dev_name = (pkg.get("DeviceName") or "").strip()
        if not dev_name or _is_infrastructure(dev_name):
            continue

        # Best match: name contains known description fragment
        if known_desc and known_desc[:12] in dev_name.lower():
            best = pkg
            break
        if best is None:
            best = pkg  # fallback: first non-infrastructure package

    if best:
        provider = (best.get("DriverProviderName") or
                    best.get("ProviderName") or
                    best.get("provider") or "")
        canonical["driver"]["version"]  = best.get("DriverVersion") or best.get("version")
        canonical["driver"]["date"]     = best.get("DriverDate")    or best.get("date")
        canonical["driver"]["provider"] = provider
        if not canonical["device"]["description"]:
            canonical["device"]["description"] = best.get("DeviceName", "")
        log(f"Driver package: {best.get('DeviceName')} v{canonical['driver']['version']}")


def extract_driver_files_windows(files_json, canonical):
    """Extract InfName / Driver file paths from driver_files.json."""
    if not files_json:
        log("No driver_files JSON; skipping.")
        return
    log("Extracting driver files (Windows).")
    files, firmware = [], []

    entries = files_json if isinstance(files_json, list) else [files_json]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        inf = entry.get("InfName")
        if inf:
            files.append(inf)
        drv = entry.get("Driver")
        if drv and drv not in (None, "null"):
            files.append(drv)
            low = drv.lower()
            if "fw" in low or low.endswith(".bin"):
                firmware.append(drv)

    canonical["driver"]["files"]    = list(dict.fromkeys(files))
    canonical["driver"]["firmware"] = list(dict.fromkeys(firmware))


def _parse_netsh_interfaces(text: str) -> dict:
    """Split 'netsh wlan show drivers' output into {iface_name: block}."""
    interfaces, name, lines = {}, None, []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"interface name\s*:", stripped, re.I):
            if name:
                interfaces[name] = "\n".join(lines)
            name = stripped.split(":", 1)[1].strip()
            lines = [line]
        elif name is not None:
            lines.append(line)
    if name and lines:
        interfaces[name] = "\n".join(lines)
    return interfaces


def extract_capabilities_from_netsh_windows(netsh_text: str, canonical: dict):
    """
    Extract WiFi bands/modes/features from netsh wlan show drivers.
    Skipped automatically for non-WiFi device types.
    Picks the interface matching canonical provider/description.
    """
    if not netsh_text:
        log("No netsh_wlan_drivers.txt; skipping capabilities.")
        return

    # Only applies to WiFi devices
    dev_type = detect_device_type(canonical)
    if dev_type != "wifi":
        log(f"Device type is '{dev_type}' — skipping netsh WiFi capabilities.")
        return

    log("Extracting WiFi capabilities from netsh (Windows).")
    interfaces = _parse_netsh_interfaces(netsh_text)
    provider   = (canonical["driver"].get("provider") or "").lower()
    desc       = (canonical["device"].get("description") or "").lower()

    block = None
    for iface_block in interfaces.values():
        low = iface_block.lower()
        if provider and provider[:8] in low:
            block = iface_block
            break
        if desc and desc[:10] in low:
            block = iface_block
            break
        if block is None:
            block = iface_block

    if not block:
        block = netsh_text

    bands, modes, features = set(), set(), set()
    for line in block.splitlines():
        low = line.lower()
        if "radio types supported" in low:
            modes.update(line.split(":")[-1].split())
        if "channel width" in low:
            features.add(line.strip())
        if "802.11ax" in low or "wi-fi 6" in low:
            features.add("wifi6")
        if "802.11be" in low or "wi-fi 7" in low:
            features.add("wifi7")
        if "6ghz" in low or "6 ghz" in low:
            bands.add("6ghz")
        if "5ghz" in low or "5 ghz" in low:
            bands.add("5ghz")
        if "2.4ghz" in low or "2.4 ghz" in low:
            bands.add("2.4ghz")

    canonical["driver"]["capabilities"]["bands"]    = sorted(bands)
    canonical["driver"]["capabilities"]["modes"]    = sorted(modes)
    canonical["driver"]["capabilities"]["features"] = sorted(features)


def extract_systeminfo_windows(sysinfo_text: str, canonical: dict):
    if not sysinfo_text:
        log("No systeminfo.txt; skipping system info.")
        return
    log("Extracting system info (Windows).")
    build, arch, notes = None, None, []
    for line in sysinfo_text.splitlines():
        stripped = line.strip()
        if re.match(r"os (name|version)\s*:", stripped, re.I):
            notes.append(stripped)
        if re.match(r"os version\s*:", stripped, re.I) and not build:
            build = stripped.split(":", 1)[-1].strip()
        if re.match(r"system type\s*:", stripped, re.I) and not arch:
            arch = stripped.split(":", 1)[-1].strip()
    canonical["system"]["kernel_or_build"] = build
    canonical["system"]["architecture"]    = arch
    canonical["system"]["notes"]           = notes


def normalize_windows(vendor_id=None, device_id=None):
    raw_path, out_path = get_paths_for_mode("windows")
    folder_name = Path(raw_path).name

    log("=== WINDOWS NORMALIZATION START ===")
    ensure_dir(Path(out_path))

    canonical  = empty_canonical("windows", folder_name)
    pci_json   = load_json(Path(raw_path) / "pci_device.json")
    pkg_json   = load_json(Path(raw_path) / "driver_package.json")
    files_json = load_json(Path(raw_path) / "driver_files.json")
    sysinfo    = load_text(Path(raw_path) / "systeminfo.txt")
    netsh      = load_text(Path(raw_path) / "netsh_wlan_drivers.txt")

    extract_device_from_windows(pci_json, canonical, vendor_id, device_id)
    extract_driver_package_windows(pkg_json, canonical, vendor_id, device_id)
    extract_driver_files_windows(files_json, canonical)
    extract_capabilities_from_netsh_windows(netsh, canonical)
    extract_systeminfo_windows(sysinfo, canonical)

    # Derive a proper chipset name from extracted device data
    chipset = _derive_chipset_name(canonical, fallback=folder_name)
    canonical["device"]["name"] = chipset
    log(f"Chipset name: {chipset}")

    timestamp   = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(out_path) / f"canonical_{chipset}_windows_{timestamp}.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(canonical, f, indent=2)
    log(f"Written: {output_file}")
    log("=== WINDOWS NORMALIZATION COMPLETE ===")
    return canonical


# ============================================================
# LINUX NORMALIZATION — any peripheral
# ============================================================

def extract_pci_from_linux(lspci_text: str, canonical: dict, vendor_id=None):
    """
    Parse standard lspci output for any peripheral device.
    Format: "BUS DESC [CLASS]: VENDOR NAME [VID:DID]"
    """
    if not lspci_text:
        log("No lspci.txt; skipping PCI extraction (Linux).")
        return
    log("Extracting PCI info (Linux).")

    target_ven = _norm_id(vendor_id) if vendor_id else None

    for line in lspci_text.splitlines():
        m = re.search(r"\[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\]", line)
        if not m:
            continue
        ven, dev = m.group(1).upper(), m.group(2).upper()

        if target_ven:
            if ven == target_ven:
                canonical["device"]["vendor_id"] = f"0x{ven}"
                canonical["device"]["device_id"] = f"0x{dev}"
                log(f"PCI match by vendor: {line.strip()}")
                return
        else:
            # Skip obvious infrastructure vendors
            if ven in {"8086", "1022"} and _is_infrastructure(line):
                continue
            canonical["device"]["vendor_id"] = f"0x{ven}"
            canonical["device"]["device_id"] = f"0x{dev}"
            log(f"PCI auto-detect: {line.strip()}")
            return

    log("No matching PCI device found in lspci output.")


def extract_usb_from_linux(lsusb_text: str, canonical: dict,
                            vendor_id=None, device_id=None):
    """
    Parse lsusb output for USB devices.
    Format: "Bus NNN Device NNN: ID VID:PID Manufacturer Product"
    """
    if not lsusb_text:
        log("No lsusb.txt; skipping USB extraction (Linux).")
        return
    log("Extracting USB info (Linux).")

    target_vid = _norm_id(vendor_id) if vendor_id else None
    target_pid = _norm_id(device_id) if device_id else None

    for line in lsusb_text.splitlines():
        m = re.search(r"ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})", line)
        if not m:
            continue
        vid, pid = m.group(1).upper(), m.group(2).upper()

        # Skip hubs and root hubs
        if vid in {"1D6B", "8087"} and "hub" in line.lower():
            continue

        if target_vid and vid != target_vid:
            continue
        if target_pid and pid != target_pid:
            continue

        canonical["device"]["bus"]       = "usb"
        canonical["device"]["vendor_id"] = f"0x{vid}"
        canonical["device"]["device_id"] = f"0x{pid}"
        # Description from remainder of line
        desc_m = re.search(r"ID\s+[0-9a-fA-F:]+\s+(.*)", line)
        if desc_m and not canonical["device"]["description"]:
            canonical["device"]["description"] = desc_m.group(1).strip()
        log(f"USB match: VID={vid} PID={pid} | {line.strip()}")
        return


def extract_systeminfo_linux(uname_text: str, canonical: dict,
                              dmesg_text: str = ""):
    if not uname_text:
        if dmesg_text:
            m = re.search(r"Linux version (\S+)", dmesg_text)
            if m:
                canonical["system"]["kernel_or_build"] = m.group(1)
                log(f"Kernel from dmesg: {m.group(1)}")
            arch_m = re.search(
                r"\b(x86_64|aarch64|armv7l|i686|riscv64|arm64)\b", dmesg_text)
            if arch_m:
                canonical["system"]["architecture"] = arch_m.group(1)
        else:
            log("No uname.txt or dmesg; skipping system info (Linux).")
        return
    log("Extracting system info (Linux).")
    parts = uname_text.split()
    if len(parts) >= 3:
        canonical["system"]["kernel_or_build"] = parts[2]
    if len(parts) >= 13:
        canonical["system"]["architecture"] = parts[12]


def extract_capabilities_linux(iw_text: str, canonical: dict):
    """Extract WiFi caps from iw output. Skipped for non-WiFi devices."""
    if not iw_text:
        return
    dev_type = detect_device_type(canonical)
    if dev_type != "wifi":
        log(f"Device type is '{dev_type}' — skipping iw WiFi capabilities.")
        return

    log("Extracting WiFi capabilities from iw (Linux).")
    bands, modes, features = set(), set(), set()
    for line in iw_text.splitlines():
        low = line.lower()
        if "capabilities" in low or "supported interface modes" in low:
            features.add(line.strip())
        if "vht" in low or " he " in low or "eht" in low:
            features.add(line.strip())
        if "6 ghz" in low or "6ghz" in low:
            bands.add("6ghz")
        if "5 ghz" in low or "5ghz" in low:
            bands.add("5ghz")
        if "2.4 ghz" in low or "2.4ghz" in low:
            bands.add("2.4ghz")
        if re.search(r"\b(managed|ap|monitor|p2p)\b", low):
            modes.add(line.strip())

    canonical["driver"]["capabilities"]["bands"]    = sorted(bands)
    canonical["driver"]["capabilities"]["modes"]    = sorted(modes)
    canonical["driver"]["capabilities"]["features"] = sorted(features)


def normalize_linux(vendor_id=None, device_id=None):
    raw_path, out_path = get_paths_for_mode("linux")
    folder_name = Path(raw_path).name

    log("=== LINUX NORMALIZATION START ===")
    ensure_dir(Path(out_path))

    canonical = empty_canonical("linux", folder_name)

    lspci   = load_text(Path(raw_path) / "lspci.txt")
    lsusb   = load_text(Path(raw_path) / "lsusb.txt")
    uname   = load_text(Path(raw_path) / "uname.txt")
    dmesg   = load_text(Path(raw_path) / "dmesg.txt")
    iw_list = load_text(Path(raw_path) / "iw_list.txt")
    iw_dev  = load_text(Path(raw_path) / "iw_dev.txt")

    extract_pci_from_linux(lspci, canonical, vendor_id)
    extract_usb_from_linux(lsusb, canonical, vendor_id, device_id)
    extract_systeminfo_linux(uname, canonical, dmesg_text=dmesg)
    extract_capabilities_linux("\n".join([iw_list, iw_dev]), canonical)

    chipset = _derive_chipset_name(canonical, fallback=folder_name)
    canonical["device"]["name"] = chipset
    log(f"Chipset name: {chipset}")

    timestamp   = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(out_path) / f"canonical_{chipset}_linux_{timestamp}.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(canonical, f, indent=2)
    log(f"Written: {output_file}")
    log("=== LINUX NORMALIZATION COMPLETE ===")
    return canonical


# ============================================================
# DIFF ENGINE
# ============================================================

def diff_canonical(win: dict, lin: dict):
    log("=== DIFF ENGINE START ===")
    diff = {"device": {}, "driver": {"capabilities": {}}, "system": {}}

    for key in ["name", "vendor_id", "device_id", "subsystem_id", "revision"]:
        diff["device"][key] = {
            "windows": win["device"].get(key),
            "linux":   lin["device"].get(key),
            "match":   win["device"].get(key) == lin["device"].get(key),
        }
    for key in ["version", "date", "provider"]:
        diff["driver"][key] = {
            "windows": win["driver"].get(key),
            "linux":   lin["driver"].get(key),
            "match":   win["driver"].get(key) == lin["driver"].get(key),
        }
    for key in ["bands", "modes", "features"]:
        w = set(win["driver"]["capabilities"].get(key) or [])
        l = set(lin["driver"]["capabilities"].get(key) or [])
        diff["driver"]["capabilities"][key] = {
            "windows_only": sorted(w - l),
            "linux_only":   sorted(l - w),
            "both":         sorted(w & l),
        }
    for key in ["kernel_or_build", "architecture"]:
        diff["system"][key] = {
            "windows": win["system"].get(key),
            "linux":   lin["system"].get(key),
            "match":   win["system"].get(key) == lin["system"].get(key),
        }

    log("=== DIFF ENGINE COMPLETE ===")
    return diff


def run_diff():
    win_path, lin_path, diff_out = get_paths_for_mode("diff")
    log("=== RUNNING CROSS-PLATFORM DIFF ===")

    win_files = sorted(Path(win_path).glob("canonical_*_windows_*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    lin_files = sorted(Path(lin_path).glob("canonical_*_linux_*.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)

    if not win_files:
        log("ERROR: No Windows canonical JSON found.")
        return
    if not lin_files:
        log("ERROR: No Linux canonical JSON found.")
        return

    with win_files[0].open("r", encoding="utf-8") as f:
        win = json.load(f)
    with lin_files[0].open("r", encoding="utf-8") as f:
        lin = json.load(f)

    diff = diff_canonical(win, lin)
    ensure_dir(Path(diff_out))

    ts       = datetime.now().strftime("%Y-%m-%d_%H-%M")
    diff_json = Path(diff_out) / f"diff_{ts}.json"
    diff_txt  = Path(diff_out) / f"summary_{ts}.txt"

    with diff_json.open("w", encoding="utf-8") as f:
        json.dump(diff, f, indent=2)

    with diff_txt.open("w", encoding="utf-8") as f:
        f.write("Cross-Platform Driver Diff Summary\n====================================\n\n")
        f.write("Device:\n")
        for k, v in diff["device"].items():
            f.write(f"  {k}: win={v['windows']} | lin={v['linux']} | match={v['match']}\n")
        f.write("\nDriver:\n")
        for k, v in diff["driver"].items():
            if k == "capabilities":
                continue
            f.write(f"  {k}: win={v['windows']} | lin={v['linux']} | match={v['match']}\n")
        f.write("\nCapabilities:\n")
        for k, v in diff["driver"]["capabilities"].items():
            f.write(f"  {k}: windows_only={v['windows_only']}  "
                    f"linux_only={v['linux_only']}  both={v['both']}\n")
        f.write("\nSystem:\n")
        for k, v in diff["system"].items():
            f.write(f"  {k}: win={v['windows']} | lin={v['linux']} | match={v['match']}\n")

    log(f"Diff: {diff_json}")
    log(f"Summary: {diff_txt}")
    log("=== DIFF OUTPUT WRITTEN ===")


# ============================================================
# LINUX DRIVER GENERATOR — type-aware
# ============================================================

def _fw_macros(firmware: list) -> str:
    return ("\n".join(f'MODULE_FIRMWARE("{fw}");' for fw in firmware)
            if firmware else "/* No firmware files identified */")


# ---- WiFi (mac80211) ----------------------------------------

def _band_2ghz(cs: str) -> str:
    return textwrap.dedent(f"""\
        #define CHAN2G(_f,_i) {{ .band=NL80211_BAND_2GHZ, .center_freq=(_f), .hw_value=(_i), .max_power=20 }}
        static struct ieee80211_channel {cs}_2ghz_ch[] = {{
            CHAN2G(2412,1),CHAN2G(2417,2),CHAN2G(2422,3),CHAN2G(2427,4),CHAN2G(2432,5),
            CHAN2G(2437,6),CHAN2G(2442,7),CHAN2G(2447,8),CHAN2G(2452,9),CHAN2G(2457,10),
            CHAN2G(2462,11),CHAN2G(2467,12),CHAN2G(2472,13),
        }};
        static struct ieee80211_rate {cs}_2ghz_rates[] = {{
            {{.bitrate=10,.hw_value=0}}, {{.bitrate=20,.hw_value=1,.flags=IEEE80211_RATE_SHORT_PREAMBLE}},
            {{.bitrate=55,.hw_value=2,.flags=IEEE80211_RATE_SHORT_PREAMBLE}},
            {{.bitrate=110,.hw_value=3,.flags=IEEE80211_RATE_SHORT_PREAMBLE}},
            {{.bitrate=60,.hw_value=4}},  {{.bitrate=90,.hw_value=5}},
            {{.bitrate=120,.hw_value=6}}, {{.bitrate=180,.hw_value=7}},
            {{.bitrate=240,.hw_value=8}}, {{.bitrate=360,.hw_value=9}},
            {{.bitrate=480,.hw_value=10}},{{.bitrate=540,.hw_value=11}},
        }};
        static struct ieee80211_supported_band {cs}_band_2ghz = {{
            .channels={cs}_2ghz_ch, .n_channels=ARRAY_SIZE({cs}_2ghz_ch),
            .rates={cs}_2ghz_rates,  .n_rates=ARRAY_SIZE({cs}_2ghz_rates),
            .ht_cap={{.ht_supported=true,
                .cap=IEEE80211_HT_CAP_SGI_20|IEEE80211_HT_CAP_SGI_40|IEEE80211_HT_CAP_SUP_WIDTH_20_40,
                .ampdu_factor=IEEE80211_HT_MAX_AMPDU_64K,
                .ampdu_density=IEEE80211_HT_MPDU_DENSITY_8,
                .mcs={{.rx_mask={{0xff,0xff}}, .tx_params=IEEE80211_HT_MCS_TX_DEFINED}},
            }},
        }};
    """)


def _band_5ghz(cs: str) -> str:
    return textwrap.dedent(f"""\
        #define CHAN5G(_f,_i) {{ .band=NL80211_BAND_5GHZ, .center_freq=(_f), .hw_value=(_i), .max_power=23 }}
        static struct ieee80211_channel {cs}_5ghz_ch[] = {{
            CHAN5G(5180,36), CHAN5G(5200,40), CHAN5G(5220,44), CHAN5G(5240,48),
            CHAN5G(5260,52), CHAN5G(5280,56), CHAN5G(5300,60), CHAN5G(5320,64),
            CHAN5G(5500,100),CHAN5G(5520,104),CHAN5G(5540,108),CHAN5G(5560,112),
            CHAN5G(5580,116),CHAN5G(5600,120),CHAN5G(5620,124),CHAN5G(5640,128),
            CHAN5G(5660,132),CHAN5G(5680,136),CHAN5G(5700,140),CHAN5G(5720,144),
            CHAN5G(5745,149),CHAN5G(5765,153),CHAN5G(5785,157),CHAN5G(5805,161),CHAN5G(5825,165),
        }};
        static struct ieee80211_rate {cs}_5ghz_rates[] = {{
            {{.bitrate=60,.hw_value=0}}, {{.bitrate=90,.hw_value=1}},
            {{.bitrate=120,.hw_value=2}},{{.bitrate=180,.hw_value=3}},
            {{.bitrate=240,.hw_value=4}},{{.bitrate=360,.hw_value=5}},
            {{.bitrate=480,.hw_value=6}},{{.bitrate=540,.hw_value=7}},
        }};
        static struct ieee80211_supported_band {cs}_band_5ghz = {{
            .channels={cs}_5ghz_ch, .n_channels=ARRAY_SIZE({cs}_5ghz_ch),
            .rates={cs}_5ghz_rates, .n_rates=ARRAY_SIZE({cs}_5ghz_rates),
            .ht_cap={{.ht_supported=true,
                .cap=IEEE80211_HT_CAP_SGI_20|IEEE80211_HT_CAP_SGI_40|IEEE80211_HT_CAP_SUP_WIDTH_20_40,
                .ampdu_factor=IEEE80211_HT_MAX_AMPDU_64K, .ampdu_density=IEEE80211_HT_MPDU_DENSITY_8,
                .mcs={{.rx_mask={{0xff,0xff}}, .tx_params=IEEE80211_HT_MCS_TX_DEFINED}},
            }},
            .vht_cap={{.vht_supported=true,
                .cap=IEEE80211_VHT_CAP_MAX_MPDU_LENGTH_11454|IEEE80211_VHT_CAP_RXLDPC|
                     IEEE80211_VHT_CAP_SHORT_GI_80|IEEE80211_VHT_CAP_TXSTBC|
                     IEEE80211_VHT_CAP_RXSTBC_1|IEEE80211_VHT_CAP_MAX_A_MPDU_LENGTH_EXPONENT_MASK,
                .vht_mcs={{.rx_mcs_map=cpu_to_le16(0xfffa), .tx_mcs_map=cpu_to_le16(0xfffa)}},
            }},
        }};
    """)


def _band_6ghz(cs: str) -> str:
    return textwrap.dedent(f"""\
        #define CHAN6G(_f,_i) {{ .band=NL80211_BAND_6GHZ, .center_freq=(_f), .hw_value=(_i), .max_power=23 }}
        static struct ieee80211_channel {cs}_6ghz_ch[] = {{
            CHAN6G(5955,1),  CHAN6G(5975,5),  CHAN6G(5995,9),  CHAN6G(6015,13),
            CHAN6G(6035,17), CHAN6G(6055,21), CHAN6G(6075,25), CHAN6G(6095,29),
            CHAN6G(6115,33), CHAN6G(6135,37), CHAN6G(6155,41), CHAN6G(6175,45),
            CHAN6G(6195,49), CHAN6G(6215,53), CHAN6G(6235,57), CHAN6G(6255,61),
            CHAN6G(6275,65), CHAN6G(6295,69), CHAN6G(6315,73), CHAN6G(6335,77),
            CHAN6G(6355,81), CHAN6G(6375,85), CHAN6G(6395,89), CHAN6G(6415,93),
            CHAN6G(6435,97), CHAN6G(6455,101),CHAN6G(6475,105),CHAN6G(6495,109),
            CHAN6G(6515,113),CHAN6G(6535,117),CHAN6G(6555,121),CHAN6G(6575,125),
            CHAN6G(6595,129),CHAN6G(6615,133),CHAN6G(6635,137),CHAN6G(6655,141),
            CHAN6G(6675,145),CHAN6G(6695,149),CHAN6G(6715,153),CHAN6G(6735,157),
            CHAN6G(6755,161),CHAN6G(6775,165),CHAN6G(6795,169),CHAN6G(6815,173),
            CHAN6G(6835,177),CHAN6G(6855,181),CHAN6G(6875,185),CHAN6G(6895,189),
            CHAN6G(6915,193),CHAN6G(6935,197),CHAN6G(6955,201),CHAN6G(6975,205),
            CHAN6G(6995,209),CHAN6G(7015,213),CHAN6G(7035,217),CHAN6G(7055,221),
            CHAN6G(7075,225),CHAN6G(7095,229),CHAN6G(7115,233),
        }};
        static struct ieee80211_supported_band {cs}_band_6ghz = {{
            .channels={cs}_6ghz_ch, .n_channels=ARRAY_SIZE({cs}_6ghz_ch),
            .rates=NULL, .n_rates=0,
        }};
    """)


def _gen_wifi(cs: str, CS: str, canonical: dict) -> tuple:
    """Returns (c_body_extra, h_extra, includes_extra)."""
    bands    = canonical["driver"]["capabilities"].get("bands") or []
    firmware = canonical["driver"].get("firmware") or []
    sub_id   = canonical["device"].get("subsystem_id")

    band_defs, band_assign = [], []
    if "2.4ghz" in bands or not bands:
        band_defs.append(_band_2ghz(cs))
        band_assign.append(f"\thw->wiphy->bands[NL80211_BAND_2GHZ] = &{cs}_band_2ghz;")
    if "5ghz" in bands or not bands:
        band_defs.append(_band_5ghz(cs))
        band_assign.append(f"\thw->wiphy->bands[NL80211_BAND_5GHZ] = &{cs}_band_5ghz;")
    if "6ghz" in bands:
        band_defs.append(_band_6ghz(cs))
        band_assign.append(f"\thw->wiphy->bands[NL80211_BAND_6GHZ] = &{cs}_band_6ghz;")

    # Subsystem PCI entry
    sub_entry = ""
    if sub_id and len(sub_id.replace("0x","").replace("0X","")) == 8:
        raw = sub_id.replace("0x","").replace("0X","")
        sub_entry = (f"\t{{ PCI_DEVICE_SUB({CS}_VENDOR_ID, {CS}_DEVICE_ID, "
                     f"0x{raw[:4].upper()}, 0x{raw[4:].upper()}) }},\n")

    fw_m = _fw_macros(firmware)
    band_defs_str   = "\n".join(band_defs)
    band_assign_str = "\n".join(band_assign)

    # Build firmware load calls for each detected firmware file
    if firmware:
        fw_lines = []
        for fw_file in firmware:
            fw_lines.append(
                f'\tret = request_firmware(&fw, "{fw_file}", &dev->pdev->dev);\n'
                f'\tif (ret) {{ dev_err(&dev->pdev->dev, "failed to load {fw_file}: %d\\n", ret); return ret; }}\n'
                f'\t/* TODO: write fw->data ({fw_file}) to device */\n'
                f'\trelease_firmware(fw);'
            )
        fw_load_calls = "\n\t".join(fw_lines)
    else:
        fw_load_calls = "\t/* TODO: load firmware with request_firmware() */\n\t\treturn 0;"

    c = textwrap.dedent(f"""\
        {fw_m}

        static const struct pci_device_id {cs}_pci_table[] = {{
        \t{{ PCI_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
        {sub_entry}\t{{ /* sentinel */ }}
        }};
        MODULE_DEVICE_TABLE(pci, {cs}_pci_table);

        /* Band / channel / rate tables */
        {band_defs_str}

        /* mac80211 ops */
        static void {cs}_tx(struct ieee80211_hw *hw,
        \t\t    struct ieee80211_tx_control *control,
        \t\t    struct sk_buff *skb)
        {{ dev_kfree_skb_any(skb); /* TODO: enqueue to TX ring */ }}

        static int {cs}_load_firmware(struct {cs}_dev *dev)
        {{
        \tconst struct firmware *fw;
        \tint ret;
        {fw_load_calls}
        \treturn 0;
        }}

        static int {cs}_start(struct ieee80211_hw *hw)
        {{
        \tstruct {cs}_dev *dev = hw->priv;
        \tint ret = {cs}_load_firmware(dev);
        \tif (ret) return ret;
        \t/* TODO: enable IRQ, start DMA */
        \treturn 0;
        }}

        static void {cs}_stop(struct ieee80211_hw *hw, bool suspend)
        {{ /* TODO: disable IRQ, stop DMA */ }}

        static int {cs}_add_interface(struct ieee80211_hw *hw,
        \t\t\t       struct ieee80211_vif *vif)
        {{ return 0; }}

        static void {cs}_remove_interface(struct ieee80211_hw *hw,
        \t\t\t\t  struct ieee80211_vif *vif) {{}}

        static int {cs}_config(struct ieee80211_hw *hw, u32 changed)
        {{ return 0; /* TODO: apply channel/power to hardware */ }}

        static void {cs}_configure_filter(struct ieee80211_hw *hw,
        \t\t\t\t  unsigned int changed_flags,
        \t\t\t\t  unsigned int *total_flags, u64 multicast)
        {{ *total_flags &= FIF_ALLMULTI; }}

        static int {cs}_set_key(struct ieee80211_hw *hw, enum set_key_cmd cmd,
        \t\t\t struct ieee80211_vif *vif, struct ieee80211_sta *sta,
        \t\t\t struct ieee80211_key_conf *key)
        {{ return -EOPNOTSUPP; /* TODO: hardware crypto */ }}

        static const struct ieee80211_ops {cs}_ops = {{
        \t.tx               = {cs}_tx,
        \t.start            = {cs}_start,
        \t.stop             = {cs}_stop,
        \t.add_interface    = {cs}_add_interface,
        \t.remove_interface = {cs}_remove_interface,
        \t.config           = {cs}_config,
        \t.configure_filter = {cs}_configure_filter,
        \t.set_key          = {cs}_set_key,
        }};

        static int {cs}_pci_probe(struct pci_dev *pdev,
        \t\t\t   const struct pci_device_id *id)
        {{
        \tstruct ieee80211_hw *hw;
        \tstruct {cs}_dev *dev;
        \tint ret;

        \tret = pcim_enable_device(pdev);
        \tif (ret) return ret;
        \tret = pcim_iomap_regions(pdev, BIT(0), DRIVER_NAME);
        \tif (ret) return ret;
        \tpci_set_master(pdev);
        \tret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
        \tif (ret) return ret;

        \thw = ieee80211_alloc_hw(sizeof(*dev), &{cs}_ops);
        \tif (!hw) return -ENOMEM;

        \tdev = hw->priv;
        \tdev->pdev = pdev;
        \tdev->hw   = hw;
        \tdev->base = pcim_iomap_table(pdev)[0];
        \tSET_IEEE80211_DEV(hw, &pdev->dev);

        \thw->wiphy->interface_modes =
        \t\tBIT(NL80211_IFTYPE_STATION) | BIT(NL80211_IFTYPE_AP) |
        \t\tBIT(NL80211_IFTYPE_MONITOR);
        \thw->queues = 4; hw->max_rates = 4; hw->max_rate_tries = 11;

        {band_assign_str}

        \tret = ieee80211_register_hw(hw);
        \tif (ret) {{ ieee80211_free_hw(hw); return ret; }}
        \tpci_set_drvdata(pdev, hw);
        \tdev_info(&pdev->dev, "%s up\\n", DRIVER_DESC);
        \treturn 0;
        }}

        static void {cs}_pci_remove(struct pci_dev *pdev)
        {{
        \tstruct ieee80211_hw *hw = pci_get_drvdata(pdev);
        \tif (hw) {{ ieee80211_unregister_hw(hw); ieee80211_free_hw(hw); }}
        }}

        static int  {cs}_suspend(struct device *d) {{ return 0; }}
        static int  {cs}_resume(struct device *d)  {{ return 0; }}
        static SIMPLE_DEV_PM_OPS({cs}_pm_ops, {cs}_suspend, {cs}_resume);

        static struct pci_driver {cs}_pci_driver = {{
        \t.name      = DRIVER_NAME,
        \t.id_table  = {cs}_pci_table,
        \t.probe     = {cs}_pci_probe,
        \t.remove    = {cs}_pci_remove,
        \t.driver.pm = &{cs}_pm_ops,
        }};
        module_pci_driver({cs}_pci_driver);
    """)

    includes = ("#include <linux/firmware.h>\n"
                "#include <net/mac80211.h>")
    h_extra  = (f"struct {cs}_dev {{\n"
                f"\tstruct pci_dev      *pdev;\n"
                f"\tstruct ieee80211_hw *hw;\n"
                f"\tvoid __iomem        *base;\n"
                f"}};\n")
    return c, h_extra, includes


# ---- Ethernet PCI (net_device + NAPI) -----------------------

def _gen_ethernet_pci(cs: str, CS: str, canonical: dict) -> tuple:
    sub_id = canonical["device"].get("subsystem_id")
    sub_entry = ""
    if sub_id and len(sub_id.replace("0x","").replace("0X","")) == 8:
        raw = sub_id.replace("0x","").replace("0X","")
        sub_entry = (f"\t{{ PCI_DEVICE_SUB({CS}_VENDOR_ID, {CS}_DEVICE_ID, "
                     f"0x{raw[:4].upper()}, 0x{raw[4:].upper()}) }},\n")

    c = textwrap.dedent(f"""\
        static const struct pci_device_id {cs}_pci_table[] = {{
        \t{{ PCI_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
        {sub_entry}\t{{ /* sentinel */ }}
        }};
        MODULE_DEVICE_TABLE(pci, {cs}_pci_table);

        static int {cs}_net_open(struct net_device *ndev)
        {{
        \tnetif_start_queue(ndev);
        \treturn 0; /* TODO: enable DMA, enable IRQ */
        }}

        static int {cs}_net_stop(struct net_device *ndev)
        {{
        \tnetif_stop_queue(ndev);
        \treturn 0; /* TODO: disable DMA, disable IRQ */
        }}

        static netdev_tx_t {cs}_start_xmit(struct sk_buff *skb,
        \t\t\t\t   struct net_device *ndev)
        {{
        \t/* TODO: enqueue skb to TX descriptor ring */
        \tdev_kfree_skb_any(skb);
        \treturn NETDEV_TX_OK;
        }}

        static void {cs}_get_stats64(struct net_device *ndev,
        \t\t\t\t struct rtnl_link_stats64 *stats)
        {{
        \t/* TODO: read hardware counters into stats */
        }}

        static const struct net_device_ops {cs}_netdev_ops = {{
        \t.ndo_open        = {cs}_net_open,
        \t.ndo_stop        = {cs}_net_stop,
        \t.ndo_start_xmit  = {cs}_start_xmit,
        \t.ndo_get_stats64 = {cs}_get_stats64,
        }};

        static int {cs}_pci_probe(struct pci_dev *pdev,
        \t\t\t   const struct pci_device_id *id)
        {{
        \tstruct net_device *ndev;
        \tstruct {cs}_dev   *priv;
        \tint ret;

        \tret = pcim_enable_device(pdev);
        \tif (ret) return ret;
        \tret = pcim_iomap_regions(pdev, BIT(0), DRIVER_NAME);
        \tif (ret) return ret;
        \tpci_set_master(pdev);
        \tret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
        \tif (ret)
        \t\tret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
        \tif (ret) return ret;

        \tndev = devm_alloc_etherdev(&pdev->dev, sizeof(*priv));
        \tif (!ndev) return -ENOMEM;

        \tpriv       = netdev_priv(ndev);
        \tpriv->pdev = pdev;
        \tpriv->base = pcim_iomap_table(pdev)[0];
        \tSET_NETDEV_DEV(ndev, &pdev->dev);
        \tndev->netdev_ops = &{cs}_netdev_ops;

        \t/* TODO: read MAC address from hardware */
        \teth_hw_addr_random(ndev);

        \tret = register_netdev(ndev);
        \tif (ret) return ret;

        \tpci_set_drvdata(pdev, ndev);
        \tdev_info(&pdev->dev, "%s up\\n", DRIVER_DESC);
        \treturn 0;
        }}

        static void {cs}_pci_remove(struct pci_dev *pdev)
        {{
        \tstruct net_device *ndev = pci_get_drvdata(pdev);
        \tif (ndev) unregister_netdev(ndev);
        }}

        static int  {cs}_suspend(struct device *d) {{ return 0; }}
        static int  {cs}_resume(struct device *d)  {{ return 0; }}
        static SIMPLE_DEV_PM_OPS({cs}_pm_ops, {cs}_suspend, {cs}_resume);

        static struct pci_driver {cs}_pci_driver = {{
        \t.name      = DRIVER_NAME,
        \t.id_table  = {cs}_pci_table,
        \t.probe     = {cs}_pci_probe,
        \t.remove    = {cs}_pci_remove,
        \t.driver.pm = &{cs}_pm_ops,
        }};
        module_pci_driver({cs}_pci_driver);
    """)
    includes = "#include <linux/netdevice.h>\n#include <linux/etherdevice.h>"
    h_extra  = (f"struct {cs}_dev {{\n"
                f"\tstruct pci_dev  *pdev;\n"
                f"\tvoid __iomem    *base;\n"
                f"}};\n")
    return c, h_extra, includes


# ---- USB Generic / USB Ethernet (usbnet) --------------------

def _gen_usb(cs: str, CS: str, canonical: dict,
             ethernet_mode: bool = False) -> tuple:
    if ethernet_mode:
        includes = ("#include <linux/usb.h>\n"
                    "#include <linux/usb/usbnet.h>\n"
                    "#include <linux/netdevice.h>\n"
                    "#include <linux/etherdevice.h>")
        c = textwrap.dedent(f"""\
            static const struct usb_device_id {cs}_usb_table[] = {{
            \t{{ USB_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
            \t{{ /* sentinel */ }}
            }};
            MODULE_DEVICE_TABLE(usb, {cs}_usb_table);

            static int {cs}_bind(struct usbnet *dev, struct usb_interface *intf)
            {{
            \t/* TODO: configure endpoints, read MAC address */
            \teth_hw_addr_random(dev->net);
            \treturn usbnet_get_endpoints(dev, intf);
            }}

            static void {cs}_unbind(struct usbnet *dev, struct usb_interface *intf) {{}}

            static int {cs}_rx_fixup(struct usbnet *dev, struct sk_buff *skb)
            {{
            \t/* TODO: strip device-specific RX header */
            \treturn 1;
            }}

            static struct sk_buff *{cs}_tx_fixup(struct usbnet *dev,
            \t\t\t\t\t  struct sk_buff *skb, gfp_t flags)
            {{
            \t/* TODO: prepend device-specific TX header */
            \treturn skb;
            }}

            static const struct driver_info {cs}_info = {{
            \t.description = DRIVER_DESC,
            \t.flags       = FLAG_ETHER | FLAG_LINK_INTR,
            \t.bind        = {cs}_bind,
            \t.unbind      = {cs}_unbind,
            \t.rx_fixup    = {cs}_rx_fixup,
            \t.tx_fixup    = {cs}_tx_fixup,
            }};

            static struct usb_driver {cs}_usb_driver = {{
            \t.name       = DRIVER_NAME,
            \t.id_table   = {cs}_usb_table,
            \t.probe      = usbnet_probe,
            \t.disconnect = usbnet_disconnect,
            \t.suspend    = usbnet_suspend,
            \t.resume     = usbnet_resume,
            }};
            module_usb_driver({cs}_usb_driver);
        """)
    else:
        includes = "#include <linux/usb.h>"
        c = textwrap.dedent(f"""\
            static const struct usb_device_id {cs}_usb_table[] = {{
            \t{{ USB_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
            \t{{ /* sentinel */ }}
            }};
            MODULE_DEVICE_TABLE(usb, {cs}_usb_table);

            static int {cs}_probe(struct usb_interface *intf,
            \t\t\t const struct usb_device_id *id)
            {{
            \tstruct usb_device *udev = interface_to_usbdev(intf);
            \t/* TODO: claim interface, allocate URBs, start I/O */
            \tdev_info(&intf->dev, "%s attached\\n", DRIVER_DESC);
            \treturn 0;
            }}

            static void {cs}_disconnect(struct usb_interface *intf)
            {{
            \t/* TODO: cancel URBs, free resources */
            }}

            static int {cs}_suspend(struct usb_interface *intf, pm_message_t msg)
            {{ return 0; }}

            static int {cs}_resume(struct usb_interface *intf)
            {{ return 0; }}

            static struct usb_driver {cs}_usb_driver = {{
            \t.name       = DRIVER_NAME,
            \t.id_table   = {cs}_usb_table,
            \t.probe      = {cs}_probe,
            \t.disconnect = {cs}_disconnect,
            \t.suspend    = {cs}_suspend,
            \t.resume     = {cs}_resume,
            }};
            module_usb_driver({cs}_usb_driver);
        """)

    h_extra = (f"struct {cs}_dev {{\n"
               f"\tstruct usb_device    *udev;\n"
               f"\tstruct usb_interface *intf;\n"
               f"}};\n")
    return c, h_extra, includes


# ---- HID (Human Interface Device) --------------------------

def _gen_hid(cs: str, CS: str, canonical: dict) -> tuple:
    c = textwrap.dedent(f"""\
        static const struct hid_device_id {cs}_hid_table[] = {{
        \t{{ HID_USB_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
        \t{{ /* sentinel */ }}
        }};
        MODULE_DEVICE_TABLE(hid, {cs}_hid_table);

        static int {cs}_probe(struct hid_device *hdev,
        \t\t\t const struct hid_device_id *id)
        {{
        \tint ret;
        \tret = hid_parse(hdev);
        \tif (ret) return ret;
        \tret = hid_hw_start(hdev, HID_CONNECT_DEFAULT);
        \tif (ret) return ret;
        \t/* TODO: device-specific init */
        \treturn 0;
        }}

        static void {cs}_remove(struct hid_device *hdev)
        {{
        \thid_hw_stop(hdev);
        \t/* TODO: cleanup */
        }}

        static int {cs}_raw_event(struct hid_device *hdev, struct hid_report *report,
        \t\t\t   u8 *data, int size)
        {{
        \t/* TODO: handle raw input reports */
        \treturn 0;
        }}

        static struct hid_driver {cs}_hid_driver = {{
        \t.name      = DRIVER_NAME,
        \t.id_table  = {cs}_hid_table,
        \t.probe     = {cs}_probe,
        \t.remove    = {cs}_remove,
        \t.raw_event = {cs}_raw_event,
        }};
        module_hid_driver({cs}_hid_driver);
    """)
    includes = "#include <linux/hid.h>"
    h_extra  = ""
    return c, h_extra, includes


# ---- Audio (ALSA / HDA) -------------------------------------

def _gen_audio(cs: str, CS: str, canonical: dict) -> tuple:
    c = textwrap.dedent(f"""\
        static const struct pci_device_id {cs}_pci_table[] = {{
        \t{{ PCI_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
        \t{{ /* sentinel */ }}
        }};
        MODULE_DEVICE_TABLE(pci, {cs}_pci_table);

        static int {cs}_pcm_open(struct snd_pcm_substream *substream)
        {{ return 0; /* TODO: allocate DMA buffer */ }}

        static int {cs}_pcm_close(struct snd_pcm_substream *substream)
        {{ return 0; }}

        static int {cs}_pcm_prepare(struct snd_pcm_substream *substream)
        {{ return 0; /* TODO: configure sample rate, channels */ }}

        static int {cs}_pcm_trigger(struct snd_pcm_substream *substream, int cmd)
        {{ return 0; /* TODO: start/stop DMA */ }}

        static snd_pcm_uframes_t {cs}_pcm_pointer(struct snd_pcm_substream *sub)
        {{ return 0; /* TODO: return current DMA position */ }}

        static const struct snd_pcm_ops {cs}_pcm_ops = {{
        \t.open    = {cs}_pcm_open,
        \t.close   = {cs}_pcm_close,
        \t.prepare = {cs}_pcm_prepare,
        \t.trigger = {cs}_pcm_trigger,
        \t.pointer = {cs}_pcm_pointer,
        }};

        static int {cs}_pci_probe(struct pci_dev *pdev,
        \t\t\t   const struct pci_device_id *id)
        {{
        \tstruct snd_card *card;
        \tstruct snd_pcm  *pcm;
        \tint ret;

        \tret = pcim_enable_device(pdev);
        \tif (ret) return ret;
        \tpci_set_master(pdev);

        \tret = snd_card_new(&pdev->dev, SNDRV_DEFAULT_IDX1, SNDRV_DEFAULT_STR1,
        \t\t\t   THIS_MODULE, 0, &card);
        \tif (ret) return ret;

        \tstrscpy(card->driver,   DRIVER_NAME, sizeof(card->driver));
        \tstrscpy(card->shortname, DRIVER_NAME, sizeof(card->shortname));
        \tstrscpy(card->longname, DRIVER_DESC, sizeof(card->longname));

        \tret = snd_pcm_new(card, DRIVER_NAME, 0, 1, 1, &pcm);
        \tif (ret) goto err_free;
        \tsnd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_PLAYBACK, &{cs}_pcm_ops);
        \tsnd_pcm_set_ops(pcm, SNDRV_PCM_STREAM_CAPTURE,  &{cs}_pcm_ops);

        \tret = snd_card_register(card);
        \tif (ret) goto err_free;

        \tpci_set_drvdata(pdev, card);
        \tdev_info(&pdev->dev, "%s up\\n", DRIVER_DESC);
        \treturn 0;
        err_free:
        \tsnd_card_free(card);
        \treturn ret;
        }}

        static void {cs}_pci_remove(struct pci_dev *pdev)
        {{
        \tstruct snd_card *card = pci_get_drvdata(pdev);
        \tif (card) snd_card_free(card);
        }}

        static int  {cs}_suspend(struct device *d) {{ return 0; }}
        static int  {cs}_resume(struct device *d)  {{ return 0; }}
        static SIMPLE_DEV_PM_OPS({cs}_pm_ops, {cs}_suspend, {cs}_resume);

        static struct pci_driver {cs}_pci_driver = {{
        \t.name      = DRIVER_NAME,
        \t.id_table  = {cs}_pci_table,
        \t.probe     = {cs}_pci_probe,
        \t.remove    = {cs}_pci_remove,
        \t.driver.pm = &{cs}_pm_ops,
        }};
        module_pci_driver({cs}_pci_driver);
    """)
    includes = ("#include <sound/core.h>\n"
                "#include <sound/pcm.h>\n"
                "#include <sound/initval.h>")
    h_extra = ""
    return c, h_extra, includes


# ---- Bluetooth (HCI) ----------------------------------------

def _gen_bluetooth(cs: str, CS: str, canonical: dict) -> tuple:
    bus = canonical["device"].get("bus", "pci")
    if bus == "usb":
        c = textwrap.dedent(f"""\
            static const struct usb_device_id {cs}_usb_table[] = {{
            \t{{ USB_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
            \t{{ /* sentinel */ }}
            }};
            MODULE_DEVICE_TABLE(usb, {cs}_usb_table);

            static int {cs}_probe(struct usb_interface *intf,
            \t\t\t const struct usb_device_id *id)
            {{
            \tstruct hci_dev *hdev;
            \tint ret;
            \thdev = hci_alloc_dev();
            \tif (!hdev) return -ENOMEM;
            \thdev->bus     = HCI_USB;
            \thdev->dev_type = HCI_PRIMARY;
            \t/* TODO: set hdev->open / close / flush / send */
            \tret = hci_register_dev(hdev);
            \tif (ret) {{ hci_free_dev(hdev); return ret; }}
            \tusb_set_intfdata(intf, hdev);
            \treturn 0;
            }}

            static void {cs}_disconnect(struct usb_interface *intf)
            {{
            \tstruct hci_dev *hdev = usb_get_intfdata(intf);
            \tif (hdev) {{ hci_unregister_dev(hdev); hci_free_dev(hdev); }}
            }}

            static struct usb_driver {cs}_usb_driver = {{
            \t.name       = DRIVER_NAME,
            \t.id_table   = {cs}_usb_table,
            \t.probe      = {cs}_probe,
            \t.disconnect = {cs}_disconnect,
            }};
            module_usb_driver({cs}_usb_driver);
        """)
        includes = ("#include <linux/usb.h>\n"
                    "#include <net/bluetooth/bluetooth.h>\n"
                    "#include <net/bluetooth/hci_core.h>")
    else:
        c = textwrap.dedent(f"""\
            static const struct pci_device_id {cs}_pci_table[] = {{
            \t{{ PCI_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
            \t{{ /* sentinel */ }}
            }};
            MODULE_DEVICE_TABLE(pci, {cs}_pci_table);

            static int {cs}_pci_probe(struct pci_dev *pdev,
            \t\t\t   const struct pci_device_id *id)
            {{
            \tstruct hci_dev *hdev;
            \tint ret;
            \tret = pcim_enable_device(pdev);
            \tif (ret) return ret;
            \tpci_set_master(pdev);
            \thdev = hci_alloc_dev();
            \tif (!hdev) return -ENOMEM;
            \thdev->bus     = HCI_PCI;
            \thdev->dev_type = HCI_PRIMARY;
            \t/* TODO: set hdev->open / close / flush / send */
            \tret = hci_register_dev(hdev);
            \tif (ret) {{ hci_free_dev(hdev); return ret; }}
            \tpci_set_drvdata(pdev, hdev);
            \treturn 0;
            }}

            static void {cs}_pci_remove(struct pci_dev *pdev)
            {{
            \tstruct hci_dev *hdev = pci_get_drvdata(pdev);
            \tif (hdev) {{ hci_unregister_dev(hdev); hci_free_dev(hdev); }}
            }}

            static struct pci_driver {cs}_pci_driver = {{
            \t.name     = DRIVER_NAME,
            \t.id_table = {cs}_pci_table,
            \t.probe    = {cs}_pci_probe,
            \t.remove   = {cs}_pci_remove,
            }};
            module_pci_driver({cs}_pci_driver);
        """)
        includes = ("#include <net/bluetooth/bluetooth.h>\n"
                    "#include <net/bluetooth/hci_core.h>")
    h_extra = ""
    return c, h_extra, includes


# ---- Generic PCI (bare fallback) ----------------------------

def _gen_generic_pci(cs: str, CS: str, canonical: dict) -> tuple:
    c = textwrap.dedent(f"""\
        static const struct pci_device_id {cs}_pci_table[] = {{
        \t{{ PCI_DEVICE({CS}_VENDOR_ID, {CS}_DEVICE_ID) }},
        \t{{ /* sentinel */ }}
        }};
        MODULE_DEVICE_TABLE(pci, {cs}_pci_table);

        static int {cs}_pci_probe(struct pci_dev *pdev,
        \t\t\t   const struct pci_device_id *id)
        {{
        \tstruct {cs}_dev *dev;
        \tint ret;

        \tret = pcim_enable_device(pdev);
        \tif (ret) return ret;
        \tret = pcim_iomap_regions(pdev, BIT(0), DRIVER_NAME);
        \tif (ret) return ret;
        \tpci_set_master(pdev);

        \tdev = devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL);
        \tif (!dev) return -ENOMEM;
        \tdev->pdev = pdev;
        \tdev->base = pcim_iomap_table(pdev)[0];
        \tpci_set_drvdata(pdev, dev);

        \t/* TODO: device-specific initialisation */
        \tdev_info(&pdev->dev, "%s up\\n", DRIVER_DESC);
        \treturn 0;
        }}

        static void {cs}_pci_remove(struct pci_dev *pdev)
        {{
        \t/* TODO: stop device */
        }}

        static int  {cs}_suspend(struct device *d) {{ return 0; }}
        static int  {cs}_resume(struct device *d)  {{ return 0; }}
        static SIMPLE_DEV_PM_OPS({cs}_pm_ops, {cs}_suspend, {cs}_resume);

        static struct pci_driver {cs}_pci_driver = {{
        \t.name      = DRIVER_NAME,
        \t.id_table  = {cs}_pci_table,
        \t.probe     = {cs}_pci_probe,
        \t.remove    = {cs}_pci_remove,
        \t.driver.pm = &{cs}_pm_ops,
        }};
        module_pci_driver({cs}_pci_driver);
    """)
    includes = ""
    h_extra  = (f"struct {cs}_dev {{\n"
                f"\tstruct pci_dev *pdev;\n"
                f"\tvoid __iomem   *base;\n"
                f"}};\n")
    return c, h_extra, includes


# ---- Dispatch -----------------------------------------------

def _dispatch_generator(dev_type: str, cs: str, CS: str, canonical: dict):
    if dev_type == "wifi":
        return _gen_wifi(cs, CS, canonical)
    if dev_type == "ethernet_pci":
        return _gen_ethernet_pci(cs, CS, canonical)
    if dev_type in ("ethernet_usb",):
        return _gen_usb(cs, CS, canonical, ethernet_mode=True)
    if dev_type == "usb_generic":
        return _gen_usb(cs, CS, canonical, ethernet_mode=False)
    if dev_type == "hid":
        return _gen_hid(cs, CS, canonical)
    if dev_type == "audio":
        return _gen_audio(cs, CS, canonical)
    if dev_type == "bluetooth":
        return _gen_bluetooth(cs, CS, canonical)
    # display, storage, generic_pci all get the generic PCI skeleton
    return _gen_generic_pci(cs, CS, canonical)


# ---- Main generator entry point -----------------------------

def generate_linux_driver(canonical: dict, out_dir: str,
                          name_override: str = ""):
    """
    Generate a compilable Linux kernel driver skeleton from any canonical JSON.
    Auto-detects device type and emits the appropriate subsystem skeleton.

    Args:
        name_override: If non-empty, use this as the module/file name instead
                       of the auto-derived chipset name.
    """
    log("=== LINUX DRIVER GENERATOR START ===")

    dev  = canonical.get("device", {})
    drv  = canonical.get("driver", {})

    auto_name   = _derive_chipset_name(canonical,
                                       fallback=dev.get("name") or "unknown")
    chipset     = _c_ident(name_override) if name_override.strip() else auto_name
    if name_override.strip():
        log(f"Module name overridden to: {chipset}")
    CS          = chipset.upper()
    description = dev.get("description") or dev.get("name") or "Unknown Device"
    vendor_id   = dev.get("vendor_id")  or "0x0000"
    device_id   = dev.get("device_id")  or "0x0000"
    version     = drv.get("version")    or "1.0.0"
    provider    = drv.get("provider")   or "Unknown"
    dev_class   = dev.get("class")      or ""
    bus         = dev.get("bus")        or "pci"
    subsys_id   = dev.get("subsystem_id")
    modes       = drv["capabilities"].get("modes") or []
    bands       = drv["capabilities"].get("bands") or []

    dev_type = detect_device_type(canonical)
    subsystem_desc = DEVICE_TYPES.get(dev_type, "Generic")

    log(f"Device type detected: {dev_type} ({subsystem_desc})")

    # ── Query knowledge base for extra context ────────────────────────────────
    kb      = get_kb()
    kb_entry = kb.lookup(vendor_id, device_id) if kb else {}
    if kb_entry:
        log(f"KB hit: {kb_entry.get('chipset','?')} — "
            f"{kb_entry.get('linux_upstream_status','')[:60]}")
        # Use KB firmware list if canonical has none
        if not canonical["driver"]["firmware"] and kb_entry.get("firmware_files"):
            canonical["driver"]["firmware"] = kb_entry["firmware_files"]
        # Use KB register map as header hints if not already set
        canonical.setdefault("_kb", kb_entry)
    else:
        log("KB: no entry for this device (add to knowledge_base/devices/)")

    out_path = Path(out_dir)
    ensure_dir(out_path)

    c_body, h_extra, extra_includes = _dispatch_generator(dev_type, chipset, CS, canonical)

    # Subsystem defines for header
    subsys_defines = ""
    if subsys_id and len(subsys_id.replace("0x","").replace("0X","")) == 8:
        raw = subsys_id.replace("0x","").replace("0X","")
        subsys_defines = (
            f"#define {CS}_SUBSYS_VENDOR  0x{raw[:4].upper()}\n"
            f"#define {CS}_SUBSYS_DEVICE  0x{raw[4:].upper()}\n"
        )

    # ---- Build KB context comment ----------------------------------------
    kb_entry    = canonical.get("_kb", {})
    kb_comment  = ""
    if kb_entry:
        similar = ", ".join(
            d.get("module","?") for d in kb_entry.get("similar_linux_drivers",[]))
        upstream = kb_entry.get("linux_upstream_driver") or "none"
        status   = kb_entry.get("linux_upstream_status","")[:80]
        kb_lines = [
            " *",
            " * ── Knowledge Base ──",
            f" * Upstream Linux driver : {upstream}",
            f" * Status                : {status}",
        ]
        if similar:
            kb_lines.append(f" * Similar Linux drivers : {similar}")
        if kb_entry.get("notes"):
            kb_lines.append(f" * Notes                 : {kb_entry['notes'][:100]}")
        kb_lines.append(" *")
        kb_comment = "\n".join(kb_lines)

    # ---- Build NDIS/KMDF mapping comment from canonical (if any) ----
    ndis_calls = canonical.get("driver", {}).get("ndis_calls") or \
                 dev.get("ndis_calls") or []
    kmdf_calls = canonical.get("driver", {}).get("kmdf_calls") or \
                 dev.get("kmdf_calls") or []

    api_comment = ""
    if ndis_calls or kmdf_calls:
        lines = [
            " *",
            " * ── Windows API → Linux mapping (from PE import analysis) ──",
        ]
        if ndis_calls:
            lines.append(" *   NDIS calls detected:")
            for win_fn, linux_fn in ndis_calls:
                lines.append(f" *     {win_fn:<50} → {linux_fn}")
        if kmdf_calls:
            lines.append(" *   KMDF calls detected:")
            for win_fn, linux_fn in kmdf_calls:
                lines.append(f" *     {win_fn:<50} → {linux_fn}")
        lines.append(" *")
        api_comment = "\n".join(lines)

    # ---- .c file ----
    c_src = textwrap.dedent(f"""\
        // SPDX-License-Identifier: GPL-2.0-only
        // Copyright (C) 2026 linuxwifi7 (Charles Ellison)
        // Generated by AstraForge v1.1 — https://github.com/linuxwifi7/TP-link-wifi-MT7927-reverse-engineer
        /*
         * {description} — Linux Driver Skeleton
         * Type     : {subsystem_desc}
         * Provider : {provider}
         * Version  : {version}
         * PCI/USB  : {vendor_id}:{device_id}  [{bus.upper()}]
         * Class    : {dev_class}
         * Bands    : {', '.join(bands) or 'n/a'}
         * Modes    : {', '.join(modes) or 'n/a'}
         *
         * This file is generated output from the AstraForge tool and is licensed
         * under GPL-2.0-only to satisfy Linux kernel licensing requirements.
         * Hardware register access is NOT implemented — fill in the TODO stubs
         * after reverse-engineering the Windows .sys binary or obtaining datasheets.
        {kb_comment}
        {api_comment}
         */

        #include <linux/module.h>
        #include <linux/pci.h>
        #include <linux/dma-mapping.h>
        {extra_includes}

        #include "{chipset}.h"

        MODULE_LICENSE("GPL");
        MODULE_AUTHOR("AstraForge <generated>");
        MODULE_DESCRIPTION(DRIVER_DESC);
        MODULE_VERSION(DRIVER_VERSION);

        {c_body}
    """)

    # ---- Build register map from KB (or placeholder) --------------------
    kb_regs = kb_entry.get("register_map", {}) if kb_entry else {}
    if kb_regs:
        reg_lines = [f"/* KB-sourced register map for {kb_entry.get('chipset','?')} */"]
        for name, offset in kb_regs.items():
            if name.startswith("_"):
                continue
            reg_lines.append(f"#define {name:<30} {offset}")
        reg_map_defines = "\n        ".join(reg_lines)
    else:
        reg_map_defines = (
            f"/* PLACEHOLDER — fill from reverse engineering */\n"
            f"        #define {CS}_REG_CTRL      0x0000\n"
            f"        #define {CS}_REG_STATUS    0x0004\n"
            f"        #define {CS}_REG_INT_MASK  0x0008\n"
            f"        #define {CS}_REG_INT_STAT  0x000c\n"
            f"        #define {CS}_REG_TX_BASE   0x0010\n"
            f"        #define {CS}_REG_RX_BASE   0x0014"
        )

    # ---- Registry keys comment for .h (from INF [AddReg] extraction) ----
    reg_keys = drv.get("registry_keys") or []
    if reg_keys:
        rk_lines = ["/* Windows Registry Keys extracted from INF [AddReg] sections",
                    " * These reveal driver configuration — suggested module_param() equivalents:"]
        for rk in reg_keys[:40]:  # cap at 40 to avoid bloat
            name  = rk.get("name") or "(default)"
            val   = rk.get("value", "")
            rtype = rk.get("type", "")
            sub   = rk.get("subkey", "")
            param = re.sub(r"[^a-z0-9]", "_", name.lower()).strip("_") or "param"
            c_type = "uint" if rtype == "REG_DWORD" else "charp"
            rk_lines.append(
                f" *   [{rtype}] {sub}\\{name} = {val!r}"
                f"  →  module_param({param}, {c_type}, 0644);"
            )
        rk_lines.append(" */")
        reg_keys_comment = "\n        ".join(rk_lines)
    else:
        reg_keys_comment = "/* No [AddReg] registry keys extracted from INF */"

    # ---- .h file ----
    h_src = textwrap.dedent(f"""\
        /* SPDX-License-Identifier: GPL-2.0-only */
        /* Copyright (C) 2026 linuxwifi7 (Charles Ellison) */
        /* Generated by AstraForge v1.1 — register offsets are placeholders */
        #ifndef _{CS}_H_
        #define _{CS}_H_

        #include <linux/types.h>
        #include <linux/pci.h>

        #define DRIVER_NAME     "{chipset}"
        #define DRIVER_DESC     "{description}"
        #define DRIVER_VERSION  "{version}"

        /* Device identifiers */
        #define {CS}_VENDOR_ID  {vendor_id}
        #define {CS}_DEVICE_ID  {device_id}
        {subsys_defines}
        /* Register map */
        {reg_map_defines}

        {reg_keys_comment}

        {h_extra}
        #endif /* _{CS}_H_ */
    """)

    # ---- Makefile ----
    makefile = textwrap.dedent(f"""\
        # Generated by AstraForge
        obj-m   := {chipset}.o
        KDIR    ?= /lib/modules/$(shell uname -r)/build
        PWD     := $(CURDIR)

        all:
        \t$(MAKE) -C $(KDIR) M=$(PWD) modules

        clean:
        \t$(MAKE) -C $(KDIR) M=$(PWD) clean

        install:
        \t$(MAKE) -C $(KDIR) M=$(PWD) modules_install
        \tdepmod -a
    """)

    # ---- Kconfig ----
    kconfig = textwrap.dedent(f"""\
        config {CS}
        \ttristate "Support for {description}"
        \tdepends on PCI
        \thelp
        \t  {subsystem_desc} driver skeleton for {description}.
        \t  {bus.upper()} ID: {vendor_id}:{device_id}
        \t  Windows driver: v{version}  ({provider})
        \t  Generated by AstraForge.  Hardware register access not yet
        \t  implemented — see TODO stubs in {chipset}.c.
        \t  To compile as a module, choose M.
    """)

    files = {
        f"{chipset}.c": c_src,
        f"{chipset}.h": h_src,
        "Makefile":     makefile,
        "Kconfig":      kconfig,
    }

    for fname, content in files.items():
        fpath = out_path / fname
        with fpath.open("w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        log(f"Written: {fpath}")

    installer = _generate_shell_installer(out_path, chipset, files, version)
    log(f"Written: {installer}")

    log("=== LINUX DRIVER GENERATOR COMPLETE ===")
    print(f"\nDevice type : {dev_type}  ({subsystem_desc})")
    print(f"Output      : {out_path.resolve()}")
    print(f"Files       : {chipset}.c  {chipset}.h  Makefile  Kconfig  install.sh")
    print(f"\nTo build on Linux:  cd <output>  &&  make")
    print(f"To install via script:  chmod +x install.sh && sudo ./install.sh")


def _generate_shell_installer(out_dir: Path, chipset: str, files: dict,
                               version: str = "1.0.0") -> Path:
    # Sanitize version for DKMS (no spaces or special chars)
    ver = re.sub(r'[^\w.]', '.', version).strip('.')  or "1.0.0"
    date_str = datetime.now().strftime('%Y-%m-%d')

    header = f"""\
#!/bin/bash
# AstraForge Generated Installer — {chipset} v{ver}
# Generated: {date_str}
# Supports: Ubuntu · Debian · Fedora · Linux Mint · Arch Linux · Manjaro
#           EndeavourOS · Pop!_OS · openSUSE (Leap & Tumbleweed)
#           MX Linux · Kali Linux
# Usage:    chmod +x install.sh && sudo ./install.sh

set -e

DRIVER="{chipset}"
VERSION="{ver}"
SRCDIR="/usr/src/${{DRIVER}}-${{VERSION}}"

# ── Root check ────────────────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run as root:  sudo ./install.sh" >&2
    exit 1
fi

# ── Distro detection ──────────────────────────────────────────────────────────
. /etc/os-release 2>/dev/null || true
DISTRO="${{ID:-unknown}}"
echo "==> Detected distro: $DISTRO (kernel $(uname -r))"

# ── Install prerequisites (fully non-interactive) ─────────────────────────────
echo "==> Installing build tools, kernel headers, and DKMS..."
export DEBIAN_FRONTEND=noninteractive
export APT_LISTCHANGES_FRONTEND=none
case "$DISTRO" in
    ubuntu|debian|linuxmint|pop|pop-os|mx|kali|raspbian|elementary|zorin)
        apt-get update -qq
        apt-get install -y -qq \
            --no-install-recommends \
            -o Dpkg::Options::="--force-confold" \
            build-essential dkms "linux-headers-$(uname -r)"
        ;;
    fedora)
        dnf install -y -q gcc make perl dkms \
            "kernel-devel-$(uname -r)" "kernel-headers-$(uname -r)" 2>/dev/null || \
        dnf install -y -q gcc make perl dkms kernel-devel kernel-headers
        ;;
    arch|manjaro|endeavouros|garuda|artix|cachyos)
        pacman -Sy --noconfirm --needed base-devel dkms linux-headers 2>/dev/null || \
        pacman -Sy --noconfirm --needed base-devel dkms
        ;;
    opensuse-leap|opensuse-tumbleweed|opensuse*|suse|sles)
        zypper --non-interactive --quiet install gcc make dkms kernel-default-devel
        ;;
    *)
        # Generic fallback: probe whichever package manager is present
        if   command -v apt-get &>/dev/null; then
            apt-get update -qq
            apt-get install -y -qq --no-install-recommends \
                -o Dpkg::Options::="--force-confold" \
                build-essential dkms "linux-headers-$(uname -r)"
        elif command -v dnf &>/dev/null; then
            dnf install -y -q gcc make dkms kernel-devel kernel-headers
        elif command -v pacman &>/dev/null; then
            pacman -Sy --noconfirm --needed base-devel dkms linux-headers
        elif command -v zypper &>/dev/null; then
            zypper --non-interactive --quiet install gcc make dkms kernel-default-devel
        else
            echo "WARNING: Unknown distro '$DISTRO' — install build-essential," >&2
            echo "         dkms, and kernel headers manually before continuing." >&2
        fi
        ;;
esac

# ── Extract driver source files ───────────────────────────────────────────────
echo "==> Extracting source to $SRCDIR"
mkdir -p "$SRCDIR"
"""

    # Base64-encode each file so driver metadata can never break out of the
    # heredoc (base64 alphabet is [A-Za-z0-9+/=] — underscores impossible).
    heredocs = []
    for fname, content in files.items():
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        wrapped = "\n".join(encoded[i:i+76] for i in range(0, len(encoded), 76))
        token = f"_AF_{fname.replace('.', '_').upper()}_B64_"
        heredocs.append(
            f"\nbase64 -d > \"$SRCDIR/{fname}\" << '{token}'\n{wrapped}\n{token}"
        )

    dkms_section = f"""
# ── Create dkms.conf ─────────────────────────────────────────────────────────
cat > "$SRCDIR/dkms.conf" << 'DKMS_CONF_END'
PACKAGE_NAME="{chipset}"
PACKAGE_VERSION="{ver}"
BUILT_MODULE_NAME="{chipset}"
DEST_MODULE_LOCATION="/kernel/drivers/net/wireless/"
AUTOINSTALL="yes"
DKMS_CONF_END

# ── Register, build, and install via DKMS ────────────────────────────────────
echo "==> Registering ${{DRIVER}} v${{VERSION}} with DKMS..."
dkms remove "${{DRIVER}}/${{VERSION}}" --all 2>/dev/null || true
dkms add "${{DRIVER}}/${{VERSION}}"

echo "==> Building kernel module (DKMS)..."
dkms build "${{DRIVER}}/${{VERSION}}"

echo "==> Installing kernel module (DKMS)..."
dkms install "${{DRIVER}}/${{VERSION}}"

# ── Load module ───────────────────────────────────────────────────────────────
echo "==> Loading module..."
modprobe "$DRIVER" 2>/dev/null || \
    insmod "/lib/modules/$(uname -r)/updates/dkms/${{DRIVER}}.ko"

echo ""
echo "==> Done!  Module '$DRIVER' is active."
echo "    Verify:      dmesg | tail -20"
echo "    DKMS status: dkms status $DRIVER"
echo "    The module will rebuild automatically on kernel updates."
"""

    out = out_dir / "install.sh"
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write(header + "".join(heredocs) + dkms_section)
    return out


def run_generate():
    canonical_dir, out_dir = get_paths_for_mode("generate")
    canon_files = sorted(
        Path(canonical_dir).glob("canonical_*.json"),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    if not canon_files:
        log("ERROR: No canonical JSON files found.")
        return
    log(f"Using canonical: {canon_files[0]}")
    with canon_files[0].open("r", encoding="utf-8") as f:
        canonical = json.load(f)

    auto_name = _derive_chipset_name(
        canonical, fallback=canonical.get("device", {}).get("name") or "driver")
    print(f"\nAuto-derived module name: {auto_name}")
    user_input = input(f"Module name [{auto_name}]: ").strip()
    name_override = user_input if user_input else auto_name

    generate_linux_driver(canonical, out_dir, name_override=name_override)


# ============================================================
# DRIVER SCANNER  (INF parser + folder walk)
# ============================================================

def _parse_inf_sections(text: str) -> dict:
    """
    Parse a Windows .inf file into {section_lower: {key_lower: last_value}}.
    Handles line continuations and strips inline comments.
    """
    sections: dict = {}
    current: str | None = None
    pending = ""

    for raw in text.splitlines():
        # Line continuation
        if pending:
            raw = pending + raw.strip()
            pending = ""
        if raw.rstrip().endswith("\\"):
            pending = raw.rstrip()[:-1]
            continue

        # Strip inline comments (but not inside quoted strings)
        line = ""
        in_q = False
        for ch in raw:
            if ch == '"':
                in_q = not in_q
            if ch == ";" and not in_q:
                break
            line += ch
        line = line.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip().lower()
            sections.setdefault(current, {})
        elif current is not None and "=" in line:
            key, _, val = line.partition("=")
            # Allow duplicate keys by appending with index suffix
            base = key.strip().lower()
            k = base
            idx = 1
            while k in sections[current]:
                k = f"{base}__{idx}"
                idx += 1
            sections[current][k] = val.strip()

    return sections


def _resolve(val: str, strings: dict) -> str:
    """Substitute %key% tokens using the [Strings] table."""
    def _sub(m):
        return strings.get(m.group(1).lower(), m.group(0))
    return re.sub(r"%([^%\r\n]+)%", _sub, val)


def _parse_hw_id(hw_id: str) -> dict | None:
    """
    Parse a PCI or USB hardware ID string into a partial device dict.
    Returns None for IDs we don't understand.

    Examples:
      PCI\\VEN_14C3&DEV_7927&SUBSYS_E104105B&REV_00
      USB\\VID_0BDA&PID_8153&REV_3100
      HID\\VID_046D&PID_C07C
    """
    hw = hw_id.upper().replace("\\\\", "\\").replace("/", "\\")

    if hw.startswith("PCI\\"):
        if "VEN_" not in hw:
            return None
        d: dict = {"bus": "pci"}
        d["vendor_id"] = "0x" + hw.split("VEN_")[1].split("&")[0].split("\\")[0]
        if "DEV_" in hw:
            d["device_id"] = "0x" + hw.split("DEV_")[1].split("&")[0].split("\\")[0]
        if "SUBSYS_" in hw:
            d["subsystem_id"] = "0x" + hw.split("SUBSYS_")[1].split("&")[0].split("\\")[0]
        if "REV_" in hw:
            d["revision"] = "0x" + hw.split("REV_")[1].split("&")[0].split("\\")[0]
        return d

    if hw.startswith(("USB\\", "HID\\")):
        if "VID_" not in hw:
            return None
        d = {"bus": "usb" if hw.startswith("USB\\") else "hid"}
        d["vendor_id"] = "0x" + hw.split("VID_")[1].split("&")[0].split("\\")[0]
        if "PID_" in hw:
            d["device_id"] = "0x" + hw.split("PID_")[1].split("&")[0].split("\\")[0]
        return d

    return None


def _parse_addreg_from_text(text: str, sections: dict, strings: dict) -> list:
    """
    Parse all AddReg sections referenced by install sections in the INF.
    Returns list of {"hive", "subkey", "name", "type", "value"} dicts.
    """
    _FLAG_TYPES = {
        0x00000000: "REG_SZ",      0x00010001: "REG_DWORD",
        0x00010002: "REG_BINARY",  0x00020000: "REG_EXPAND_SZ",
        0x00010008: "REG_QWORD",   0x00000010: "REG_MULTI_SZ",
    }
    # Collect AddReg target section names from all install sections
    addreg_names: set = set()
    for sec_data in sections.values():
        for key, val in sec_data.items():
            if key == "addreg" or key.startswith("addreg__"):
                for name in val.split(","):
                    addreg_names.add(name.strip().lower())

    if not addreg_names:
        return []

    result, seen, current_sec, in_target = [], set(), None, False
    for raw in text.splitlines():
        line, in_q = "", False
        for ch in raw:
            if ch == '"': in_q = not in_q
            if ch == ';' and not in_q: break
            line += ch
        line = line.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current_sec = line[1:-1].strip().lower()
            in_target = current_sec in addreg_names
            continue
        if not in_target:
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]
        hive = parts[0].upper() if parts else ""
        if not hive.startswith("HK"):
            continue
        subkey = _resolve(parts[1], strings) if len(parts) > 1 else ""
        name   = _resolve(parts[2], strings) if len(parts) > 2 else ""
        flags_s = parts[3] if len(parts) > 3 else "0"
        value  = _resolve(",".join(parts[4:]), strings) if len(parts) > 4 else ""
        try:
            flags = int(flags_s, 0)
        except ValueError:
            flags = 0
        type_str = _FLAG_TYPES.get(flags & 0xFFFF00FF, f"0x{flags:08X}")
        dedup = (hive, subkey.lower(), name.lower())
        if dedup in seen:
            continue
        seen.add(dedup)
        result.append({"hive": hive, "subkey": subkey,
                        "name": name, "type": type_str, "value": value})
    return result


def parse_inf(inf_path: Path) -> list:
    """
    Parse a single Windows .inf file.
    Returns a list of device dicts, one per hardware ID found.

    Each dict has:
      description, class, bus, vendor_id, device_id,
      subsystem_id?, revision?, version, provider, inf_path
    """
    try:
        text = load_text(inf_path)
        if not text:
            return []
    except Exception:
        return []

    sections = _parse_inf_sections(text)
    strings  = {k: v.strip('"') for k, v in sections.get("strings", {}).items()}

    # ── [Version] ────────────────────────────────────────────
    ver_sec   = sections.get("version", {})
    dev_class = _resolve(ver_sec.get("class", ""), strings)
    provider  = _resolve(ver_sec.get("provider", ""), strings)

    raw_ver = ver_sec.get("driverver", "") or ver_sec.get("driververobsolete", "")
    version = raw_ver.split(",")[-1].strip() if "," in raw_ver else raw_ver.strip()
    ver_date = raw_ver.split(",")[0].strip() if "," in raw_ver else ""

    # ── [Manufacturer] → locate Models section(s) ────────────
    mfg_sec = sections.get("manufacturer", {})
    if not mfg_sec:
        return []

    devices: list = []
    seen: set = set()  # deduplicate by (vid, pid)

    # Preferred architectures in priority order
    arch_suffixes = [".ntamd64", ".ntarm64", ".ntx86.10", ".ntx86", ".nt", ""]

    for mfg_val in mfg_sec.values():
        # "ModelsSection,NTx86,NTamd64" — first token is base section name
        parts    = [p.strip() for p in mfg_val.split(",")]
        base_sec = _resolve(parts[0], strings).lower()

        # Find the best matching architecture variant
        models_section = None
        for suf in arch_suffixes:
            candidate = base_sec + suf
            if candidate in sections:
                models_section = sections[candidate]
                break

        if not models_section:
            continue

        for dev_key, dev_val in models_section.items():
            dev_name = _resolve(dev_key.split("__")[0], strings)  # strip dup suffix
            # Values: "InstallSection, HW_ID1, HW_ID2, ..."
            hw_ids = [p.strip() for p in dev_val.split(",")[1:]]

            for hw_id in hw_ids:
                if not hw_id:
                    continue
                parsed = _parse_hw_id(hw_id)
                if not parsed:
                    continue

                key = (parsed.get("vendor_id", ""), parsed.get("device_id", ""))
                if key in seen:
                    continue
                seen.add(key)

                devices.append({
                    "description": dev_name,
                    "class":       dev_class,
                    "bus":         parsed.get("bus", "pci"),
                    "vendor_id":   parsed.get("vendor_id"),
                    "device_id":   parsed.get("device_id"),
                    "subsystem_id": parsed.get("subsystem_id"),
                    "revision":    parsed.get("revision"),
                    "version":     version,
                    "ver_date":    ver_date,
                    "provider":    provider,
                    "inf_path":    str(inf_path),
                })

    # Attach registry keys to every device from this INF
    registry_keys = _parse_addreg_from_text(text, sections, strings)
    for dev in devices:
        dev["registry_keys"] = registry_keys

    return devices


# ── PE binary helpers ────────────────────────────────────────────────────────

import struct as _struct

# ── NDIS / KMDF → Linux kernel mapping table ─────────────────────────────────
# Used to annotate generated drivers with mapping hints when the Windows
# binary imports these functions.

NDIS_TO_LINUX = {
    # Receive path
    "NdisMIndicateReceiveNetBufferLists": "ieee80211_rx_irqsafe",
    "NdisReturnNetBufferLists":           "/* handled by mac80211 */",
    # Transmit path
    "NdisMSendNetBufferListsComplete":    "ieee80211_tx_status",
    "NdisMResetComplete":                 "ieee80211_wake_queues",
    # Memory
    "NdisAllocateMemoryWithTagPriority":  "kzalloc / dma_alloc_coherent",
    "NdisFreeMemoryWithTagPriority":      "kfree / dma_free_coherent",
    "NdisAllocateNetBuffer":              "dev_alloc_skb",
    "NdisFreeNetBuffer":                  "dev_kfree_skb_any",
    "NdisAllocateMdl":                    "virt_to_page / sg_init_one",
    # Synchronisation
    "NdisInterlockedIncrement":           "atomic_inc",
    "NdisInterlockedDecrement":           "atomic_dec",
    "NdisAcquireSpinLock":               "spin_lock_irqsave",
    "NdisReleaseSpinLock":               "spin_unlock_irqrestore",
    "NdisInitializeEvent":               "init_completion",
    "NdisSetEvent":                      "complete",
    "NdisWaitEvent":                     "wait_for_completion_timeout",
    # Timers
    "NdisSetTimerObject":                "mod_timer",
    "NdisCancelTimerObject":             "del_timer_sync",
    "NdisAllocateTimerObject":           "timer_setup",
    # DMA
    "NdisMAllocateSharedMemory":         "dma_alloc_coherent",
    "NdisMFreeSharedMemory":             "dma_free_coherent",
    "NdisMMapIoSpace":                   "ioremap",
    "NdisMUnmapIoSpace":                 "iounmap",
    # Registration
    "NdisMRegisterMiniportDriver":       "module_pci_driver",
    "NdisMDeregisterMiniportDriver":     "/* handled by module_pci_driver */",
    "NdisMSetMiniportAttributes":        "SET_IEEE80211_DEV / ieee80211_alloc_hw",
    # I/O
    "NdisRawReadPortUlong":              "inl",
    "NdisRawWritePortUlong":             "outl",
    "NdisReadRegisterUlong":             "readl",
    "NdisWriteRegisterUlong":            "writel",
    # Interrupt
    "NdisMRegisterInterruptEx":          "request_irq",
    "NdisMDeregisterInterruptEx":        "free_irq",
    "NdisMSynchronizeWithInterruptEx":   "synchronize_irq",
}

KMDF_TO_LINUX = {
    "WdfDriverCreate":             "module_init",
    "WdfDeviceCreate":             "ieee80211_alloc_hw / alloc_netdev",
    "WdfInterruptCreate":          "request_irq",
    "WdfInterruptDisable":         "disable_irq",
    "WdfInterruptEnable":          "enable_irq",
    "WdfDmaEnablerCreate":         "dma_set_mask_and_coherent",
    "WdfCommonBufferCreate":       "dma_alloc_coherent",
    "WdfCommonBufferFree":         "dma_free_coherent",
    "WdfTimerCreate":              "timer_setup",
    "WdfTimerStart":               "mod_timer",
    "WdfTimerStop":                "del_timer_sync",
    "WdfSpinLockCreate":           "spin_lock_init",
    "WdfSpinLockAcquire":          "spin_lock_irqsave",
    "WdfSpinLockRelease":          "spin_unlock_irqrestore",
    "WdfRequestComplete":          "complete",
    "WdfIoQueueCreate":            "/* use workqueue: alloc_workqueue */",
    "WdfMemoryCreate":             "kzalloc",
    "WdfMemoryGetBuffer":          "/* pointer from kzalloc */",
    "WdfObjectDelete":             "kfree",
    "WdfDeviceInitSetIoType":      "/* handled by kernel I/O model */",
    "WdfPdoInitAllocate":          "device_register",
    "WdfChildListCreate":          "/* use bus_register */",
}

# Modules whose imports signal NDIS/KMDF usage
_NDIS_MODULES  = {"ndis.sys", "ndis6.sys"}
_KMDF_MODULES  = {"wdf01000.sys", "wdfldr.sys"}
_KNOWN_MODULES = _NDIS_MODULES | _KMDF_MODULES


def _parse_pe_imports(binary: bytes) -> dict:
    """
    Parse the PE Import Directory to extract {dll_name: [function_names]}.
    No external deps. Returns empty dict on any parse error.
    """
    try:
        if len(binary) < 0x40:
            return {}
        pe_off = _struct.unpack_from("<I", binary, 0x3C)[0]
        if binary[pe_off:pe_off+4] != b"PE\x00\x00":
            return {}

        # Optional header offset = pe_off + 4 (COFF) + 20 (COFF header)
        coff_off   = pe_off + 4
        opt_off    = coff_off + 20
        magic      = _struct.unpack_from("<H", binary, opt_off)[0]
        is_pe32p   = (magic == 0x20B)   # PE32+ (64-bit)

        # Data directory starts at opt_off + 96 (PE32) or 112 (PE32+)
        dd_base    = opt_off + (112 if is_pe32p else 96)
        # Import table is data directory entry 1
        imp_rva, _ = _struct.unpack_from("<II", binary, dd_base + 8)
        if imp_rva == 0:
            return {}

        # Collect section headers to convert RVA → file offset
        # Cap at 256 to prevent O(n²) walk on crafted PEs with 65535 sections.
        num_sections = min(_struct.unpack_from("<H", binary, coff_off + 2)[0], 256)
        sec_off      = opt_off + _struct.unpack_from("<H", binary, coff_off + 16)[0]

        def rva_to_off(rva):
            for i in range(num_sections):
                s = sec_off + i * 40
                vaddr  = _struct.unpack_from("<I", binary, s + 12)[0]
                vsize  = _struct.unpack_from("<I", binary, s + 16)[0]
                rawoff = _struct.unpack_from("<I", binary, s + 20)[0]
                if vaddr <= rva < vaddr + vsize:
                    return rawoff + (rva - vaddr)
            return None

        imports   = {}
        imp_off   = rva_to_off(imp_rva)
        if imp_off is None:
            return {}

        # Walk Import Descriptor Table (20 bytes each, ends with all-zeros)
        idx = imp_off
        while idx + 20 <= len(binary):
            orig_thunk, _, _, name_rva, thunk = _struct.unpack_from("<IIIII", binary, idx)
            if name_rva == 0 and thunk == 0:
                break
            idx += 20
            if name_rva == 0:
                continue

            # DLL name — cap search at 512 bytes; find() returns -1 if no NUL
            name_off = rva_to_off(name_rva)
            if name_off is None:
                continue
            end = binary.find(b"\x00", name_off, name_off + 512)
            if end == -1:
                end = name_off + 512
            dll_name = binary[name_off:end].decode("ascii", errors="replace").lower()

            # Import Name Table
            ilt_off = rva_to_off(orig_thunk or thunk)
            if ilt_off is None:
                continue

            funcs = []
            entry_size = 8 if is_pe32p else 4
            fmt        = "<Q" if is_pe32p else "<I"
            ordinal_flag = 0x8000000000000000 if is_pe32p else 0x80000000

            t = ilt_off
            while t + entry_size <= len(binary):
                val, = _struct.unpack_from(fmt, binary, t)
                t += entry_size
                if val == 0:
                    break
                if val & ordinal_flag:
                    continue   # skip ordinal imports
                hint_rva = val & (0x7FFFFFFFFFFFFFFF if is_pe32p else 0x7FFFFFFF)
                hint_off = rva_to_off(hint_rva)
                if hint_off is None:
                    continue
                fn_end = binary.find(b"\x00", hint_off + 2, hint_off + 258)
                if fn_end == -1:
                    fn_end = hint_off + 258
                fn_name = binary[hint_off+2:fn_end].decode("ascii", errors="replace")
                if fn_name:
                    funcs.append(fn_name)

            imports[dll_name] = funcs

        return imports

    except Exception:
        return {}


def extract_api_mappings(binary: bytes) -> dict:
    """
    Scan a PE binary's import table for NDIS/KMDF function calls and return
    a mapping report.

    Returns:
      {
        "ndis_calls":  [(windows_fn, linux_equivalent), ...],
        "kmdf_calls":  [(windows_fn, linux_equivalent), ...],
        "other_imports": {dll: [fn, ...]},
      }
    """
    imports = _parse_pe_imports(binary)
    ndis_calls, kmdf_calls, other = [], [], {}

    for dll, funcs in imports.items():
        if dll in _NDIS_MODULES:
            for fn in funcs:
                linux = NDIS_TO_LINUX.get(fn, "/* TODO: map manually */")
                ndis_calls.append((fn, linux))
        elif dll in _KMDF_MODULES:
            for fn in funcs:
                linux = KMDF_TO_LINUX.get(fn, "/* TODO: map manually */")
                kmdf_calls.append((fn, linux))
        else:
            other[dll] = funcs

    return {
        "ndis_calls":    ndis_calls,
        "kmdf_calls":    kmdf_calls,
        "other_imports": other,
    }


def _detect_pe_arch(binary: bytes) -> str:
    """Read CPU architecture from PE COFF header. No external deps."""
    if len(binary) < 0x40:
        return "unknown"
    try:
        pe_off = _struct.unpack_from("<I", binary, 0x3C)[0]
        if pe_off + 6 > len(binary):
            return "unknown"
        if binary[pe_off:pe_off + 4] != b"PE\x00\x00":
            return "unknown"
        machine = _struct.unpack_from("<H", binary, pe_off + 4)[0]
    except Exception:
        return "unknown"
    return {
        0x014C: "x86",
        0x8664: "x64",
        0xAA64: "ARM64",
        0x01C4: "ARM",
        0x0200: "IA64",
    }.get(machine, f"0x{machine:04X}")


def _read_pe_version_strings(binary: bytes) -> dict:
    """
    Extract version resource strings from a PE binary by scanning for
    UTF-16 LE key/value pairs inside the VS_VERSION_INFO resource block.
    No external deps required.
    """
    KEYS = ["FileVersion", "FileDescription", "CompanyName",
            "ProductName", "ProductVersion", "OriginalFilename",
            "InternalName", "LegalCopyright"]
    result: dict = {}

    for key in KEYS:
        needle = key.encode("utf-16-le")
        idx = binary.find(needle)
        if idx == -1:
            continue
        # Skip past key + UTF-16 NUL terminator (2 bytes)
        start = idx + len(needle) + 2
        # Align to even byte boundary
        if start % 2:
            start += 1
        # Read UTF-16 LE characters until double-NUL; cap at 512 chars (1024 bytes)
        val_bytes = bytearray()
        i = start
        while i + 1 < len(binary) and len(val_bytes) < 1024:
            ch = binary[i: i + 2]
            if ch == b"\x00\x00":
                break
            val_bytes += ch
            i += 2
        try:
            val = val_bytes.decode("utf-16-le").strip()
            if val and len(val) < 256:
                result[key] = val
        except UnicodeDecodeError:
            pass

    return result


def _scan_binary_ids(binary: bytes) -> tuple:
    """
    Scan binary content (treated as latin-1) for embedded device IDs
    and firmware file references.
    Returns (device_id_list, firmware_ref_list).
    """
    text = binary.decode("latin-1", errors="replace")
    device_ids: list = []
    firmware_refs: list = []

    # PCI device IDs
    for m in re.finditer(
            r"VEN_([0-9A-Fa-f]{4})[^\n]{0,40}?DEV_([0-9A-Fa-f]{4})", text):
        did = f"PCI\\VEN_{m.group(1).upper()}&DEV_{m.group(2).upper()}"
        if did not in device_ids:
            device_ids.append(did)

    # USB / HID device IDs
    for m in re.finditer(
            r"VID_([0-9A-Fa-f]{4})[^\n]{0,20}?PID_([0-9A-Fa-f]{4})", text):
        bus = "HID" if text[max(0, m.start()-4):m.start()].endswith("HID") \
              else "USB"
        did = f"{bus}\\VID_{m.group(1).upper()}&PID_{m.group(2).upper()}"
        if did not in device_ids:
            device_ids.append(did)

    # Firmware file references
    for m in re.finditer(
            r"[\w/\\.\-]{4,50}\.(bin|fw|fwu|hcd|nvm|img)", text, re.I):
        ref = m.group(0).strip()
        # Filter out noise (path separators, reasonable length)
        if 6 <= len(ref) <= 80 and ref not in firmware_refs:
            firmware_refs.append(ref)

    return device_ids, firmware_refs


def parse_dll(dll_path: Path) -> dict:
    """
    Extract metadata from a Windows .dll or .sys binary.

    Returns a dict with:
      file_type, filename, path, arch, version, description, company,
      device_ids (list of hardware ID strings found in binary),
      firmware_refs (list of .bin/.fw file paths found in binary)
    """
    suffix = dll_path.suffix.lstrip(".").upper() or "BIN"
    entry = {
        "file_type":    suffix,           # DLL / SYS / EXE
        "type_tag":     suffix,           # used by GUI for colouring
        "filename":     dll_path.name,
        "path":         str(dll_path),
        "inf_path":     str(dll_path),    # re-use inf_path slot for table
        "arch":         "unknown",
        "version":      None,
        "description":  None,
        "company":      None,
        "device_ids":   [],
        "firmware_refs": [],
        # Canonical-compatible fields (populated from binary data)
        "bus":          "pci",
        "vendor_id":    None,
        "device_id":    None,
        "subsystem_id": None,
        "revision":     None,
        "class":        suffix,
        "provider":     None,
    }

    _WARN_BYTES = 256 * 1024 * 1024   # 256 MB — prompt before loading
    _HARD_BYTES = 2  * 1024 * 1024 * 1024  # 2 GB  — hard skip (OS limit risk)
    try:
        sz = dll_path.stat().st_size
        if sz > _HARD_BYTES:
            log(f"Skipping {dll_path.name}: {sz // (1024*1024)} MB exceeds 2 GB hard limit")
            return entry
        if sz > _WARN_BYTES:
            mb = sz // (1024 * 1024)
            with _OVERSIZE_PROMPT_LOCK:
                try:
                    ans = input(
                        f"\n[WARNING] {dll_path.name} is {mb} MB "
                        f"(real drivers are rarely above 40 MB — this may be corrupt or malicious).\n"
                        f"Load anyway? (y/N): "
                    ).strip().lower()
                except EOFError:
                    ans = "n"
            if ans not in ("y", "yes"):
                log(f"Skipping {dll_path.name}: user declined ({mb} MB)")
                return entry
        binary = dll_path.read_bytes()
    except Exception as exc:
        log(f"Could not read {dll_path.name}: {exc}")
        return entry

    entry["arch"] = _detect_pe_arch(binary)

    ver_strings = _read_pe_version_strings(binary)
    entry["version"]     = (ver_strings.get("FileVersion") or
                            ver_strings.get("ProductVersion"))
    entry["description"] = (ver_strings.get("FileDescription") or
                            ver_strings.get("ProductName") or
                            dll_path.stem)
    entry["company"]  = ver_strings.get("CompanyName")
    entry["provider"] = entry["company"]

    # Store manufacturer's original filename (e.g. "mt7927.sys" → "mt7927")
    orig = (ver_strings.get("OriginalFilename") or
            ver_strings.get("InternalName") or "")
    orig_stem = Path(orig).stem if orig else ""
    entry["original_filename"] = orig_stem  # used by _derive_chipset_name

    device_ids, firmware_refs = _scan_binary_ids(binary)
    entry["device_ids"]    = device_ids
    entry["firmware_refs"] = firmware_refs

    # API mapping analysis (NDIS/KMDF imports)
    api_maps = extract_api_mappings(binary)
    entry["ndis_calls"] = api_maps["ndis_calls"]
    entry["kmdf_calls"] = api_maps["kmdf_calls"]
    if api_maps["ndis_calls"] or api_maps["kmdf_calls"]:
        log(f"{dll_path.name}: {len(api_maps['ndis_calls'])} NDIS  "
            f"{len(api_maps['kmdf_calls'])} KMDF imports mapped")

    # Extract first PCI vendor/device ID found
    for hw_id in device_ids:
        parsed = _parse_hw_id(hw_id)
        if parsed:
            entry["bus"]       = parsed.get("bus", "pci")
            entry["vendor_id"] = parsed.get("vendor_id")
            entry["device_id"] = parsed.get("device_id")
            break

    return entry


# ── Helpers shared by scanner and batch generator ────────────────────────────

def _default_workers() -> int:
    """Sensible default thread count: all logical CPUs, capped at 16."""
    return min(os.cpu_count() or 4, 16)


def entry_to_canonical(entry: dict) -> dict:
    """
    Build a canonical dict from a scan entry (INF / DLL / SYS).
    Used by the batch generator so it doesn't need a raw data folder.
    """
    canonical = empty_canonical("windows", "unknown")
    canonical["device"]["description"]  = entry.get("description")
    canonical["device"]["class"]        = entry.get("class")
    canonical["device"]["bus"]          = entry.get("bus", "pci")
    canonical["device"]["vendor_id"]    = entry.get("vendor_id")
    canonical["device"]["device_id"]    = entry.get("device_id")
    canonical["device"]["subsystem_id"] = entry.get("subsystem_id")
    canonical["device"]["revision"]     = entry.get("revision")
    canonical["driver"]["version"]      = entry.get("version")
    canonical["driver"]["provider"]     = (entry.get("provider") or
                                           entry.get("company"))
    canonical["driver"]["firmware"]          = list(entry.get("firmware_refs") or [])
    canonical["driver"]["registry_keys"]     = list(entry.get("registry_keys") or [])
    canonical["device"]["original_filename"] = entry.get("original_filename", "")
    name = _derive_chipset_name(canonical,
                                fallback=entry.get("filename", "driver"))
    canonical["device"]["name"] = name
    return canonical


# ── Main scanner (parallel) ───────────────────────────────────────────────────

def scan_for_drivers(folder: str, recursive: bool = True,
                     progress_cb=None, workers: int = 0) -> list:
    """
    Walk *folder* for driver files (.inf, .dll, .sys) and return a unified
    list of device/binary entries.  Files are parsed in parallel using a
    thread pool.

    Args:
        folder      : Root path to scan.
        recursive   : Walk subdirectories when True.
        progress_cb : Optional callable(current_file_path, found_so_far).
                      Called from worker threads — must be thread-safe.
        workers     : Thread count (0 = auto: all logical CPUs, max 16).
    """
    root = Path(folder)
    if not root.exists():
        log(f"Scan: folder does not exist: {root}")
        return []

    n_workers = workers if workers > 0 else _default_workers()
    glob_pat  = "**/*" if recursive else "*"

    all_files = [
        p for p in root.glob(glob_pat)
        if p.is_file() and p.suffix.lower() in {".inf", ".dll", ".sys"}
    ]
    inf_files = [p for p in all_files if p.suffix.lower() == ".inf"]
    bin_files = [p for p in all_files if p.suffix.lower() in {".dll", ".sys"}]

    n_dll = sum(1 for p in bin_files if p.suffix.lower() == ".dll")
    n_sys = sum(1 for p in bin_files if p.suffix.lower() == ".sys")
    log(f"Scan: {len(inf_files)} .inf  |  {n_dll} .dll  |  {n_sys} .sys  "
        f"under {root}  [workers={n_workers}]")

    results:  list          = []
    lock:     threading.Lock = threading.Lock()
    counter:  list          = [0]          # mutable int for thread-safe count

    def _parse_inf_worker(path: Path):
        entries = parse_inf(path)
        for e in entries:
            e["file_type"] = "INF"
            e["type_tag"]  = "INF"
        with lock:
            results.extend(entries)
            counter[0] += len(entries)
            if progress_cb:
                progress_cb(str(path), counter[0])

    def _parse_bin_worker(path: Path):
        entry = parse_dll(path)
        with lock:
            results.append(entry)
            counter[0] += 1
            if progress_cb:
                progress_cb(str(path), counter[0])

    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = (
            [pool.submit(_parse_inf_worker, p) for p in inf_files] +
            [pool.submit(_parse_bin_worker, p) for p in bin_files]
        )
        # Wait for all; surface any exceptions
        for fut in as_completed(futures):
            exc = fut.exception()
            if exc:
                log(f"Scan worker error: {exc}")

    # Deduplicate
    seen:   set  = set()
    unique: list = []
    for d in results:
        ft = d.get("file_type", "INF")
        key = ((d.get("vendor_id"), d.get("device_id"), d.get("inf_path"))
               if ft == "INF" else (ft, d.get("inf_path")))
        if key not in seen:
            seen.add(key)
            unique.append(d)

    n_i = sum(1 for d in unique if d.get("file_type") == "INF")
    n_d = sum(1 for d in unique if d.get("file_type") == "DLL")
    n_s = sum(1 for d in unique if d.get("file_type") == "SYS")
    log(f"Scan complete: {n_i} INF  {n_d} DLL  {n_s} SYS  "
        f"({len(unique)} total unique)")
    return unique


# ── Batch generator (parallel) ────────────────────────────────────────────────

def batch_generate_drivers(entries: list, out_base_dir: str,
                            workers: int = 0,
                            progress_cb=None) -> list:
    """
    Generate Linux driver skeletons for multiple scan entries in parallel.

    Each entry gets its own subdirectory under *out_base_dir* named after
    the derived chipset name (e.g. out_base_dir/mt7927/, out_base_dir/rtl8125/).

    Args:
        entries     : List of scan entry dicts (from scan_for_drivers).
        out_base_dir: Root output directory.
        workers     : Thread count (0 = auto).
        progress_cb : Optional callable(chipset_name, success, error_or_None)
                      called after each driver finishes.

    Returns list of (chipset_name, output_path, success, error_message) tuples.
    """
    n_workers = workers if workers > 0 else min(_default_workers(), len(entries))
    out_base  = Path(out_base_dir)
    out_base.mkdir(parents=True, exist_ok=True)

    log(f"Batch generate: {len(entries)} drivers  [workers={n_workers}]")

    def _gen_one(entry: dict):
        canonical = entry_to_canonical(entry)
        chipset   = canonical["device"]["name"]
        out_dir   = out_base / chipset
        try:
            generate_linux_driver(canonical, str(out_dir))
            if progress_cb:
                progress_cb(chipset, True, None)
            return (chipset, str(out_dir), True, None)
        except Exception as exc:
            msg = str(exc)
            log(f"Batch generate ERROR [{chipset}]: {msg}")
            if progress_cb:
                progress_cb(chipset, False, msg)
            return (chipset, str(out_dir), False, msg)

    results = []
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = {pool.submit(_gen_one, e): e for e in entries}
        for fut in as_completed(futures):
            results.append(fut.result())

    n_ok  = sum(1 for r in results if r[2])
    n_err = sum(1 for r in results if not r[2])
    log(f"Batch complete: {n_ok} OK  {n_err} errors")

    master = out_base / "install_all.sh"
    with master.open("w", encoding="utf-8", newline="\n") as f:
        f.write("#!/bin/bash\n# AstraForge — install all generated drivers\nset -e\n")
        for name, path, ok, _ in results:
            if ok:
                f.write(f'echo "--- Installing {name} ---"\n')
                f.write(f'bash "{path}/install.sh"\n')
    log(f"Written: {master}")

    return results


# ============================================================
# KNOWLEDGE BASE
# ============================================================

# Default KB locations checked in order
_KB_SEARCH_PATHS = [
    Path(__file__).parent.parent.parent / "knowledge_base",   # project root
    Path(__file__).parent.parent       / "knowledge_base",   # tools/
    Path(__file__).parent              / "knowledge_base",   # AstraForge/
]


class KnowledgeBase:
    """
    Lightweight JSON-based reference database for Windows/Linux driver data.

    Loaded lazily on first use. Keeps AF core fast when KB is absent.

    Directory layout:
        knowledge_base/
        ├── index.json
        ├── mappings/ndis.json
        ├── mappings/kmdf.json
        └── devices/{VID}_{DID}.json
    """

    def __init__(self, kb_path: Path):
        self.path     = kb_path
        self._devices: dict = {}
        self._ndis:    dict = {}
        self._kmdf:    dict = {}
        self._loaded   = False

    def _load(self):
        if self._loaded:
            return
        self._loaded = True

        # Extended API mappings
        ndis_f = self.path / "mappings" / "ndis.json"
        kmdf_f = self.path / "mappings" / "kmdf.json"
        if ndis_f.exists():
            try:
                raw = json.loads(ndis_f.read_text(encoding="utf-8"))
                self._ndis = {k: v for k, v in raw.items() if not k.startswith("_")}
            except Exception as e:
                log(f"KB: could not load ndis.json: {e}")
        if kmdf_f.exists():
            try:
                raw = json.loads(kmdf_f.read_text(encoding="utf-8"))
                self._kmdf = {k: v for k, v in raw.items() if not k.startswith("_")}
            except Exception as e:
                log(f"KB: could not load kmdf.json: {e}")

        # Device entries
        dev_dir = self.path / "devices"
        if dev_dir.exists():
            for f in dev_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    key = f.stem.lower()                   # "14c3_7927"
                    self._devices[key] = data
                except Exception:
                    pass

        n_d = len(self._devices)
        n_n = len(self._ndis)
        n_k = len(self._kmdf)
        log(f"KB loaded: {n_d} devices  {n_n} NDIS  {n_k} KMDF mappings  [{self.path.name}]")

    # ── public API ────────────────────────────────────────────────────────────

    def lookup(self, vendor_id: str, device_id: str) -> dict:
        """Return KB entry for a device or empty dict if not found."""
        self._load()
        if not vendor_id or not device_id:
            return {}
        vid = vendor_id.upper().replace("0X", "").lstrip("0") or "0"
        did = device_id.upper().replace("0X", "").lstrip("0") or "0"
        key = f"{vid.lower().zfill(4)}_{did.lower().zfill(4)}"
        return self._devices.get(key, {})

    def get_ndis_mappings(self) -> dict:
        """Return merged NDIS mapping table (built-in + KB extended)."""
        self._load()
        return {**NDIS_TO_LINUX, **self._ndis}

    def get_kmdf_mappings(self) -> dict:
        """Return merged KMDF mapping table (built-in + KB extended)."""
        self._load()
        return {**KMDF_TO_LINUX, **self._kmdf}

    def search(self, query: str) -> list:
        """Search devices by any text field. Returns list of matching entries."""
        self._load()
        q = query.lower()
        results = []
        for entry in self._devices.values():
            searchable = " ".join(str(v) for v in entry.values()).lower()
            if q in searchable:
                results.append(entry)
        return results

    def all_devices(self) -> list:
        self._load()
        return list(self._devices.values())


def _find_kb() -> "KnowledgeBase | None":
    """Find the knowledge_base directory, checking config then default paths."""
    cfg_path = load_config().get("kb_path", "")
    search   = ([Path(cfg_path)] if cfg_path else []) + _KB_SEARCH_PATHS
    for p in search:
        if p.exists() and (p / "index.json").exists():
            return KnowledgeBase(p)
    return None


# Module-level singleton (loaded lazily on first use)
_kb: "KnowledgeBase | None" = None

def get_kb() -> "KnowledgeBase | None":
    global _kb
    if _kb is None:
        _kb = _find_kb()
    return _kb


def kb_save_device(canonical: dict) -> Path:
    """
    Write the canonical device entry to knowledge_base/devices/{VID}_{DID}.json.
    Creates the directory structure if needed. Returns the path written.
    """
    dev = canonical.get("device", {})
    drv = canonical.get("driver", {})
    vid = (dev.get("vendor_id") or "0x0000").upper().replace("0X", "").lstrip("0") or "0"
    did = (dev.get("device_id") or "0x0000").upper().replace("0X", "").lstrip("0") or "0"
    key = f"{vid.lower().zfill(4)}_{did.lower().zfill(4)}"

    # Prefer configured KB path; fall back to project root
    cfg_path = load_config().get("kb_path", "")
    if cfg_path and Path(cfg_path).exists():
        kb_root = Path(cfg_path)
    else:
        kb_root = _KB_SEARCH_PATHS[0]

    devices_dir = kb_root / "devices"
    devices_dir.mkdir(parents=True, exist_ok=True)

    entry = {
        "vendor_id":              dev.get("vendor_id"),
        "device_id":              dev.get("device_id"),
        "chipset":                dev.get("name"),
        "description":            dev.get("description"),
        "class":                  dev.get("class"),
        "bus":                    dev.get("bus", "pci"),
        "version":                drv.get("version"),
        "provider":               drv.get("provider"),
        "firmware_files":         drv.get("firmware", []),
        "registry_keys":          drv.get("registry_keys", []),
        "linux_upstream_driver":  None,
        "linux_upstream_status":  "Unknown — reverse engineering in progress",
        "similar_linux_drivers":  [],
        "register_map":           {},
        "notes":                  "",
    }

    out = devices_dir / f"{key}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)
    log(f"KB: saved device entry → {out}")

    # Invalidate singleton so next get_kb() reloads
    global _kb
    _kb = None
    return out


def run_kb(args):
    """CLI handler for the 'kb' command."""
    kb = get_kb()
    if kb is None:
        print("Knowledge base not found.")
        print("Expected location:", _KB_SEARCH_PATHS[0])
        print("Or set 'kb_path' in AstraForge.config.json")
        return

    if args.search:
        results = kb.search(args.search)
        if not results:
            print(f"No devices found matching '{args.search}'")
            return
        print(f"Found {len(results)} device(s):\n")
        for r in results:
            _print_kb_entry(r)
    elif args.lookup:
        parts  = args.lookup.upper().replace("0X","").split(":")
        vid    = f"0x{parts[0]}" if parts else ""
        did    = f"0x{parts[1]}" if len(parts) > 1 else ""
        entry  = kb.lookup(vid, did)
        if entry:
            _print_kb_entry(entry)
        else:
            print(f"No KB entry for {args.lookup}")
    else:
        # List all
        devices = kb.all_devices()
        ndis    = kb.get_ndis_mappings()
        kmdf    = kb.get_kmdf_mappings()
        print(f"Knowledge Base: {kb.path}")
        print(f"  {len(devices)} devices  |  {len(ndis)} NDIS mappings  |  {len(kmdf)} KMDF mappings\n")
        for d in devices:
            upstream = d.get("linux_upstream_driver") or "no upstream"
            print(f"  [{d.get('vendor_id','?')}:{d.get('device_id','?')}]  "
                  f"{d.get('chipset','?'):<12}  {d.get('description',''):<45}  "
                  f"linux={upstream}")


def _print_kb_entry(entry: dict):
    print(f"  {entry.get('chipset','?')}  "
          f"[{entry.get('vendor_id','?')}:{entry.get('device_id','?')}]")
    print(f"  {entry.get('description','')}")
    print(f"  Linux driver : {entry.get('linux_upstream_driver') or 'none (no upstream)'}")
    print(f"  Status       : {entry.get('linux_upstream_status','unknown')}")
    if entry.get("similar_linux_drivers"):
        print("  Similar      :", ", ".join(
            d.get("module","?") for d in entry["similar_linux_drivers"]))
    if entry.get("firmware_files"):
        print("  Firmware     :", ", ".join(entry["firmware_files"]))
    if entry.get("notes"):
        print(f"  Notes        : {entry['notes'][:120]}")
    print()


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "AstraForge (AF) — Windows-to-Linux driver reverse-engineering toolkit.\n\n"
            "Commands:\n"
            "  windows   normalise Windows driver data\n"
            "  linux     normalise Linux driver data\n"
            "  diff      compare Windows vs Linux canonical JSONs\n"
            "  generate  emit a compilable Linux kernel driver skeleton\n"
            "  kb        query the knowledge base"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        choices=["windows", "linux", "diff", "generate", "kb"],
    )
    parser.add_argument("--vendor-id", metavar="VID",
        help="PCI vendor ID or USB VID (e.g. 0x14C3).")
    parser.add_argument("--device-id", metavar="DID",
        help="PCI device ID or USB PID (e.g. 0x7927).")
    parser.add_argument("--search", metavar="TERM",
        help="(kb) Search knowledge base by any text.")
    parser.add_argument("--lookup", metavar="VID:DID",
        help="(kb) Look up a specific device e.g. 14C3:7927.")

    args = parser.parse_args()

    if args.command == "windows":
        normalize_windows(vendor_id=args.vendor_id, device_id=args.device_id)
    elif args.command == "linux":
        normalize_linux(vendor_id=args.vendor_id, device_id=args.device_id)
    elif args.command == "diff":
        run_diff()
    elif args.command == "generate":
        run_generate()
    elif args.command == "kb":
        run_kb(args)


if __name__ == "__main__":
    main()

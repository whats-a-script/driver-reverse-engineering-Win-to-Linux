"""Local known-devices repository handler with hardware-ID hashing support.

This module manages the local known-devices repository and provides
functions to check if a device is known and load its canonical data.
Supports lookup by chipset name or hardware-ID hash.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Optional


def get_known_devices_root() -> Path:
    """Get the root directory for known devices data."""
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    return repo_root / "data" / "known_devices"


def find_by_hardware_hash(hardware_hash: str, platform: str) -> Optional[dict]:
    """
    Find a known-device by its hardware-ID hash.
    
    This searches all known-device files in the platform directory
    and returns the first one that matches the hardware_id_hash.
    
    Args:
        hardware_hash: The SHA-256 hardware ID hash to search for
        platform: The platform ('windows' or 'linux')
        
    Returns:
        Dictionary with known-device data, or None if not found
    """
    known_devices_root = get_known_devices_root()
    platform_dir = known_devices_root / platform
    
    if not platform_dir.exists():
        return None
    
    # Search all JSON files in the platform directory
    for device_file in platform_dir.glob("*.json"):
        try:
            with open(device_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if this device matches the hardware hash
            if data.get("hardware_id_hash") == hardware_hash:
                return data
        except (json.JSONDecodeError, OSError):
            continue
    
    return None


def compute_hardware_id_hash(vendor_id: str, device_id: str, 
                             subsystem_id: Optional[str] = None,
                             revision: Optional[str] = None) -> str:
    """
    Compute a deterministic SHA-256 hash from hardware identifiers.
    
    Format: VEN_<vendor>|DEV_<device>|SUBSYS_<subsystem>|REV_<revision>
    
    Note: Vendor, device, and subsystem IDs are 16-bit values (4 hex chars),
    while revision is an 8-bit value (2 hex chars), per PCI specification.
    
    Args:
        vendor_id: PCI vendor ID (hex string)
        device_id: PCI device ID (hex string)
        subsystem_id: Optional subsystem ID (hex string)
        revision: Optional revision (hex string, 8-bit value)
        
    Returns:
        SHA-256 hash as hex string
    """
    # Normalize IDs (remove 0x prefix, lowercase, pad to proper length)
    def normalize_id(id_str: Optional[str], width: int = 4) -> str:
        if not id_str:
            return "0" * width
        cleaned = id_str.strip().lower()
        if cleaned.startswith("0x"):
            cleaned = cleaned[2:]
        return cleaned.zfill(width)
    
    vendor = normalize_id(vendor_id, 4)  # 16-bit
    device = normalize_id(device_id, 4)  # 16-bit
    subsys = normalize_id(subsystem_id, 4) if subsystem_id else "0000"  # 16-bit
    rev = normalize_id(revision, 2) if revision else "00"  # 8-bit per PCI spec
    
    # Build normalized string
    normalized = f"VEN_{vendor}|DEV_{device}|SUBSYS_{subsys}|REV_{rev}"
    
    # Compute SHA-256
    return hashlib.sha256(normalized.encode()).hexdigest()


def is_known_device(chipset: str, platform: str) -> bool:
    """
    Check if a device is in the local known-devices repository.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        
    Returns:
        True if the device has a known-device JSON file locally, False otherwise
    """
    known_devices_root = get_known_devices_root()
    device_file = known_devices_root / platform / f"{chipset}.json"
    return device_file.exists()


def load_known_device(chipset: str, platform: str) -> Optional[dict]:
    """
    Load known-device data from the local repository.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        
    Returns:
        Dictionary with known-device data, or None if not found or invalid
    """
    known_devices_root = get_known_devices_root()
    device_file = known_devices_root / platform / f"{chipset}.json"
    
    if not device_file.exists():
        return None
    
    try:
        with open(device_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to load known device {chipset}/{platform}: {e}")
        return None


def save_known_device(chipset: str, platform: str, data: dict) -> bool:
    """
    Save known-device data to the local repository.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        data: The known-device data to save
        
    Returns:
        True if saved successfully, False otherwise
    """
    known_devices_root = get_known_devices_root()
    platform_dir = known_devices_root / platform
    
    # Create platform directory if it doesn't exist
    platform_dir.mkdir(parents=True, exist_ok=True)
    
    device_file = platform_dir / f"{chipset}.json"
    
    try:
        with open(device_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except (OSError, TypeError) as e:
        print(f"Error: Failed to save known device {chipset}/{platform}: {e}")
        return False


def merge_known_into_canonical(canonical: dict, known: dict) -> dict:
    """
    Merge known-device data into a canonical JSON structure.
    
    This function takes validated known-device data and merges it into
    the canonical structure, filling in gaps and providing baseline values.
    
    Rules:
    - Canonical values override known-good values
    - Known-good values fill missing canonical fields
    - Must not remove canonical fields
    
    Args:
        canonical: The canonical JSON structure being built
        known: The known-device data from local or remote repository
        
    Returns:
        Updated canonical dictionary with known-device data merged in
    """
    # Add known_device marker
    if "metadata" not in canonical:
        canonical["metadata"] = {}
    
    canonical["metadata"]["known_device_source"] = "local"
    canonical["metadata"]["known_device_chipset"] = known.get("chipset", "unknown")
    
    # Add hardware_id_hash from known device if not already present
    if "device" not in canonical:
        canonical["device"] = {}
    
    if not canonical["device"].get("hardware_id_hash") and known.get("hardware_id_hash"):
        canonical["device"]["hardware_id_hash"] = known["hardware_id_hash"]
    
    # Merge known_good data if present
    if "known_good" in known:
        known_good = known["known_good"]
        
        # Update driver version if known and not already set
        if known_good.get("driver_version") and not canonical.get("metadata", {}).get("driver_version"):
            canonical["metadata"]["driver_version"] = known_good["driver_version"]
        
        # Add firmware info if present
        if known_good.get("firmware"):
            if "firmware" not in canonical:
                canonical["firmware"] = {}
            canonical["firmware"]["known_blobs"] = known_good["firmware"]
        
        # Add INF file info for Windows
        if canonical.get("platform") == "windows" and known_good.get("inf"):
            if "windows_nav_card" not in canonical:
                canonical["windows_nav_card"] = {}
            if not canonical["windows_nav_card"].get("inf_file_path"):
                canonical["windows_nav_card"]["inf_file_path"] = known_good["inf"]
    
    # Merge canonical data if present (only fill missing fields)
    if "canonical" in known:
        known_canonical = known["canonical"]
        
        # Deep merge register_map if present
        if "register_map" in known_canonical:
            if "register_map" not in canonical:
                canonical["register_map"] = []
            # Add known registers that aren't already present
            existing_addresses = {reg.get("address") for reg in canonical["register_map"]}
            for known_reg in known_canonical["register_map"]:
                if known_reg.get("address") not in existing_addresses:
                    canonical["register_map"].append(known_reg)
        
        # Deep merge functions if present
        if "functions" in known_canonical:
            if "functions" not in canonical:
                canonical["functions"] = []
            # Add known functions that aren't already present
            existing_functions = {fn.get("name") for fn in canonical["functions"]}
            for known_fn in known_canonical["functions"]:
                if known_fn.get("name") not in existing_functions:
                    canonical["functions"].append(known_fn)
    
    return canonical


def validate_against_known(canonical: dict, known: dict) -> dict:
    """
    Validate canonical data against known-device expectations.
    
    Args:
        canonical: The canonical JSON structure
        known: The known-device data
        
    Returns:
        Dictionary with validation results including hardware hash match
    """
    validation = {
        "known_device_matched": True,
        "hardware_hash_match": False,
        "driver_version_match": None,
        "missing_fields": [],
        "warnings": [],
        "info": []
    }
    
    # Check hardware ID hash match
    canonical_hash = canonical.get("device", {}).get("hardware_id_hash")
    known_hash = known.get("hardware_id_hash")
    
    if canonical_hash and known_hash:
        validation["hardware_hash_match"] = (canonical_hash == known_hash)
        if not validation["hardware_hash_match"]:
            validation["warnings"].append(
                f"Hardware ID hash mismatch: expected {known_hash}, found {canonical_hash}"
            )
    elif known_hash and not canonical_hash:
        validation["missing_fields"].append("device.hardware_id_hash")
    
    # Check driver version if known_good specifies it
    if "known_good" in known and known["known_good"].get("driver_version"):
        expected_version = known["known_good"]["driver_version"]
        actual_version = canonical.get("metadata", {}).get("driver_version")
        
        if actual_version:
            validation["driver_version_match"] = (actual_version == expected_version)
            if actual_version != expected_version:
                validation["warnings"].append(
                    f"Driver version mismatch: expected {expected_version}, found {actual_version}"
                )
        else:
            validation["driver_version_match"] = False
            validation["missing_fields"].append("metadata.driver_version")
    
    # Check firmware if known_good specifies it
    if "known_good" in known and known["known_good"].get("firmware"):
        expected_firmware = set(known["known_good"]["firmware"])
        actual_firmware = set(canonical.get("firmware", {}).get("known_blobs", []))
        
        missing = expected_firmware - actual_firmware
        if missing:
            validation["info"].append(
                f"Known firmware blobs not found: {', '.join(sorted(missing))}"
            )
    
    return validation

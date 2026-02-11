"""Local known-devices repository handler.

This module manages the local known-devices repository and provides
functions to check if a device is known and load its canonical data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def get_known_devices_root() -> Path:
    """Get the root directory for known devices data."""
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[3]
    return repo_root / "data" / "known_devices"


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
    
    # Merge canonical data if present
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
        Dictionary with validation results
    """
    validation = {
        "known_device_matched": True,
        "warnings": [],
        "info": []
    }
    
    # Check driver version if known_good specifies it
    if "known_good" in known and known["known_good"].get("driver_version"):
        expected_version = known["known_good"]["driver_version"]
        actual_version = canonical.get("metadata", {}).get("driver_version")
        
        if actual_version and actual_version != expected_version:
            validation["warnings"].append(
                f"Driver version mismatch: expected {expected_version}, found {actual_version}"
            )
    
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

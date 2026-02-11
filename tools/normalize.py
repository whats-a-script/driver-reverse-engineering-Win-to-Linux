#!/usr/bin/env python3
"""
normalize.py - Driver data normalization tool

SYNOPSIS:
    python normalize.py <device_id> <platform>

DESCRIPTION:
    Converts raw Windows or Linux driver data into canonical JSON format
    for the MT7927 analysis pipeline. Parses binary drivers (Windows .sys)
    using PE analysis and source drivers (Linux .c/.h) using AST parsing.

PARAMETERS:
    device_id - Unique identifier for the device (e.g., "intel_ax210")
    platform  - Target platform: "windows" or "linux"

EXAMPLES:
    python normalize.py intel_ax210 windows
    python normalize.py intel_ax210 linux

NOTES:
    Author: MT7927 Analysis Project
    Version: 1.0.0 - SCAFFOLDING
    
    This is a minimal scaffolding script. Future implementation should:
    - Parse Windows PE files (.sys) for exports, imports, sections
    - Parse Linux source files (.c, .h) using Python AST or clang
    - Extract register definitions (address, name, access type)
    - Identify function signatures and purposes
    - Parse device IDs and supported hardware
    - Generate canonical JSON conforming to schema in AGENT_INSTRUCTIONS.md
    - Validate output against JSON schema
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from AstraForge.modules import chipset_detector
from AstraForge.modules import known_devices_remote
import normalize_windows as norm_win


def normalize_windows(device_id: str, chipset: str, raw_data_path) -> dict:
    """
    Normalize Windows driver data to canonical JSON format.
    
    Phase 1 Implementation:
    - Extract driver metadata from driver_files.json and driver_package.json
    - Populate canonical['driver']['files'], version, provider, date
    - Populate canonical['device']['manufacturer']
    
    TODO for future phases:
    - PE file parsing for .sys files
    - Export/import table analysis
    - String extraction for register names
    """
    print(f"Normalizing Windows driver for {device_id}")
    print(f"  Reading from: {raw_data_path}")
    print(f"  Detected chipset: {chipset}")
    
    # Create base canonical structure
    canonical = create_placeholder_canonical(device_id, "windows", chipset)
    
    # Phase 1: Extract driver data from JSON files
    canonical = norm_win.populate_windows_driver_data(canonical, raw_data_path)
    
    # Check for known-device data (local first, then remote)
    print(f"  Checking for known-device data for chipset: {chipset}")
    known = known_devices_remote.get_known_device_with_fallback(chipset, "windows")
    
    if known:
        print(f"  ✓ Found known-device data for {chipset}")
        from AstraForge.modules import known_devices
        canonical = known_devices.merge_known_into_canonical(canonical, known)
        canonical["known_device_validation"] = known_devices.validate_against_known(canonical, known)
    else:
        print(f"  ℹ No known-device data found for {chipset}")
    
    return canonical


def normalize_linux(device_id: str, chipset: str) -> dict:
    """
    Normalize Linux driver data to canonical JSON format.
    
    TODO: Implement:
    - C source file parsing (.c, .h)
    - AST analysis for function signatures
    - Register map extraction from #define statements
    - Device ID parsing from MODULE_DEVICE_TABLE
    - Kconfig parsing for driver options
    """
    print(f"[TODO] Linux normalization for {device_id}")
    print("  - Parse C source files with AST")
    print("  - Extract function signatures")
    print("  - Parse #define statements for registers")
    print("  - Extract MODULE_DEVICE_TABLE entries")
    
    canonical = create_placeholder_canonical(device_id, "linux", chipset)
    
    # Check for known-device data (local first, then remote)
    print(f"  Checking for known-device data for chipset: {chipset}")
    known = known_devices_remote.get_known_device_with_fallback(chipset, "linux")
    
    if known:
        print(f"  ✓ Found known-device data for {chipset}")
        from AstraForge.modules import known_devices
        canonical = known_devices.merge_known_into_canonical(canonical, known)
        canonical["known_device_validation"] = known_devices.validate_against_known(canonical, known)
    else:
        print(f"  ℹ No known-device data found for {chipset}")
    
    return canonical


def create_placeholder_canonical(device_id: str, platform: str, chipset: str) -> dict:
    """
    Create a placeholder canonical JSON structure.
    
    This is used for scaffolding. Real implementation should parse actual
    driver data and populate these fields accurately.
    """
    return {
        "device_id": device_id,
        "device_name": f"{device_id.replace('_', ' ').title()} (Placeholder)",
        "platform": platform,
        "metadata": {
            "driver_version": "0.0.0.SYNTHETIC",
            "driver_date": datetime.now().strftime("%Y-%m-%d"),
            "vendor": "Unknown",
            "chipset": chipset,
            "source_url": None,  # Do not invent URLs
            "collection_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "SYNTHETIC - Placeholder data created by scaffolding script."
        },
        "windows_nav_card": {
            "driver_download_url": None,  # Do not invent URLs
            "support_page_url": None,  # Do not invent URLs
            "inf_file_path": None
        } if platform == "windows" else None,
        "driver_components": {
            "modules": [],
            "config_files": []
        },
        "register_map": [
            {
                "address": "0x0000",
                "name": "PLACEHOLDER_REG",
                "description": "Placeholder register for scaffolding",
                "access": "rw"
            }
        ],
        "functions": [
            {
                "name": "placeholder_function",
                "signature": "void placeholder_function(void)",
                "purpose": "Placeholder function for scaffolding"
            }
        ]
    }


def main():
    """Main entry point for normalization script."""
    if len(sys.argv) != 3:
        print("Usage: python normalize.py <device_id> <platform>")
        print("  platform: windows | linux")
        sys.exit(1)
    
    device_id = sys.argv[1]
    platform = sys.argv[2].lower()
    
    if platform not in ["windows", "linux"]:
        print(f"ERROR: Invalid platform '{platform}'. Must be 'windows' or 'linux'.")
        sys.exit(1)
    
    print("=" * 60)
    print("Driver Normalization Tool - SCAFFOLDING VERSION")
    print("=" * 60)
    print(f"Device ID: {device_id}")
    print(f"Platform:  {platform}")
    print()
    
    # Determine paths
    repo_root = SCRIPT_DIR.parent
    raw_data_path = repo_root / "data" / "raw" / platform / device_id
    canonical_path = repo_root / "data" / "canonical"
    output_file = canonical_path / f"{device_id}_{platform}.json"
    
    print(f"Input:  {raw_data_path}")
    print(f"Output: {output_file}")
    print()
    
    vendor_id, device_id_value, subsystem = chipset_detector._extract_pci_ids(
        raw_data_path, platform
    )
    detected_chipset = chipset_detector.detect_chipset(
        vendor_id or "", device_id_value or "", subsystem
    )
    if detected_chipset == "unknown":
        # Fallback to folder name when PCI detection fails.
        detected_chipset = raw_data_path.name or device_id

    # Normalize based on platform
    if platform == "windows":
        canonical_data = normalize_windows(device_id, detected_chipset, raw_data_path)
    else:
        canonical_data = normalize_linux(device_id, detected_chipset)
    
    # Create output directory if needed
    canonical_path.mkdir(parents=True, exist_ok=True)
    
    # Write canonical JSON
    with open(output_file, 'w') as f:
        json.dump(canonical_data, f, indent=2)
    
    print()
    print(f"✓ Canonical JSON written to: {output_file}")
    print()
    print("NOTICE: This is a SCAFFOLDING script producing SYNTHETIC data.")
    print("Real implementation required for actual driver parsing.")
    print()


if __name__ == "__main__":
    main()

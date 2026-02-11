#!/usr/bin/env python3
"""
normalize_linux.py - Linux driver data extraction and normalization

This module extracts driver metadata from raw Linux driver files
(modinfo.txt, uname.txt, etc.) and populates the canonical format.

This is Phase 1B implementation, symmetrical to normalize_windows.py.

Author: MT7927 Analysis Project
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


def load_text_file(file_path: Path) -> Optional[str]:
    """
    Load a text file and return its contents.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        String with file contents, or None if file doesn't exist or is invalid
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except OSError as e:
        print(f"Warning: Failed to load {file_path}: {e}")
        return None


def parse_modinfo(modinfo_content: Optional[str]) -> Dict[str, List[str]]:
    """
    Parse modinfo.txt content into a structured dictionary.
    
    Args:
        modinfo_content: Content of modinfo.txt file
        
    Returns:
        Dictionary mapping field names to lists of values
        (some fields like 'firmware' can have multiple values)
    """
    if not modinfo_content:
        return {}
    
    parsed = {}
    for line in modinfo_content.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        
        # Split on first colon
        field, value = line.split(':', 1)
        field = field.strip()
        value = value.strip()
        
        if field not in parsed:
            parsed[field] = []
        parsed[field].append(value)
    
    return parsed


def extract_driver_files(modinfo_data: Dict[str, List[str]]) -> List[Dict]:
    """
    Extract driver file information from parsed modinfo data.
    
    Extracts:
    - Module file (.ko) from 'filename' field
    - Firmware files from 'firmware' fields
    
    Args:
        modinfo_data: Parsed modinfo dictionary
        
    Returns:
        List of file dictionaries for canonical['driver']['files']
    """
    canonical_files = []
    
    # Extract module file
    if 'filename' in modinfo_data and modinfo_data['filename']:
        filename_path = modinfo_data['filename'][0]
        module_name = Path(filename_path).name
        
        canonical_file = {
            'name': module_name,
            'type': 'ko',  # kernel object
        }
        canonical_files.append(canonical_file)
    
    # Extract firmware files
    if 'firmware' in modinfo_data:
        for firmware_name in modinfo_data['firmware']:
            canonical_file = {
                'name': firmware_name,
                'type': 'firmware',
            }
            canonical_files.append(canonical_file)
    
    return canonical_files


def extract_driver_version(modinfo_data: Dict[str, List[str]], 
                           uname_content: Optional[str]) -> Optional[str]:
    """
    Best-effort extraction of driver version.
    
    Tries in order:
    1. modinfo 'version' field
    2. modinfo 'vermagic' field (kernel version)
    3. uname output (kernel version)
    
    Args:
        modinfo_data: Parsed modinfo dictionary
        uname_content: Content of uname.txt file (optional)
        
    Returns:
        Driver version string or None
    """
    # Try explicit version field first
    if 'version' in modinfo_data and modinfo_data['version']:
        version = modinfo_data['version'][0]
        # Skip generic values like "in-tree:"
        if version and version not in ['in-tree:', 'in-tree']:
            return version
    
    # Try vermagic (contains kernel version)
    if 'vermagic' in modinfo_data and modinfo_data['vermagic']:
        vermagic = modinfo_data['vermagic'][0]
        # Extract kernel version from vermagic (e.g., "6.1.0-17-amd64 SMP ...")
        match = re.match(r'^([\d\.\-\w]+)', vermagic)
        if match:
            return f"kernel-{match.group(1)}"
    
    # Fallback to uname
    if uname_content:
        # uname -r output is just the kernel version
        uname_content = uname_content.strip()
        if uname_content:
            return f"kernel-{uname_content}"
    
    return None


def extract_driver_metadata(modinfo_data: Dict[str, List[str]]) -> Dict:
    """
    Extract driver metadata from parsed modinfo data.
    
    Args:
        modinfo_data: Parsed modinfo dictionary
        
    Returns:
        Dictionary with driver metadata (version, provider, description)
    """
    metadata = {
        'provider': None,
        'description': None,
        'license': None,
    }
    
    # Extract author as provider
    if 'author' in modinfo_data and modinfo_data['author']:
        metadata['provider'] = modinfo_data['author'][0]
    
    # Extract description
    if 'description' in modinfo_data and modinfo_data['description']:
        metadata['description'] = modinfo_data['description'][0]
    
    # Extract license
    if 'license' in modinfo_data and modinfo_data['license']:
        metadata['license'] = modinfo_data['license'][0]
    
    return metadata


def extract_firmware_references(modinfo_data: Dict[str, List[str]]) -> List[str]:
    """
    Extract firmware file references for Phase 2 analysis.
    
    Args:
        modinfo_data: Parsed modinfo dictionary
        
    Returns:
        List of firmware filenames
    """
    if 'firmware' in modinfo_data:
        return modinfo_data['firmware']
    return []


def populate_linux_driver_data(canonical: Dict, raw_data_path: Path) -> Dict:
    """
    Populate canonical JSON with Linux driver data from raw files.
    
    This function reads modinfo.txt and optional files from the raw data
    directory and populates the canonical dictionary with:
    - canonical['driver']['files'] (module + firmware files)
    - canonical['driver']['version'] (best-effort)
    - canonical['driver']['provider'] (author)
    - canonical['driver']['description']
    - canonical['driver']['firmware_references'] (for Phase 2)
    
    Args:
        canonical: The canonical dictionary to populate
        raw_data_path: Path to the raw data directory for this device
        
    Returns:
        Updated canonical dictionary
    """
    # Load raw text files
    modinfo_path = raw_data_path / "modinfo.txt"
    uname_path = raw_data_path / "uname.txt"
    
    modinfo_content = load_text_file(modinfo_path)
    uname_content = load_text_file(uname_path)
    
    # Parse modinfo
    modinfo_data = parse_modinfo(modinfo_content)
    
    # Initialize driver and device sections if they don't exist
    if 'driver' not in canonical:
        canonical['driver'] = {}
    if 'device' not in canonical:
        canonical['device'] = {}
    
    # Extract and populate driver files
    canonical['driver']['files'] = extract_driver_files(modinfo_data)
    
    # Extract and populate driver version (best-effort)
    version = extract_driver_version(modinfo_data, uname_content)
    if version is not None:
        canonical['driver']['version'] = version
    
    # Extract and populate driver metadata
    metadata = extract_driver_metadata(modinfo_data)
    
    if metadata['provider'] is not None:
        canonical['driver']['provider'] = metadata['provider']
    if metadata['description'] is not None:
        canonical['driver']['description'] = metadata['description']
    if metadata['license'] is not None:
        canonical['driver']['license'] = metadata['license']
    
    # Extract firmware references for Phase 2
    firmware_refs = extract_firmware_references(modinfo_data)
    if firmware_refs:
        canonical['driver']['firmware_references'] = firmware_refs
    
    return canonical

#!/usr/bin/env python3
"""
normalize_linux.py - Linux driver data extraction and normalization

This module extracts driver metadata from raw Linux driver files
(modinfo.txt) and populates the canonical format.

Author: MT7927 Analysis Project
Phase: 1B - Linux Driver File Extraction
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


def parse_modinfo(modinfo_content: str) -> Dict[str, List[str]]:
    """
    Parse modinfo output into structured dictionary.
    
    modinfo output format is:
    key:        value
    key:        another value
    
    Some keys can appear multiple times (e.g., firmware, alias).
    
    Args:
        modinfo_content: Content of modinfo.txt file
        
    Returns:
        Dictionary mapping keys to lists of values
    """
    parsed = {}
    
    for line in modinfo_content.splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()
        
        if not key or not value:
            continue
        
        if key not in parsed:
            parsed[key] = []
        parsed[key].append(value)
    
    return parsed


def extract_driver_files_from_modinfo(modinfo_data: Dict[str, List[str]]) -> List[Dict]:
    """
    Extract driver file information from parsed modinfo data.
    
    Args:
        modinfo_data: Parsed modinfo dictionary
        
    Returns:
        List of file dictionaries for canonical['driver']['files']
    """
    files = []
    
    # Extract the main module file
    if 'filename' in modinfo_data:
        filename = modinfo_data['filename'][0]
        module_name = Path(filename).name
        
        file_entry = {
            'name': module_name,
            'type': 'ko',  # Linux kernel module
            'path': filename
        }
        files.append(file_entry)
    
    return files


def extract_driver_version(modinfo_data: Dict[str, List[str]]) -> Optional[str]:
    """
    Extract driver version from modinfo data (best-effort).
    
    Args:
        modinfo_data: Parsed modinfo dictionary
        
    Returns:
        Driver version string, or None if not found
    """
    if 'version' in modinfo_data:
        return modinfo_data['version'][0]
    
    # Fallback: try to extract from vermagic
    if 'vermagic' in modinfo_data:
        vermagic = modinfo_data['vermagic'][0]
        # vermagic format: "6.8.0-49-generic SMP preempt mod_unload modversions"
        # Extract kernel version part
        parts = vermagic.split()
        if parts:
            return parts[0]
    
    return None


def extract_firmware_references(modinfo_data: Dict[str, List[str]]) -> List[str]:
    """
    Extract firmware file references from modinfo data (for Phase 2).
    
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
    
    This function reads modinfo.txt from the raw data directory and populates
    the canonical dictionary with:
    - canonical['driver']['files']
    - canonical['driver']['version'] (best-effort)
    - canonical['driver']['provider'] (from author field)
    - canonical['driver']['firmware'] (for Phase 2)
    
    Args:
        canonical: The canonical dictionary to populate
        raw_data_path: Path to the raw data directory for this device
        
    Returns:
        Updated canonical dictionary
    """
    # Load modinfo.txt
    modinfo_path = raw_data_path / "modinfo.txt"
    modinfo_content = load_text_file(modinfo_path)
    
    if not modinfo_content:
        print(f"  Warning: modinfo.txt not found or empty at {modinfo_path}")
        return canonical
    
    # Parse modinfo data
    modinfo_data = parse_modinfo(modinfo_content)
    
    # Initialize driver section if it doesn't exist
    if 'driver' not in canonical:
        canonical['driver'] = {}
    
    # Extract and populate driver files
    canonical['driver']['files'] = extract_driver_files_from_modinfo(modinfo_data)
    
    # Extract and populate driver version (best-effort)
    version = extract_driver_version(modinfo_data)
    if version:
        canonical['driver']['version'] = version
    
    # Extract and populate driver provider/author
    if 'author' in modinfo_data:
        canonical['driver']['provider'] = modinfo_data['author'][0]
    
    # Extract firmware references for Phase 2
    firmware_refs = extract_firmware_references(modinfo_data)
    if firmware_refs:
        canonical['driver']['firmware'] = firmware_refs
    
    # Extract license information
    if 'license' in modinfo_data:
        canonical['driver']['license'] = modinfo_data['license'][0]
    
    # Extract description
    if 'description' in modinfo_data:
        canonical['driver']['description'] = modinfo_data['description'][0]
    
    return canonical

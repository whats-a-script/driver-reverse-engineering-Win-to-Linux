#!/usr/bin/env python3
"""
normalize_windows.py - Windows driver data extraction and normalization

This module extracts driver metadata from raw Windows driver files
(driver_files.json, driver_package.json) and populates the canonical format.

Author: MT7927 Analysis Project
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def load_json_file(file_path: Path) -> Optional[Dict]:
    """
    Load a JSON file and return its contents.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary with JSON contents, or None if file doesn't exist or is invalid
    """
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to load {file_path}: {e}")
        return None


def extract_driver_files(driver_files_data: Optional[Dict]) -> List[Dict]:
    """
    Extract driver file information from driver_files.json.
    
    Args:
        driver_files_data: Parsed driver_files.json content
        
    Returns:
        List of file dictionaries for canonical['driver']['files']
    """
    if not driver_files_data:
        return []
    
    files = driver_files_data.get('files', [])
    canonical_files = []
    
    for file_info in files:
        canonical_file = {
            'name': file_info.get('name', ''),
            'type': file_info.get('type', ''),
        }
        
        # Add optional fields if present
        if 'size_bytes' in file_info:
            canonical_file['size_bytes'] = file_info['size_bytes']
        if 'hash_sha256' in file_info:
            canonical_file['hash_sha256'] = file_info['hash_sha256']
        if 'version' in file_info:
            canonical_file['version'] = file_info['version']
        if 'product_name' in file_info:
            canonical_file['product_name'] = file_info['product_name']
        if 'file_description' in file_info:
            canonical_file['file_description'] = file_info['file_description']
            
        canonical_files.append(canonical_file)
    
    return canonical_files


def extract_driver_metadata(driver_package_data: Optional[Dict]) -> Dict:
    """
    Extract driver metadata from driver_package.json.
    
    Args:
        driver_package_data: Parsed driver_package.json content
        
    Returns:
        Dictionary with driver metadata (version, provider, date, manufacturer)
    """
    metadata = {
        'version': None,
        'provider': None,
        'date': None,
        'manufacturer': None
    }
    
    if not driver_package_data:
        return metadata
    
    # Extract from driver section
    driver_info = driver_package_data.get('driver', {})
    metadata['version'] = driver_info.get('version')
    metadata['provider'] = driver_info.get('provider')
    metadata['date'] = driver_info.get('date')
    
    # Extract manufacturer from device section
    device_info = driver_package_data.get('device', {})
    metadata['manufacturer'] = device_info.get('manufacturer')
    
    return metadata


def populate_windows_driver_data(canonical: Dict, raw_data_path: Path) -> Dict:
    """
    Populate canonical JSON with Windows driver data from raw files.
    
    This function reads driver_files.json and driver_package.json from the
    raw data directory and populates the canonical dictionary with:
    - canonical['driver']['files']
    - canonical['driver']['version']
    - canonical['driver']['provider']
    - canonical['driver']['date']
    - canonical['device']['manufacturer']
    
    Args:
        canonical: The canonical dictionary to populate
        raw_data_path: Path to the raw data directory for this device
        
    Returns:
        Updated canonical dictionary
    """
    # Load raw JSON files
    driver_files_path = raw_data_path / "driver_files.json"
    driver_package_path = raw_data_path / "driver_package.json"
    
    driver_files_data = load_json_file(driver_files_path)
    driver_package_data = load_json_file(driver_package_path)
    
    # Initialize driver and device sections if they don't exist
    if 'driver' not in canonical:
        canonical['driver'] = {}
    if 'device' not in canonical:
        canonical['device'] = {}
    
    # Extract and populate driver files
    canonical['driver']['files'] = extract_driver_files(driver_files_data)
    
    # Extract and populate driver metadata
    metadata = extract_driver_metadata(driver_package_data)
    
    if metadata['version'] is not None:
        canonical['driver']['version'] = metadata['version']
    if metadata['provider'] is not None:
        canonical['driver']['provider'] = metadata['provider']
    if metadata['date'] is not None:
        canonical['driver']['date'] = metadata['date']
    if metadata['manufacturer'] is not None:
        canonical['device']['manufacturer'] = metadata['manufacturer']
    
    return canonical

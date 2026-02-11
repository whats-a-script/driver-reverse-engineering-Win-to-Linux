"""Remote GitHub-hosted known-devices support.

This module provides functions to fetch known-device data from a remote
GitHub repository branch, check for remote existence, and sync remote
data to the local repository.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Tuple
from . import known_devices


# Default GitHub configuration
# Users can override these by setting environment variables or config file
DEFAULT_GITHUB_OWNER = "whats-a-script"
DEFAULT_GITHUB_REPO = "TP-link-wifi-MT7927-reverse-engineer"
DEFAULT_GITHUB_BRANCH = "main"


def _get_github_config() -> Tuple[str, str, str]:
    """
    Get GitHub configuration for remote known-devices repository.
    
    Returns:
        Tuple of (owner, repo, branch)
    """
    # In a production system, this would read from environment variables or config file
    # For now, use defaults
    import os
    owner = os.environ.get("KNOWN_DEVICES_GITHUB_OWNER", DEFAULT_GITHUB_OWNER)
    repo = os.environ.get("KNOWN_DEVICES_GITHUB_REPO", DEFAULT_GITHUB_REPO)
    branch = os.environ.get("KNOWN_DEVICES_GITHUB_BRANCH", DEFAULT_GITHUB_BRANCH)
    return owner, repo, branch


def _build_remote_url(chipset: str, platform: str) -> str:
    """
    Build the GitHub raw URL for a known-device JSON file.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        
    Returns:
        Full GitHub raw URL to the known-device JSON file
    """
    owner, repo, branch = _get_github_config()
    return (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/"
        f"data/known_devices/{platform}/{chipset}.json"
    )


def remote_is_known_device(chipset: str, platform: str) -> bool:
    """
    Check if a known-device file exists in the remote GitHub repository.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        
    Returns:
        True if the remote file exists (HTTP 200), False otherwise
    """
    url = _build_remote_url(chipset, platform)
    
    try:
        # Use HEAD request to check existence without downloading content
        request = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return False


def fetch_remote_known_device(chipset: str, platform: str) -> Optional[dict]:
    """
    Fetch known-device data from the remote GitHub repository.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        
    Returns:
        Dictionary with known-device data, or None if not found or invalid
    """
    url = _build_remote_url(chipset, platform)
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status != 200:
                return None
            
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to fetch remote known device {chipset}/{platform}: {e}")
        return None


def cache_remote_known_device(chipset: str, platform: str, data: dict) -> bool:
    """
    Cache remote known-device data to the local repository.
    
    This is a convenience wrapper around known_devices.save_known_device()
    that adds metadata about the remote source.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        data: The known-device data to cache
        
    Returns:
        True if cached successfully, False otherwise
    """
    # Add metadata about remote source
    if "metadata" not in data:
        data["metadata"] = {}
    
    data["metadata"]["cached_from_remote"] = True
    data["metadata"]["remote_url"] = _build_remote_url(chipset, platform)
    
    return known_devices.save_known_device(chipset, platform, data)


def fetch_remote_manifest(platform: Optional[str] = None) -> Optional[dict]:
    """
    Fetch the remote manifest of available known-devices.
    
    The manifest file lists all available known-device files in the remote
    repository, allowing discovery without GitHub API authentication.
    
    Args:
        platform: Optional platform filter ('windows' or 'linux')
        
    Returns:
        Dictionary with manifest data, or None if not found
    """
    owner, repo, branch = _get_github_config()
    manifest_url = (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/"
        f"data/known_devices/manifest.json"
    )
    
    try:
        with urllib.request.urlopen(manifest_url, timeout=10) as response:
            if response.status != 200:
                return None
            
            data = response.read()
            manifest = json.loads(data.decode('utf-8'))
            
            # Filter by platform if specified
            if platform and "devices" in manifest:
                manifest["devices"] = [
                    d for d in manifest["devices"]
                    if d.get("platform") == platform
                ]
            
            return manifest
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError) as e:
        print(f"Warning: Failed to fetch remote manifest: {e}")
        return None


def list_remote_known_devices(platform: str) -> List[str]:
    """
    List all known-device chipsets available remotely for a platform.
    
    This reads from a manifest.json file in the remote repository to
    discover available known-device files without GitHub API access.
    
    Args:
        platform: The platform ('windows' or 'linux')
        
    Returns:
        List of chipset identifiers available remotely
    """
    manifest = fetch_remote_manifest(platform)
    
    if not manifest or "devices" not in manifest:
        return []
    
    chipsets = []
    for device in manifest["devices"]:
        if device.get("platform") == platform and "chipset" in device:
            chipsets.append(device["chipset"])
    
    return chipsets


def build_driver_list_from_github() -> dict:
    """
    Build a complete list of available drivers from GitHub repositories.
    
    This function queries the remote known-devices repository and catalogs
    all available driver information, creating a comprehensive inventory.
    
    Returns:
        Dictionary with driver catalog organized by platform and chipset
    """
    catalog = {
        "source": "github",
        "timestamp": None,
        "platforms": {
            "windows": [],
            "linux": []
        },
        "total_count": 0
    }
    
    # Fetch manifest for both platforms
    for platform in ["windows", "linux"]:
        chipsets = list_remote_known_devices(platform)
        
        for chipset in chipsets:
            # Fetch full device data
            device_data = fetch_remote_known_device(chipset, platform)
            
            if device_data:
                catalog["platforms"][platform].append({
                    "chipset": chipset,
                    "platform": platform,
                    "has_known_good": "known_good" in device_data,
                    "has_canonical": "canonical" in device_data
                })
                catalog["total_count"] += 1
    
    # Add timestamp
    from datetime import datetime
    catalog["timestamp"] = datetime.now().isoformat()
    
    return catalog


def sync_remote_to_local(platform: Optional[str] = None) -> dict:
    """
    Download all remote known-device JSONs and mirror them to local storage.
    
    This function iterates through all available remote known-devices
    (discovered via manifest) and downloads them to the local cache.
    
    Args:
        platform: Optional platform filter ('windows' or 'linux'). 
                 If None, syncs both platforms.
    
    Returns:
        Dictionary with sync results (downloaded count, failed count, etc.)
    """
    results = {
        "downloaded": 0,
        "failed": 0,
        "skipped": 0,
        "platforms": {}
    }
    
    platforms_to_sync = [platform] if platform else ["windows", "linux"]
    
    for plat in platforms_to_sync:
        results["platforms"][plat] = {
            "downloaded": 0,
            "failed": 0,
            "skipped": 0
        }
        
        chipsets = list_remote_known_devices(plat)
        
        for chipset in chipsets:
            # Check if already exists locally
            if known_devices.is_known_device(chipset, plat):
                results["skipped"] += 1
                results["platforms"][plat]["skipped"] += 1
                print(f"  Skipping {chipset}/{plat} (already exists locally)")
                continue
            
            # Fetch and cache
            data = fetch_remote_known_device(chipset, plat)
            if data:
                if cache_remote_known_device(chipset, plat, data):
                    results["downloaded"] += 1
                    results["platforms"][plat]["downloaded"] += 1
                    print(f"  ✓ Downloaded {chipset}/{plat}")
                else:
                    results["failed"] += 1
                    results["platforms"][plat]["failed"] += 1
                    print(f"  ✗ Failed to cache {chipset}/{plat}")
            else:
                results["failed"] += 1
                results["platforms"][plat]["failed"] += 1
                print(f"  ✗ Failed to fetch {chipset}/{plat}")
    
    return results


def get_known_device_with_fallback(chipset: str, platform: str) -> Optional[dict]:
    """
    Get known-device data, checking local first, then remote.
    
    This is the main entry point for known-device lookup with remote fallback.
    Local repository always takes precedence. If not found locally, checks
    remote and caches the result locally.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        
    Returns:
        Dictionary with known-device data, or None if not found anywhere
    """
    # Check local first
    if known_devices.is_known_device(chipset, platform):
        data = known_devices.load_known_device(chipset, platform)
        if data:
            return data
    
    # Check remote if not found locally
    if remote_is_known_device(chipset, platform):
        data = fetch_remote_known_device(chipset, platform)
        if data:
            # Cache locally for future use
            cache_remote_known_device(chipset, platform, data)
            return data
    
    return None

"""Remote GitHub-hosted known-devices support with self-updating capabilities.

This module provides functions to fetch known-device data from a remote
GitHub repository branch, check for remote existence, sync remote data
to the local repository, and automatically update when newer versions
are available.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from . import known_devices


# Default GitHub configuration
# Users can override these by setting environment variables or config file
DEFAULT_GITHUB_OWNER = "whats-a-script"
DEFAULT_GITHUB_REPO = "TP-link-wifi-MT7927-reverse-engineer"
DEFAULT_GITHUB_BRANCH = "main"

# Auto-update configuration
AUTO_UPDATE_ENABLED = True  # Enable auto-updates by default
AUTO_UPDATE_CHECK_INTERVAL_HOURS = 24  # Check for updates every 24 hours
UPDATE_METADATA_FILE = ".known_devices_update_metadata.json"


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
    that adds metadata about the remote source and caching timestamp.
    
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
    data["metadata"]["local_cache_timestamp"] = datetime.now().isoformat()
    
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


def _get_update_metadata_path() -> Path:
    """Get the path to the update metadata file."""
    known_devices_root = known_devices.get_known_devices_root()
    return known_devices_root / UPDATE_METADATA_FILE


def _load_update_metadata() -> dict:
    """Load update metadata from file."""
    metadata_path = _get_update_metadata_path()
    
    if not metadata_path.exists():
        return {
            "last_check": None,
            "last_update": None,
            "devices": {}
        }
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {
            "last_check": None,
            "last_update": None,
            "devices": {}
        }


def _save_update_metadata(metadata: dict) -> bool:
    """Save update metadata to file."""
    metadata_path = _get_update_metadata_path()
    
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        return True
    except (OSError, TypeError):
        return False


def _should_check_for_updates() -> bool:
    """
    Determine if we should check for updates based on last check time.
    
    Returns:
        True if enough time has passed since last check, False otherwise
    """
    if not AUTO_UPDATE_ENABLED:
        return False
    
    metadata = _load_update_metadata()
    last_check_str = metadata.get("last_check")
    
    if not last_check_str:
        return True  # Never checked before
    
    try:
        last_check = datetime.fromisoformat(last_check_str)
        now = datetime.now()
        elapsed = now - last_check
        
        return elapsed > timedelta(hours=AUTO_UPDATE_CHECK_INTERVAL_HOURS)
    except (ValueError, TypeError):
        return True  # Invalid timestamp, check again


def _is_remote_newer(local_data: dict, remote_data: dict) -> bool:
    """
    Compare timestamps to determine if remote data is newer.
    
    Args:
        local_data: Local known-device data
        remote_data: Remote known-device data
        
    Returns:
        True if remote is newer, False otherwise
    """
    local_updated = local_data.get("metadata", {}).get("last_updated")
    remote_updated = remote_data.get("metadata", {}).get("last_updated")
    
    # If either doesn't have timestamp, assume remote is newer to be safe
    if not local_updated:
        return True
    if not remote_updated:
        return False
    
    try:
        local_date = datetime.fromisoformat(local_updated)
        remote_date = datetime.fromisoformat(remote_updated)
        return remote_date > local_date
    except (ValueError, TypeError):
        # Can't parse dates, assume remote is newer
        return True


def check_for_updates(platform: Optional[str] = None, verbose: bool = True) -> dict:
    """
    Check for updates to known-device data from remote repository.
    
    This function compares local known-devices with remote versions and
    identifies which devices have updates available.
    
    Args:
        platform: Optional platform filter ('windows' or 'linux')
        verbose: Print progress messages
        
    Returns:
        Dictionary with update check results
    """
    results = {
        "updates_available": [],
        "up_to_date": [],
        "new_devices": [],
        "errors": []
    }
    
    platforms_to_check = [platform] if platform else ["windows", "linux"]
    
    # Check manifest for available devices
    manifest = fetch_remote_manifest()
    if not manifest:
        results["errors"].append("Failed to fetch remote manifest")
        return results
    
    for plat in platforms_to_check:
        remote_chipsets = list_remote_known_devices(plat)
        
        for chipset in remote_chipsets:
            # Check if we have it locally
            if known_devices.is_known_device(chipset, plat):
                # Compare versions
                local_data = known_devices.load_known_device(chipset, plat)
                remote_data = fetch_remote_known_device(chipset, plat)
                
                if local_data and remote_data:
                    if _is_remote_newer(local_data, remote_data):
                        results["updates_available"].append({
                            "chipset": chipset,
                            "platform": plat,
                            "local_version": local_data.get("metadata", {}).get("last_updated"),
                            "remote_version": remote_data.get("metadata", {}).get("last_updated")
                        })
                        if verbose:
                            print(f"  Update available: {chipset}/{plat}")
                    else:
                        results["up_to_date"].append({
                            "chipset": chipset,
                            "platform": plat
                        })
                else:
                    results["errors"].append(f"Failed to load {chipset}/{plat}")
            else:
                # New device not in local cache
                results["new_devices"].append({
                    "chipset": chipset,
                    "platform": plat
                })
                if verbose:
                    print(f"  New device available: {chipset}/{plat}")
    
    # Update metadata
    metadata = _load_update_metadata()
    metadata["last_check"] = datetime.now().isoformat()
    _save_update_metadata(metadata)
    
    return results


def auto_update(platform: Optional[str] = None, verbose: bool = True) -> dict:
    """
    Automatically update known-device data from remote repository.
    
    This checks for updates and downloads newer versions. Only updates
    devices that were originally cached from remote (not manually created local files).
    
    Args:
        platform: Optional platform filter ('windows' or 'linux')
        verbose: Print progress messages
        
    Returns:
        Dictionary with update results
    """
    results = {
        "updated": 0,
        "added": 0,
        "failed": 0,
        "skipped": 0,
        "devices": []
    }
    
    if not AUTO_UPDATE_ENABLED:
        if verbose:
            print("Auto-update is disabled")
        return results
    
    if verbose:
        print("Checking for updates...")
    
    # Check what needs updating
    update_check = check_for_updates(platform, verbose=False)
    
    # Update existing devices with newer versions
    for item in update_check["updates_available"]:
        chipset = item["chipset"]
        plat = item["platform"]
        
        # Only auto-update if it was cached from remote originally
        local_data = known_devices.load_known_device(chipset, plat)
        if local_data and local_data.get("metadata", {}).get("cached_from_remote"):
            remote_data = fetch_remote_known_device(chipset, plat)
            if remote_data and cache_remote_known_device(chipset, plat, remote_data):
                results["updated"] += 1
                results["devices"].append({
                    "chipset": chipset,
                    "platform": plat,
                    "action": "updated"
                })
                if verbose:
                    print(f"  ✓ Updated {chipset}/{plat}")
            else:
                results["failed"] += 1
                if verbose:
                    print(f"  ✗ Failed to update {chipset}/{plat}")
        else:
            results["skipped"] += 1
            if verbose:
                print(f"  ⊘ Skipped {chipset}/{plat} (manual local file)")
    
    # Add new devices
    for item in update_check["new_devices"]:
        chipset = item["chipset"]
        plat = item["platform"]
        
        remote_data = fetch_remote_known_device(chipset, plat)
        if remote_data and cache_remote_known_device(chipset, plat, remote_data):
            results["added"] += 1
            results["devices"].append({
                "chipset": chipset,
                "platform": plat,
                "action": "added"
            })
            if verbose:
                print(f"  ✓ Added {chipset}/{plat}")
        else:
            results["failed"] += 1
            if verbose:
                print(f"  ✗ Failed to add {chipset}/{plat}")
    
    # Update metadata
    if results["updated"] > 0 or results["added"] > 0:
        metadata = _load_update_metadata()
        metadata["last_update"] = datetime.now().isoformat()
        _save_update_metadata(metadata)
    
    if verbose:
        print(f"\nUpdate summary: {results['updated']} updated, {results['added']} added, "
              f"{results['skipped']} skipped, {results['failed']} failed")
    
    return results


def get_known_device_with_auto_update(chipset: str, platform: str) -> Optional[dict]:
    """
    Get known-device data with automatic update checking.
    
    This is an enhanced version of get_known_device_with_fallback() that
    also checks if local data needs updating and refreshes it automatically.
    
    Args:
        chipset: The chipset identifier (e.g., 'mt7927', 'ax210')
        platform: The platform ('windows' or 'linux')
        
    Returns:
        Dictionary with known-device data, or None if not found anywhere
    """
    # Check if it's time to check for updates
    if _should_check_for_updates():
        # Run auto-update silently
        auto_update(platform=platform, verbose=False)
    
    # Now get the device (should be up-to-date)
    return get_known_device_with_fallback(chipset, platform)

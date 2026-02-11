#!/usr/bin/env python3
"""
Known-Devices Management CLI

This tool provides commands for managing the known-devices intelligence system,
including checking for updates, syncing from remote, and viewing device information.
"""

import sys
import json
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from AstraForge.modules import known_devices, known_devices_remote


def cmd_list(args):
    """List all locally cached known-devices."""
    print("Known Devices (Local Cache)")
    print("=" * 60)
    
    known_devices_root = known_devices.get_known_devices_root()
    
    for platform in ["windows", "linux"]:
        platform_dir = known_devices_root / platform
        if not platform_dir.exists():
            continue
        
        device_files = sorted(platform_dir.glob("*.json"))
        if device_files:
            print(f"\n{platform.upper()}:")
            for device_file in device_files:
                chipset = device_file.stem
                data = known_devices.load_known_device(chipset, platform)
                if data:
                    vendor = data.get("metadata", {}).get("vendor", "Unknown")
                    desc = data.get("metadata", {}).get("description", "")
                    cached = data.get("metadata", {}).get("cached_from_remote", False)
                    source = "remote" if cached else "local"
                    print(f"  • {chipset:<15} {vendor:<20} [{source}]")
                    if desc:
                        print(f"    {desc}")


def cmd_check_updates(args):
    """Check for available updates from remote repository."""
    print("Checking for updates...")
    print("=" * 60)
    
    results = known_devices_remote.check_for_updates(
        platform=args.platform,
        verbose=True
    )
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Updates available: {len(results['updates_available'])}")
    print(f"  Up to date: {len(results['up_to_date'])}")
    print(f"  New devices: {len(results['new_devices'])}")
    print(f"  Errors: {len(results['errors'])}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  ✗ {error}")
    
    return 0


def cmd_update(args):
    """Update known-devices from remote repository."""
    print("Auto-updating known-devices...")
    print("=" * 60)
    
    results = known_devices_remote.auto_update(
        platform=args.platform,
        verbose=True
    )
    
    return 0


def cmd_sync(args):
    """Sync all known-devices from remote repository."""
    print("Syncing all known-devices from remote...")
    print("=" * 60)
    
    results = known_devices_remote.sync_remote_to_local(platform=args.platform)
    
    print("\n" + "=" * 60)
    print("Sync complete:")
    print(f"  Downloaded: {results['downloaded']}")
    print(f"  Skipped (already cached): {results['skipped']}")
    print(f"  Failed: {results['failed']}")
    
    return 0


def cmd_info(args):
    """Show detailed information about a specific known-device."""
    data = known_devices.load_known_device(args.chipset, args.platform)
    
    if not data:
        print(f"Error: Known-device not found: {args.chipset}/{args.platform}")
        return 1
    
    print(f"Known Device: {args.chipset} ({args.platform})")
    print("=" * 60)
    
    metadata = data.get("metadata", {})
    print("\nMetadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    if "known_good" in data:
        print("\nKnown Good Configuration:")
        known_good = data["known_good"]
        if known_good.get("driver_version"):
            print(f"  Driver Version: {known_good['driver_version']}")
        if known_good.get("firmware"):
            print(f"  Firmware Blobs:")
            for blob in known_good["firmware"]:
                print(f"    - {blob}")
        if known_good.get("inf"):
            print(f"  INF File: {known_good['inf']}")
    
    if "canonical" in data:
        canonical = data["canonical"]
        if "register_map" in canonical:
            print(f"\n  Register Map: {len(canonical['register_map'])} registers")
        if "functions" in canonical:
            print(f"  Functions: {len(canonical['functions'])} functions")
    
    return 0


def cmd_build_catalog(args):
    """Build a complete catalog of available drivers from GitHub."""
    print("Building driver catalog from GitHub...")
    print("=" * 60)
    
    catalog = known_devices_remote.build_driver_list_from_github()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(catalog, f, indent=2)
        print(f"\n✓ Catalog saved to: {args.output}")
    else:
        print(json.dumps(catalog, indent=2))
    
    return 0


def cmd_status(args):
    """Show status of the known-devices system."""
    print("Known-Devices System Status")
    print("=" * 60)
    
    # Count local devices
    known_devices_root = known_devices.get_known_devices_root()
    windows_count = len(list((known_devices_root / "windows").glob("*.json")))
    linux_count = len(list((known_devices_root / "linux").glob("*.json")))
    
    print(f"\nLocal Cache:")
    print(f"  Windows devices: {windows_count}")
    print(f"  Linux devices: {linux_count}")
    print(f"  Total: {windows_count + linux_count}")
    
    # Load update metadata
    try:
        metadata_path = known_devices_root / known_devices_remote.UPDATE_METADATA_FILE
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            print(f"\nAuto-Update Status:")
            print(f"  Enabled: {known_devices_remote.AUTO_UPDATE_ENABLED}")
            print(f"  Check Interval: {known_devices_remote.AUTO_UPDATE_CHECK_INTERVAL_HOURS} hours")
            print(f"  Last Check: {metadata.get('last_check', 'Never')}")
            print(f"  Last Update: {metadata.get('last_update', 'Never')}")
        else:
            print(f"\nAuto-Update Status:")
            print(f"  Enabled: {known_devices_remote.AUTO_UPDATE_ENABLED}")
            print(f"  Never checked for updates")
    except (OSError, json.JSONDecodeError):
        pass
    
    # Check remote availability
    print(f"\nRemote Repository:")
    owner, repo, branch = known_devices_remote._get_github_config()
    print(f"  Owner: {owner}")
    print(f"  Repo: {repo}")
    print(f"  Branch: {branch}")
    
    manifest = known_devices_remote.fetch_remote_manifest()
    if manifest:
        print(f"  Status: ✓ Available")
        print(f"  Remote devices: {len(manifest.get('devices', []))}")
    else:
        print(f"  Status: ✗ Not accessible")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Known-Devices Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all cached known-devices
  python known_devices_cli.py list
  
  # Check for updates
  python known_devices_cli.py check-updates
  
  # Update all known-devices
  python known_devices_cli.py update
  
  # Show system status
  python known_devices_cli.py status
  
  # Show info about a specific device
  python known_devices_cli.py info mt7927 windows
  
  # Build driver catalog from GitHub
  python known_devices_cli.py build-catalog --output catalog.json
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.required = True
    
    # list command
    list_parser = subparsers.add_parser("list", help="List all locally cached known-devices")
    list_parser.set_defaults(func=cmd_list)
    
    # check-updates command
    check_parser = subparsers.add_parser("check-updates", help="Check for available updates")
    check_parser.add_argument("--platform", choices=["windows", "linux"],
                             help="Check only specific platform")
    check_parser.set_defaults(func=cmd_check_updates)
    
    # update command
    update_parser = subparsers.add_parser("update", help="Update known-devices from remote")
    update_parser.add_argument("--platform", choices=["windows", "linux"],
                               help="Update only specific platform")
    update_parser.set_defaults(func=cmd_update)
    
    # sync command
    sync_parser = subparsers.add_parser("sync", help="Sync all known-devices from remote")
    sync_parser.add_argument("--platform", choices=["windows", "linux"],
                            help="Sync only specific platform")
    sync_parser.set_defaults(func=cmd_sync)
    
    # info command
    info_parser = subparsers.add_parser("info", help="Show detailed info about a device")
    info_parser.add_argument("chipset", help="Chipset identifier (e.g., mt7927)")
    info_parser.add_argument("platform", choices=["windows", "linux"],
                            help="Platform")
    info_parser.set_defaults(func=cmd_info)
    
    # build-catalog command
    catalog_parser = subparsers.add_parser("build-catalog",
                                          help="Build driver catalog from GitHub")
    catalog_parser.add_argument("--output", help="Output file path (JSON)")
    catalog_parser.set_defaults(func=cmd_build_catalog)
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

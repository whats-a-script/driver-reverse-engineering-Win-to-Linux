# Known-Devices System with GitHub Sync and Self-Updating

## Overview

The known-devices system provides AstraForge with **self-updating intelligence** about well-characterized WiFi chipsets. When normalizing driver data, AstraForge can automatically:

1. Check the local known-devices repository
2. Fall back to remote GitHub-hosted known-devices
3. Cache remote data locally for future use
4. **Automatically check for and download updates** from remote sources
5. Build a complete driver catalog from GitHub repositories

This enables AstraForge to auto-bootstrap itself with baseline knowledge and **stay up-to-date automatically** instead of requiring manual updates.

## Key Features

### 🔄 Self-Updating Intelligence
- Automatically checks for updates every 24 hours (configurable)
- Downloads newer versions of known-device data from remote repository
- Only updates devices that were originally from remote (preserves manual local files)
- Tracks last check and update timestamps
- Graceful fallback if remote is unavailable

### 📦 Smart Caching
- Remote data is cached locally on first access
- Local cache is automatically refreshed when newer versions are available
- Version/timestamp comparison ensures you always have the latest data
- Manual local files always take precedence over remote

### 🎯 Zero Configuration
- Works out of the box with sensible defaults
- Automatically integrates with normalization process
- No user intervention required for updates
- Can be disabled or configured via environment variables

## Architecture

### Local Known-Devices Repository

Location: `data/known_devices/`

```
data/known_devices/
  ├── windows/
  │   ├── mt7927.json
  │   ├── ax210.json
  │   └── ...
  ├── linux/
  │   ├── mt7927.json
  │   └── ...
  └── manifest.json
```

### Remote GitHub Sync

The system can fetch known-device data from a GitHub repository branch. Remote data is cached locally on first access.

**Priority**: Local always overrides remote

## Known-Device JSON Schema

Each known-device file follows this schema:

```json
{
  "chipset": "string (e.g., 'mt7927', 'ax210')",
  "platform": "windows|linux",
  "known_good": {
    "driver_version": "string or null",
    "firmware": ["array of firmware blob filenames"],
    "inf": "string or null (Windows INF file name)"
  },
  "canonical": {
    "register_map": [
      {
        "address": "string (hex)",
        "name": "string",
        "description": "string",
        "access": "ro|wo|rw"
      }
    ],
    "functions": [
      {
        "name": "string",
        "signature": "string",
        "purpose": "string"
      }
    ]
  },
  "metadata": {
    "description": "string",
    "vendor": "string",
    "last_updated": "YYYY-MM-DD",
    "validated": "boolean"
  }
}
```

## Configuration

### Environment Variables

Configure the remote GitHub source and auto-update behavior using environment variables:

```bash
# GitHub repository configuration
export KNOWN_DEVICES_GITHUB_OWNER="whats-a-script"
export KNOWN_DEVICES_GITHUB_REPO="TP-link-wifi-MT7927-reverse-engineer"
export KNOWN_DEVICES_GITHUB_BRANCH="main"

# Auto-update configuration (optional)
export KNOWN_DEVICES_AUTO_UPDATE="true"  # Enable/disable auto-updates
export KNOWN_DEVICES_UPDATE_INTERVAL="24"  # Check interval in hours
```

### Default Configuration

If not configured, the system uses these defaults:

- **Owner**: `whats-a-script`
- **Repo**: `TP-link-wifi-MT7927-reverse-engineer`
- **Branch**: `main`
- **Auto-Update**: Enabled
- **Check Interval**: 24 hours

## Usage

### Automatic Integration with Self-Updating

The known-devices system is automatically integrated into the normalization process **with self-updating enabled**:

```bash
# Normalizing a device automatically checks for known-device data
# AND checks for updates if 24 hours have passed since last check
python tools/normalize.py intel_ax210 windows
```

Output:
```
Normalizing Windows driver for intel_ax210
  Reading from: data/raw/windows/intel_ax210
  Detected chipset: ax210
  Checking for known-device data for chipset: ax210
  ✓ Found known-device data for ax210
```

**First time**: Fetches from remote and caches locally  
**Subsequent runs**: Uses local cache  
**After 24 hours**: Automatically checks for and downloads updates

### Command-Line Management Tool

Use the `known_devices_cli.py` tool for manual operations:

#### Show System Status
```bash
python tools/known_devices_cli.py status
```

Output shows:
- Number of cached devices per platform
- Auto-update configuration and status
- Last check/update timestamps
- Remote repository availability

#### List All Known Devices
```bash
python tools/known_devices_cli.py list
```

Shows all cached devices with vendor and source (local/remote).

#### Check for Updates
```bash
python tools/known_devices_cli.py check-updates

# Check specific platform only
python tools/known_devices_cli.py check-updates --platform windows
```

Reports which devices have updates available, which are up-to-date, and any new devices.

#### Update Known-Devices
```bash
python tools/known_devices_cli.py update

# Update specific platform only
python tools/known_devices_cli.py update --platform linux
```

Downloads and installs all available updates.

#### Sync All from Remote
```bash
python tools/known_devices_cli.py sync

# Sync specific platform only
python tools/known_devices_cli.py sync --platform windows
```

Downloads all remote known-devices, even those not cached yet.

#### Show Device Info
```bash
python tools/known_devices_cli.py info mt7927 windows
```

Shows detailed information about a specific known-device.

#### Build Driver Catalog
```bash
# Print to stdout
python tools/known_devices_cli.py build-catalog

# Save to file
python tools/known_devices_cli.py build-catalog --output catalog.json
```

Builds a complete catalog of all available drivers from GitHub.

## Self-Updating Behavior

### How Auto-Update Works

1. **Periodic Check**: Every 24 hours (configurable), the system checks for updates
2. **Version Comparison**: Compares `last_updated` timestamps between local and remote
3. **Selective Update**: Only updates devices that were cached from remote originally
4. **Preserves Manual Files**: Never overwrites manually created local files
5. **Graceful Degradation**: If remote is unavailable, uses local cache without errors

### Update Metadata

The system maintains update metadata in `.known_devices_update_metadata.json`:

```json
{
  "last_check": "2026-02-11T21:30:00",
  "last_update": "2026-02-11T21:30:00",
  "devices": {}
}
```

This tracks when the last update check occurred and when devices were last updated.

### Controlling Auto-Updates

#### Disable Auto-Updates Globally
```python
# In your code
from AstraForge.modules import known_devices_remote
known_devices_remote.AUTO_UPDATE_ENABLED = False
```

Or via environment variable:
```bash
export KNOWN_DEVICES_AUTO_UPDATE="false"
```

#### Adjust Check Interval
```python
# Check every 6 hours instead of 24
from AstraForge.modules import known_devices_remote
known_devices_remote.AUTO_UPDATE_CHECK_INTERVAL_HOURS = 6
```

Or via environment variable:
```bash
export KNOWN_DEVICES_UPDATE_INTERVAL="6"
```

#### Force Immediate Update
```bash
python tools/known_devices_cli.py update
```

This bypasses the check interval and updates immediately.

### Update Priority and Safety

**Priority Chain**:
1. **Manual local files** (created by user) are never auto-updated
2. **Cached remote files** are updated when newer versions are available
3. **New remote files** are automatically downloaded and cached

**Safety Guarantees**:
- Local changes are never overwritten
- Updates only apply to remote-sourced files
- Failed updates don't corrupt existing data
- System continues working if remote is unavailable
- No data loss on update failures

#### Check if a Device is Known

```python
from AstraForge.modules import known_devices

if known_devices.is_known_device("mt7927", "windows"):
    data = known_devices.load_known_device("mt7927", "windows")
    print(f"Found known device: {data['metadata']['description']}")
```

#### Fetch from Remote

```python
from AstraForge.modules import known_devices_remote

# Check if remote has data
if known_devices_remote.remote_is_known_device("mt7927", "windows"):
    data = known_devices_remote.fetch_remote_known_device("mt7927", "windows")
    # Cache locally
    known_devices_remote.cache_remote_known_device("mt7927", "windows", data)
```

#### Build Complete Driver List

```python
from AstraForge.modules import known_devices_remote

# Build catalog of all available drivers from GitHub
catalog = known_devices_remote.build_driver_list_from_github()

print(f"Total drivers: {catalog['total_count']}")
print(f"Windows drivers: {len(catalog['platforms']['windows'])}")
print(f"Linux drivers: {len(catalog['platforms']['linux'])}")
```

#### Sync All Remote to Local

```python
from AstraForge.modules import known_devices_remote

# Sync all remote known-devices to local cache
results = known_devices_remote.sync_remote_to_local()

print(f"Downloaded: {results['downloaded']}")
print(f"Failed: {results['failed']}")
print(f"Skipped (already local): {results['skipped']}")
```

## Integration with Normalization

When normalizing driver data, AstraForge:

1. **Detects the chipset** using PCI IDs or other identifiers
2. **Checks for known-device data**:
   - First checks local repository
   - If not found, checks remote GitHub
   - Caches remote data locally if found
3. **Merges known data** into canonical structure:
   - Fills in baseline register maps
   - Adds known function signatures
   - Provides known-good firmware versions
4. **Validates** against known-good baselines:
   - Checks driver version matches expectations
   - Verifies firmware blobs are present
   - Reports warnings for mismatches

### Canonical JSON Enhancement

When a known-device is found, the canonical JSON is enhanced with:

```json
{
  "metadata": {
    "known_device_source": "local|remote",
    "known_device_chipset": "mt7927",
    ...
  },
  "firmware": {
    "known_blobs": ["mt7927_rom_patch.bin", "mt7927_ram_code.bin"]
  },
  "known_device_validation": {
    "known_device_matched": true,
    "warnings": [],
    "info": ["Known firmware blobs not found: ..."]
  }
}
```

## Behavior and Safety

### Deterministic Operation

- Local known-devices **always** override remote
- Remote data is cached locally on first access
- Normalization remains deterministic
- No wild crawling or scanning of GitHub

### Safe Boundaries

- Only accesses the designated GitHub repository
- Uses public GitHub raw content URLs (no authentication required)
- Manifest-based discovery (no directory listing)
- Timeout protection (5-10 seconds)
- Graceful fallback on failure

### Priority Chain

1. **Local first**: If device exists in `data/known_devices/`, use it
2. **Remote fallback**: If not local, check remote GitHub
3. **Cache on fetch**: Remote data is cached locally
4. **Proceed without**: If neither found, continue normalization without known-device data

## Adding New Known-Devices

### Local Addition

1. Create a JSON file in `data/known_devices/<platform>/<chipset>.json`
2. Follow the schema documented above
3. Update `data/known_devices/manifest.json` to include the new device

### Remote Addition

1. Fork or update the GitHub repository
2. Add the known-device JSON to `data/known_devices/<platform>/`
3. Update `data/known_devices/manifest.json`
4. Commit and push to the designated branch
5. The remote will be automatically discovered via manifest

## Manifest File

The `manifest.json` file enables discovery without GitHub API access:

```json
{
  "version": "1.0",
  "description": "Manifest of known-devices available in this repository",
  "last_updated": "YYYY-MM-DD",
  "devices": [
    {
      "chipset": "mt7927",
      "platform": "windows",
      "vendor": "MediaTek",
      "description": "MediaTek MT7927 WiFi 6E chipset"
    }
  ],
  "repository": {
    "owner": "whats-a-script",
    "repo": "TP-link-wifi-MT7927-reverse-engineer",
    "branch": "main"
  }
}
```

## Examples

### Example 1: Normalize with Known-Device

```bash
$ python tools/normalize.py intel_ax210 windows

Normalizing Windows driver for intel_ax210
  Reading from: data/raw/windows/intel_ax210
  Detected chipset: ax210
  Checking for known-device data for chipset: ax210
  ✓ Found known-device data for ax210
  
✓ Canonical JSON written to: data/canonical/intel_ax210_windows.json
```

The resulting canonical includes baseline register maps and functions from the known-device.

### Example 2: Build Driver Catalog

```python
from AstraForge.modules import known_devices_remote
import json

catalog = known_devices_remote.build_driver_list_from_github()
print(json.dumps(catalog, indent=2))
```

Output:
```json
{
  "source": "github",
  "timestamp": "2026-02-11T21:30:00",
  "platforms": {
    "windows": [
      {
        "chipset": "mt7927",
        "platform": "windows",
        "has_known_good": true,
        "has_canonical": true
      },
      {
        "chipset": "ax210",
        "platform": "windows",
        "has_known_good": true,
        "has_canonical": true
      }
    ],
    "linux": []
  },
  "total_count": 2
}
```

## Troubleshooting

### Remote Fetch Failing

If remote fetching fails:

1. Check network connectivity
2. Verify GitHub repository is public
3. Check environment variables are set correctly
4. Test the URL manually:
   ```
   https://raw.githubusercontent.com/<OWNER>/<REPO>/<BRANCH>/data/known_devices/manifest.json
   ```

### Data Not Being Used

If known-device data isn't being used:

1. Check chipset detection is working correctly
2. Verify the chipset name matches the JSON filename
3. Check platform matches ('windows' vs 'linux')
4. Enable verbose output to see lookup messages

### Cache Issues

To clear the local cache:

```bash
rm -rf data/known_devices/windows/*.json
rm -rf data/known_devices/linux/*.json
```

The manifest file is not cached and should not be deleted.

## Future Enhancements

Potential future enhancements:

1. **GitHub API integration** for authenticated access
2. **Version tracking** to update stale cached data
3. **Contributor system** for crowd-sourced known-devices
4. **Validation scores** for data quality metrics
5. **Diff detection** to identify deviations from known-good

## Security Considerations

- No authentication required (uses public GitHub raw URLs)
- No write access to remote repository
- Local cache is read/write by user only
- No code execution from remote data (JSON only)
- Timeout protection prevents hanging
- Graceful degradation on failure

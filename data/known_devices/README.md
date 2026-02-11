# Known-Devices System with GitHub Sync

## Overview

The known-devices system provides AstraForge with intelligence about well-characterized WiFi chipsets. When normalizing driver data, AstraForge can automatically:

1. Check the local known-devices repository
2. Fall back to remote GitHub-hosted known-devices
3. Cache remote data locally for future use
4. Build a complete driver catalog from GitHub repositories

This enables AstraForge to auto-bootstrap itself with baseline knowledge instead of starting from zero for each device.

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

Configure the remote GitHub source using environment variables:

```bash
# GitHub repository configuration
export KNOWN_DEVICES_GITHUB_OWNER="whats-a-script"
export KNOWN_DEVICES_GITHUB_REPO="TP-link-wifi-MT7927-reverse-engineer"
export KNOWN_DEVICES_GITHUB_BRANCH="main"
```

### Default Configuration

If not configured, the system uses these defaults:

- **Owner**: `whats-a-script`
- **Repo**: `TP-link-wifi-MT7927-reverse-engineer`
- **Branch**: `main`

## Usage

### Automatic Integration

The known-devices system is automatically integrated into the normalization process:

```bash
# Normalizing a device automatically checks for known-device data
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

### Manual Operations

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

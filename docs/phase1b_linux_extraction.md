# Phase 1B Linux Driver File Extraction - Implementation Documentation

## Overview

This document describes the implementation of Phase 1B Linux Driver File Extraction for AstraForge, which extracts driver metadata from Linux raw data artifacts and populates canonical JSON fields.

## Implementation Date
February 11, 2026

## Scope

Phase 1B implements:
- ✅ Linux driver file reference extraction
- ✅ Canonical driver.files population
- ✅ Best-effort driver version extraction
- ✅ Firmware references capture for Phase 2
- ✅ Symmetrical structure to Windows Phase 1

Phase 1B does NOT:
- ❌ Modify diff_engine or CLI tools
- ❌ Parse C source code (.c, .h files)
- ❌ Extract register maps or function signatures
- ❌ Analyze firmware binaries

## Architecture

### Module: `tools/normalize_linux.py`

This module mirrors the structure of `tools/normalize_windows.py` and provides Linux-specific extraction logic.

#### Key Functions

1. **`load_text_file(file_path: Path) -> Optional[str]`**
   - Loads text files with UTF-8 encoding
   - Handles missing files gracefully
   - Returns None if file doesn't exist or is invalid

2. **`parse_modinfo(modinfo_content: Optional[str]) -> Dict[str, List[str]]`**
   - Parses modinfo.txt format (key: value pairs)
   - Handles multi-value fields (e.g., multiple firmware entries)
   - Returns dictionary mapping field names to value lists

3. **`extract_driver_files(modinfo_data: Dict) -> List[Dict]`**
   - Extracts kernel module (.ko) from 'filename' field
   - Extracts firmware files from 'firmware' fields
   - Returns list of file dictionaries for canonical['driver']['files']

4. **`extract_driver_version(modinfo_data: Dict, uname_content: Optional[str]) -> Optional[str]`**
   - Best-effort version extraction with fallback chain:
     1. modinfo 'version' field (skips generic "in-tree:")
     2. modinfo 'vermagic' field (kernel version)
     3. uname.txt content (kernel version)
   - Returns version string or None

5. **`extract_driver_metadata(modinfo_data: Dict) -> Dict`**
   - Extracts: provider (author), description, license
   - Returns metadata dictionary

6. **`extract_firmware_references(modinfo_data: Dict) -> List[str]`**
   - Extracts firmware filenames for Phase 2 analysis
   - Returns list of firmware file references

7. **`populate_linux_driver_data(canonical: Dict, raw_data_path: Path) -> Dict`**
   - Main orchestrator function
   - Loads modinfo.txt and uname.txt
   - Populates canonical JSON driver section
   - Returns updated canonical dictionary

### Integration Points

#### `tools/normalize.py`
- Updated `normalize_linux()` function to call Phase 1B extraction
- Added import for `normalize_linux` module
- Passes `raw_data_path` to extraction logic

#### `tools/AstraForge/modules/validator.py`
- Added `modinfo.txt` to `LINUX_OPTIONAL` file list
- Validator now recognizes modinfo.txt as valid optional artifact

## Input Artifacts

### Required Files (Linux)
- `lspci.txt` - PCI device information for chipset detection

### Optional Files (Linux) - Phase 1B
- **`modinfo.txt`** - Module information output
  - Format: Key-value pairs (field: value)
  - Multi-value fields supported (e.g., multiple firmware entries)
  - Contains: filename, version, author, description, license, firmware, vermagic, etc.

- **`uname.txt`** - Kernel version (fallback for version extraction)
  - Format: Single line with kernel version string
  - Used when modinfo version is generic or missing

## Output Schema

### Canonical JSON - `driver` Section

```json
{
  "driver": {
    "files": [
      {
        "name": "iwlwifi.ko",
        "type": "ko"
      },
      {
        "name": "iwlwifi-ty-a0-gf-a0-72.ucode",
        "type": "firmware"
      }
    ],
    "version": "kernel-6.1.0-17-amd64",
    "provider": "Intel Corporation <linuxwifi@intel.com>",
    "description": "Intel(R) Wireless WiFi driver for Linux",
    "license": "GPL",
    "firmware_references": [
      "iwlwifi-ty-a0-gf-a0-72.ucode",
      "iwlwifi-ty-a0-gf-a0-71.ucode"
    ]
  }
}
```

## Symmetry with Windows Phase 1

### Structural Similarities

| Aspect | Windows Phase 1 | Linux Phase 1B |
|--------|----------------|----------------|
| Module | `normalize_windows.py` | `normalize_linux.py` |
| File loader | `load_json_file()` | `load_text_file()` |
| File extraction | `extract_driver_files()` | `extract_driver_files()` |
| Metadata extraction | `extract_driver_metadata()` | `extract_driver_metadata()` |
| Main orchestrator | `populate_windows_driver_data()` | `populate_linux_driver_data()` |

## Testing

### Test Scenarios

1. **Complete modinfo.txt with all fields**
   - Device: intel_ax210
   - Result: ✅ All fields populated, 10 files extracted

2. **Minimal modinfo.txt with version fallback**
   - Device: test_minimal
   - Result: ✅ Version from uname.txt, single .ko file

3. **Missing modinfo.txt**
   - Device: test_no_modinfo
   - Result: ✅ Graceful handling, empty driver.files

4. **Edge cases**
   - Empty modinfo: ✅ Returns empty dict
   - Invalid format: ✅ Skips invalid lines
   - Multiple firmware: ✅ All extracted
   - In-tree version: ✅ Falls back to vermagic/uname

### Validation

```bash
# Validate raw data
python3 tools/AstraForge/AstraForge.py validate --platform linux --device intel_ax210

# Run normalization
python3 tools/normalize.py intel_ax210 linux

# Verify output
cat data/canonical/intel_ax210_linux.json
```

## Limitations

1. **Version detection**: Best-effort, may return kernel version instead of driver version
2. **File metadata**: Size, hash not available from modinfo.txt
3. **Date information**: Not available in modinfo output
4. **Device manufacturer**: Not extracted in Phase 1B
5. **Source parsing**: Deferred to future phases

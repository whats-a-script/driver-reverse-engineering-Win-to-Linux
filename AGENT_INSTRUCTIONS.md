# MT7927 Cross-Platform Driver Analysis Pipeline

## Overview

This repository contains the workflow and tooling for analyzing the TP-Link MT7927 WiFi driver across multiple platforms (Windows and Linux). The goal is to systematically collect, normalize, and compare driver implementations to identify commonalities, differences, and potential reverse-engineering insights.

## Workflow

The driver analysis follows a device-by-device iterative workflow:

### Phase 1: Data Collection
1. **Windows Driver Collection** (`scripts/collect_windows.ps1`)
   - Download driver package from vendor or Windows Update
   - Extract driver files (.sys, .inf, .cat)
   - Capture metadata (version, date, vendor info)
   - Store in `data/raw/windows/<device_id>/`

2. **Linux Driver Collection** (`scripts/collect_linux.sh`)
   - Identify kernel module sources
   - Download from kernel.org or vendor repository
   - Extract driver sources (.c, .h files)
   - Capture metadata (kernel version, maintainer)
   - Store in `data/raw/linux/<device_id>/`

### Phase 2: Normalization
3. **Data Normalization** (`tools/normalize.py`)
   - Parse driver metadata
   - Extract function signatures, structures, constants
   - Convert to canonical JSON format
   - Store in `data/canonical/<device_id>_<platform>.json`

### Phase 3: Analysis
4. **Cross-Platform Diff** (`tools/diff_engine.py`)
   - Compare Windows vs Linux implementations
   - Identify common patterns (register addresses, commands)
   - Detect platform-specific behaviors
   - Generate diff reports in `reports/<device_id>_diff.json`

### Phase 4: Validation
5. **Automated Validation** (`ci/validate.yml`)
   - Verify JSON schema compliance
   - Check for required fields
   - Validate cross-references
   - Ensure data quality

## Data Schemas

### Canonical JSON Format (`data/canonical/`)

Each normalized driver analysis must conform to this schema:

```json
{
  "device_id": "string (e.g., 'intel_ax210')",
  "device_name": "string (e.g., 'Intel Wi-Fi 6E AX210')",
  "platform": "windows|linux",
  "metadata": {
    "driver_version": "string",
    "driver_date": "YYYY-MM-DD",
    "vendor": "string",
    "chipset": "string (e.g., 'MT7927')",
    "source_url": "string|null (DO NOT invent; leave null if unknown)",
    "collection_date": "YYYY-MM-DD",
    "notes": "string (mark as SYNTHETIC if placeholder data)"
  },
  "windows_nav_card": {
    "driver_download_url": "string|null (DO NOT invent)",
    "support_page_url": "string|null (DO NOT invent)",
    "inf_file_path": "string|null"
  },
  "driver_components": {
    "modules": [
      {
        "name": "string",
        "type": "sys|ko|so",
        "size_bytes": "number|null",
        "hash_sha256": "string|null"
      }
    ],
    "config_files": ["string"]
  },
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
}
```

### Diff Report Format (`reports/`)

```json
{
  "device_id": "string",
  "comparison": "windows_vs_linux",
  "generated_date": "YYYY-MM-DD",
  "commonalities": {
    "register_overlap": ["list of common registers"],
    "shared_commands": ["list of common commands"]
  },
  "differences": {
    "windows_only": ["list of Windows-specific features"],
    "linux_only": ["list of Linux-specific features"]
  },
  "insights": [
    {
      "category": "string",
      "finding": "string",
      "confidence": "high|medium|low"
    }
  ]
}
```

## Device Inventory

The `drivers/wifi_inventory.csv` file tracks all devices in the analysis pipeline:

### CSV Headers
```
device_id,device_name,chipset,vendor,windows_collected,linux_collected,normalized,diffed,notes
```

### Example Row
```
intel_ax210,Intel Wi-Fi 6E AX210,MT7927,Intel,yes,yes,yes,yes,First iteration device
```

## Helper Scripts

### `scripts/collect_windows.ps1`
Windows PowerShell script to automate driver collection:
- Download from vendor URL or Windows Update catalog
- Extract CAB/ZIP archives
- Parse INF files for metadata
- Organize files in `data/raw/windows/<device_id>/`

### `scripts/collect_linux.sh`
Bash script to automate Linux driver collection:
- Clone kernel sources or vendor repositories
- Extract relevant driver files
- Parse Kconfig/Makefile for metadata
- Organize files in `data/raw/linux/<device_id>/`

### `tools/normalize.py`
Python script to convert raw drivers to canonical JSON:
- Parse binary drivers (Windows .sys) using PE analysis
- Parse source drivers (Linux .c/.h) using AST parsing
- Extract register maps, function signatures
- Output standardized JSON

### `tools/diff_engine.py`
Python script to compare canonical JSONs:
- Load Windows and Linux JSONs for same device
- Identify overlapping registers, functions
- Detect platform-specific implementations
- Generate structured diff report

## Validation Rules (`ci/validate.yml`)

The CI pipeline enforces these validations:

1. **Schema Compliance**
   - All canonical JSONs match the defined schema
   - Required fields are present
   - Data types are correct

2. **Integrity Checks**
   - device_id consistency across files
   - No duplicate entries in wifi_inventory.csv
   - All referenced files exist

3. **Quality Standards**
   - No invented URLs (must be null if unknown)
   - Synthetic data is clearly marked in `notes` field
   - Secondary check document (`reports/secondary_check.md`) exists and lists all synthetic data

4. **Cross-Reference Validation**
   - Devices in CSV exist in canonical data
   - Diff reports reference valid canonical JSONs

## Synthetic Data Policy

When real driver data is unavailable:

1. **Mark as Synthetic**: Add `"SYNTHETIC"` to the `notes` field in metadata
2. **Document in Secondary Check**: Add entry to `reports/secondary_check.md`
3. **Leave URLs Null**: Do not invent vendor URLs; use `null`
4. **Use Placeholders**: Use realistic but clearly placeholder values (e.g., version "0.0.0.SYNTHETIC")

## Device Iteration Process

For each new device:

1. Add entry to `drivers/wifi_inventory.csv`
2. Collect Windows driver (if available) using `scripts/collect_windows.ps1`
3. Collect Linux driver (if available) using `scripts/collect_linux.sh`
4. Normalize both using `tools/normalize.py`
5. Generate diff using `tools/diff_engine.py`
6. Update inventory CSV status columns
7. Commit all artifacts with clear commit message

## First Device: Intel AX210

Start the pipeline with Intel AX210:
- Create placeholder canonical JSONs for both Windows and Linux
- If real data unavailable, mark as SYNTHETIC
- Document in `reports/secondary_check.md`
- Create example diff report
- Update inventory CSV

## Repository Readiness

Before considering the repository ready for execution:

- [ ] All directory structures exist
- [ ] AGENT_INSTRUCTIONS.md is complete
- [ ] TEST_PLAN.md is aligned with workflow
- [ ] wifi_inventory.csv has correct headers
- [ ] All helper scripts exist with documented scaffolding
- [ ] ci/validate.yml performs listed validations
- [ ] Example canonical JSONs and diffs exist
- [ ] Intel AX210 entry is added with appropriate synthetic markers
- [ ] reports/secondary_check.md documents all synthetic data

## Notes

- This is a research repository; data quality is paramount
- Prioritize accuracy over completeness
- Document all assumptions and limitations
- Follow schema strictly to enable automated processing
- Synthetic data is acceptable for scaffolding but must be clearly marked

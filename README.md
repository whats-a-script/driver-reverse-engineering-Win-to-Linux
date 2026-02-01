# TP-link-wifi-MT7927-reverse-engineer

Cross-platform driver analysis pipeline for the MediaTek MT7927 WiFi chipset used in TP-Link and other devices.

## Overview

This repository contains tools and workflows for systematically analyzing WiFi drivers across Windows and Linux platforms to identify commonalities, differences, and reverse-engineering insights for the MT7927 chipset.

## Quick Start

1. **Read the documentation**:
   - [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md) - Complete workflow and schema documentation
   - [TEST_PLAN.md](TEST_PLAN.md) - Validation and testing procedures

2. **Review the structure**:
   ```
   ├── drivers/           # Device inventory and metadata
   ├── scripts/           # Data collection automation
   ├── tools/             # Normalization and analysis tools
   ├── data/
   │   ├── raw/          # Raw driver files (Windows/Linux)
   │   └── canonical/    # Normalized JSON data
   ├── reports/          # Analysis results and diffs
   └── ci/               # Automated validation
   ```

3. **Check the inventory**:
   - See [drivers/wifi_inventory.csv](drivers/wifi_inventory.csv) for tracked devices
   - Current status: Intel AX210 (synthetic placeholder data)

## Workflow

The analysis follows a device-by-device iterative process:

1. **Collect** - Gather Windows and Linux drivers
2. **Normalize** - Convert to canonical JSON format
3. **Analyze** - Generate cross-platform diff reports
4. **Validate** - Automated quality checks via CI

See [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md) for detailed workflow documentation.

## Data Quality

- All synthetic/placeholder data is clearly marked with `SYNTHETIC` in notes
- See [reports/secondary_check.md](reports/secondary_check.md) for synthetic data documentation
- No invented URLs - unknowns are set to `null`
- Strict schema validation via CI pipeline

## Current Status

**Repository Status**: ✅ Ready for device-by-device execution

**Devices**:
- Intel AX210: SYNTHETIC placeholder data (scaffolding)

**Next Steps**:
1. Collect real Intel AX210 driver data
2. Re-normalize with actual metadata
3. Add additional MT7927-based devices
4. Expand analysis patterns

## Contributing

When adding new devices:

1. Update `drivers/wifi_inventory.csv`
2. Collect raw data using scripts
3. Normalize to canonical JSON
4. Generate diff reports
5. Document any synthetic data in `reports/secondary_check.md`
6. Ensure CI validation passes

## Tools

- `scripts/collect_windows.ps1` - Windows driver collection
- `scripts/collect_linux.sh` - Linux driver collection  
- `tools/normalize.py` - Convert to canonical JSON
- `tools/diff_engine.py` - Cross-platform comparison

## License

Research and educational purposes.

# Secondary Check: Synthetic Data Documentation

## Overview

This document tracks all synthetic/placeholder data in the repository that was created for scaffolding purposes. Real data collection is required for each item listed here.

## Synthetic Data Items

### Intel AX210 (intel_ax210)

**Status**: SYNTHETIC - Placeholder data  
**Created**: 2026-02-01  
**Reason**: Initial repository scaffolding; real driver data not yet collected

**Affected Files**:
- `data/canonical/intel_ax210_windows.json`
- `data/canonical/intel_ax210_linux.json`
- `reports/intel_ax210_diff.json`

**Synthetic Elements**:
- Driver version: "0.0.0.SYNTHETIC"
- Vendor: "Unknown" (should be "Intel")
- Device name: Placeholder format
- source_url: `null` (real URLs not available)
- windows_nav_card URLs: All `null` (real URLs not available)
- Register map: Single placeholder register (0x0000)
- Functions: Single placeholder function
- Driver components: Empty arrays

**Required for Real Data**:
1. Download actual Intel AX210 Windows driver from:
   - Intel Download Center: https://www.intel.com/content/www/us/en/download-center/home.html
   - Or Windows Update Catalog
2. Extract Linux iwlwifi driver sources from kernel.org
3. Run `scripts/collect_windows.ps1` and `scripts/collect_linux.sh`
4. Re-run normalization tools to extract real metadata
5. Update `drivers/wifi_inventory.csv` to remove synthetic markers
6. Remove this entry from secondary_check.md

**URL Policy Compliance**:
✓ No URLs were invented - all unknown URLs set to `null`  
✓ Synthetic data clearly marked in `metadata.notes` field  
✓ Device documented in this secondary check file

---

## Future Devices

As new devices are added to the pipeline, document any synthetic data here following the same format:

### [Device Name] ([device_id])

**Status**: SYNTHETIC/PARTIAL/REAL  
**Created**: [YYYY-MM-DD]  
**Reason**: [Why synthetic data was used]

**Affected Files**:
- [List of files with synthetic data]

**Synthetic Elements**:
- [List specific synthetic fields/values]

**Required for Real Data**:
- [Steps to collect real data]

---

## Data Quality Policy

**Acceptable Synthetic Data**:
- Placeholder data for initial repository setup
- Scaffolding examples demonstrating schema compliance
- Test fixtures for validation scripts

**Unacceptable Synthetic Data**:
- Invented vendor URLs or download links
- Fake register addresses without clear SYNTHETIC marking
- Production analysis based on placeholder values

**Removal Criteria**:
Synthetic data entries should be removed from this document when:
1. Real driver data has been collected
2. Canonical JSONs updated with actual metadata
3. Diff reports regenerated from real data
4. Validation confirms no synthetic markers remain

---

## Validation Status

**Last Validated**: 2026-02-01

**Current Synthetic Count**: 1 device (intel_ax210)

**CI/CD Integration**: 
- CI pipeline checks for SYNTHETIC markers in canonical JSON `notes` fields
- Cross-references with this document to ensure all synthetic data is documented
- Warnings issued if synthetic data found without documentation

---

## Notes

- This document is part of the data quality assurance process
- All contributors must update this file when adding synthetic data
- Synthetic data should be temporary; real data collection is the goal
- When in doubt, mark data as SYNTHETIC rather than risk incorrect analysis

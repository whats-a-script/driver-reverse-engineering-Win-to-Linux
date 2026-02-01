# Test Plan: MT7927 Driver Analysis Pipeline

## Overview

This document outlines the validation and testing strategy for the MT7927 cross-platform driver analysis pipeline. Tests are organized by phase and align with the workflow defined in AGENT_INSTRUCTIONS.md.

## Test Categories

### 1. Directory Structure Tests

**Test ID**: `TS-001`  
**Description**: Verify all required directories exist  
**Steps**:
1. Check for existence of `drivers/`, `scripts/`, `tools/`, `data/raw/windows/`, `data/raw/linux/`, `data/canonical/`, `reports/`, `ci/`
2. Verify directory permissions are correct

**Expected Result**: All directories exist and are accessible

---

### 2. Schema Validation Tests

**Test ID**: `SV-001`  
**Description**: Validate canonical JSON schema compliance  
**Steps**:
1. Load all JSON files from `data/canonical/`
2. Parse and validate against canonical schema defined in AGENT_INSTRUCTIONS.md
3. Check all required fields: `device_id`, `device_name`, `platform`, `metadata`, `driver_components`
4. Validate data types (strings, numbers, arrays, objects)

**Expected Result**: All canonical JSONs pass schema validation

---

**Test ID**: `SV-002`  
**Description**: Validate diff report schema compliance  
**Steps**:
1. Load all JSON files from `reports/`
2. Parse and validate against diff report schema
3. Check required fields: `device_id`, `comparison`, `generated_date`, `commonalities`, `differences`

**Expected Result**: All diff reports pass schema validation

---

### 3. Data Integrity Tests

**Test ID**: `DI-001`  
**Description**: Verify device_id consistency  
**Steps**:
1. Load `drivers/wifi_inventory.csv`
2. Extract all device_ids from CSV
3. For each device_id, verify corresponding canonical JSON files exist
4. Check device_id field in JSON matches filename

**Expected Result**: No orphaned or mismatched device_ids

---

**Test ID**: `DI-002`  
**Description**: Validate CSV format and headers  
**Steps**:
1. Load `drivers/wifi_inventory.csv`
2. Verify header row matches: `device_id,device_name,chipset,vendor,windows_collected,linux_collected,normalized,diffed,notes`
3. Validate no duplicate device_ids
4. Check boolean columns contain only: `yes`, `no`, or empty

**Expected Result**: CSV is well-formed with correct headers

---

**Test ID**: `DI-003`  
**Description**: Verify file existence references  
**Steps**:
1. For each device in inventory with `windows_collected=yes`, verify `data/raw/windows/<device_id>/` exists
2. For each device with `linux_collected=yes`, verify `data/raw/linux/<device_id>/` exists
3. For each device with `normalized=yes`, verify canonical JSONs exist
4. For each device with `diffed=yes`, verify diff report exists

**Expected Result**: All referenced files and directories exist

---

### 4. Synthetic Data Tests

**Test ID**: `SD-001`  
**Description**: Verify synthetic data is properly marked  
**Steps**:
1. Load all canonical JSONs
2. Check `metadata.notes` field for "SYNTHETIC" marker
3. Verify `reports/secondary_check.md` exists
4. Confirm all synthetic devices are documented in secondary_check.md

**Expected Result**: All synthetic data is clearly marked and documented

---

**Test ID**: `SD-002`  
**Description**: Validate no invented URLs  
**Steps**:
1. Load all canonical JSONs
2. Check `metadata.source_url` and `windows_nav_card` fields
3. Verify no obviously fake URLs (e.g., "example.com", "placeholder.url")
4. Confirm null values are used when URL is unknown

**Expected Result**: No invented URLs; nulls used appropriately

---

### 5. Script Existence Tests

**Test ID**: `SE-001`  
**Description**: Verify all helper scripts exist  
**Steps**:
1. Check for `scripts/collect_windows.ps1`
2. Check for `scripts/collect_linux.sh`
3. Check for `tools/normalize.py`
4. Check for `tools/diff_engine.py`
5. Verify scripts are executable (Linux) or have proper extensions (Windows)

**Expected Result**: All scripts exist and are properly configured

---

**Test ID**: `SE-002`  
**Description**: Validate script documentation  
**Steps**:
1. Open each script file
2. Verify header comments explaining purpose
3. Check for usage examples or help text
4. Confirm minimal scaffolding is present

**Expected Result**: Scripts are documented with purpose and usage

---

### 6. CI/CD Validation Tests

**Test ID**: `CI-001`  
**Description**: Verify CI validation configuration exists  
**Steps**:
1. Check for `ci/validate.yml`
2. Parse YAML syntax
3. Verify validation steps align with rules in AGENT_INSTRUCTIONS.md
4. Confirm schema validation is included
5. Check integrity checks are present

**Expected Result**: CI configuration is complete and valid

---

### 7. First Device Tests (Intel AX210)

**Test ID**: `FD-001`  
**Description**: Verify Intel AX210 entry exists  
**Steps**:
1. Check `drivers/wifi_inventory.csv` for `intel_ax210` entry
2. Verify device_name is "Intel Wi-Fi 6E AX210" or similar
3. Check status columns reflect collection state
4. Verify notes indicate synthetic data if applicable

**Expected Result**: Intel AX210 is properly entered in inventory

---

**Test ID**: `FD-002`  
**Description**: Validate Intel AX210 canonical JSONs  
**Steps**:
1. Check for `data/canonical/intel_ax210_windows.json`
2. Check for `data/canonical/intel_ax210_linux.json`
3. Validate both pass schema tests (SV-001)
4. Verify metadata indicates synthetic data if applicable

**Expected Result**: Intel AX210 canonical data exists and is valid

---

**Test ID**: `FD-003`  
**Description**: Verify Intel AX210 diff report  
**Steps**:
1. Check for `reports/intel_ax210_diff.json`
2. Validate against diff schema (SV-002)
3. Verify commonalities and differences sections are populated
4. Check that it references the canonical JSONs

**Expected Result**: Diff report exists and is properly structured

---

## Manual Validation Steps

### MV-001: Visual Inspection of Repository Structure
1. Open repository in file explorer
2. Verify directory layout matches specification
3. Check that placeholder files are appropriately minimal
4. Confirm no unnecessary files (build artifacts, etc.)

### MV-002: Review AGENT_INSTRUCTIONS.md
1. Read through complete document
2. Verify workflow is clear and complete
3. Check schemas are well-defined
4. Ensure policy sections are comprehensive

### MV-003: Review Synthetic Data Documentation
1. Open `reports/secondary_check.md`
2. Verify all synthetic data is listed
3. Check that justifications are provided
4. Confirm plan for future real data collection

## Automated Test Execution

The CI pipeline (`ci/validate.yml`) will automatically run:
1. Schema validation tests (SV-001, SV-002)
2. Data integrity tests (DI-001, DI-002, DI-003)
3. Synthetic data tests (SD-001, SD-002)
4. Script existence tests (SE-001)

Manual tests (MV-*) should be performed during code review.

## Test Success Criteria

The repository is ready for device-by-device execution when:
- [ ] All automated tests pass in CI
- [ ] All manual validation steps are complete
- [ ] Intel AX210 example data is present and valid
- [ ] No test failures or warnings
- [ ] Documentation is complete and accurate

## Future Test Additions

As the pipeline evolves, add tests for:
- Script functionality (unit tests for normalize.py, diff_engine.py)
- Performance benchmarks (processing time per device)
- Data quality metrics (register map completeness)
- Cross-device comparison tests

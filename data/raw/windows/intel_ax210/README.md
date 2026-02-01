# Intel AX210 - Windows Driver Data

This directory should contain raw Windows driver files for the Intel AX210 device.

## Expected Contents

- Driver `.sys` files
- Driver `.inf` configuration files
- `.cat` catalog files
- `metadata.json` with collection information

## Data Status

**SYNTHETIC**: This directory is currently a placeholder. Real driver data has not been collected.

## Collection Instructions

1. Download Intel AX210 Windows driver from:
   - Intel Download Center
   - Or Windows Update Catalog
2. Run: `../../scripts/collect_windows.ps1 -DeviceId intel_ax210 -DriverUrl <url>`
3. Verify files are extracted to this directory
4. Update `drivers/wifi_inventory.csv` to reflect collection status

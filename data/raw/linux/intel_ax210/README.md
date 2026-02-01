# Intel AX210 - Linux Driver Data

This directory should contain raw Linux driver files for the Intel AX210 device.

## Expected Contents

- Driver `.c` source files
- Driver `.h` header files
- `Makefile` and `Kconfig` files
- `metadata.json` with collection information

## Data Status

**SYNTHETIC**: This directory is currently a placeholder. Real driver data has not been collected.

## Collection Instructions

1. Identify Intel AX210 driver in Linux kernel sources (likely iwlwifi)
2. Run: `../../scripts/collect_linux.sh intel_ax210 <source_url>`
3. Verify source files are extracted to this directory
4. Update `drivers/wifi_inventory.csv` to reflect collection status

## Driver Location

Intel AX210 typically uses the iwlwifi driver from:
- Kernel path: `drivers/net/wireless/intel/iwlwifi/`
- Upstream: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

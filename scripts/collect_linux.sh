#!/bin/bash

################################################################################
# collect_linux.sh - Linux WiFi driver collection script
#
# SYNOPSIS:
#   ./collect_linux.sh <device_id> [source_url]
#
# DESCRIPTION:
#   Automates collection of Linux WiFi drivers for MT7927 analysis pipeline.
#   Downloads kernel sources or vendor repositories, extracts driver files,
#   and organizes them into data/raw/linux/ directory structure.
#
# PARAMETERS:
#   device_id    - Unique identifier for the device (e.g., "intel_ax210")
#   source_url   - Optional URL to kernel.org or vendor git repository
#
# EXAMPLES:
#   ./collect_linux.sh intel_ax210
#   ./collect_linux.sh intel_ax210 "https://git.kernel.org/pub/scm/linux/..."
#
# NOTES:
#   Author: MT7927 Analysis Project
#   Version: 1.0.0 - SCAFFOLDING
#
#   This is a minimal scaffolding script. Future implementation should:
#   - Clone kernel sources or vendor repositories
#   - Identify relevant driver directories (e.g., drivers/net/wireless/intel/)
#   - Extract .c, .h, Makefile, Kconfig files
#   - Parse kernel version and maintainer info
#   - Extract module parameters and device IDs
#   - Organize files in data/raw/linux/<device_id>/
#   - Generate metadata.json with collection info
################################################################################

set -e  # Exit on error

DEVICE_ID="$1"
SOURCE_URL="${2:-}"

# Validate arguments
if [ -z "$DEVICE_ID" ]; then
    echo "ERROR: device_id is required"
    echo "Usage: $0 <device_id> [source_url]"
    exit 1
fi

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_DATA_PATH="$SCRIPT_DIR/../data/raw/linux"
DEVICE_PATH="$RAW_DATA_PATH/$DEVICE_ID"

echo "=========================================="
echo "Linux Driver Collection Script"
echo "SCAFFOLDING VERSION"
echo "=========================================="
echo "Device ID: $DEVICE_ID"
echo "Target Directory: $DEVICE_PATH"
echo "Source URL: ${SOURCE_URL:-<not provided>}"
echo ""

# TODO: Implement kernel source download/clone
# TODO: Implement driver file identification
# TODO: Implement source extraction
# TODO: Implement Kconfig/Makefile parsing
# TODO: Generate metadata.json

echo "NOTICE: This is a scaffolding script. Implementation required for:"
echo "  - Kernel source download or git clone"
echo "  - Driver directory identification (drivers/net/wireless/...)"
echo "  - Source file extraction (.c, .h, Makefile, Kconfig)"
echo "  - Module parameter and device ID extraction"
echo "  - Metadata generation (kernel version, maintainer, etc.)"
echo ""
echo "For manual collection:"
echo "  1. Download or clone kernel sources"
echo "  2. Identify driver files (e.g., drivers/net/wireless/intel/)"
echo "  3. Copy to $DEVICE_PATH"
echo "  4. Create metadata.json with driver info"
echo ""

exit 0

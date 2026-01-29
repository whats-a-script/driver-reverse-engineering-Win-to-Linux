# MediaTek MT7927 (Filogic 380) Linux Driver - Experimental

## ⚠️ WARNING - EXPERIMENTAL DRIVER ⚠️

This is an **EXPERIMENTAL**, **REVERSE-ENGINEERED** driver for the MediaTek MT7927 (Filogic 380) Wi-Fi 7 PCIe chipset. 

**THIS DRIVER IS NOT READY FOR PRODUCTION USE.**

- Hardware functionality is **NOT IMPLEMENTED**
- Register addresses are **UNKNOWN** and need reverse engineering
- Firmware protocol is **UNKNOWN**
- May not work at all or could **DAMAGE HARDWARE**
- No official support from MediaTek
- Use entirely at your own risk

## Overview

The MediaTek MT7927 (Filogic 380) is a Wi-Fi 7 (802.11be) PCIe chipset found in some TP-Link wireless adapters. No official Linux driver exists for this hardware. This project is an educational attempt to create an open-source driver through reverse engineering.

### Hardware Details

- **Chipset**: MediaTek Filogic 380 (MT7927)
- **PCI Vendor ID**: 0x14C3 (MediaTek)
- **PCI Device ID**: 0x7927
- **Interface**: PCIe (Gen 3 assumed)
- **Wi-Fi Standards**: 802.11be (Wi-Fi 7), backward compatible with 802.11ax/ac/n/a/g/b
- **Bands**: 2.4 GHz, 5 GHz, 6 GHz (tri-band)
- **Known Devices**: TP-Link Archer TXE70E, possibly others

## Project Status

### ✅ Completed
- [x] Basic repository structure
- [x] Linux kernel driver skeleton
- [x] PCI device detection and binding
- [x] PCIe resource allocation (BARs, DMA, interrupts)
- [x] mac80211 framework integration (stub)
- [x] Kconfig and Makefile for out-of-tree build
- [x] Code compiles successfully

### ⏳ In Progress / TODO
- [ ] Reverse engineer register map from Windows driver
- [ ] Determine firmware format and loading protocol
- [ ] Implement MAC layer initialization
- [ ] Implement PHY layer initialization
- [ ] Implement DMA ring setup and management
- [ ] Implement interrupt handling
- [ ] Implement TX/RX packet processing
- [ ] Channel switching and frequency control
- [ ] Power management
- [ ] Hardware encryption/decryption
- [ ] Real-world testing with hardware

### ❌ Known Limitations
- Driver does **NOT** initialize hardware
- Driver does **NOT** load firmware
- Driver does **NOT** transmit or receive packets
- All register addresses are **PLACEHOLDERS**
- Hardware may not respond correctly
- No regulatory domain support yet
- No calibration data handling

## Building the Driver

### Prerequisites

```bash
# Install kernel headers for your running kernel
sudo apt-get install linux-headers-$(uname -r)  # Ubuntu/Debian
sudo yum install kernel-devel                    # RHEL/CentOS
sudo pacman -S linux-headers                     # Arch Linux
```

### Build Steps

```bash
cd driver
make
```

This will produce `mt7927.ko` kernel module.

### Installation (NOT RECOMMENDED)

```bash
# Load the module
sudo insmod mt7927.ko

# Check if device was detected
dmesg | tail -30

# Unload the module
sudo rmmod mt7927
```

**WARNING**: Loading this driver on real hardware is NOT RECOMMENDED. It will bind to the device but will not make it functional and could potentially cause issues.

## Architecture

The driver is modeled after the upstream `mt76` driver family for other MediaTek chips:

```
driver/
├── Kconfig              # Kernel configuration options
├── Makefile             # Build system
├── mt7927.h             # Main header with device structures
├── mt7927_regs.h        # Register definitions (mostly TODO)
├── mt7927_main.c        # mac80211 integration and lifecycle
└── mt7927_pci.c         # PCIe probe/remove and hardware init
```

### Key Components

1. **PCI Layer** (`mt7927_pci.c`)
   - Device detection and binding
   - PCIe resource management
   - Interrupt registration
   - Hardware reset and initialization

2. **MAC80211 Integration** (`mt7927_main.c`)
   - Wireless stack interface
   - TX/RX callbacks (stubs)
   - Configuration and state management

3. **Register Definitions** (`mt7927_regs.h`)
   - Hardware register addresses
   - **WARNING**: Most addresses are UNKNOWN placeholders

## Reverse Engineering Notes

See [REVERSE_ENGINEERING.md](docs/REVERSE_ENGINEERING.md) for detailed notes on reverse engineering process, findings, and methodologies.

### What We Know
- PCI Vendor/Device ID: 14C3:7927
- Device uses PCIe interface
- Likely uses similar architecture to MT7921/MT7922
- Supports Wi-Fi 7 (802.11be)

### What We Don't Know (Yet)
- Exact register memory map
- Firmware format and loading protocol
- DMA descriptor format
- Interrupt bit meanings
- MAC/PHY initialization sequence
- Calibration data format
- Power management registers

## Contributing

This is an open reverse engineering project. Contributions are welcome!

### How to Help

1. **Hardware Analysis**
   - Dump PCI configuration space
   - Capture PCIe traffic with Windows driver
   - Analyze register access patterns

2. **Firmware Analysis**
   - Extract Windows driver firmware
   - Analyze firmware format
   - Document firmware commands

3. **Driver Development**
   - Implement TODOs in code
   - Add functionality as hardware behavior is discovered
   - Write tests and validation code

4. **Documentation**
   - Document findings
   - Create guides for reverse engineering process
   - Explain hardware behavior

### Code Style

- Follow Linux kernel coding style
- Use `scripts/checkpatch.pl` from kernel tree
- Add comments explaining unknowns
- Mark speculative code with TODO/FIXME

## Legal and Ethical Considerations

### Legality
- Reverse engineering for interoperability is generally legal in most jurisdictions
- No proprietary code from MediaTek or TP-Link is included
- Driver is clean-room implementation based on hardware observation
- Firmware remains proprietary and is not included

### Ethics
- Goal is interoperability, not circumventing security
- Driver will not implement DRM or copy protection bypasses
- Findings may be shared with MediaTek for potential official support

## Resources

### Similar Drivers (Reference)
- [mt76](https://github.com/torvalds/linux/tree/master/drivers/net/wireless/mediatek/mt76) - Upstream MediaTek driver family
- [mt7921](https://github.com/torvalds/linux/tree/master/drivers/net/wireless/mediatek/mt76/mt7921) - Similar PCIe Wi-Fi 6E chip

### Tools
- `lspci` - List PCI devices
- `setpci` - Read/write PCI config space
- `pcileech` - PCIe DMA analysis
- Ghidra/IDA Pro - Binary analysis
- Wireshark - Packet capture

### Documentation
- [Linux Wireless](https://wireless.wiki.kernel.org/) - mac80211 documentation
- [PCI Express](https://pcisig.com/) - PCIe specifications
- [IEEE 802.11](https://www.ieee802.org/11/) - Wi-Fi standards

## License

This driver is licensed under GPL-2.0-only to match Linux kernel licensing requirements.

## Disclaimer

THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND. THE AUTHORS TAKE NO RESPONSIBILITY FOR ANY DAMAGE TO HARDWARE OR DATA THAT MAY RESULT FROM USE OF THIS SOFTWARE.

Use of this driver is entirely at your own risk. The driver is experimental and incomplete. It may cause system instability, hardware malfunction, or data loss.

## Contact

Project Repository: https://github.com/whats-a-script/TP-link-wifi-MT7927-reverse-engineer

For questions or to contribute, please open an issue or pull request on GitHub.

---

**Last Updated**: January 2024  
**Driver Version**: 0.0.1-experimental  
**Kernel Compatibility**: Linux 5.15+

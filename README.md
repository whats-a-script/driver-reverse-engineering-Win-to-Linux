# AstraForge —  Windows-to-Linux Driver Reverse Engineering Toolkit

> **Copyright (C) 2026 (Charles Ellison). All intellectual property rights reserved.**
> All proprietary rights in this software, its source code, tooling, methodology, and documentation are reserved by the author. No license, express or implied, is granted except as explicitly stated herein.

---

## LEGAL NOTICE

**ALL RIGHTS RESERVED.** This repository, including but not limited to its source code, documentation, tooling (AstraForge), analysis methodologies, generated outputs, and all derivative works, is the exclusive proprietary and intellectual property of linuxwifi7 (Charles Ellison).

- Reproduction, redistribution, sublicensing, or commercial use of any portion of this repository without express written permission from the author is strictly prohibited.
- No patent rights, trademark rights, or other intellectual property rights are granted by implication, estoppel, or otherwise.
- Viewing this repository on a public platform does not constitute a grant of any rights to copy, modify, or distribute its contents.

**NO LIABILITY ASSUMED.** This software is provided strictly for educational, research purposes, self repair. The author assumes no liability whatsoever for any direct, indirect, incidental, special, exemplary, or consequential damages (including but not limited to hardware damage, data loss, system instability, or financial loss) arising from the use, misuse, or inability to use this software, even if the author has been advised of the possibility of such damages. **Use entirely at your own risk.**

---

## WARNING — EXPERIMENTAL

This is an **EXPERIMENTAL**, **INCOMPLETE**, reverse-engineered driver skeleton for windows to linux drivers.


- Hardware functionality is **NOT IMPLEMENTED**
- Register addresses are **UNKNOWN** placeholders requiring further reverse engineering
- Firmware protocol is **UNKNOWN**
- Loading on real hardware is **NOT RECOMMENDED**
- No official support from MediaTek or TP-Link

---

## Overview
The "test" driver below.
The MediaTek MT7927 (Filogic 380) is a Wi-Fi 7 (802.11be) PCIe chipset found in TP-Link wireless adapters. No official Linux driver exists. This project is an educational research effort to develop an driver through reverse engineering, powered by the **AstraForge** analysis toolkit developed in-house.

### Hardware Details

| Property | Value |
|---|---|
| Chipset | MediaTek Filogic 380 (MT7927) |
| PCI Vendor ID | 0x14C3 (MediaTek) |
| PCI Device ID | 0x7927 |
| Interface | PCIe Gen 3 |
| Wi-Fi Standards | 802.11be (Wi-Fi 7), backward compatible 802.11ax/ac/n/a/g/b |
| Bands | 2.4 GHz, 5 GHz, 6 GHz (tri-band) |
| Known Devices | TP-Link Archer TXE70E |

---

## AstraForge Toolkit

AstraForge is a proprietary reverse engineering toolkit developed for this project. It analyzes Windows driver binaries and generates Linux kernel driver skeletons.

### Features
- Windows INF and PE binary analysis
- PCI/USB device ID extraction
- Canonical JSON driver representation
- Linux kernel module skeleton generation
- GUI (AstraForge.exe) and CLI (AstraForgeCLI.exe) interfaces
- Knowledge base for discovered driver patterns

### Downloads (v1.0)

Pre-built Windows executables are located in `dist/`:

| Executable | Description |
|---|---|
| `AstraForge.exe` | GUI application (no Python required) |
| `AstraForgeCLI.exe` | Command-line interface (no Python required) |

To rebuild from source:
```powershell
.\tools\AstraForge\build.ps1
```

To produce a Windows installer, open `tools/AstraForge/installer.iss` in [Inno Setup Compiler](https://jrsoftware.org/isinfo.php) and build.

**AstraForge is proprietary software. All rights reserved. No redistribution permitted without express written consent.**

---

## Project Status

### Completed
- [x] Repository structure and documentation
- [x] AstraForge v1.0 (GUI + CLI) — Windows EXE build
- [x] Linux kernel driver skeleton (mt7927.ko)
- [x] PCI device detection and binding
- [x] PCIe resource allocation (BARs, DMA, interrupts)
- [x] mac80211 framework integration (stub)
- [x] Kconfig and Makefile for out-of-tree build
- [x] Successful kernel module compilation

### In Progress / TODO
- [ ] Reverse engineer register map from Windows driver binaries
- [ ] Determine firmware format and loading protocol
- [ ] MAC layer initialization
- [ ] PHY layer initialization
- [ ] DMA ring setup and management
- [ ] Interrupt handling
- [ ] TX/RX packet processing
- [ ] Channel switching and frequency control
- [ ] Power management
- [ ] Hardware encryption/decryption
- [ ] Real-world hardware testing

### Known Limitations
- Driver does **NOT** initialize hardware
- Driver does **NOT** load firmware
- Driver does **NOT** transmit or receive packets
- All register addresses are **PLACEHOLDERS**
- No regulatory domain support
- No calibration data handling

---

## Building the Driver

### Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get install linux-headers-$(uname -r)

# RHEL/CentOS
sudo yum install kernel-devel

# Arch Linux
sudo pacman -S linux-headers
```

### Build

```bash
cd driver
make
```

Produces `mt7927.ko`.

### Loading (NOT RECOMMENDED on real hardware)

```bash
sudo insmod mt7927.ko
dmesg | tail -30
sudo rmmod mt7927
```

---

## Repository Structure

```
.
├── dist/                        # Pre-built AstraForge executables (v1.0)
│   ├── AstraForge.exe           # GUI
│   └── AstraForgeCLI.exe        # CLI
├── tools/
│   └── AstraForge/              # AstraForge source and build config
│       ├── AstraForge.py        # Core logic / CLI entry point
│       ├── AstraForgeGUI.py     # GUI entry point
│       ├── config.py            # Configuration management
│       ├── AstraForgeGUI.spec   # PyInstaller GUI spec
│       ├── AstraForgeCLI.spec   # PyInstaller CLI spec
│       ├── build.ps1            # One-command build script
│       └── installer.iss        # Inno Setup installer script
├── driver/                      # Linux kernel driver source
│   ├── Kconfig
│   ├── Makefile
│   ├── mt7927.h
│   ├── mt7927_regs.h            # Register definitions (placeholders)
│   ├── mt7927_main.c            # mac80211 integration
│   └── mt7927_pci.c             # PCIe probe/remove
├── knowledge_base/              # Discovered device patterns
├── reports/                     # Analysis outputs
├── pulled drivers/              # Raw Windows/Linux driver files
└── docs/
    ├── QUICKSTART.md
    ├── REVERSE_ENGINEERING.md
    ├── TESTING.md
    └── CONTRIBUTING.md
```

---

## Reverse Engineering Methodology

See [docs/REVERSE_ENGINEERING.md](docs/REVERSE_ENGINEERING.md) for full details.

### Known
- PCI Vendor/Device ID: `14C3:7927`
- PCIe interface confirmed
- Likely shares architecture with MT7921/MT7922 family
- Supports Wi-Fi 7 (802.11be)

### Unknown (Actively Researching)
- Register memory map
- Firmware format and loading protocol
- DMA descriptor format
- Interrupt bit assignments
- MAC/PHY initialization sequence
- Calibration data format
- Power management registers

---

## Legal and Ethical Considerations

### Intellectual Property

All original work in this repository — including the AstraForge toolkit, analysis methodology, generated driver skeletons, and documentation — is the proprietary intellectual property of linuxwifi7 (Charlie Ellison). **All intellectual property rights are reserved.**

The Linux kernel driver skeleton (`driver/`) is derived from original work and is offered under GPL-2.0-only solely for the purpose of kernel linkage compliance. This GPL grant does not extend to the AstraForge toolkit or any other component of this repository.

No proprietary code, firmware, or binary assets from MediaTek or TP-Link are included in this repository. The driver is a clean-room implementation based on hardware observation only.

### No Warranty / No Liability

THIS SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY — WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE — ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR ITS USE. **ALL RISK IS ASSUMED BY THE USER.**

### Legality
- Reverse engineering for interoperability purposes is generally lawful in most jurisdictions under fair use, interoperability exceptions (e.g., EU Directive 2009/24/EC, 17 U.S.C. § 1201(f)).
- No proprietary MediaTek or TP-Link code is reproduced herein.
- Firmware is not included and remains proprietary to its respective owners.

---

## Reference Resources

### Related Drivers
- [mt76](https://github.com/torvalds/linux/tree/master/drivers/net/wireless/mediatek/mt76) — upstream MediaTek driver family
- [mt7921](https://github.com/torvalds/linux/tree/master/drivers/net/wireless/mediatek/mt76/mt7921) — similar PCIe Wi-Fi 6E chip

### Tools
- `lspci` / `setpci` — PCI configuration inspection
- Ghidra / IDA Pro — binary analysis
- Wireshark — packet capture
- pcileech — PCIe DMA analysis

### Standards
- [Linux Wireless (mac80211)](https://wireless.wiki.kernel.org/)
- [IEEE 802.11be](https://www.ieee802.org/11/)
- [PCIe Specification](https://pcisig.com/)

---

## Contact

Project Repository: https://github.com/linuxwifi7/TP-link-wifi-MT7927-reverse-engineer

For questions, please open an issue on GitHub.

---

**Copyright (C) 2026 AstraForge (Charlie Ellison). All Rights Reserved.**
**Last Updated**: April 2026 | **AstraForge Version**: 1.0 | **Driver Version**: 0.0.1-experimental | **Kernel Compatibility**: Linux 5.15+

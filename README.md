# Windows to Linux Driver Conversion Framework

> **⚠️ CONFIDENTIAL & PROPRIETARY - NDA REQUIRED**
> 
> This repository contains confidential and proprietary information.
> 
> **By accessing this repository, you acknowledge that:**
> - You must sign a Non-Disclosure Agreement (see [NDA.md](NDA.md))
> - All information is confidential and may not be shared
> - Unauthorized access or use is prohibited
> - All Rights Reserved - No permissions granted without signed NDA
>
> **For authorized access, contact the project maintainers.**

---

A comprehensive, staged engineering program for repairing and adapting device drivers to work with non-Windows operating systems (Linux/Unix) for PCIe, USB, and add-in/on-board peripherals.

> **⚠️ IMPORTANT LEGAL DISCLAIMERS:**
>
> **Third-Party Intellectual Property:**
> - The project and its maintainers DO NOT CLAIM OWNERSHIP OF, OR RIGHTS TO, ANY THIRD-PARTY DRIVER.
> - All third-party drivers and firmware are the intellectual property of their respective manufacturers.
>
> **No Warranty:**
> - The software is provided "AS IS," without warranty of any kind, express or implied.
>
> **Limitation of Liability:**
> - The project, its contributors, maintainers, and affiliates SHALL NOT BE LIABLE for any damages, losses, or claims (including third-party claims) resulting from the use, modification, or redistribution of third-party drivers.
> - Users are solely responsible for obtaining any rights, licenses, or permissions required to use, modify, or redistribute third-party drivers.
>
> **Indemnity:**
> - Users agree to indemnify and hold harmless the project and its maintainers from claims arising from their use or distribution of third-party drivers.
>
> **Purpose:**
> - This software is intended solely for repairing drivers to work with the subject's operating system (not Windows/Microsoft).
>
> **Release Gate:**
> - Any decision to include or redistribute third-party binaries in a public release requires documented legal signoff and must pass the Release Gate checklist.

## 🎯 Project Vision

Transform Windows device drivers into production-ready Linux drivers through a combination of:
- **Automated analysis** of Windows driver binaries
- **Intelligent strategy selection** (wrapper, reimplementation, or passthrough)
- **Guided reimplementation** with generated skeletons and test harnesses
- **Production packaging** with DKMS, signing, and CI/CD integration

## 📋 Project Status

**Current Phase:** Research & Foundation (Week 0-4)  
**Initial Test Case:** MediaTek MT7927 Wi-Fi  
**Target OSes:** Linux (primary), BSD/Unix (notes provided where feasible)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  ┌──────────────────────┐   ┌──────────────────────────┐   │
│  │   GUI (Qt/Electron)  │   │   CLI (Python/Rust)      │   │
│  └──────────────────────┘   └──────────────────────────┘   │
└────────────────────────┬────────────────────────┬───────────┘
                         │                        │
┌────────────────────────┴────────────────────────┴───────────┐
│                    Orchestration Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Strategy   │  │  Packaging   │  │   Testing    │     │
│  │   Engine     │  │  Pipeline    │  │   Harness    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────┴───────────────────────────────────┐
│                    Core Analysis Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Driver     │  │  Wrapper     │  │Reimplementation│    │
│  │   Analyzer   │  │  Runtime     │  │   Pipeline   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Core Components

### 1. Driver Analyzer
Analyzes Windows driver binaries to extract metadata and interfaces.

**Capabilities:**
- PE/driver file parser
- Driver model classification (WDM/WDF/NDIS/UMDF)
- Exported symbol and IOCTL enumeration
- Dependency graph generation
- Automated reverse engineering (Ghidra/IDA integration)

**Output:** Structured JSON with driver model, interfaces, PCI/USB IDs, and conversion strategies.

### 2. Strategy Engine
Recommends optimal conversion approach with confidence scores.

**Strategies:**
- **Wrapper:** For well-understood, legacy drivers (e.g., NDIS Wi-Fi)
- **Reimplementation:** Preferred for production safety and maintainability
- **Passthrough:** VM-based solution when conversion is infeasible

### 3. Wrapper Runtime (Prototype)
Kernel shim for limited binary reuse (research/prototype only).

**Features:**
- Kernel compatibility layer (C)
- Userland helper (Rust/C++)
- Sandboxing and runtime integrity checks
- Logging and kill-switch mechanisms

**Scope:** Limited to safe, documented driver models only.

### 4. Reimplementation Pipeline
Generates driver skeletons from interface descriptions.

**Outputs:**
- Kernel module templates (C and Rust)
- Protocol/state diagrams
- Automated test harnesses
- Template drivers for common device classes

### 5. Packaging & Distribution
Production-ready packaging workflow.

**Features:**
- DKMS integration
- deb/rpm package generation
- Module signing workflow
- Secure Boot guidance
- Cross-kernel build matrix (5.x, 6.x+)

### 6. GUI & CLI Tools
Cross-platform interface for all operations.

**GUI (Qt/Electron):**
- Import driver binaries
- Run analysis and view results
- Select conversion strategy
- Build and test packages

**CLI:**
- Automation and CI/CD integration
- Batch processing
- Headless operation

### 7. Testing & CI
Comprehensive validation framework.

**Test Types:**
- QEMU + VFIO automation
- Hardware-in-the-loop testing
- Regression testing across kernel versions
- Performance benchmarking

**Metrics:**
- Functional pass rate
- Performance vs vendor driver
- Stability (uptime)
- Security audit results

### 8. Security & Legal
Compliance and safety framework.

**Legal Checklist:**
- EULA review
- Copyright/redistribution risk
- Export controls
- Vendor engagement plan

**Security Requirements:**
- No unsigned vendor kernel code in production
- Required: signing, sandboxing, integrity checks
- Runtime monitoring and audit trails

## 📅 Milestone Timeline

### Week 0-4: Research Phase
- [x] Repository setup and documentation
- [ ] MT7927 feasibility analysis
- [ ] Legal risk assessment
- [ ] Tool selection and architecture design

### Week 5-10: Prototype Phase
- [ ] Driver analyzer implementation
- [ ] Strategy engine v1
- [ ] Wrapper runtime prototype
- [ ] GUI mockups
- [ ] Test harness for prototype

### Week 11-18: MVP Phase
- [ ] Reimplementation pipeline demo
- [ ] USB device driver example
- [ ] DKMS packaging pipeline
- [ ] CI integration (kernel 5.x, 6.x)

### Week 19-30: Production Phase
- [ ] Hardened wrapper (if validated)
- [ ] Expanded device templates
- [ ] Full GUI implementation
- [ ] Module signing and Secure Boot
- [ ] Hardware test matrix
- [ ] User documentation
- [ ] Release artifacts

## 🎓 Quick Start

### Prerequisites
```bash
# Install required tools
sudo apt-get install -y \
    build-essential \
    linux-headers-$(uname -r) \
    dkms \
    python3 \
    python3-pip \
    git \
    ghidra \
    binutils \
    pev

# Optional: Rust toolchain for components
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Analyze a Driver
```bash
# Using the CLI tool (coming soon)
./bin/driver-analyzer analyze --input driver.sys --output analysis.json

# View analysis results
./bin/driver-analyzer report --input analysis.json
```

### Generate a Linux Driver Skeleton
```bash
# From analysis results
./bin/driver-generator create \
    --analysis analysis.json \
    --output-dir ./mt7927-linux-driver \
    --language c \
    --driver-type network
```

### Build and Package
```bash
# Build kernel module
cd ./mt7927-linux-driver
make

# Create DKMS package
./scripts/package-dkms.sh --version 1.0.0 --distro ubuntu
```

## 📚 Documentation

- [MT7927 Feasibility Analysis](docs/MT7927-FEASIBILITY.md)
- [Analyzer Data Schema](docs/ANALYZER-SCHEMA.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Security Guidelines](docs/SECURITY.md)
- [Legal Compliance](docs/LEGAL-COMPLIANCE.md)
- [Release Gate Checklist](docs/RELEASE-GATE-CHECKLIST.md) - **Required for third-party binary releases**
- [Contributing Guide](docs/CONTRIBUTING.md)

## 🔬 Initial Test Case: MediaTek MT7927

The MT7927 Wi-Fi device serves as our primary validation case. See [MT7927 Feasibility Analysis](docs/MT7927-FEASIBILITY.md) for details on:
- Device specifications
- Windows driver analysis
- Hardware requirements
- Test plan

## 🛡️ Safety & Compliance

### Safety First
- **Prefer reimplementation** over binary reuse
- Binary wrappers are **prototype/research only**
- Production requires signing and sandboxing
- User consent required for any binary reuse

### Legal Compliance
All conversion work must:
- Respect vendor intellectual property
- Review and comply with EULAs
- Document redistribution constraints
- Maintain audit trail

See [Legal Compliance Checklist](docs/LEGAL-COMPLIANCE.md) for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- PR process

### Areas Needing Help
- Device-specific driver templates
- Testing on various hardware
- Documentation improvements
- Security audits

## 📊 Supported Device Classes

| Device Class | Support Level | Example Devices |
|-------------|---------------|-----------------|
| PCIe Network | ✅ Primary | MT7927, Intel Wi-Fi |
| USB Serial | 🟡 Planned | FTDI, CH340 |
| USB Audio | 🟡 Planned | USB Sound Cards |
| USB Camera | 🟡 Planned | UVC Cameras |
| PCIe Multimedia | 🟡 Planned | Capture Cards |
| Other PCIe | 🔵 Future | Various |

## 🐛 Known Limitations

1. **Not a Silver Bullet:** Automatic conversion is not possible for all drivers
2. **Binary Wrappers:** Limited scope, prototype only, requires sandboxing
3. **Hardware Access:** Some devices may require VM passthrough
4. **Legal:** Vendor EULA may prohibit reverse engineering
5. **Complexity:** Complex drivers may require significant manual work

## 📞 Support & Contact

- **Issues:** GitHub Issues for bug reports and feature requests
- **Discussions:** GitHub Discussions for questions and community support
- **Security:** See [SECURITY.md](SECURITY.md) for vulnerability reporting

## 📄 License

Copyright (c) 2026 TP-link-wifi-MT7927-reverse-engineer Contributors. All Rights Reserved.

This software is proprietary and confidential. 

**⚠️ ACCESS REQUIRES SIGNED NDA:** All users must sign a Non-Disclosure Agreement before accessing or using this software. See [NDA.md](NDA.md) for the complete agreement.

**⚠️ COMPREHENSIVE LEGAL DISCLAIMERS:** This project does not claim ownership of any third-party drivers. Users are solely responsible for compliance with third-party IP rights and accept all liability. See [LICENSE](LICENSE) for complete terms including:
- No warranty (provided "as is")
- Limitation of liability for damages/losses/claims
- User indemnity obligations
- Release gate requirements for third-party binaries

Unauthorized copying, distribution, modification, or use is strictly prohibited without express written permission and a signed NDA.

**Note:** This software is intended solely for repairing drivers to work with non-Windows operating systems. Linux kernel modules may be subject to GPLv2 for kernel compatibility.

## 🙏 Acknowledgments

- MediaTek for MT7927 hardware specifications
- The Linux kernel community
- Ghidra and IDA Pro teams
- All contributors and testers

---

**⚠️ Important:** This is a research and development project. Binary driver reuse should only be used for prototyping and testing. Production deployments should use fully reimplemented, open-source drivers whenever possible.

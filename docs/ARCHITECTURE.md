# Architecture Documentation

This document provides a comprehensive technical architecture overview of the Windows to Linux Driver Conversion Framework.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Interface Specifications](#interface-specifications)
6. [Deployment Architecture](#deployment-architecture)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           User Layer                                 │
│  ┌──────────────────┐                    ┌──────────────────┐      │
│  │   Web/Desktop    │◄──────────────────►│   CLI Interface  │      │
│  │   GUI (Qt)       │   REST/IPC/gRPC    │   (Python/Rust)  │      │
│  └────────┬─────────┘                    └─────────┬────────┘      │
└───────────┼──────────────────────────────────────────┼──────────────┘
            │                                          │
            └──────────────────┬───────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────┐
│                    Orchestration Layer                                │
│                               │                                       │
│     ┌────────────────────────▼──────────────────────┐               │
│     │        Workflow Engine (Core Service)         │               │
│     │  • Task scheduling  • State management        │               │
│     │  • Progress tracking • Error handling         │               │
│     └──┬─────────┬──────────┬──────────┬───────┬───┘               │
│        │         │          │          │       │                    │
└────────┼─────────┼──────────┼──────────┼───────┼────────────────────┘
         │         │          │          │       │
         ▼         ▼          ▼          ▼       ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Processing Layer                               │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐  ┌─────────┐ │
│  │ Driver  │  │ Strategy │  │ Wrapper │  │ Reimp. │  │ Package │ │
│  │Analyzer │  │  Engine  │  │ Runtime │  │Pipeline│  │ Builder │ │
│  └─────────┘  └──────────┘  └─────────┘  └────────┘  └─────────┘ │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐  ┌─────────┐ │
│  │  Test   │  │ Security │  │  Legal  │  │  Docs  │  │  CI/CD  │ │
│  │ Harness │  │ Scanner  │  │ Checker │  │  Gen   │  │ Pipeline│ │
│  └─────────┘  └──────────┘  └─────────┘  └────────┘  └─────────┘ │
└────────────────────────────────────────────────────────────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────────┐
│                    Data Layer                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐              │
│  │  Database   │  │  File Store  │  │    Cache    │              │
│  │ (SQLite/PG) │  │  (Artifacts) │  │   (Redis)   │              │
│  └─────────────┘  └──────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
         │              │              │
         └──────────────┴──────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────────┐
│                   External Tools Layer                              │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐              │
│  │ Ghidra  │  │  QEMU   │  │  DKMS  │  │ Compiler │              │
│  │   IDA   │  │  VFIO   │  │  dpkg  │  │   gcc    │              │
│  └─────────┘  └─────────┘  └────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Driver Analyzer

**Purpose:** Extract structured metadata from Windows driver binaries.

**Subcomponents:**
- **PE Parser:** Parses Windows PE/COFF format
- **Driver Classifier:** Identifies driver model (WDM/WDF/NDIS)
- **Symbol Extractor:** Extracts imports/exports
- **Disassembler Interface:** Ghidra/IDA automation
- **Pattern Matcher:** Recognizes common driver patterns

**Input:** Windows driver binary (.sys, .dll)  
**Output:** JSON metadata (see ANALYZER-SCHEMA.md)

**Technology:**
- Core: Python 3.10+
- Libraries: pefile, capstone, angr, radare2-python
- Optional: Ghidra Headless (Java), IDA Python API

**APIs:**
```python
class DriverAnalyzer:
    def analyze(self, driver_path: str) -> AnalysisResult
    def classify_driver_model(self, pe_data) -> DriverModel
    def extract_symbols(self, pe_data) -> SymbolTable
    def find_ioctls(self, disasm_data) -> List[IOCTL]
```

---

### 2.2 Strategy Engine

**Purpose:** Recommend optimal conversion strategy based on analysis.

**Decision Factors:**
- Driver complexity (function count, dependencies)
- Driver model (legacy vs modern)
- Legal constraints (EULA analysis)
- Security risks (binary signing, unsafe APIs)
- Available reference implementations

**Output:** Ranked list of strategies with confidence scores

**Technology:**
- Core: Python 3.10+
- ML: scikit-learn (optional for scoring)
- Rules: YAML-based rule engine

**APIs:**
```python
class StrategyEngine:
    def recommend_strategy(self, analysis: AnalysisResult) -> List[Strategy]
    def score_strategy(self, strategy: Strategy, analysis: AnalysisResult) -> float
    def explain_recommendation(self, strategy: Strategy) -> str
```

---

### 2.3 Wrapper Runtime (Prototype)

**Purpose:** Shim layer for binary driver reuse (limited scope).

**Architecture:**
```
┌──────────────────────────────────────┐
│    Linux Userspace Application       │
└───────────────┬──────────────────────┘
                │ ioctl/netlink
┌───────────────▼──────────────────────┐
│    Wrapper Kernel Module (Linux)     │
│  ┌────────────────────────────────┐  │
│  │  NDIS Compatibility Layer      │  │
│  │  • ndis.sys API emulation      │  │
│  │  • Memory management           │  │
│  │  • Synchronization primitives  │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  Security Sandbox              │  │
│  │  • Memory isolation            │  │
│  │  • API filtering               │  │
│  │  • Runtime monitoring          │  │
│  └────────────────────────────────┘  │
└───────────────┬──────────────────────┘
                │
┌───────────────▼──────────────────────┐
│   Windows Driver Binary (.sys)       │
│   (Loaded as blob, NOT executed)     │
└──────────────────────────────────────┘
```

**Status:** Research only. Not recommended for production.

**Technology:**
- Kernel module: C
- Userspace helper: Rust
- Sandboxing: Seccomp, namespaces

---

### 2.4 Reimplementation Pipeline

**Purpose:** Generate Linux driver skeletons from analysis data.

**Components:**
- **Template Engine:** Jinja2-based code generation
- **Skeleton Generator:** Creates boilerplate driver code
- **State Machine Generator:** Converts Windows state machines to Linux
- **Build System Generator:** Creates Makefile, Kconfig, DKMS config

**Templates:**
- Network drivers (cfg80211/mac80211 for Wi-Fi)
- USB drivers (USB core API)
- PCIe drivers (PCI core API)
- Character devices

**Technology:**
- Core: Python 3.10+
- Templates: Jinja2
- Output: C code, Rust code (optional)

**APIs:**
```python
class ReimplementationPipeline:
    def generate_skeleton(self, analysis: AnalysisResult, config: Config) -> DriverSkeleton
    def generate_makefile(self, skeleton: DriverSkeleton) -> str
    def generate_dkms_config(self, skeleton: DriverSkeleton) -> str
```

---

### 2.5 Packaging Pipeline

**Purpose:** Create distributable packages (DKMS, deb, rpm).

**Features:**
- DKMS module configuration
- Debian package builder
- RPM spec file generator
- Module signing integration
- Dependency resolution

**Technology:**
- Scripts: Bash, Python
- Tools: dpkg-buildpackage, rpmbuild, DKMS

**APIs:**
```python
class PackagingPipeline:
    def create_dkms_package(self, driver_path: str, version: str) -> Package
    def create_deb_package(self, driver_path: str) -> Package
    def create_rpm_package(self, driver_path: str) -> Package
    def sign_module(self, module_path: str, key: Key) -> None
```

---

### 2.6 Testing Framework

**Purpose:** Automated validation of generated drivers.

**Test Types:**
1. **Unit Tests:** Per-function testing
2. **Integration Tests:** Driver load/unload, device detection
3. **Functional Tests:** Device operation (network connectivity, data transfer)
4. **Regression Tests:** Kernel version compatibility
5. **Performance Tests:** Throughput, latency benchmarks

**Infrastructure:**
- **QEMU/KVM:** Virtual testing
- **VFIO:** PCIe device passthrough
- **Hardware-in-the-Loop:** Real device testing

**Technology:**
- Framework: pytest
- Automation: Ansible, shell scripts
- Virtualization: QEMU, libvirt

---

### 2.7 GUI Application

**Purpose:** User-friendly interface for all operations.

**Framework:** Qt 6 (C++ or Python bindings) or Electron (TypeScript)

**Views:**
1. **Welcome:** Project setup, driver import
2. **Analysis:** Display analysis results, visualizations
3. **Strategy:** Show recommended strategies, allow selection
4. **Generation:** Configure and generate driver skeleton
5. **Build:** Compile, package, test
6. **Deploy:** Install, load module, verify

**Technology Options:**
- **Qt 6:** C++ or PyQt6 (native, high performance)
- **Electron:** TypeScript/React (cross-platform, web tech)

---

### 2.8 CLI Tool

**Purpose:** Scriptable interface for automation and CI/CD.

**Commands:**
```bash
driver-converter analyze <driver.sys> -o analysis.json
driver-converter recommend-strategy analysis.json
driver-converter generate --analysis analysis.json --output driver-skeleton/
driver-converter build driver-skeleton/
driver-converter test driver-skeleton/
driver-converter package driver-skeleton/ -o driver.deb
```

**Technology:**
- Language: Python (Click framework) or Rust (clap)
- Output: JSON, YAML, human-readable text

---

## 3. Data Flow

### 3.1 Analysis Flow

```
Windows Driver Binary (driver.sys)
        │
        ├──► PE Parser ──► Basic Metadata
        │                  (file size, version, arch)
        │
        ├──► Symbol Extractor ──► Imports/Exports
        │                          (ntoskrnl, ndis.sys)
        │
        ├──► Disassembler (Ghidra) ──► Function Analysis
        │                                (entry points, IOCTLs)
        │
        ├──► Pattern Matcher ──► Driver Model Classification
        │                         (WDM, NDIS 6.x, etc.)
        │
        └──► Static Analyzer ──► Security Issues
                                  (unsafe APIs, unsigned code)
                 │
                 ▼
        Analyzer Output JSON
        (see ANALYZER-SCHEMA.md)
```

### 3.2 Strategy Selection Flow

```
Analyzer Output JSON
        │
        ├──► Complexity Scorer
        ├──► Legal Risk Assessor
        ├──► Security Risk Assessor
        └──► Reference Availability Checker
                 │
                 ▼
        Strategy Candidates
        (wrapper, reimplementation, passthrough)
                 │
                 ├──► Confidence Scoring
                 ├──► Feasibility Assessment
                 └──► Effort Estimation
                         │
                         ▼
        Ranked Strategy List
        (recommended strategy + alternatives)
```

### 3.3 Reimplementation Flow

```
Analyzer Output JSON + User Config
        │
        ├──► Template Selector
        │    (network, USB, PCIe, etc.)
        │
        ├──► Skeleton Generator
        │    ├─► Module init/exit functions
        │    ├─► Device probe/remove
        │    ├─► Interrupt handlers (stubs)
        │    ├─► DMA management (stubs)
        │    └─► IOCTL handlers (stubs)
        │
        ├──► Build System Generator
        │    ├─► Makefile
        │    ├─► Kconfig
        │    └─► DKMS config
        │
        └──► Documentation Generator
             ├─► README.md
             ├─► TODO.md (hardware-specific items)
             └─► ARCHITECTURE.md
                     │
                     ▼
        Driver Skeleton (C code + build files)
```

### 3.4 Build & Package Flow

```
Driver Skeleton
        │
        ├──► Kernel Module Build
        │    (make, gcc, clang)
        │         │
        │         ▼
        │    driver.ko
        │
        ├──► Module Signing (optional)
        │    (sign-file, MOK)
        │
        ├──► DKMS Package
        │    (dkms.conf + source)
        │
        ├──► Debian Package
        │    (dpkg-buildpackage)
        │         │
        │         ▼
        │    driver.deb
        │
        └──► RPM Package
             (rpmbuild)
                  │
                  ▼
             driver.rpm
```

---

## 4. Technology Stack

### 4.1 Core Components

| Component | Language | Key Libraries/Frameworks |
|-----------|----------|-------------------------|
| Driver Analyzer | Python 3.10+ | pefile, capstone, angr |
| Strategy Engine | Python 3.10+ | scikit-learn, YAML |
| Code Generator | Python 3.10+ | Jinja2 |
| Wrapper Runtime | C, Rust | Linux kernel API, libc |
| CLI Tool | Python | Click, rich (UI) |
| GUI Application | Qt/Electron | Qt 6 / React + TypeScript |
| Test Framework | Python, Bash | pytest, QEMU, Ansible |
| CI/CD | YAML | GitHub Actions / GitLab CI |

### 4.2 External Tools

- **Reverse Engineering:** Ghidra, IDA Pro, radare2
- **Virtualization:** QEMU, KVM, libvirt
- **Build Tools:** gcc, clang, make, cmake
- **Packaging:** DKMS, dpkg, rpmbuild
- **Testing:** VFIO, hardware test rigs

### 4.3 Data Storage

- **Metadata:** SQLite (lightweight) or PostgreSQL (production)
- **File Artifacts:** Filesystem (with version control)
- **Cache:** Redis (optional, for distributed builds)
- **Configuration:** YAML, TOML

---

## 5. Interface Specifications

### 5.1 Analyzer API

**REST Endpoint (optional, for GUI):**
```
POST /api/v1/analyze
Content-Type: multipart/form-data

Body: driver_file=<binary>

Response:
{
  "job_id": "uuid",
  "status": "queued|running|completed|failed",
  "result": <AnalysisResult JSON>
}
```

**Python API:**
```python
from driver_analyzer import DriverAnalyzer

analyzer = DriverAnalyzer()
result = analyzer.analyze("/path/to/driver.sys")
print(result.to_json())
```

### 5.2 Strategy API

**Python API:**
```python
from strategy_engine import StrategyEngine

engine = StrategyEngine()
strategies = engine.recommend_strategy(analysis_result)

for strategy in strategies:
    print(f"{strategy.name}: {strategy.confidence}")
```

### 5.3 CLI Commands

```bash
# Analyze driver
driver-converter analyze driver.sys -o analysis.json

# Show strategy recommendations
driver-converter recommend analysis.json

# Generate skeleton
driver-converter generate \
    --analysis analysis.json \
    --template network \
    --language c \
    --output ./driver-skeleton

# Build driver
driver-converter build ./driver-skeleton

# Run tests
driver-converter test ./driver-skeleton --vm qemu

# Create package
driver-converter package ./driver-skeleton \
    --format deb \
    --version 1.0.0 \
    -o driver-mt7927.deb
```

---

## 6. Deployment Architecture

### 6.1 Development Environment

```
Developer Workstation
├── IDE (VSCode, CLion)
├── Driver Converter Tools (local install)
├── QEMU/KVM (for testing)
├── Hardware Test Device (PCIe/USB)
└── Git Repository (source control)
```

### 6.2 CI/CD Environment

```
GitHub Actions / GitLab CI
├── Analysis Job
│   └── Run analyzer on test drivers
├── Build Job
│   ├── Build for kernel 5.15 (LTS)
│   ├── Build for kernel 6.1 (LTS)
│   └── Build for kernel 6.6+
├── Test Job
│   ├── QEMU functional tests
│   └── VFIO passthrough tests
├── Package Job
│   ├── Create DKMS package
│   ├── Create .deb package
│   └── Create .rpm package
└── Release Job
    └── Publish to GitHub Releases
```

### 6.3 Production Deployment (End User)

```
End User System (Linux)
├── Install driver package (deb/rpm)
├── DKMS auto-builds for current kernel
├── Module loads at boot (if configured)
└── Device operational
```

---

## 7. Security Architecture

### 7.1 Threat Model

**Threats:**
1. **Malicious Driver Binary:** User analyzes malware
2. **Supply Chain Attack:** Compromised analyzer tools
3. **Privilege Escalation:** Wrapper runtime vulnerability
4. **Data Exfiltration:** Driver collects sensitive data

**Mitigations:**
1. Sandbox analyzer (containers, VMs)
2. Verify tool signatures
3. Strict kernel module signing
4. Runtime monitoring and audit logs

### 7.2 Security Boundaries

```
┌─────────────────────────────────────┐
│  User Space (Unprivileged)          │
│  • GUI/CLI (no elevated privileges) │
└───────────┬─────────────────────────┘
            │
┌───────────▼─────────────────────────┐
│  Analyzer (Sandboxed)                │
│  • Runs in container                 │
│  • No network access                 │
│  • Read-only input                   │
└───────────┬─────────────────────────┘
            │
┌───────────▼─────────────────────────┐
│  Build System (Controlled)           │
│  • Verified toolchain                │
│  • Reproducible builds               │
└───────────┬─────────────────────────┘
            │
┌───────────▼─────────────────────────┐
│  Kernel Space (Signed)               │
│  • Module signed with secure key     │
│  • Kernel lockdown mode compatible   │
│  • Secure Boot compatible            │
└──────────────────────────────────────┘
```

---

## 8. Extension Points

### 8.1 Plugin Architecture

The system supports plugins for:
- **Custom Analyzers:** Device-specific analysis logic
- **Custom Templates:** New driver class templates
- **Custom Strategies:** Proprietary conversion approaches
- **Custom Tests:** Hardware-specific test suites

**Plugin API (Python):**
```python
from driver_converter.plugin import AnalyzerPlugin

class MyCustomAnalyzer(AnalyzerPlugin):
    def analyze(self, driver_data):
        # Custom analysis logic
        return custom_result

# Register plugin
PluginRegistry.register(MyCustomAnalyzer)
```

### 8.2 Future Enhancements

- **ML-based Strategy Selection:** Train on successful conversions
- **Community Knowledge Base:** Crowdsourced driver patterns
- **Hardware Database:** Verified device compatibility matrix
- **Automated Testing:** Continuous integration with real hardware
- **Cloud Service:** SaaS offering for driver conversion

---

## Appendix A: Component Dependencies

```
GUI ──────────► Core API ──────────► Analyzer
                   │                     │
CLI ──────────────►│                     ├──► Disassembler
                   │                     │     (Ghidra/IDA)
                   │                     │
                   ├───────────────────► Strategy Engine
                   │                     │
                   ├───────────────────► Code Generator
                   │                     │
                   ├───────────────────► Build System
                   │                     │
                   └───────────────────► Test Framework
                                         │
                                         ├──► QEMU
                                         └──► Hardware Test Rig
```

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Maintainer:** Driver Conversion Framework Team

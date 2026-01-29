# MT7927 Wi-Fi Driver Conversion - Feasibility Analysis

**Device:** MediaTek MT7927 Wi-Fi 6E/7 Network Adapter  
**Target:** Linux kernel module (native reimplementation preferred)  
**Analysis Date:** January 2026  
**Status:** Research Phase (Week 0-4)

---

## Executive Summary

The MediaTek MT7927 is a modern Wi-Fi 6E/7 chipset found in TP-Link and other wireless adapters. Conversion to a native Linux driver is **feasible but challenging**, requiring significant reverse engineering effort. We recommend a **phased approach**: analysis → prototype wrapper (if safe) → guided reimplementation.

**Recommendation:** Proceed with staged implementation. Priority on reimplementation over binary reuse.

---

## 1. Device Specifications

### Hardware Details
- **Chipset:** MediaTek MT7927
- **Bus Interface:** PCIe (Gen3 x1 or x2)
- **Wi-Fi Standards:** 802.11be (Wi-Fi 7), 802.11ax (Wi-Fi 6E), backward compatible
- **Bands:** 2.4 GHz, 5 GHz, 6 GHz (6E/7)
- **Antenna Configuration:** 2x2 or 3x3 MIMO
- **Max Speed:** Up to 2.4 Gbps (theoretical)
- **Features:**
  - MU-MIMO
  - OFDMA
  - Beamforming
  - WPA3 security
  - 160 MHz channel width (Wi-Fi 6E/7)

### PCI IDs
- **Vendor ID:** 0x14c3 (MediaTek)
- **Device ID:** TBD (needs verification from hardware)
  - Likely range: 0x7927 or similar
- **Subsystem IDs:** Varies by OEM (TP-Link, etc.)

### Known Products
- TP-Link Archer TXE75E (PCIe)
- TP-Link AXE75 (USB variant: different chip)
- Various laptop WiFi modules

---

## 2. Windows Driver Analysis Plan

### 2.1 Driver Files to Acquire
- **Primary:** `mt7927e.sys` (kernel driver)
- **Supporting:**
  - `mt7927.inf` (installation metadata)
  - `mt7927co.dll` (configuration DLL, if present)
  - Related `.cat` (catalog) files
- **Source:** OEM download or driver extraction from Windows installation

### 2.2 Analysis Tools Required

| Tool | Purpose | Priority |
|------|---------|----------|
| **Ghidra** | Reverse engineering, disassembly | Critical |
| **IDA Pro** (optional) | Advanced analysis | High |
| **WinDbg** | Dynamic analysis on Windows VM | High |
| **PEview / CFF Explorer** | PE structure inspection | Medium |
| **Dependency Walker** | DLL dependencies | Medium |
| **Process Monitor** | Runtime I/O tracing | High |
| **Wireshark** | Network protocol analysis | Medium |

### 2.3 Analysis Steps

#### Phase 1: Static Analysis (Week 1-2)
1. **PE Header Inspection:**
   - Extract driver model (WDM/WDF/NDIS)
   - Identify NDIS version
   - Extract exported functions
   - Map imports and dependencies

2. **Disassembly in Ghidra:**
   - Load `mt7927e.sys` into Ghidra
   - Run auto-analysis
   - Identify key functions:
     - DriverEntry / AddDevice
     - I/O control handlers
     - Interrupt service routines
     - DMA operations
     - Power management callbacks
   - Export function signatures and structures

3. **INF File Analysis:**
   - Extract PCI IDs (vendor/device/subsystem)
   - Identify required registry settings
   - Document installation parameters
   - Extract firmware paths (if any)

#### Phase 2: Dynamic Analysis (Week 2-3)
1. **Windows VM Setup (QEMU/VirtualBox):**
   - Install Windows 10/11
   - Pass through PCIe device (if available) OR use USB variant
   - Install vendor driver

2. **Runtime Tracing:**
   - Use WinDbg to trace driver initialization
   - Monitor IOCTL calls with Process Monitor
   - Capture register access patterns
   - Log DMA operations
   - Trace interrupt handling

3. **Protocol Analysis:**
   - Use Wireshark to capture 802.11 management frames
   - Monitor configuration commands sent to hardware
   - Reverse engineer firmware command structures

#### Phase 3: Hardware Interaction Study (Week 3-4)
1. **Register Mapping:**
   - Identify MMIO regions from PCIe BAR
   - Document register offsets and purposes
   - Map configuration registers
   - Document interrupt registers

2. **Firmware Analysis:**
   - Extract firmware blobs (if loadable)
   - Analyze firmware format and loading mechanism
   - Document firmware API/command interface

3. **State Machine Documentation:**
   - Document initialization sequence
   - Map device power states
   - Document connection/authentication flow
   - Identify error handling paths

---

## 3. Data Requirements

### 3.1 From Windows Driver
- [ ] Driver binary (`mt7927e.sys`, latest version)
- [ ] INF file and installation package
- [ ] Firmware files (if separate)
- [ ] Any userspace utilities or DLLs
- [ ] Driver release notes / changelog (if available)

### 3.2 From Hardware Testing
- [ ] Actual MT7927 PCIe card or USB adapter
- [ ] Test system with PCIe slot (for passthrough testing)
- [ ] Access point with Wi-Fi 6E/7 support (for validation)
- [ ] USB protocol analyzer (if USB variant)

### 3.3 From Documentation Research
- [ ] MediaTek public datasheets (if available)
- [ ] 802.11be/ax specification documents
- [ ] Existing Linux driver code for similar MediaTek chips (mt76 series)
- [ ] Community documentation / forums

### 3.4 From Reference Implementations
- [ ] Linux `mt76` driver source (MT7921, MT7922 similar chips)
- [ ] Linux `ath11k` driver (Qualcomm Wi-Fi 6E reference)
- [ ] Linux `iwlwifi` driver (Intel, modern architecture)

---

## 4. Test Hardware Requirements

### 4.1 Minimum Test Setup
- **Host System:** Linux workstation or laptop
  - CPU with VT-d/IOMMU support (for VFIO passthrough testing)
  - Available PCIe slot (x1 minimum)
  - 8GB+ RAM
  - SSD for fast builds

- **Test Device:** MT7927 PCIe adapter
  - TP-Link Archer TXE75E or equivalent
  - Alternatively: Laptop with integrated MT7927 (harder to work with)

- **Test Network:**
  - Wi-Fi 6E/7 capable access point or router
  - Wired Ethernet for fallback connection
  - Network analyzer setup (optional but helpful)

### 4.2 Recommended Test Setup
All of the above plus:
- **Windows VM:** For driver tracing and comparison
  - 4GB RAM allocated
  - PCIe passthrough configured
- **Second Test Machine:** For connectivity testing
- **USB Wi-Fi Adapter:** Backup connection during testing
- **Logic Analyzer / Bus Sniffer:** For deep PCIe debugging (advanced)

### 4.3 Optional Advanced Setup
- **FPGA Development Board:** For hardware simulation (if custom firmware needed)
- **Spectrum Analyzer:** For RF validation
- **Anechoic Chamber:** For RF compliance testing (production only)

---

## 5. Conversion Strategy Assessment

### 5.1 Wrapper Approach (Low Confidence)
**Feasibility:** 🟡 Possible but not recommended

**Analysis:**
- MT7927 likely uses NDIS 6.x or 7.x (modern)
- Modern NDIS drivers have deep Windows kernel dependencies
- Binary wrapper would require extensive shim implementation
- High risk of instability and security issues

**Recommendation:** Use only for early prototyping; do not pursue for production.

### 5.2 Reimplementation Approach (High Confidence)
**Feasibility:** 🟢 Recommended

**Analysis:**
- MediaTek has existing Linux support (mt76 driver family)
- MT7921, MT7922 are similar architectures
- Community knowledge available
- Can leverage existing cfg80211/mac80211 Linux Wi-Fi stack
- Better long-term maintainability

**Challenges:**
- Significant development effort (6-12 months for full feature parity)
- Requires detailed register/firmware interface knowledge
- Wi-Fi 7 features may lack kernel API support (cutting edge)

**Recommendation:** Primary approach for production.

### 5.3 Passthrough Approach (Fallback)
**Feasibility:** 🟢 Viable fallback

**Analysis:**
- VFIO/QEMU passthrough is well-supported
- Can run Windows VM with vendor driver
- Good for testing and comparison

**Use Cases:**
- Development reference (compare against vendor driver)
- Temporary solution while native driver is developed
- Fallback for users who need immediate functionality

---

## 6. Risk Assessment

### 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Insufficient documentation | High | High | Leverage mt76 driver, community forums |
| Proprietary firmware protocol | Medium | High | Reverse engineer, contact MediaTek |
| Hardware unavailable for testing | Low | Critical | Acquire multiple units, use USB variant |
| Kernel API changes (Wi-Fi 7) | Medium | Medium | Target stable kernel APIs first |
| DMA/IOMMU issues | Low | High | Extensive testing, hardware debugging |

### 6.2 Legal Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| EULA prohibits reverse engineering | Medium | High | Review EULA, seek legal counsel |
| Firmware redistribution issues | Medium | Medium | Extract from Windows driver, document source |
| Patent infringement (Wi-Fi 7) | Low | Critical | Implement using public specs only |
| Trademark issues | Low | Low | Avoid MediaTek branding in code |

### 6.3 Timeline Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Analysis takes longer than expected | High | Medium | Allocate buffer time, phased approach |
| Hardware delays | Medium | Medium | Order early, have backup devices |
| Kernel API instability | Low | Medium | Target LTS kernels |
| Developer availability | Medium | High | Document thoroughly, modular design |

---

## 7. Success Criteria

### 7.1 Analysis Phase Success (Week 4)
- [ ] Windows driver model identified (NDIS version)
- [ ] PCI IDs extracted and verified
- [ ] Major function entry points mapped
- [ ] Register access patterns documented
- [ ] Firmware loading mechanism understood
- [ ] Conversion strategy selected with confidence score

### 7.2 Prototype Phase Success (Week 10)
- [ ] Linux kernel module loads without errors
- [ ] Device recognized by kernel (PCI enumeration)
- [ ] Basic register read/write functional
- [ ] Firmware loads successfully
- [ ] Device responds to basic commands

### 7.3 MVP Phase Success (Week 18)
- [ ] Scan for networks functional
- [ ] Association with open network successful
- [ ] WPA2/WPA3 authentication working
- [ ] Basic data transfer (TCP/IP) functional
- [ ] Stable for 1+ hours of operation

### 7.4 Production Phase Success (Week 30)
- [ ] Feature parity with vendor driver (key features)
- [ ] Stable for 24+ hours continuous operation
- [ ] Performance within 80% of vendor driver
- [ ] DKMS package builds on major distros
- [ ] Passes security audit
- [ ] Documentation complete

---

## 8. Resource Requirements

### 8.1 Personnel
- **Lead Driver Developer:** 1 FTE (kernel experience, Wi-Fi stack knowledge)
- **Reverse Engineer:** 0.5 FTE (Ghidra/IDA expertise)
- **QA/Test Engineer:** 0.5 FTE (hardware testing, automation)
- **Legal Counsel:** As needed (EULA review, compliance)

### 8.2 Hardware Budget
- MT7927 adapters: $50 × 3 = $150
- Test systems: $500-1000 (if new hardware needed)
- Wi-Fi 6E router: $200-300
- Misc tools/cables: $100
- **Total:** ~$1,000-1,500

### 8.3 Software Tools
- Ghidra: Free (open source)
- IDA Pro: $1,800+ (optional)
- Windows licenses: $200 (for VMs)
- **Total:** $200-2,000

### 8.4 Time Investment
- Analysis: 4 weeks × 40 hours = 160 hours
- Prototype: 6 weeks × 40 hours = 240 hours
- MVP: 8 weeks × 40 hours = 320 hours
- Production: 12 weeks × 40 hours = 480 hours
- **Total:** ~1,200 hours (~7 months at 1 FTE)

---

## 9. Recommended Action Plan

### Immediate Next Steps (Week 1)
1. **Acquire Hardware:**
   - Order MT7927 PCIe adapter (TP-Link TXE75E)
   - Verify PCI IDs match expectations
   - Test on Linux (current status: no driver)

2. **Acquire Software:**
   - Download latest Windows driver from TP-Link
   - Extract driver files (.sys, .inf, firmware)
   - Set up Ghidra analysis environment

3. **Legal Review:**
   - Review TP-Link driver EULA
   - Document any redistribution restrictions
   - Consult legal if reverse engineering is prohibited

4. **Community Research:**
   - Check mt76 mailing list for MT7927 mentions
   - Search for existing reverse engineering efforts
   - Contact MediaTek for open source support (unlikely but worth trying)

### Analysis Phase (Week 2-4)
1. Run full static analysis (see Section 2.3)
2. Set up Windows VM with PCIe passthrough
3. Perform runtime tracing and protocol analysis
4. Generate analyzer output JSON (see ANALYZER-SCHEMA.md)
5. Present findings and select conversion strategy

### Decision Point (End of Week 4)
Based on analysis results:
- **If sufficient documentation:** Proceed to reimplementation
- **If moderate documentation:** Prototype wrapper + reimplementation
- **If insufficient documentation:** Escalate for additional research/resources

---

## 10. Conclusion

The MT7927 driver conversion is a challenging but achievable project. Key success factors:

1. **Leverage Existing Work:** Use mt76 driver as reference
2. **Phased Approach:** Don't try to implement everything at once
3. **Community Engagement:** MediaTek may have unpublished docs
4. **Safety First:** Prioritize reimplementation over binary reuse
5. **Thorough Testing:** Wi-Fi drivers are critical for user experience

**Overall Feasibility:** ✅ **PROCEED** with recommended staged approach.

---

## Appendix A: Related Linux Drivers

### MT76 Driver Family (MediaTek)
- **MT7921:** Wi-Fi 6 (802.11ax), very similar architecture
- **MT7922:** Wi-Fi 6E, closest sibling to MT7927
- **MT7615:** Older Wi-Fi 5, different but related
- **Repository:** https://github.com/torvalds/linux/tree/master/drivers/net/wireless/mediatek/mt76

### Reference Architecture
```
mt76 (core)
  ├── mt7921 (chipset-specific)
  │   ├── pci.c (PCIe interface)
  │   ├── mac.c (MAC layer)
  │   ├── main.c (cfg80211 interface)
  │   └── dma.c (DMA operations)
  └── mt7927 (to be created)
      └── ... (similar structure)
```

---

## Appendix B: Key References

### Technical Documentation
- IEEE 802.11be specification (Wi-Fi 7)
- IEEE 802.11ax specification (Wi-Fi 6E)
- Linux Wireless Wiki: https://wireless.wiki.kernel.org/
- Linux Device Drivers (LDD3): O'Reilly book

### Community Resources
- Linux Wireless Mailing List: linux-wireless@vger.kernel.org
- MediaTek Linux Open Source: https://www.mediatek.com/
- LinuxQuestions.org forums

### Tools Documentation
- Ghidra Documentation: https://ghidra-sre.org/
- Linux Kernel Documentation: https://www.kernel.org/doc/html/latest/

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Author:** Driver Conversion Framework Team  
**Review Status:** Draft - Pending hardware acquisition and legal review

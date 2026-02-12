# MT7927 Operational Requirements Evaluation

## Top-level summary
- The repository currently contains scaffolding (schemas, inventory, tooling) but no MT7927-specific host driver sources, register maps, firmware blobs, or mac80211 integration code. All operational pieces are missing.
- Making the driver functional requires end-to-end bring-up: PCIe/WFDMA initialization, firmware loading and MCU command handling, mac80211/mt76 integration, PHY calibration, power management, and validation against real hardware and firmware.
- Major blockers are the absence of register/bitfield definitions, unknown firmware command/event formats, missing firmware binaries, and lack of hardware traces (lspci/dmesg) to confirm BAR layout and interrupts.

## Dependency-ordered checklist
1. [ ] Collect MT7927 firmware blobs (ROM patch, RAM/WM image, Bluetooth coexistence if applicable) from Windows package or TP-Link OEM source; document filenames and expected load order.
2. [ ] Capture hardware enumeration artifacts (lspci -vv, setpci, dmesg, ACPI tables) to confirm PCI IDs, BAR sizes, and MSI/MSI-X capabilities.
3. [ ] Reverse-engineer and document PCIe BAR layout, WFDMA/TOP register maps, interrupt controller registers, reset and power domain controls.
4. [ ] Implement firmware loader: request_firmware paths, ROM-patch download, RAM firmware download, patch status polling, and MCU handshake/feature negotiation.
5. [ ] Define MCU host interface (command/event IDs, mailbox/CCIF/HIF queues), DMA descriptor formats, and ring setup (TX/RX + event rings).
6. [ ] Wire up mac80211/mt76 integration (hw caps, interface combinations, mac80211 ops, rate control hookup, TX/RX data path).
7. [ ] Implement PHY initialization and calibration flows (DPD/LO/RC calibrations, channel/band setup for 2.4/5/6 GHz, EHT/HE/VHT/HT capability negotiation).
8. [ ] Add power management (ASPM, runtime PM, wowlan/suspend-resume), clock gating, and reset sequencing.
9. [ ] Add observability (debugfs, tracing, error reporting) and module parameters for tuning.
10. [ ] Validate on hardware: PCIe enumeration, firmware boot, association, throughput, power states, coexistence, and regression tests.

## Detailed requirements by domain

### 1. PCIe Bring-Up Requirements
- Missing BAR mappings: need BAR0/BAR1 layout, mapping of WFDMA/TOP/MCU register windows; confirm endianness and access width.
- Missing register definitions: host CSR, WFDMA0/1 configuration, interrupt status/enable registers, reset and clock control blocks, AXI/PCIe glue logic.
- Missing interrupt controller logic: MSI/MSI-X setup, WHISR/WHEISR equivalents, interrupt aggregation/ack flow, mitigation and NAPI budget integration.
- Missing DMA ring initialization: descriptor formats, doorbell registers, DMA engine enable bits, ring size limits, tx/rx queue to AC mapping.
- Missing reset sequences: WFSYS/WMCU reset asserts/deasserts, SER (soft error recovery), PDMA/WFDMA reset ordering, device-level PERST handling.
- Missing power-on sequences: top clock enable, PCIe link training dependencies, host-to-MCU readiness handshakes, download-mode entry if required.

### 2. Firmware Requirements
- Required firmware blobs: ROM patch, RAM firmware (N9/WM), possibly Wi-Fi/Bluetooth coexistence binaries; filenames and checksums unknown.
- Expected firmware load order: need confirmed sequence (ROM patch → patch status poll → RAM firmware → feature negotiation); watchdog/retry handling not defined.
- MCU communication requirements: command/event IDs, mailbox queue indices, event routing, timeout and reset policies, capability exchange.
- Patch RAM vs ROM patch handling: criteria for skipping/forcing ROM patch, OTP/efuse feature toggles, secure boot/version checks.
- Missing firmware loader code: request_firmware paths, storage in /lib/firmware/mediatek/, download chunking, DMA-to-IMEM/DMEM offsets.

### 3. MAC Layer Requirements
- Missing mac80211 ops: start/stop, add_interface/remove_interface, config, bss_info_changed, hw_scan, remain-on-channel, channel switch, ampdu actions.
- Missing hardware capability tables: supported bands (2.4/5/6 GHz), EHT/HE/VHT/HT capabilities, NSS/chain limits, interface combinations, cipher suites, offload flags.
- Missing rate control integration: hookup to mt76 rate control (rc) or minstrel fallback, per-phy rc tables, firmware-assisted rate reporting parsing.
- Missing TX/RX path implementation: sk_buff to WFDMA descriptor mapping, tx status reporting, rx status/radiotap population, encryption offload handling.

### 4. PHY Layer Requirements
- Missing calibration routines: DPD/LO/RC calibrations, temperature compensation, TSSI, power tables; MCU command flows unknown.
- Missing band/mode support: 160 MHz/EHT support for 6 GHz, DFS handling, TPC, SAR/geo-power constraints, multi-phy/DBDC behavior.
- Missing channel configuration logic: set_channel sequencing, BBP/AGC configuration, channel/bandwidth switch timing, PHY error counters.

### 5. DMA + Queueing Requirements
- TX ring setup: AC0-AC3, mgmt, MCU command/event rings; ring sizes, thresholds, refill policy, doorbell semantics, QoS-to-ring mapping.
- RX ring setup: data/event rings, rx buffer allocation strategy, page recycling, RX aggregation offload handling, scatter-gather support.
- Interrupt-driven completion handling: WFDMA interrupt sources, per-ring IRQ masks, NAPI scheduling, watchdogs for stalled rings.
- Buffer allocation strategy: coherent vs streaming DMA, cache management, headroom/tailroom requirements for firmware headers, skbuff lifetime rules.

### 6. Register Map Requirements
- Missing register addresses: WFDMA host registers, MCU shared memory windows, interrupt status/enable blocks, reset/clock control, efuse/OTP access, thermal sensors.
- Missing bitfields: DMA enable bits, interrupt masks/acks, SER controls, power domain gates, feature toggles, L1SS/ASPM controls.
- Missing masks/shifts: descriptor field offsets, packet ID, token management, tx/rx byte counts, error causes.
- Missing initialization sequences: power/clock bring-up order, WFDMA enable, interrupt unmasking, MCU ready polling, SER init.

### 7. Power Management Requirements
- Suspend/resume: firmware suspend commands, wake reason reporting, reconfiguring rings and beacons after resume, reloading firmware if needed.
- PCIe ASPM: L0s/L1/L1SS policy, latency tolerance reporting, PME handling, link training retry logic.
- Clock gating: per-block clock enables, dynamic gating policies, low-power idle state, wake sources.
- Reset domains: WFSYS/WMCU/DMA reset coordination, error recovery flows, isolation of BT coex blocks if present.

### 8. Debug + Logging Requirements
- Debugfs entries: firmware state, WFDMA ring dumps, interrupt counters, EEPROM/efuse dumps, calibration status, firmware log drains.
- Tracing hooks: tracepoints for tx/rx submission/completion, firmware commands/events, reset/power transitions.
- Error reporting: firmware assert capture, SER reasons, DMA error decoding, firmware crash dump retrieval, rate control anomalies.

### 9. Build + Integration Requirements
- Kconfig entries: new mt76 subdriver entry (MT7927), firmware file names, dependency selection (MAC80211, MTD if needed), experimental gating.
- Makefile entries: object list for MT7927 module, reuse of shared mt76 code, inclusion of PCI support and MCU message handlers.
- Module parameters: fw path overrides, debug level, disable_aspm, skip_rom_patch, force_wed/disable_wed toggles.
- Dependencies on mt76 libraries: reuse common WFDMA/MCU helpers, mt76-connac3 patterns, tx/rx/status helpers, tracing infrastructure.

### 10. Validation Requirements
- Hardware tests: PCIe enumeration (lspci, setpci), MSI/MSI-X firing, BAR access, WFDMA traffic with firmware up, SER/recovery drills.
- Firmware tests: ROM patch + RAM firmware load success, command/event round-trip, beaconing and association, rate control sanity.
- mac80211 tests: cfg80211 registration, scan/assoc, AP/STA/monitor modes, throughput, aggregation, AMSDU/A-MPDU, QoS mapping.
- PCIe enumeration tests: hot reset handling, surprise removal tolerance, ASPM transitions, link retrain robustness.

## Critical path (must be implemented first)
- Acquire and load correct firmware blobs (ROM patch + RAM firmware) and confirm MCU handshake.
- Reverse-engineer PCIe BAR layout, WFDMA registers, and interrupt controller to enable basic DMA/IRQ.
- Implement DMA rings (TX/RX + command/event) and MCU command transport to move data.
- Bring up mac80211 registration with minimal caps and basic TX/RX status path.
- Implement minimal power/reset sequencing to survive firmware reloads and recovery.

## Blocked on reverse-engineering
- Exact register map (addresses/bitfields) for WFDMA, interrupt controller, reset/clock domains, and efuse/OTP access.
- Firmware command/event IDs, payload formats, and required sequencing for calibration and configuration.
- DMA descriptor formats and token management rules unique to MT7927 generation.
- Calibration flows (DPD/LO/TSSI) and per-band power table formats.
- Secure boot/ROM patch validation rules and any anti-rollback/version gating.

## Safe to stub (initial bring-up)
- Advanced debugfs and tracing hooks (can add after basic data path works).
- Optimized rate control (can start with conservative defaults or firmware-driven RC).
- Full power management (ASPM/clock gating) beyond basic link up; can force ASPM off initially.
- WoWLAN and coex fine-tuning; basic STA/AP without coex optimizations first.

## Requires hardware access
- Validating PCIe link training, MSI/MSI-X delivery, and BAR decode.
- Running firmware load + MCU handshake, observing firmware logs/asserts.
- Executing calibration routines and verifying RF performance across bands.
- Throughput, roaming, and stability testing under traffic and thermal variation.
- Suspend/resume, ASPM, and recovery testing under real platform firmware/BIOS.

## Requires firmware extraction
- ROM patch binary specific to MT7927 (likely `mt7927_rom_patch.bin` or vendor-specific name).
- Main RAM/Wi-Fi firmware image (e.g., `mt7927_WM.bin`/`WIFI_RAM_CODE` equivalent).
- Coexistence/BT or secondary firmware components if bundled.
- Version metadata (build ID, feature flags) from Windows INF/CAB to drive compatibility checks.

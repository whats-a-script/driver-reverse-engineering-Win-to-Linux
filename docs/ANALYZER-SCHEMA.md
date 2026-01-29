# Driver Analyzer Data Schema

This document defines the JSON Schema for the output of the Driver Analyzer component. The analyzer produces structured metadata about Windows drivers to enable automated conversion strategy selection and guided reimplementation.

---

## Schema Version

**Current Version:** 1.0.0  
**Schema ID:** `https://github.com/whats-a-script/TP-link-wifi-MT7927-reverse-engineer/schemas/analyzer-output.json`

---

## JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/whats-a-script/TP-link-wifi-MT7927-reverse-engineer/schemas/analyzer-output-v1.json",
  "title": "Driver Analyzer Output Schema",
  "description": "Structured output from Windows driver binary analysis",
  "type": "object",
  "required": [
    "schema_version",
    "analysis_metadata",
    "driver_info",
    "driver_classification",
    "conversion_strategies"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "description": "Version of this schema (semver)",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
      "example": "1.0.0"
    },
    "analysis_metadata": {
      "type": "object",
      "description": "Metadata about the analysis process",
      "required": ["timestamp", "analyzer_version", "source_file"],
      "properties": {
        "timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "ISO 8601 timestamp of analysis"
        },
        "analyzer_version": {
          "type": "string",
          "description": "Version of the analyzer tool"
        },
        "source_file": {
          "type": "string",
          "description": "Path to the analyzed driver file"
        },
        "analysis_duration_seconds": {
          "type": "number",
          "description": "Time taken to complete analysis"
        },
        "tools_used": {
          "type": "array",
          "description": "List of tools used in analysis",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "driver_info": {
      "type": "object",
      "description": "Basic driver information",
      "required": ["file_name", "file_size", "file_hash"],
      "properties": {
        "file_name": {
          "type": "string",
          "description": "Name of the driver file"
        },
        "file_size": {
          "type": "integer",
          "description": "Size of the driver file in bytes"
        },
        "file_hash": {
          "type": "object",
          "description": "Cryptographic hashes of the file",
          "properties": {
            "md5": { "type": "string" },
            "sha1": { "type": "string" },
            "sha256": { "type": "string" }
          }
        },
        "pe_info": {
          "type": "object",
          "description": "PE (Portable Executable) file information",
          "properties": {
            "machine_type": {
              "type": "string",
              "enum": ["x86", "x64", "ARM", "ARM64"],
              "description": "Target architecture"
            },
            "timestamp": {
              "type": "string",
              "format": "date-time",
              "description": "PE compilation timestamp"
            },
            "subsystem": {
              "type": "string",
              "description": "PE subsystem (typically 'Native' for drivers)"
            },
            "linker_version": {
              "type": "string",
              "description": "Linker version string"
            }
          }
        },
        "version_info": {
          "type": "object",
          "description": "Driver version information",
          "properties": {
            "file_version": { "type": "string" },
            "product_version": { "type": "string" },
            "company_name": { "type": "string" },
            "product_name": { "type": "string" },
            "file_description": { "type": "string" },
            "copyright": { "type": "string" },
            "original_filename": { "type": "string" }
          }
        }
      }
    },
    "driver_classification": {
      "type": "object",
      "description": "Driver model and type classification",
      "required": ["driver_model", "driver_type", "confidence"],
      "properties": {
        "driver_model": {
          "type": "string",
          "enum": [
            "WDM",
            "WDF_KMDF",
            "WDF_UMDF",
            "NDIS",
            "NDIS_MINIPORT",
            "NDIS_FILTER",
            "NDIS_PROTOCOL",
            "StorPort",
            "SCSI_Miniport",
            "Unknown"
          ],
          "description": "Windows driver model"
        },
        "driver_type": {
          "type": "string",
          "enum": [
            "Network",
            "Storage",
            "Display",
            "USB",
            "Audio",
            "HID",
            "Printer",
            "Camera",
            "Bluetooth",
            "Other"
          ],
          "description": "Device class/type"
        },
        "confidence": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Confidence score for classification (0.0-1.0)"
        },
        "ndis_version": {
          "type": "string",
          "description": "NDIS version if applicable (e.g., '6.30', '6.83')",
          "pattern": "^[0-9]+\\.[0-9]+$"
        },
        "wdf_version": {
          "type": "string",
          "description": "WDF version if applicable",
          "pattern": "^[0-9]+\\.[0-9]+$"
        },
        "is_filter_driver": {
          "type": "boolean",
          "description": "Whether this is a filter driver"
        },
        "evidence": {
          "type": "array",
          "description": "Evidence for classification decision",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "hardware_interfaces": {
      "type": "object",
      "description": "Hardware interface information",
      "properties": {
        "bus_types": {
          "type": "array",
          "description": "Supported bus types",
          "items": {
            "type": "string",
            "enum": ["PCI", "PCIe", "USB", "SDIO", "Bluetooth", "Other"]
          }
        },
        "pci_ids": {
          "type": "array",
          "description": "PCI/PCIe device identifiers",
          "items": {
            "type": "object",
            "properties": {
              "vendor_id": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]{4}$",
                "description": "PCI vendor ID (e.g., '0x14c3')"
              },
              "device_id": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]{4}$",
                "description": "PCI device ID"
              },
              "subsystem_vendor_id": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]{4}$",
                "description": "PCI subsystem vendor ID"
              },
              "subsystem_device_id": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]{4}$",
                "description": "PCI subsystem device ID"
              },
              "revision": {
                "type": "string",
                "description": "Device revision"
              }
            }
          }
        },
        "usb_ids": {
          "type": "array",
          "description": "USB device identifiers",
          "items": {
            "type": "object",
            "properties": {
              "vendor_id": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]{4}$",
                "description": "USB vendor ID"
              },
              "product_id": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]{4}$",
                "description": "USB product ID"
              },
              "device_class": {
                "type": "string",
                "description": "USB device class"
              },
              "interface_class": {
                "type": "string",
                "description": "USB interface class"
              }
            }
          }
        },
        "resources": {
          "type": "object",
          "description": "Hardware resources used",
          "properties": {
            "uses_interrupts": { "type": "boolean" },
            "uses_dma": { "type": "boolean" },
            "uses_mmio": { "type": "boolean" },
            "uses_port_io": { "type": "boolean" },
            "num_bars": {
              "type": "integer",
              "description": "Number of PCI BARs used"
            }
          }
        }
      }
    },
    "exported_symbols": {
      "type": "object",
      "description": "Exported functions and symbols",
      "properties": {
        "entry_points": {
          "type": "object",
          "description": "Key driver entry points",
          "properties": {
            "DriverEntry": {
              "type": "object",
              "properties": {
                "address": { "type": "string" },
                "signature": { "type": "string" }
              }
            },
            "DriverUnload": {
              "type": "object",
              "properties": {
                "address": { "type": "string" },
                "signature": { "type": "string" }
              }
            },
            "AddDevice": {
              "type": "object",
              "properties": {
                "address": { "type": "string" },
                "signature": { "type": "string" }
              }
            }
          }
        },
        "exported_functions": {
          "type": "array",
          "description": "List of exported functions",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "address": { "type": "string" },
              "ordinal": { "type": "integer" }
            }
          }
        }
      }
    },
    "imported_symbols": {
      "type": "object",
      "description": "Imported functions and dependencies",
      "properties": {
        "kernel_imports": {
          "type": "array",
          "description": "Functions imported from kernel modules",
          "items": {
            "type": "object",
            "properties": {
              "module": {
                "type": "string",
                "description": "Source module (e.g., 'ntoskrnl.exe', 'ndis.sys')"
              },
              "function": {
                "type": "string",
                "description": "Imported function name"
              }
            }
          }
        },
        "dependencies": {
          "type": "array",
          "description": "List of dependent modules",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "ioctls": {
      "type": "object",
      "description": "IOCTL codes and handlers",
      "properties": {
        "discovered_codes": {
          "type": "array",
          "description": "List of IOCTL codes found",
          "items": {
            "type": "object",
            "properties": {
              "code": {
                "type": "string",
                "pattern": "^0x[0-9A-Fa-f]+$",
                "description": "IOCTL control code"
              },
              "name": {
                "type": "string",
                "description": "Symbolic name if known"
              },
              "handler_address": {
                "type": "string",
                "description": "Address of handler function"
              },
              "description": {
                "type": "string",
                "description": "Purpose of this IOCTL"
              }
            }
          }
        },
        "dispatch_routine": {
          "type": "string",
          "description": "Address of IOCTL dispatch routine"
        }
      }
    },
    "firmware": {
      "type": "object",
      "description": "Firmware loading information",
      "properties": {
        "requires_firmware": {
          "type": "boolean",
          "description": "Whether driver requires firmware"
        },
        "firmware_files": {
          "type": "array",
          "description": "List of firmware files",
          "items": {
            "type": "object",
            "properties": {
              "filename": { "type": "string" },
              "hash": { "type": "string" },
              "size": { "type": "integer" },
              "load_address": { "type": "string" },
              "format": {
                "type": "string",
                "description": "Firmware file format if known"
              }
            }
          }
        },
        "loading_mechanism": {
          "type": "string",
          "description": "How firmware is loaded (e.g., 'DMA', 'MMIO writes')"
        }
      }
    },
    "register_map": {
      "type": "object",
      "description": "Hardware register access patterns",
      "properties": {
        "mmio_regions": {
          "type": "array",
          "description": "Memory-mapped I/O regions",
          "items": {
            "type": "object",
            "properties": {
              "bar_index": { "type": "integer" },
              "offset": { "type": "string" },
              "size": { "type": "integer" },
              "purpose": { "type": "string" }
            }
          }
        },
        "known_registers": {
          "type": "array",
          "description": "Known register offsets and purposes",
          "items": {
            "type": "object",
            "properties": {
              "offset": { "type": "string" },
              "name": { "type": "string" },
              "size": {
                "type": "integer",
                "description": "Register size in bytes"
              },
              "access": {
                "type": "string",
                "enum": ["RO", "WO", "RW"],
                "description": "Read-only, Write-only, or Read-Write"
              },
              "description": { "type": "string" }
            }
          }
        }
      }
    },
    "state_machine": {
      "type": "object",
      "description": "Driver state machine information",
      "properties": {
        "power_states": {
          "type": "array",
          "description": "Supported power states",
          "items": {
            "type": "string"
          }
        },
        "initialization_sequence": {
          "type": "array",
          "description": "Sequence of initialization steps",
          "items": {
            "type": "object",
            "properties": {
              "step": { "type": "integer" },
              "description": { "type": "string" },
              "function": { "type": "string" }
            }
          }
        },
        "operational_states": {
          "type": "array",
          "description": "Runtime operational states",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "conversion_strategies": {
      "type": "object",
      "description": "Recommended conversion strategies",
      "required": ["recommended_strategy", "strategies"],
      "properties": {
        "recommended_strategy": {
          "type": "string",
          "enum": ["wrapper", "reimplementation", "passthrough", "hybrid"],
          "description": "Primary recommended strategy"
        },
        "strategies": {
          "type": "array",
          "description": "List of possible strategies with scores",
          "items": {
            "type": "object",
            "required": ["name", "confidence", "rationale"],
            "properties": {
              "name": {
                "type": "string",
                "enum": ["wrapper", "reimplementation", "passthrough", "hybrid"]
              },
              "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence score (0.0-1.0)"
              },
              "feasibility": {
                "type": "string",
                "enum": ["high", "medium", "low"],
                "description": "Overall feasibility assessment"
              },
              "effort_estimate": {
                "type": "string",
                "enum": ["low", "medium", "high", "very_high"],
                "description": "Estimated development effort"
              },
              "risk_level": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "description": "Technical and legal risk level"
              },
              "rationale": {
                "type": "string",
                "description": "Explanation for this strategy assessment"
              },
              "pros": {
                "type": "array",
                "items": { "type": "string" }
              },
              "cons": {
                "type": "array",
                "items": { "type": "string" }
              },
              "requirements": {
                "type": "array",
                "description": "Technical requirements for this strategy",
                "items": { "type": "string" }
              }
            }
          }
        }
      }
    },
    "security_analysis": {
      "type": "object",
      "description": "Security-related findings",
      "properties": {
        "is_signed": {
          "type": "boolean",
          "description": "Whether driver binary is digitally signed"
        },
        "signer": {
          "type": "string",
          "description": "Certificate signer if signed"
        },
        "potential_issues": {
          "type": "array",
          "description": "List of potential security concerns",
          "items": {
            "type": "object",
            "properties": {
              "severity": {
                "type": "string",
                "enum": ["info", "low", "medium", "high", "critical"]
              },
              "description": { "type": "string" },
              "location": { "type": "string" }
            }
          }
        },
        "uses_unsafe_apis": {
          "type": "boolean",
          "description": "Whether driver uses known unsafe APIs"
        }
      }
    },
    "legal_flags": {
      "type": "object",
      "description": "Legal and compliance flags",
      "properties": {
        "eula_present": {
          "type": "boolean",
          "description": "Whether EULA was found"
        },
        "redistribution_allowed": {
          "type": "boolean",
          "description": "Whether redistribution appears to be allowed"
        },
        "reverse_engineering_prohibited": {
          "type": "boolean",
          "description": "Whether EULA prohibits reverse engineering"
        },
        "requires_legal_review": {
          "type": "boolean",
          "description": "Whether legal counsel review is recommended"
        },
        "notes": {
          "type": "string",
          "description": "Additional legal notes"
        }
      }
    },
    "additional_files": {
      "type": "array",
      "description": "Related files found in driver package",
      "items": {
        "type": "object",
        "properties": {
          "filename": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["INF", "CAT", "DLL", "SYS", "EXE", "DAT", "Other"]
          },
          "purpose": { "type": "string" },
          "hash": { "type": "string" }
        }
      }
    },
    "notes": {
      "type": "string",
      "description": "Additional analysis notes"
    },
    "errors": {
      "type": "array",
      "description": "Errors encountered during analysis",
      "items": {
        "type": "object",
        "properties": {
          "severity": {
            "type": "string",
            "enum": ["warning", "error", "critical"]
          },
          "message": { "type": "string" },
          "context": { "type": "string" }
        }
      }
    }
  }
}
```

---

## Example Output: MT7927 Driver

Below is an example of what the analyzer output might look like for the MediaTek MT7927 driver:

```json
{
  "schema_version": "1.0.0",
  "analysis_metadata": {
    "timestamp": "2026-01-29T12:00:00Z",
    "analyzer_version": "0.1.0",
    "source_file": "/path/to/mt7927e.sys",
    "analysis_duration_seconds": 45.2,
    "tools_used": ["ghidra-10.4", "pefile", "yara"]
  },
  "driver_info": {
    "file_name": "mt7927e.sys",
    "file_size": 2458624,
    "file_hash": {
      "md5": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
      "sha1": "1234567890abcdef1234567890abcdef12345678",
      "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    },
    "pe_info": {
      "machine_type": "x64",
      "timestamp": "2025-11-15T08:30:00Z",
      "subsystem": "Native",
      "linker_version": "14.35"
    },
    "version_info": {
      "file_version": "3.2.8.0",
      "product_version": "3.2.8.0",
      "company_name": "MediaTek Inc.",
      "product_name": "MediaTek WiFi 7 Wireless LAN Card",
      "file_description": "MediaTek WiFi 7 802.11be Wireless LAN Adapter",
      "copyright": "Copyright (C) 2025 MediaTek Inc.",
      "original_filename": "mt7927e.sys"
    }
  },
  "driver_classification": {
    "driver_model": "NDIS_MINIPORT",
    "driver_type": "Network",
    "confidence": 0.98,
    "ndis_version": "6.85",
    "is_filter_driver": false,
    "evidence": [
      "Imports NdisMRegisterMiniportDriver",
      "Exports NdisDriverEntry",
      "References NDIS 6.85 APIs",
      "INF file declares Class=Net"
    ]
  },
  "hardware_interfaces": {
    "bus_types": ["PCIe"],
    "pci_ids": [
      {
        "vendor_id": "0x14c3",
        "device_id": "0x7927",
        "subsystem_vendor_id": "0x14c3",
        "subsystem_device_id": "0x7927",
        "revision": "0x00"
      }
    ],
    "resources": {
      "uses_interrupts": true,
      "uses_dma": true,
      "uses_mmio": true,
      "uses_port_io": false,
      "num_bars": 1
    }
  },
  "exported_symbols": {
    "entry_points": {
      "DriverEntry": {
        "address": "0x1000",
        "signature": "NTSTATUS DriverEntry(PDRIVER_OBJECT, PUNICODE_STRING)"
      }
    },
    "exported_functions": [
      {
        "name": "NdisDriverEntry",
        "address": "0x1000",
        "ordinal": 1
      }
    ]
  },
  "imported_symbols": {
    "kernel_imports": [
      {
        "module": "ndis.sys",
        "function": "NdisMRegisterMiniportDriver"
      },
      {
        "module": "ndis.sys",
        "function": "NdisMAllocateSharedMemory"
      },
      {
        "module": "ntoskrnl.exe",
        "function": "IoAllocateWorkItem"
      }
    ],
    "dependencies": [
      "ndis.sys",
      "ntoskrnl.exe",
      "hal.dll"
    ]
  },
  "ioctls": {
    "discovered_codes": [
      {
        "code": "0x22C007",
        "name": "IOCTL_SET_CONFIG",
        "handler_address": "0x5A400",
        "description": "Set device configuration parameters"
      },
      {
        "code": "0x22C00B",
        "name": "IOCTL_GET_STATUS",
        "handler_address": "0x5A600",
        "description": "Query device status"
      }
    ],
    "dispatch_routine": "0x5A000"
  },
  "firmware": {
    "requires_firmware": true,
    "firmware_files": [
      {
        "filename": "MT7927_WIFI.bin",
        "hash": "fedcba0987654321fedcba0987654321",
        "size": 524288,
        "format": "Binary blob"
      }
    ],
    "loading_mechanism": "DMA to device memory"
  },
  "register_map": {
    "mmio_regions": [
      {
        "bar_index": 0,
        "offset": "0x0",
        "size": 65536,
        "purpose": "Device control registers"
      }
    ],
    "known_registers": [
      {
        "offset": "0x0000",
        "name": "CHIP_ID",
        "size": 4,
        "access": "RO",
        "description": "Chip identification register"
      },
      {
        "offset": "0x0100",
        "name": "INT_STATUS",
        "size": 4,
        "access": "RW",
        "description": "Interrupt status register"
      }
    ]
  },
  "state_machine": {
    "power_states": ["D0", "D3"],
    "initialization_sequence": [
      {
        "step": 1,
        "description": "Initialize PCIe BAR mappings",
        "function": "InitializeHardware"
      },
      {
        "step": 2,
        "description": "Load firmware",
        "function": "LoadFirmware"
      },
      {
        "step": 3,
        "description": "Configure MAC address",
        "function": "SetMacAddress"
      }
    ],
    "operational_states": ["Init", "Ready", "Scanning", "Connected", "Error"]
  },
  "conversion_strategies": {
    "recommended_strategy": "reimplementation",
    "strategies": [
      {
        "name": "reimplementation",
        "confidence": 0.85,
        "feasibility": "high",
        "effort_estimate": "high",
        "risk_level": "low",
        "rationale": "MediaTek has strong Linux support with mt76 driver family. MT7921/MT7922 provide excellent reference implementations. Reimplementation is safest long-term approach.",
        "pros": [
          "Best long-term maintainability",
          "Can leverage existing mt76 infrastructure",
          "Full kernel integration",
          "No legal/licensing concerns",
          "Community support available"
        ],
        "cons": [
          "6-12 month development timeline",
          "Requires WiFi 7 kernel API updates",
          "Significant testing required",
          "Performance optimization needed"
        ],
        "requirements": [
          "Linux kernel 6.1+ with cfg80211/mac80211",
          "Hardware test units",
          "WiFi 6E/7 test infrastructure",
          "Experienced WiFi driver developer"
        ]
      },
      {
        "name": "wrapper",
        "confidence": 0.40,
        "feasibility": "medium",
        "effort_estimate": "medium",
        "risk_level": "high",
        "rationale": "Modern NDIS 6.85 has deep Windows dependencies. Wrapper would require extensive shim implementation with uncertain stability and legal risk.",
        "pros": [
          "Faster initial prototype",
          "Can test hardware access patterns",
          "Useful for reverse engineering"
        ],
        "cons": [
          "High instability risk",
          "Security concerns (kernel binary)",
          "Legal EULA concerns",
          "Not suitable for production",
          "Maintenance burden"
        ],
        "requirements": [
          "NDIS shim layer",
          "Sandbox/isolation mechanism",
          "Legal clearance",
          "Windows VM for testing"
        ]
      },
      {
        "name": "passthrough",
        "confidence": 0.70,
        "feasibility": "high",
        "effort_estimate": "low",
        "risk_level": "medium",
        "rationale": "VFIO/QEMU passthrough is well-supported and can provide immediate functionality while native driver is developed.",
        "pros": [
          "Immediate functionality",
          "Full vendor driver features",
          "Good for development reference",
          "Low implementation effort"
        ],
        "cons": [
          "Requires VM overhead",
          "Not native performance",
          "User experience impact",
          "Not a long-term solution"
        ],
        "requirements": [
          "CPU with VT-d/IOMMU",
          "QEMU/KVM setup",
          "Windows license",
          "PCIe device passthrough config"
        ]
      }
    ]
  },
  "security_analysis": {
    "is_signed": true,
    "signer": "MediaTek Inc.",
    "potential_issues": [
      {
        "severity": "low",
        "description": "Driver uses legacy pool allocation APIs",
        "location": "Multiple locations"
      }
    ],
    "uses_unsafe_apis": false
  },
  "legal_flags": {
    "eula_present": true,
    "redistribution_allowed": false,
    "reverse_engineering_prohibited": true,
    "requires_legal_review": true,
    "notes": "EULA prohibits reverse engineering. Binary redistribution not explicitly allowed. Legal review required before proceeding with wrapper approach. Reimplementation from scratch is legally safer."
  },
  "additional_files": [
    {
      "filename": "mt7927e.inf",
      "type": "INF",
      "purpose": "Driver installation metadata",
      "hash": "abc123def456"
    },
    {
      "filename": "mt7927e.cat",
      "type": "CAT",
      "purpose": "Driver catalog signature",
      "hash": "def456abc123"
    }
  ],
  "notes": "Driver appears to be modern NDIS 6.85 implementation with WiFi 7 support. Strong similarity to MT7921/MT7922 suggests good prospects for reimplementation using mt76 framework. Recommend proceeding with reimplementation strategy.",
  "errors": []
}
```

---

## Usage Guidelines

### For Analyzer Tool Developers
1. Implement parsers for each section of the schema
2. Prioritize accuracy over completeness - mark unknown fields as null
3. Include confidence scores for machine-learning classifications
4. Log errors clearly in the `errors` array

### For Strategy Engine Developers
1. Use `driver_classification.confidence` to weight decisions
2. Prioritize `conversion_strategies.recommended_strategy`
3. Consider `legal_flags.requires_legal_review` before binary reuse
4. Factor `security_analysis` into risk assessment

### For GUI/CLI Developers
1. Present `conversion_strategies` in ranked order
2. Highlight legal and security warnings prominently
3. Allow users to override strategy selection with warnings
4. Export full JSON for debugging and auditing

---

## Schema Evolution

Future versions may add:
- Machine learning model metadata
- Dynamic analysis results (from Windows VM tracing)
- Protocol state machines
- Performance benchmarks
- Community knowledge base references

**Backward Compatibility:** Minor version bumps (1.x.0) will be backward compatible. Major version bumps (2.0.0) may break compatibility.

---

## Validation

Validate analyzer output using standard JSON Schema validators:

```bash
# Using Python
pip install jsonschema
jsonschema -i output.json analyzer-schema.json

# Using Node.js
npm install -g ajv-cli
ajv validate -s analyzer-schema.json -d output.json
```

---

## References

- [JSON Schema Specification](https://json-schema.org/)
- [Windows Driver Models](https://learn.microsoft.com/en-us/windows-hardware/drivers/)
- [Linux Kernel Driver API](https://www.kernel.org/doc/html/latest/)

---

**Schema Version:** 1.0.0  
**Last Updated:** January 2026  
**Maintainer:** Driver Conversion Framework Team

"""
Driver Classifier Module

Classifies Windows driver model (WDM, WDF, NDIS, etc.) based on imports and patterns.
"""

import logging
from enum import Enum
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class DriverModel(Enum):
    """Windows driver models."""
    WDM = "WDM"
    WDF_KMDF = "WDF_KMDF"
    WDF_UMDF = "WDF_UMDF"
    NDIS = "NDIS"
    NDIS_MINIPORT = "NDIS_MINIPORT"
    NDIS_FILTER = "NDIS_FILTER"
    NDIS_PROTOCOL = "NDIS_PROTOCOL"
    STORPORT = "StorPort"
    SCSI_MINIPORT = "SCSI_Miniport"
    UNKNOWN = "Unknown"


class DriverType(Enum):
    """Device class types."""
    NETWORK = "Network"
    STORAGE = "Storage"
    DISPLAY = "Display"
    USB = "USB"
    AUDIO = "Audio"
    HID = "HID"
    PRINTER = "Printer"
    CAMERA = "Camera"
    BLUETOOTH = "Bluetooth"
    OTHER = "Other"


class DriverClassifier:
    """Classifies Windows drivers based on imports and patterns."""
    
    # Key imports that indicate driver models
    NDIS_IMPORTS = [
        "NdisMRegisterMiniportDriver",
        "NdisRegisterProtocolDriver",
        "NdisFRegisterFilterDriver",
        "NdisMAllocateSharedMemory"
    ]
    
    WDF_IMPORTS = [
        "WdfDriverCreate",
        "WdfDeviceCreate",
        "WdfIoQueueCreate"
    ]
    
    WDM_IMPORTS = [
        "IoCreateDevice",
        "IoRegisterDeviceInterface",
        "IoAttachDeviceToDeviceStack"
    ]
    
    STORPORT_IMPORTS = [
        "StorPortInitialize",
        "StorPortGetDeviceBase"
    ]
    
    def __init__(self):
        pass
    
    def classify(self, imports: List[str], exports: List[str]) -> Tuple[DriverModel, float]:
        """
        Classify driver model based on imports and exports.
        
        Args:
            imports: List of imported function names
            exports: List of exported function names
        
        Returns:
            Tuple of (DriverModel, confidence_score)
        """
        scores = {}
        
        # Check for NDIS
        ndis_score = self._count_matches(imports, self.NDIS_IMPORTS)
        if ndis_score > 0:
            scores[DriverModel.NDIS_MINIPORT] = ndis_score / len(self.NDIS_IMPORTS)
        
        # Check for WDF
        wdf_score = self._count_matches(imports, self.WDF_IMPORTS)
        if wdf_score > 0:
            scores[DriverModel.WDF_KMDF] = wdf_score / len(self.WDF_IMPORTS)
        
        # Check for WDM
        wdm_score = self._count_matches(imports, self.WDM_IMPORTS)
        if wdm_score > 0:
            scores[DriverModel.WDM] = wdm_score / len(self.WDM_IMPORTS)
        
        # Check for StorPort
        storport_score = self._count_matches(imports, self.STORPORT_IMPORTS)
        if storport_score > 0:
            scores[DriverModel.STORPORT] = storport_score / len(self.STORPORT_IMPORTS)
        
        # Return highest scoring model
        if scores:
            best_model = max(scores.items(), key=lambda x: x[1])
            return best_model[0], best_model[1]
        else:
            return DriverModel.UNKNOWN, 0.0
    
    def classify_type(self, model: DriverModel, imports: List[str]) -> DriverType:
        """
        Classify device type based on driver model and imports.
        
        Args:
            model: Detected driver model
            imports: List of imported functions
        
        Returns:
            DriverType enum
        """
        # Network indicators
        if model in [DriverModel.NDIS, DriverModel.NDIS_MINIPORT]:
            return DriverType.NETWORK
        
        # Storage indicators
        if model in [DriverModel.STORPORT, DriverModel.SCSI_MINIPORT]:
            return DriverType.STORAGE
        
        # USB indicators
        if any("Usb" in imp for imp in imports):
            return DriverType.USB
        
        # Audio indicators
        if any("Audio" in imp or "Sound" in imp for imp in imports):
            return DriverType.AUDIO
        
        return DriverType.OTHER
    
    def _count_matches(self, imports: List[str], patterns: List[str]) -> int:
        """Count how many pattern imports are present."""
        matches = 0
        for pattern in patterns:
            if pattern in imports:
                matches += 1
        return matches
    
    def get_ndis_version(self, imports: List[str]) -> str:
        """
        Detect NDIS version from imports.
        
        Args:
            imports: List of imported functions
        
        Returns:
            NDIS version string (e.g., "6.30") or None
        """
        # TODO: Implement NDIS version detection based on API usage
        # NDIS 6.0+: NdisM* APIs
        # NDIS 6.20+: RSS APIs
        # NDIS 6.30+: VF APIs
        # NDIS 6.50+: RSC APIs
        # NDIS 6.85+: WiFi 7 APIs
        
        if any("NdisM" in imp for imp in imports):
            return "6.30"  # Placeholder
        
        return None

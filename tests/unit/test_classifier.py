"""
Unit tests for the driver classifier module.
"""

import pytest
from src.analyzer.classifier import DriverClassifier, DriverModel, DriverType


class TestDriverClassifier:
    """Test suite for DriverClassifier."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.classifier = DriverClassifier()
    
    def test_classify_ndis_driver(self):
        """Test NDIS driver classification."""
        imports = [
            "NdisMRegisterMiniportDriver",
            "NdisMAllocateSharedMemory",
            "NdisAllocateMemoryWithTagPriority"
        ]
        exports = []
        
        model, confidence = self.classifier.classify(imports, exports)
        
        assert model == DriverModel.NDIS_MINIPORT
        assert confidence > 0.0
    
    def test_classify_wdf_driver(self):
        """Test WDF driver classification."""
        imports = [
            "WdfDriverCreate",
            "WdfDeviceCreate",
            "WdfIoQueueCreate"
        ]
        exports = []
        
        model, confidence = self.classifier.classify(imports, exports)
        
        assert model == DriverModel.WDF_KMDF
        assert confidence > 0.0
    
    def test_classify_unknown_driver(self):
        """Test unknown driver classification."""
        imports = []
        exports = []
        
        model, confidence = self.classifier.classify(imports, exports)
        
        assert model == DriverModel.UNKNOWN
        assert confidence == 0.0
    
    def test_classify_type_network(self):
        """Test network device type classification."""
        device_type = self.classifier.classify_type(
            DriverModel.NDIS_MINIPORT,
            []
        )
        
        assert device_type == DriverType.NETWORK
    
    def test_classify_type_storage(self):
        """Test storage device type classification."""
        device_type = self.classifier.classify_type(
            DriverModel.STORPORT,
            []
        )
        
        assert device_type == DriverType.STORAGE
    
    def test_classify_type_usb(self):
        """Test USB device type classification."""
        imports = ["UsbBuildInterruptTransfer", "UsbSubmitUrb"]
        device_type = self.classifier.classify_type(
            DriverModel.WDF_KMDF,
            imports
        )
        
        assert device_type == DriverType.USB
    
    def test_get_ndis_version(self):
        """Test NDIS version detection."""
        imports = ["NdisMRegisterMiniportDriver"]
        
        version = self.classifier.get_ndis_version(imports)
        
        assert version is not None
        assert isinstance(version, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

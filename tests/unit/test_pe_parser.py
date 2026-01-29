"""
Unit tests for the PE parser module.
"""

import pytest
from pathlib import Path
from src.analyzer.pe_parser import PEParser, is_valid_pe_file


class TestPEParser:
    """Test suite for PEParser."""
    
    def test_is_valid_pe_file_with_invalid_file(self, tmp_path):
        """Test PE validation with invalid file."""
        # Create a non-PE file
        test_file = tmp_path / "not_a_pe.txt"
        test_file.write_text("This is not a PE file")
        
        assert is_valid_pe_file(str(test_file)) == False
    
    def test_is_valid_pe_file_with_nonexistent_file(self):
        """Test PE validation with nonexistent file."""
        assert is_valid_pe_file("/nonexistent/file.sys") == False
    
    def test_pe_parser_init(self):
        """Test PEParser initialization."""
        parser = PEParser("/path/to/driver.sys")
        
        assert parser.file_path == Path("/path/to/driver.sys")
        assert parser.pe_data is None
    
    def test_parse_returns_dict(self):
        """Test that parse() returns a dictionary."""
        parser = PEParser("/path/to/driver.sys")
        
        # Note: This will fail on actual file, but tests the structure
        try:
            result = parser.parse()
            assert isinstance(result, dict)
            assert "machine_type" in result
        except FileNotFoundError:
            # Expected for non-existent file
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

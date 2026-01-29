# Driver Analyzer - Core Component

This module analyzes Windows driver binaries and extracts structured metadata.

## Components

- `pe_parser.py` - PE/COFF format parser
- `classifier.py` - Driver model classifier (WDM/WDF/NDIS)
- `symbol_extractor.py` - Import/export extraction
- `ioctl_finder.py` - IOCTL code discovery
- `disasm_interface.py` - Ghidra/IDA automation

## Usage

```python
from analyzer import DriverAnalyzer

analyzer = DriverAnalyzer()
result = analyzer.analyze("driver.sys")
print(result.to_json())
```

## Output

See `docs/ANALYZER-SCHEMA.md` for the complete output schema.

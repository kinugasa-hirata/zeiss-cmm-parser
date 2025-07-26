# CMM Measurement Parser

[![PyPI version](https://badge.fury.io/py/cmm-measurement-parser.svg)](https://badge.fury.io/py/cmm-measurement-parser)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Professional Python package for parsing CMM (Coordinate Measuring Machine) measurement data from Japanese measurement reports, specifically Carl Zeiss CALYPSO format.

## Features

- ✅ **Parse Japanese CMM Reports**: Handles Japanese characters and measurement formats
- ✅ **Structured DataFrame Output**: Clean, analyzable pandas DataFrames
- ✅ **Automatic Tolerance Analysis**: PASS/FAIL determination with tolerance utilization
- ✅ **Excel Export**: Proper Japanese character encoding for Excel compatibility
- ✅ **Summary Statistics**: Grouped analysis by measurement element
- ✅ **Quality Control Ready**: Professional reporting for manufacturing QC

## Installation

```bash
pip install cmm-measurement-parser
```

## Quick Start

```python
import cmm_measurement_parser as cmp

# Parse your CMM measurement data
lines = your_text_data.split('\n')  # Your extracted CMM report text
df, summary = cmp.process_cmm_data(lines)

# Export results to Excel
cmp.export_to_excel(df, 'My_CMM_Analysis')

# View results
print(f"Parsed {len(df)} measurements from {len(summary)} elements")
print(f"Pass rate: {len(df[df['status'] == 'PASS']) / len(df) * 100:.1f}%")
```

## Usage Examples

### Basic Parsing

```python
import cmm_measurement_parser as cmp

# Simple parsing
df = cmp.parse_cmm_data(lines)

# Complete processing with summary
df, summary = cmp.process_cmm_data(lines)
```

### Advanced Usage

```python
# Using the class directly for more control
parser = cmp.CMMParser()
df = parser.parse_lines_to_dataframe(lines)
summary = parser.create_summary_by_element(df)
```

### Working with Results

```python
# Filter failed measurements
failed = df[df['status'] == 'FAIL']
print(f"Failed measurements: {len(failed)}")

# Analyze by element
element_summary = df.groupby('element_name')['status'].value_counts()

# Export different formats
cmp.export_to_excel(df, 'Detailed_Analysis')
cmp.export_to_excel(summary, 'Summary_Report')
```

## DataFrame Structure

The output DataFrame includes these columns:

| Column | Description |
|--------|-------------|
| `element_name` | Measurement element (ｄ-1, 円1, etc.) |
| `measurement_type` | Type of measurement (円(最小二乗法), etc.) |
| `coordinate_type` | X, Y, Z, or D coordinate |
| `measured_value` | Actual measured value |
| `reference_value` | Target/reference value |
| `deviation` | Difference from reference |
| `upper_tolerance` | Upper tolerance limit |
| `lower_tolerance` | Lower tolerance limit |
| `within_tolerance` | Boolean pass/fail |
| `status` | 'PASS' or 'FAIL' |
| `tolerance_utilization` | Percentage of tolerance used |

## Supported Formats

- **Carl Zeiss CALYPSO** measurement reports
- **Japanese measurement data** with proper character encoding
- **Coordinate measurements**: X, Y, Z coordinates and diameter (D) measurements
- **Multiple element types**: Circles (円), planes (平面), lines (線), dimensions (ｄ-)

## Requirements

- Python 3.7+
- pandas >= 1.0.0
- numpy >= 1.18.0  
- openpyxl >= 3.0.0 (for Excel export)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/shuhei-kinugasa/cmm-measurement-parser/issues) page.

## Author

Created by **shuhei** for professional CMM measurement analysis.
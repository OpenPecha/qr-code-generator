# qr_code_generator

`qr_code_generator` is a small Python package for generating rounded monochrome QR codes as PNG or SVG files. It is intentionally focused on one clean visual style instead of exposing a large preset system.

## Features
- Rounded QR modules with a monochrome palette.
- Rounded outer finder eyes and circular inner finder dots.
- Simple Python API for generating one QR at a time.
- CLI entry point for quick file generation.

## Requirements
- Python 3.9+

## Install

```bash
pip install -e .
```

For development tools:

```bash
pip install -e ".[dev]"
```

## Python usage

```python
from qr_code_generator import generate_qr

generate_qr(
    "https://example.com",
    "output/example.png",
)
```

You can also customize the basic size and print settings:

```python
from qr_code_generator import QRCodeStyle, generate_qr

style = QRCodeStyle(size_inches=2.5, dpi=300, border=4)
generate_qr("https://example.com", "output/example.svg", style=style)
```

## CLI usage

```bash
qr-code-generator "https://example.com" --output output/example.png
```

```bash
qr-code-generator "https://example.com" --output output/example.svg --format svg
```

## Package layout
- `src/qr_code_generator/generator.py`: core PNG and SVG generation logic.
- `src/qr_code_generator/cli.py`: command-line entry point.
- `tests/test_generator.py`: smoke tests for package import and file output.

## License

Licensed under the MIT License. See `LICENSE`.

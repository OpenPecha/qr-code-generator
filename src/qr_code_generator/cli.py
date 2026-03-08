from __future__ import annotations

import argparse
from pathlib import Path

from .generator import DEFAULT_STYLE, QRCodeStyle, generate_qr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a rounded monochrome QR code as PNG or SVG.",
    )
    parser.add_argument("data", help="Text or URL to encode in the QR code.")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path. Use .png or .svg, or pair with --format.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["png", "svg"],
        help="Output format. Defaults to the output file extension or png.",
    )
    parser.add_argument("--size-inches", type=float, default=DEFAULT_STYLE.size_inches)
    parser.add_argument("--dpi", type=int, default=DEFAULT_STYLE.dpi)
    parser.add_argument("--border", type=int, default=DEFAULT_STYLE.border)
    parser.add_argument(
        "--error-correction",
        choices=["L", "M", "Q", "H"],
        default=DEFAULT_STYLE.error_correction,
    )
    parser.add_argument(
        "--mask-pattern",
        type=int,
        default=DEFAULT_STYLE.mask_pattern,
        help="Optional QR mask pattern from 0 to 7.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    style = QRCodeStyle(
        size_inches=args.size_inches,
        dpi=args.dpi,
        border=args.border,
        error_correction=args.error_correction,
        mask_pattern=args.mask_pattern,
    )

    output_path = generate_qr(
        args.data,
        Path(args.output),
        format=args.format,
        style=style,
    )
    print(output_path)


if __name__ == "__main__":
    main()

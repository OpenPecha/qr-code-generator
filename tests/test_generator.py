from pathlib import Path

from qr_code_generator import DEFAULT_STYLE, generate_qr


def test_generate_png_creates_file(tmp_path: Path) -> None:
    output_path = tmp_path / "sample.png"

    result = generate_qr("https://example.com", output_path)

    assert result == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_svg_creates_svg_markup(tmp_path: Path) -> None:
    output_path = tmp_path / "sample.svg"

    result = generate_qr(
        "https://example.com",
        output_path,
        format="svg",
        style=DEFAULT_STYLE,
    )

    assert result == output_path
    assert output_path.exists()
    assert "<svg" in output_path.read_text(encoding="utf-8")

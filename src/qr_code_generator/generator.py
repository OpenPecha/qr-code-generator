from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import qrcode
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.moduledrawers.svg import SvgPathCircleDrawer
from qrcode.image.svg import SvgPathImage

PNG_BOX_SIZE = 40
SVG_BOX_SIZE = 10
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
VALID_FORMATS = {"png", "svg"}
VALID_EYE_STYLES = {"square", "rounded", "circle"}
ERROR_CORRECTION_MAP = {
    "L": qrcode.ERROR_CORRECT_L,
    "M": qrcode.ERROR_CORRECT_M,
    "Q": qrcode.ERROR_CORRECT_Q,
    "H": qrcode.ERROR_CORRECT_H,
}


@dataclass(frozen=True)
class QRCodeStyle:
    """Rounded monochrome QR style inspired by the sample preset."""

    foreground_color: str = "#000000"
    background_color: str = "#ffffff"
    dot_radius_ratio: float = 1.0
    eye_border_style: str = "rounded"
    eye_center_style: str = "circle"
    dpi: int = 300
    size_inches: float = 2.1
    border: int = 4
    error_correction: str = "H"
    version: Optional[int] = None
    mask_pattern: Optional[int] = 4


DEFAULT_STYLE = QRCodeStyle()


def generate_qr(
    data: str,
    output_path: Union[str, Path],
    *,
    format: Optional[str] = None,
    style: QRCodeStyle = DEFAULT_STYLE,
) -> Path:
    """Generate a QR code and save it to disk."""
    destination = Path(output_path)
    resolved_format = _resolve_format(destination, format)
    _validate_style(style)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if resolved_format == "png":
        return generate_png(data, destination, style=style)
    if resolved_format == "svg":
        return generate_svg(data, destination, style=style)
    raise ValueError(f"Unsupported format: {resolved_format}")


def generate_png(
    data: str,
    output_path: Union[str, Path],
    *,
    style: QRCodeStyle = DEFAULT_STYLE,
) -> Path:
    """Generate a rounded monochrome QR code as PNG."""
    _validate_style(style)
    destination = Path(output_path)
    qr = _create_qr_code(data, style, PNG_BOX_SIZE)

    image = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(radius_ratio=style.dot_radius_ratio),
        color_mask=SolidFillColorMask(
            back_color=_hex_to_rgb(style.background_color),
            front_color=_hex_to_rgb(style.foreground_color),
        ),
    )

    pil_image = image.get_image().convert("RGBA")
    pil_image = _overlay_custom_eyes_png(pil_image, qr, style)
    target_px = int(style.dpi * style.size_inches)
    pil_image = pil_image.resize((target_px, target_px), Image.Resampling.LANCZOS)
    pil_image.convert("RGB").save(destination, dpi=(style.dpi, style.dpi))
    return destination


def generate_svg(
    data: str,
    output_path: Union[str, Path],
    *,
    style: QRCodeStyle = DEFAULT_STYLE,
) -> Path:
    """Generate a rounded monochrome QR code as SVG."""
    _validate_style(style)
    destination = Path(output_path)
    qr = _create_qr_code(data, style, SVG_BOX_SIZE)

    image = qr.make_image(
        image_factory=SvgPathImage,
        module_drawer=SvgPathCircleDrawer(),
    )
    root = ET.fromstring(image.to_string())
    root.set("xmlns", SVG_NAMESPACE)
    size_mm = style.size_inches * 25.4
    root.set("width", f"{size_mm:.1f}mm")
    root.set("height", f"{size_mm:.1f}mm")

    _ensure_svg_background(root, style.background_color)
    _apply_svg_fill(root, style.foreground_color)
    _overlay_custom_eyes_svg(root, qr, style)

    destination.write_text(
        ET.tostring(root, encoding="unicode", xml_declaration=True),
        encoding="utf-8",
    )
    return destination


def _resolve_format(output_path: Path, format: Optional[str]) -> str:
    if format is not None:
        normalized = format.lower()
    elif output_path.suffix:
        normalized = output_path.suffix.lstrip(".").lower()
    else:
        normalized = "png"

    if normalized not in VALID_FORMATS:
        raise ValueError(f"Format must be one of {sorted(VALID_FORMATS)}")
    return normalized


def _validate_style(style: QRCodeStyle) -> None:
    if not style.foreground_color.startswith("#") or len(style.foreground_color) != 7:
        raise ValueError("foreground_color must be a hex color like #000000")
    if not style.background_color.startswith("#") or len(style.background_color) != 7:
        raise ValueError("background_color must be a hex color like #ffffff")
    if not (0.1 <= style.dot_radius_ratio <= 1.0):
        raise ValueError("dot_radius_ratio must be between 0.1 and 1.0")
    if style.eye_border_style not in VALID_EYE_STYLES:
        raise ValueError(f"eye_border_style must be one of {sorted(VALID_EYE_STYLES)}")
    if style.eye_center_style not in VALID_EYE_STYLES:
        raise ValueError(f"eye_center_style must be one of {sorted(VALID_EYE_STYLES)}")
    if style.error_correction not in ERROR_CORRECTION_MAP:
        raise ValueError(f"error_correction must be one of {sorted(ERROR_CORRECTION_MAP)}")
    if style.version is not None and not (1 <= style.version <= 40):
        raise ValueError("version must be between 1 and 40")
    if style.mask_pattern is not None and not (0 <= style.mask_pattern <= 7):
        raise ValueError("mask_pattern must be between 0 and 7")
    if style.border < 0:
        raise ValueError("border must be 0 or greater")
    if style.dpi < 72:
        raise ValueError("dpi must be at least 72")
    if style.size_inches <= 0:
        raise ValueError("size_inches must be greater than 0")


def _create_qr_code(data: str, style: QRCodeStyle, box_size: int) -> qrcode.QRCode:
    qr = qrcode.QRCode(
        version=style.version,
        error_correction=ERROR_CORRECTION_MAP[style.error_correction],
        box_size=box_size,
        border=style.border,
        mask_pattern=style.mask_pattern,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    color = hex_color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _eye_origins(modules_count: int) -> list[tuple[int, int]]:
    return [(0, 0), (0, modules_count - 7), (modules_count - 7, 0)]


def _draw_pil_shape(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    size: float,
    style_name: str,
    fill: tuple[int, int, int],
) -> None:
    radius = max(1, int(size * 0.18))
    x1 = x + size
    y1 = y + size
    if style_name == "circle":
        draw.ellipse((x, y, x1, y1), fill=fill)
    elif style_name == "rounded":
        draw.rounded_rectangle((x, y, x1, y1), radius=radius, fill=fill)
    else:
        draw.rectangle((x, y, x1, y1), fill=fill)


def _overlay_custom_eyes_png(image: Image.Image, qr: qrcode.QRCode, style: QRCodeStyle) -> Image.Image:
    background = _hex_to_rgb(style.background_color)
    foreground = _hex_to_rgb(style.foreground_color)
    draw = ImageDraw.Draw(image)
    module_size = qr.box_size

    for row, col in _eye_origins(qr.modules_count):
        x = (col + style.border) * module_size
        y = (row + style.border) * module_size
        outer_size = 7 * module_size

        draw.rectangle((x, y, x + outer_size, y + outer_size), fill=background)
        _draw_pil_shape(draw, x, y, outer_size, style.eye_border_style, foreground)
        _draw_pil_shape(
            draw,
            x + module_size,
            y + module_size,
            5 * module_size,
            "square",
            background,
        )
        _draw_pil_shape(
            draw,
            x + (2 * module_size),
            y + (2 * module_size),
            3 * module_size,
            style.eye_center_style,
            foreground,
        )

    return image


def _svg_tag(name: str) -> str:
    return f"{{{SVG_NAMESPACE}}}{name}"


def _add_svg_shape(
    root: ET.Element,
    x: float,
    y: float,
    size: float,
    style_name: str,
    fill: str,
) -> None:
    if style_name == "circle":
        ET.SubElement(
            root,
            _svg_tag("circle"),
            {
                "cx": f"{x + (size / 2):.2f}",
                "cy": f"{y + (size / 2):.2f}",
                "r": f"{size / 2:.2f}",
                "fill": fill,
            },
        )
        return

    attrs = {
        "x": f"{x:.2f}",
        "y": f"{y:.2f}",
        "width": f"{size:.2f}",
        "height": f"{size:.2f}",
        "fill": fill,
    }
    if style_name == "rounded":
        radius = max(1.0, size * 0.18)
        attrs["rx"] = f"{radius:.2f}"
        attrs["ry"] = f"{radius:.2f}"
    ET.SubElement(root, _svg_tag("rect"), attrs)


def _find_svg_path(root: ET.Element) -> Optional[ET.Element]:
    for child in root:
        if child.tag == _svg_tag("path") or child.tag == "path":
            return child
    return None


def _ensure_svg_background(root: ET.Element, color: str) -> None:
    root.insert(
        0,
        ET.Element(
            _svg_tag("rect"),
            {
                "x": "0",
                "y": "0",
                "width": "100%",
                "height": "100%",
                "fill": color,
            },
        ),
    )


def _apply_svg_fill(root: ET.Element, color: str) -> None:
    path = _find_svg_path(root)
    if path is not None:
        path.set("fill", color)


def _overlay_custom_eyes_svg(root: ET.Element, qr: qrcode.QRCode, style: QRCodeStyle) -> None:
    module_size = qr.box_size / 10

    for row, col in _eye_origins(qr.modules_count):
        x = (col + style.border) * module_size
        y = (row + style.border) * module_size
        outer_size = 7 * module_size
        ET.SubElement(
            root,
            _svg_tag("rect"),
            {
                "x": f"{x:.2f}",
                "y": f"{y:.2f}",
                "width": f"{outer_size:.2f}",
                "height": f"{outer_size:.2f}",
                "fill": style.background_color,
            },
        )
        _add_svg_shape(root, x, y, outer_size, style.eye_border_style, style.foreground_color)
        _add_svg_shape(
            root,
            x + module_size,
            y + module_size,
            5 * module_size,
            "square",
            style.background_color,
        )
        _add_svg_shape(
            root,
            x + (2 * module_size),
            y + (2 * module_size),
            3 * module_size,
            style.eye_center_style,
            style.foreground_color,
        )

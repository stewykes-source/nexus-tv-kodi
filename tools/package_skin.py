#!/usr/bin/env python3
"""Build and validate a Kodi-installable Nexus skin ZIP using only Python stdlib."""
from __future__ import annotations

import argparse
import math
import shutil
import struct
import tempfile
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / "skin.nexus"


def png_chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def write_png(path: Path, width: int, height: int, pixel_fn) -> None:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(pixel_fn(x, y, width, height))
    raw = bytes(rows)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def create_brand_assets(folder: Path) -> None:
    # A tiny solid texture is tinted by Kodi controls to create the skin's panels.
    write_png(folder / "media" / "white.png", 2, 2, lambda *_: (255, 255, 255))

    def icon_pixel(x: int, y: int, w: int, h: int):
        nx, ny = x / (w - 1), y / (h - 1)
        glow = max(0.0, 1.0 - math.sqrt((nx - 0.72) ** 2 + (ny - 0.25) ** 2) * 1.6)
        return (
            int(7 + 15 * glow),
            int(13 + 65 * glow),
            int(23 + 48 * glow),
        )

    write_png(folder / "icon.png", 256, 256, icon_pixel)

    def fanart_pixel(x: int, y: int, w: int, h: int):
        nx, ny = x / (w - 1), y / (h - 1)
        glow = max(0.0, 1.0 - math.sqrt(((nx - 0.78) * 1.1) ** 2 + ((ny - 0.28) * 1.4) ** 2) * 1.25)
        lower = max(0.0, 1.0 - ny)
        return (
            int(5 + 8 * glow + 2 * lower),
            int(10 + 46 * glow + 3 * lower),
            int(19 + 39 * glow + 7 * lower),
        )

    write_png(folder / "fanart.png", 1920, 1080, fanart_pixel)


def validate_skin(folder: Path) -> None:
    xml_files = sorted(folder.rglob("*.xml"))
    if not xml_files:
        raise SystemExit("No XML files found in skin package.")
    for xml_file in xml_files:
        ET.parse(xml_file)

    manifest = ET.parse(folder / "addon.xml").getroot()
    if manifest.attrib.get("id") != "skin.nexus":
        raise SystemExit("Unexpected add-on id; expected skin.nexus.")
    version = manifest.attrib.get("version")
    if not version:
        raise SystemExit("Missing add-on version.")

    font_xml = folder / "1080i" / "Font.xml"
    fonts = ET.parse(font_xml).getroot()
    font_names = {
        node.findtext("name")
        for node in fonts.findall(".//font")
        if node.findtext("name")
    }
    if "font13" not in font_names:
        raise SystemExit("Kodi requires a font13 definition in Font.xml.")

    for required in ("media/white.png", "icon.png", "fanart.png"):
        if not (folder / required).is_file():
            raise SystemExit(f"Missing required packaged asset: {required}")

    print(f"Validated {len(xml_files)} XML files; skin version {version}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist", help="Output directory")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="nexus-skin-") as temp:
        staging = Path(temp) / "skin.nexus"
        shutil.copytree(SKIN, staging)
        create_brand_assets(staging)
        validate_skin(staging)

        manifest = ET.parse(staging / "addon.xml").getroot()
        version = manifest.attrib["version"]
        archive = output / f"skin.nexus-{version}.zip"
        with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=9) as package:
            for file in sorted(staging.rglob("*")):
                if file.is_file():
                    package.write(file, file.relative_to(staging.parent))
        print(f"Created {archive}")


if __name__ == "__main__":
    main()

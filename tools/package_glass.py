#!/usr/bin/env python3
"""Build the optional Nexus Glass Kodi skin as a separate installable add-on.

The Glass look is an original Kodi implementation inspired by the visual
principles of CleanYourTV's Glass theme. No CleanYourTV launcher code or
wallpaper assets are copied into this package.
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def png_chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)


def write_png(path: Path, width: int, height: int, pixel_fn) -> None:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(pixel_fn(x, y, width, height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def make_glass_wallpaper(path: Path) -> None:
    """Create original navy artwork with soft teal and violet light ribbons."""
    def pixel(x: int, y: int, w: int, h: int):
        nx, ny = x / (w - 1), y / (h - 1)
        base = [9.0, 12.0, 20.0]
        ribbons = (
            (0.20 + 0.13 * math.sin(nx * 3.0 + 0.4), 0.060, (43, 190, 190), 0.52),
            (0.56 + 0.12 * math.sin(nx * 2.7 + 1.7), 0.075, (106, 83, 190), 0.54),
            (0.82 + 0.07 * math.sin(nx * 3.5 + 2.1), 0.045, (44, 133, 160), 0.30),
        )
        for center, thickness, rgb, strength in ribbons:
            distance = abs(ny - center)
            glow = math.exp(-((distance / (thickness * 3.2)) ** 2)) * strength
            rim = math.exp(-(((distance - thickness) / (thickness * 0.42)) ** 2)) * 0.22
            amount = min(0.82, glow + rim) * min(1.0, max(0.0, (nx - 0.08) * 1.8))
            for i in range(3):
                base[i] += (rgb[i] - base[i]) * amount
        # Gentle teal and violet bloom, kept away from the text-safe upper left.
        for cx, cy, rgb, strength in (
            (0.82, 0.34, (31, 124, 151), 0.24),
            (0.64, 0.72, (101, 59, 157), 0.20),
        ):
            bloom = max(0.0, 1.0 - math.sqrt(((nx - cx) * 1.15) ** 2 + ((ny - cy) * 1.25) ** 2) * 1.8) * strength
            for i in range(3):
                base[i] += (rgb[i] - base[i]) * bloom
        return tuple(max(0, min(255, int(v))) for v in base)

    write_png(path, 1920, 1080, pixel)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-skin", required=True, help="Path to the pinned Kodi Estuary skin source")
    parser.add_argument("--output", default="dist", help="Output directory")
    args = parser.parse_args()

    output = (ROOT / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="nexus-glass-") as temp:
        temp_path = Path(temp)
        classic_dist = temp_path / "classic"
        subprocess.run(
            [
                "python", str(ROOT / "tools" / "package_skin.py"),
                "--base-skin", str(Path(args.base_skin).resolve()),
                "--output", str(classic_dist),
            ],
            check=True,
            cwd=ROOT,
        )
        source_zip = next(classic_dist.glob("skin.nexus-*.zip"))
        staging_root = temp_path / "unpacked"
        staging_root.mkdir()
        with ZipFile(source_zip) as archive:
            archive.extractall(staging_root)
        skin = staging_root / "skin.nexus"

        # Give Glass its own add-on identity so both skins can be installed
        # and selected independently in Kodi's Interface > Skin settings.
        manifest_path = skin / "addon.xml"
        manifest = ET.parse(manifest_path)
        root = manifest.getroot()
        root.set("id", "skin.nexus.glass")
        root.set("name", "Nexus Glass")
        root.set("version", "1.0.0")
        metadata = root.find("./extension[@point='xbmc.addon.metadata']")
        if metadata is not None:
            summary = metadata.find("summary")
            if summary is not None:
                summary.text = "Nexus Glass — a cinematic frosted-glass Kodi interface"
            description = metadata.find("description")
            if description is not None:
                description.text = (
                    "A navy, teal and violet glass-style variant of Nexus for Kodi 21, "
                    "with the same Xstream Pro routes and native Kodi playback."
                )
        ET.indent(manifest, space="  ")
        manifest.write(manifest_path, encoding="UTF-8", xml_declaration=True)

        home_path = skin / "xml" / "Home.xml"
        home = home_path.read_text(encoding="utf-8")
        replacements = {
            "FF09090C": "FF090C14",
            "nexus-background.png": "nexus-glass-background.png",
            "FFFF902A": "FF63D7D0",
            "FFFF861F": "FF5ACBC8",
            "FFFF9A36": "FF8BE5DF",
            "FFCBD3DC": "FFD5E1EA",
            "FF9BA8B8": "FF9CB5C4",
            "D9141822": "C9111C2B",
            "100" end="104"": "100" end="102"",
            "100" end="103"": "100" end="102"",
        }
        for old, new in replacements.items():
            home = home.replace(old, new)
        # The source Nexus skin has decorative multicolour reflection bars;
        # Glass keeps the cleaner, cinematic dock without those stripes.
        home = re.sub(
            r"\\s*<!-- Neon reflection bars under the dock -->.*?(?=\\s*<!-- Secondary Quick Access Pill Navigation Bar -->)",
            "\\n",
            home,
            flags=re.S,
        )
        home_path.write_text(home, encoding="utf-8")

        colors_path = skin / "colors" / "defaults.xml"
        colors = colors_path.read_text(encoding="utf-8")
        for old, new in {
            "FF09090C": "FF090C14",
            "FF211D20": "FF111C2A",
            "552D2424": "663D5A70",
            "FFFF9A36": "FF8BE5DF",
            "CCFF861F": "CC5ACBC8",
            "FFFFB35D": "FF63D7D0",
            "FF5AA8FF": "FF7D9CFF",
            "FF09090C": "FF090C14",
            "D91B1B20": "C9111C2B",
            "FFFF861F": "FF5ACBC8",
            "FFB9B1AC": "FFB7C5D1",
            "FFB06BDC": "FF9B83E6",
        }.items():
            colors = colors.replace(old, new)
        colors_path.write_text(colors, encoding="utf-8")

        make_glass_wallpaper(skin / "media" / "nexus-glass-background.png")

        # Keep the upstream Estuary notices and Nexus licence in the package.
        # Add explicit attribution for the visual reference in the repository.
        glass_root = output / "glass-package"
        if glass_root.exists():
            shutil.rmtree(glass_root)
        glass_root.mkdir()
        final_skin = glass_root / "skin.nexus.glass"
        shutil.copytree(skin, final_skin)

        # Validate all XML and the add-on identity before creating the ZIP.
        xml_files = list(final_skin.rglob("*.xml"))
        if len(xml_files) < 40:
            raise SystemExit(f"Incomplete Kodi skin: only {len(xml_files)} XML files found.")
        for xml_file in xml_files:
            ET.parse(xml_file)
        if ET.parse(final_skin / "addon.xml").getroot().attrib.get("id") != "skin.nexus.glass":
            raise SystemExit("Glass add-on identity validation failed.")
        home_check = ET.parse(final_skin / "xml" / "Home.xml").getroot()
        home_text = ET.tostring(home_check, encoding="unicode")
        for route in (
            "mode=live_menu", "mode=movies_menu", "mode=series_menu",
            "mode=open_pvr", "mode=open_pvr_guide", "mode=replay_menu", "mode=search_global",
        ):
            if route not in home_text:
                raise SystemExit(f"Glass variant lost Xstream Pro route: {route}")
        if not (final_skin / "media" / "nexus-glass-background.png").is_file():
            raise SystemExit("Glass wallpaper was not packaged.")

        archive_path = output / "skin.nexus.glass-1.0.0.zip"
        with ZipFile(archive_path, "w", ZIP_DEFLATED, compresslevel=9) as archive:
            for file in sorted(final_skin.rglob("*")):
                if file.is_file():
                    archive.write(file, file.relative_to(glass_root))
        print(f"Validated {len(xml_files)} XML files; created {archive_path}")


if __name__ == "__main__":
    main()

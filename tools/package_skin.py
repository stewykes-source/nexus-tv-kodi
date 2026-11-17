#!/usr/bin/env python3
"""Build Nexus as a branded Kodi 21 skin, layered over the pinned Estuary base."""
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
    png = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">2I5B", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def create_brand_assets(folder: Path) -> None:
    media_dst = folder / "media"
    media_dst.mkdir(parents=True, exist_ok=True)

    # Copy custom textures from skin.nexus/media if available
    media_src = SKIN / "media"
    if media_src.is_dir():
        for item in media_src.iterdir():
            if item.is_file():
                shutil.copy2(item, media_dst / item.name)

    # 1px texture for solid colour tints
    if not (media_dst / "nexus-white.png").is_file():
        write_png(media_dst / "nexus-white.png", 1, 1, lambda *_: (255, 255, 255))

    # Ambient wave wallpaper fallback if not provided
    if not (media_dst / "nexus-background.png").is_file():
        def background_pixel(x: int, y: int, w: int, h: int):
            nx, ny = x / (w - 1), y / (h - 1)
            base = [9.0, 9.0, 12.0]
            curves = (
                (0.12 + 0.18 * math.sin(nx * 4.2 + 0.2), 0.035, (255, 91, 15), 0.72),
                (0.39 + 0.16 * math.sin(nx * 3.4 + 1.2), 0.030, (255, 132, 36), 0.78),
                (0.70 + 0.12 * math.sin(nx * 3.1 + 2.0), 0.045, (255, 177, 86), 0.48),
            )
            for center, thickness, rgb, strength in curves:
                distance = abs(ny - center)
                glow = math.exp(-((distance / (thickness * 3.8)) ** 2)) * strength
                rim = math.exp(-(((distance - thickness) / (thickness * 0.34)) ** 2)) * 0.50
                amount = min(1.0, glow + rim) * min(1.0, max(0.0, (nx - 0.12) * 2.0))
                for i in range(3):
                    base[i] += (rgb[i] - base[i]) * amount * 0.72
            bloom = max(0.0, 1.0 - math.sqrt(((nx - 0.88) * 1.1) ** 2 + ((ny - 0.47) * 1.1) ** 2) * 1.7)
            base[0] += 22 * bloom
            base[1] += 8 * bloom
            base[2] += 2 * bloom
            return tuple(max(0, min(255, int(v))) for v in base)

        write_png(media_dst / "nexus-background.png", 1920, 1080, background_pixel)

    def icon_pixel(x: int, y: int, w: int, h: int):
        nx, ny = x / (w - 1), y / (h - 1)
        glow = max(0.0, 1.0 - math.sqrt((nx - 0.72) ** 2 + (ny - 0.25) ** 2) * 1.6)
        return (int(7 + 15 * glow), int(13 + 65 * glow), int(23 + 48 * glow))

    write_png(folder / "icon.png", 256, 256, icon_pixel)

    def fanart_pixel(x: int, y: int, w: int, h: int):
        nx, ny = x / (w - 1), y / (h - 1)
        glow = max(0.0, 1.0 - math.sqrt(((nx - 0.78) * 1.1) ** 2 + ((ny - 0.28) * 1.4) ** 2) * 1.25)
        lower = max(0.0, 1.0 - ny)
        return (int(5 + 8 * glow + 2 * lower), int(10 + 46 * glow + 3 * lower), int(19 + 39 * glow + 7 * lower))

    write_png(folder / "fanart.png", 1920, 1080, fanart_pixel)


def merge_xml(base_file: Path, custom_file: Path, child_tag: str, overwrite: bool = False) -> None:
    base_root = ET.parse(base_file).getroot()
    custom_root = ET.parse(custom_file).getroot()
    if base_root.tag != custom_root.tag:
        raise SystemExit(f"Cannot merge {custom_file}: root tag differs from {base_file}")
    existing = {}
    for index, child in enumerate(list(base_root.findall(child_tag))):
        name = child.findtext("name") or child.attrib.get("name")
        if name:
            existing[name] = (index, child)
    for child in custom_root.findall(child_tag):
        name = child.findtext("name") or child.attrib.get("name")
        if name and name in existing:
            if overwrite:
                index, old = existing[name]
                base_root.remove(old)
                base_root.insert(index, child)
                existing[name] = (index, child)
            continue
        base_root.append(child)
        if name:
            existing[name] = (len(base_root) - 1, child)
    ET.indent(base_root, space="  ")
    base_file.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(base_root, encoding="unicode") + "\n", encoding="utf-8")


def merge_fonts(base_file: Path, custom_file: Path) -> None:
    base_root = ET.parse(base_file).getroot()
    custom_root = ET.parse(custom_file).getroot()
    base_set = base_root.find("fontset")
    custom_set = custom_root.find("fontset")
    if base_set is None or custom_set is None:
        raise SystemExit("Font.xml must contain a fontset.")
    existing = {node.findtext("name") for node in base_set.findall("font")}
    for node in custom_set.findall("font"):
        name = node.findtext("name")
        if name and name not in existing:
            base_set.append(node)
            existing.add(name)
    ET.indent(base_root, space="  ")
    base_file.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(base_root, encoding="unicode") + "\n", encoding="utf-8")


def validate_skin(folder: Path) -> None:
    xml_files = sorted(folder.rglob("*.xml"))
    if len(xml_files) < 40:
        raise SystemExit(f"Expected a complete Kodi skin framework; found only {len(xml_files)} XML files.")
    for xml_file in xml_files:
        ET.parse(xml_file)

    manifest = ET.parse(folder / "addon.xml").getroot()
    if manifest.attrib.get("id") != "skin.nexus":
        raise SystemExit("Unexpected add-on id; expected skin.nexus.")
    version = manifest.attrib.get("version")
    if not version:
        raise SystemExit("Missing add-on version.")

    fonts = ET.parse(folder / "xml" / "Font.xml").getroot()
    font_names = {node.findtext("name") for node in fonts.findall(".//font") if node.findtext("name")}
    for required_font in ("font13", "NexusLogo", "NexusCard", "NexusSmall"):
        if required_font not in font_names:
            raise SystemExit(f"Missing required font definition: {required_font}")

    home = ET.parse(folder / "xml" / "Home.xml").getroot()
    controls = {
        node.attrib.get("id"): node
        for node in home.findall(".//control")
        if node.attrib.get("id")
    }
    nav_ids = {str(value) for value in range(9101, 9108)}
    for control_id in sorted(nav_ids):
        node = controls.get(control_id)
        if node is None or node.attrib.get("type") != "button":
            raise SystemExit(f"Missing Nexus navigation button {control_id}.")
        for direction in ("onleft", "onright", "onup", "ondown"):
            action = node.findtext(direction, default="")
            target = action.removeprefix("SetFocus(").removesuffix(")")
            if target not in nav_ids | {"9200"}:
                raise SystemExit(f"Invalid {direction} focus target on navigation button {control_id}: {action}")
    settings = controls.get("9200")
    if settings is None or settings.findtext("onclick") != "ActivateWindow(Settings)":
        raise SystemExit("Nexus Settings shortcut is missing or invalid.")
    if settings.findtext("onup") != "SetFocus(9107)":
        raise SystemExit("Nexus Settings shortcut must return focus to Search.")

    home_xml = ET.tostring(home, encoding="unicode")
    for route in ("mode=live_menu", "mode=movies_menu", "mode=series_menu", "mode=open_pvr", "mode=open_pvr_guide", "mode=replay_menu", "mode=search_global"):
        if route not in home_xml:
            raise SystemExit(f"Missing Xstream Pro home route: {route}")
    if "\\nAll in one place." in home_xml:
        raise SystemExit("Hero headline contains a literal escaped newline.")

    for required in ("xml/Home.xml", "xml/MyVideoNav.xml", "media/nexus-white.png", "media/nexus-background.png", "icon.png", "fanart.png", "LICENSE.txt", "LICENSE-NEXUS.txt"):
        if not (folder / required).is_file():
            raise SystemExit(f"Missing required packaged asset: {required}")

    print(f"Validated {len(xml_files)} XML files; skin version {version}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-skin", required=True, help="Path to the pinned Kodi Estuary skin source")
    parser.add_argument("--output", default="dist", help="Output directory")
    args = parser.parse_args()
    base = Path(args.base_skin).resolve()
    if not (base / "addon.xml").is_file() or not (base / "xml" / "Home.xml").is_file():
        raise SystemExit("Base skin path must point to the Kodi skin.estuary add-on folder.")

    output = (ROOT / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="nexus-skin-") as temp:
        staging = Path(temp) / "skin.nexus"
        shutil.copytree(base, staging)

        # Replace Kodi's default landing page with Nexus, while retaining the full
        # upstream set of working Kodi windows, dialogs, media views and playback UI.
        shutil.copy2(SKIN / "1080i" / "Home.xml", staging / "xml" / "Home.xml")
        shutil.copy2(SKIN / "addon.xml", staging / "addon.xml")
        merge_fonts(staging / "xml" / "Font.xml", SKIN / "1080i" / "Font.xml")

        # Add Nexus colours without removing the base skin's required colour names.
        base_colors = staging / "colors" / "defaults.xml"
        custom_colors = SKIN / "colors" / "defaults.xml"
        if base_colors.exists() and custom_colors.exists():
            merge_xml(base_colors, custom_colors, "color", overwrite=True)

        # Retain Estuary's complete include graph and append Nexus-specific includes.
        base_includes = staging / "xml" / "Includes.xml"
        custom_includes = SKIN / "1080i" / "Includes.xml"
        if base_includes.exists() and custom_includes.exists():
            merge_xml(base_includes, custom_includes, "include")

        # Keep upstream notices intact; ship the Nexus-specific licence separately.
        shutil.copy2(SKIN / "LICENSE.txt", staging / "LICENSE-NEXUS.txt")
        shutil.copy2(SKIN / "changelog.txt", staging / "changelog-nexus.txt")
        create_brand_assets(staging)
        validate_skin(staging)

        version = ET.parse(staging / "addon.xml").getroot().attrib["version"]
        archive = output / f"skin.nexus-{version}.zip"
        with ZipFile(archive, "w", ZIP_DEFLATED, compresslevel=9) as package:
            for file in sorted(staging.rglob("*")):
                if file.is_file():
                    package.write(file, file.relative_to(staging.parent))
        print(f"Created {archive}")


if __name__ == "__main__":
    main()

# Nexus Glass

Nexus Glass is an optional, separately installable Kodi 21 skin variant for Nexus TV.

It adapts the visual direction of the **Glass** theme published on CleanYourTV by **matheus-caldeira**:
- deep navy background
- soft teal and violet ambient light
- cinematic top shelf
- translucent dock treatment
- restrained focus movement without overshoot

This is a Kodi-native recreation, not a CleanYourTV theme import. CleanYourTV's `config.json` controls its own Android TV launcher and is not understood by Kodi. Nexus Glass uses Kodi skin XML, textures and colour definitions.

## Attribution

Visual reference: [CleanYourTV — Glass theme](https://cleanyour.tv/addons), by matheus-caldeira. The original theme configuration is available at [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv/tree/main/themes/glass).

Nexus Glass does not copy CleanYourTV launcher code or its wallpaper assets. Its navy/teal/violet wallpaper is generated specifically for this Kodi skin. The underlying Kodi Estuary source and Nexus additions retain their respective licences and notices in the packaged add-on.

## Build

The GitHub Actions workflow builds this variant alongside the original Nexus skin:

```bash
python tools/package_glass.py --base-skin upstream-kodi/addons/skin.estuary --output dist
```

The resulting `skin.nexus.glass-1.0.0.zip` is directly installable through Kodi's **Add-ons → Install from zip file** menu. Once installed, choose **Nexus Glass** under **Settings → Interface → Skin**. The original **Nexus** skin remains installed and selectable.

Both variants retain the same Xstream Pro Static profile routes and Kodi playback framework.

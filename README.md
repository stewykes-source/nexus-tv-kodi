# Nexus TV for Kodi

Nexus is an Apple TV-inspired, remote-first Kodi skin for Fire TV and Android TV.

## Current milestone

This repository starts the Kodi 21 Omega skin package. Kodi remains the playback engine and the existing Xstream Pro add-on remains responsible for provider access. Nexus does not store IPTV credentials.

### Compatibility
- Kodi 21 Omega (target)
- 1920×1080 / 16:9 layout, scaled by Kodi
- Fire TV / Android TV remote navigation

### Install the skin ZIP
1. Download the latest `skin.nexus` ZIP from the repository's Releases page (once a release is published).
2. In Kodi, enable **Unknown sources** if required.
3. Open **Add-ons → Install from zip file** and select the ZIP.
4. Go to **Settings → Interface → Skin** and select **Nexus**.

The ZIP installs a skin add-on only. It does not replace the Kodi Android application or create a standalone APK. A branded APK is a separate build/release milestone.

## Xstream Pro integration

Nexus opens the existing Xstream Pro add-on using the user's existing **Profile 1** (labelled **Static** in their setup). No server URL, username, password, or token is included in this repository.

- Live TV: `plugin://plugin.video.xstream-pro/?mode=live_menu&profile_num=1`
- Movies: `plugin://plugin.video.xstream-pro/?mode=movies_menu&profile_num=1`
- Series: `plugin://plugin.video.xstream-pro/?mode=series_menu&profile_num=1`
- Search: `plugin://plugin.video.xstream-pro/?mode=search_global&profile_num=1`

## Development

Edit the skin XML under `skin.nexus/1080i/`. The packaging workflow creates a Kodi-installable ZIP with the required top-level `skin.nexus/` folder.

See [Kodi's skin development guide](https://kodi.wiki/view/Skin_development_introduction).

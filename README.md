# Nexus TV for Kodi

Nexus is an Apple TV-inspired, remote-first Kodi skin for Fire TV and Android TV.

## Project direction

Kodi remains the playback engine. Nexus replaces the home-screen experience while retaining Kodi's established window, dialog, media browsing, playback and PVR framework. The current package is based on the Kodi 21 Omega Estuary skin source pinned to commit `f8815ee40f49a700c047982d752be4b2a61420e2`, with Nexus branding and home screen layered over it.

The existing Xstream Pro add-on is opened using Profile 1 (**Static**). Nexus does not store IPTV credentials or make provider API calls itself.

### Target compatibility

- Kodi 21 Omega
- Fire TV Stick 4K / Android TV
- 1920×1080, 16:9 layout
- Remote-first navigation (D-pad and Select/Back)
- Existing Xstream Pro add-on, Profile 1 (labelled **Static**)

## Install the skin ZIP

1. Download the latest `skin.nexus-*.zip` from the [Actions artifacts](https://github.com/stewykes-source/nexus-tv-kodi/actions) or a versioned [GitHub Release](https://github.com/stewykes-source/nexus-tv-kodi/releases).
2. In Kodi, enable **Unknown sources** if required.
3. Open **Add-ons → Install from zip file** and select the ZIP.
4. Go to **Settings → Interface → Skin** and select **Nexus**.

The ZIP installs the skin add-on only. It does not replace the Kodi Android application or create a standalone APK. A branded Fire OS APK is a separate packaging milestone and must bundle Kodi itself.

## Xstream Pro integration

Nexus opens the existing Xstream Pro add-on using Profile 1 (**Static**). No server URL, username, password, or token is included in this repository.

- Live TV: `plugin://plugin.video.xstream-pro/?mode=live_menu&profile_num=1`
- Movies: `plugin://plugin.video.xstream-pro/?mode=movies_menu&profile_num=1`
- Series: `plugin://plugin.video.xstream-pro/?mode=series_menu&profile_num=1`
- Search: `plugin://plugin.video.xstream-pro/?mode=search_global&profile_num=1`

## Build

The GitHub Actions workflow checks out the pinned Kodi 21 Estuary source, overlays Nexus files, validates the full XML tree and packages `dist/skin.nexus-<version>.zip`.

For a local build, check out the pinned Kodi source into `upstream-kodi` and run:

```bash
python tools/package_skin.py --base-skin upstream-kodi/addons/skin.estuary --output dist
```

## Licensing and attribution

The Kodi Estuary base is distributed under its upstream licences. Its original `LICENSE.txt` and all upstream source/assets are retained in the package. Nexus-specific additions and branding are separately identified in `LICENSE-NEXUS.txt`.

## Development notes

- Nexus home-screen source: `skin.nexus/1080i/Home.xml`.
- Nexus font additions: `skin.nexus/1080i/Font.xml`.
- Nexus palette additions: `skin.nexus/colors/defaults.xml`.
- Kodi 21 Estuary source is pinned in `.github/workflows/package-skin.yml`.
- Do not commit provider credentials, account tokens, or private IPTV URLs.
- A successful ZIP build is not the same as a successful runtime test. Test the skin in Kodi 21 on Windows first, then Fire OS.

See [Kodi's skin development guide](https://kodi.wiki/view/Skin_development_introduction).

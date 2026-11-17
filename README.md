# Nexus TV for Kodi

Nexus is an Apple TV-inspired, remote-first Kodi skin for Fire TV and Android TV.

## Project direction

Kodi remains the playback engine. Nexus replaces the home-screen experience while preserving compatible Kodi add-ons, including the existing Xstream Pro installation. Nexus does not store IPTV credentials or make provider API calls itself.

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

Nexus opens the user's existing Xstream Pro add-on using Profile 1 (**Static**). No server URL, username, password, or token is included in this repository.

- Live TV: `plugin://plugin.video.xstream-pro/?mode=live_menu&profile_num=1`
- Movies: `plugin://plugin.video.xstream-pro/?mode=movies_menu&profile_num=1`
- Series: `plugin://plugin.video.xstream-pro/?mode=series_menu&profile_num=1`
- Search: `plugin://plugin.video.xstream-pro/?mode=search_global&profile_num=1`

## Build locally

Python 3.10+ is sufficient; the packager uses only the Python standard library.

```bash
python tools/package_skin.py --output dist
```

The build validates XML and required Kodi font/texture definitions, generates Nexus artwork and creates `dist/skin.nexus-<version>.zip`. GitHub Actions runs the same build on pushes to `main` and publishes a GitHub Release when a `v*` tag is pushed.

## Development notes

- Skin XML lives in `skin.nexus/1080i/`.
- Palette definitions live in `skin.nexus/colors/defaults.xml`.
- Do not commit provider credentials, account tokens, or private IPTV URLs.
- A successful ZIP build is not the same as a successful runtime test. Test the skin in Kodi 21 on Windows first, then Fire OS.

See [Kodi's skin development guide](https://kodi.wiki/view/Skin_development_introduction).

English fan translation of **Ore no Shikabane o Koete Yuke** for PSP (**UCJS-10117**).

### Apply

Repacked download: **2.44 MiB** instead of 180.66 MiB. The patched ISO is byte-for-byte identical to the original 0.2.38 release.

**Recommended:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools/releases/latest) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO, choose **0.2.38** (or **Latest**), and select a new output filename. The app downloads the matching patch and verifies the result.

**Manual patching:** [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) and [xdelta3](https://github.com/jmacd/xdelta) accept the same asset:

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO (UCJS-10117) | `OreNoShikabane-English-0.2.38-compact.xdelta` |

```text
xdelta3 -d -s "Ore no Shikabane o Koete Yuke (Japan).iso" OreNoShikabane-English-0.2.38-compact.xdelta "Ore no Shikabane o Koete Yuke English 0.2.38.iso"
```

Original ISO: 847,937,536 bytes; SHA-256 `03791a833656ddebadff7848a6296fc1698b52dfd7052c91572dd8b800fd569a`.

Release output: 1,081,079,808 bytes; SHA-256 `c7a51ee07bf8f42d47d65c670c80e270eae9fe7743551b1ffe732e3efe6569f8`.

`BUILD-MANIFEST.json` records the exact source, output and patch identities. `VALIDATION.json` records the complete xdelta round trip, and `SHA256SUMS.txt` covers the downloads. This first public release provides a full patch from the original; it does not offer upgrade patches from unpublished local test builds.

### What's included

- English drafts for all **8,027 distinct indexed main strings**, covering 11,026 Japanese-bearing archive records: dialogue/narration, menus/help, descriptions, character/item text, credits and original subtitle text. Additional executable and native graphic labels are tracked separately.
- A proportional **Noto Sans** font with embedded 4x rasters, including UI/battle artwork and digits. Texture replacement is disabled in the verified build.
- Latin name entry and Auto-name pools; translated setup/date, shop, equipment, status, party, calendar, Chronicle and catalog interfaces, with selected overlap and clipping fixes.
- Full character creeds/sayings, clearer Potential labels, original Oreshika: Tainted Bloodlines vital/element icon designs, compact battle item names and wrapped battle descriptions.
- Wider story dialogue with a partly transparent background. Build 0.2.38 also widens the centered home help panel, retaining the complete Rest description.

See the [changelog](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke/blob/main/CHANGELOG.md) for the accumulated local changes and selected runtime evidence.

### Release status

**This is an early draft build. Human proofreading and full-game playtesting are needed.** Indexed draft coverage does not certify meaning or visual fit throughout the game. Selected setup, inventory/shop, character/status, battle and home screens were checked in PPSSPP. The last build's Rest and Divine Union help were checked in the final ISO; all 34 related fixed help entries were measured, with only those selected entries navigated live.

- Full playthrough and physical PSP testing remain pending.
- Some names/readings remain provisional, including 62 Auto-name readings and 23 credit readings. Some decorative Japanese artwork remains; other long/dynamic text may need further layout changes.
- Japanese audio is retained. This release does not add subtitles to voices that had no text in the original game.
- The image contains a decrypted EBOOT and was tested in PPSSPP. Native 1x rendering scales the same 4x glyph rasters down.

**Boot the patched ISO fresh and load a normal save.** Save states keep older text, fonts and textures in memory. Local QA used an isolated emulator profile and restored its saves; the user's normal save source was not changed.

### How it was translated

This is a **machine translation**, produced with large language models and then edited using neighboring scene text and a project glossary. Translation choices, provisional readings, static checks and selected in-game evidence are recorded in the repository. Human proofreading and playtesting are welcome.

### Acknowledgements

- **Noto Sans**, © 2018 The Noto Project Authors, SIL Open Font License 1.1; font provenance and licence are in the repository.
- **PPSSPP**, used for native framebuffer captures, debugger checks and gameplay/UI verification.
- The original **Oreshika: Tainted Bloodlines** vital/element icon designs, adapted for this PSP patch. Original game artwork retains its owners' rights.
- [Macross Triangle Frontier](https://github.com/retro-trans/Macross-Triangle-Frontier), whose repository and release format served as the reference, and [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools) for verified packaging and automatic patch discovery.

### Source code

English translation exports, glossaries, UI metadata and tools are in the [project repository](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke). GitHub's source archives contain the tagged repository snapshot. Apply the `.xdelta` asset to patch the game; complete ISO files are not distributed.

### Contribute

Bug reports, proofreading and playtesting are welcome at **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)** or in repository issues. Include the patch version, steps and affected text/screen.

No complete game images are included. Apply the patch to your own disc image.

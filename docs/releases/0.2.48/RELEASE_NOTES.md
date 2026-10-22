English fan translation of **Ore no Shikabane o Koete Yuke** for PSP (**UCJS-10117**).

### Apply

**Recommended:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools/releases/latest) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or the public **0.2.38** patched ISO, choose **0.2.48** (or **Latest**), and choose a new output filename. The app selects the matching patch and verifies the complete result.

**Manual patching:** Use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or [xdelta3](https://github.com/jmacd/xdelta) with the patch matching your input:

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO (UCJS-10117) | `OreNoShikabane-English-0.2.48-full.xdelta` |
| Public English 0.2.38 ISO | `OreNoShikabane-English-0.2.38-to-0.2.48.xdelta` |

Downloads: full patch **2.46 MiB** (2,576,551 bytes); 0.2.38 upgrade **66.4 KiB** (67,946 bytes).

```text
xdelta3 -d -s "Ore no Shikabane o Koete Yuke (Japan).iso" OreNoShikabane-English-0.2.48-full.xdelta "Ore no Shikabane o Koete Yuke English 0.2.48.iso"
```

Original ISO: 847,937,536 bytes; SHA-256 `03791a833656ddebadff7848a6296fc1698b52dfd7052c91572dd8b800fd569a`.

English 0.2.38 input: 1,081,079,808 bytes; SHA-256 `c7a51ee07bf8f42d47d65c670c80e270eae9fe7743551b1ffe732e3efe6569f8`.

Release output: 1,081,337,856 bytes; SHA-256 `43569c29fb58ece6ade5f02f4ac39ea8df86041ba6bce7fc461f7293e1dcc907`.

Both patches produce the same tested 0.2.48 ISO. `BUILD-MANIFEST.json` identifies every source, output and patch; `VALIDATION.json` records both complete encode/decode round trips; `SHA256SUMS.txt` covers the downloads. Unpublished local builds are not upgrade inputs.

### What's changed since 0.2.38

- Fixed a memory corruption bug that could garble prologue/battle names, icons and other patch data after a fresh boot.
- Kept Circle/Triangle prompts on the sharper proportional font; rewrapped the reported prologue and Help passages without cutting dialogue.
- Widened the party action popup, Help dialogue and deity sort menu; separated the required offering points caption and value on the confirmation card.
- Translated the investment banner, investment amount unit and Emperor speaker label; improved weather-banner spacing and tournament rule formatting.
- Shortened long tournament team names to fit the bracket, with full/display-name mappings in the repository.
- Expanded class descriptions and moved button hints directly above them. All eight descriptions pass width checks; actual class-screen visual verification remains pending.

The build includes all local fixes from 0.2.39 through 0.2.48. See the [changelog](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke/blob/main/CHANGELOG.md) for details and recorded testing limits.

### What's included

- English drafts for all **8,027 distinct indexed main strings**, covering 11,026 Japanese-bearing archive records: dialogue/narration, menus/help, descriptions, character/item text, credits and original subtitle text. Executable and native graphic labels are tracked separately.
- A proportional **Noto Sans** font with embedded 4x rasters; no emulator texture replacement pack is required.
- Latin name entry and Auto-name pools; translated setup/date, shop, equipment, status, party, calendar, Chronicle and catalog interfaces, with selected overlap and clipping fixes.
- Full character creeds/sayings, clearer Potential labels, original Oreshika: Tainted Bloodlines vital/element icon designs, compact battle item names and wrapped battle descriptions.

### Release status

**This is an early draft build. Human proofreading and full-game playtesting are needed.** Indexed coverage does not certify meaning or visual fit throughout the game. Selected screens and fixes were checked in a cold-started PPSSPP instance; static measurements and actual in-game checks are recorded separately.

- Full playthrough and physical PSP testing remain pending. The new-child class-description screen has not been visually verified.
- Some names/readings remain provisional, including 62 Auto-name readings and 23 credit readings. Some decorative Japanese artwork remains; other long/dynamic text may need layout changes.
- Japanese audio is retained. Voices without original text do not gain subtitles.
- The image contains a decrypted EBOOT and was tested in PPSSPP. Native 1x rendering scales the same 4x glyph rasters down.

**Boot the patched ISO fresh and load a normal save.** Save states retain older text, fonts and patch data. QA used an isolated emulator profile and restored its saves; the user's normal save source was not changed.

### How it was translated

This is a **machine translation**, produced with large language models and edited using neighboring scene text and a project glossary. Translation choices, provisional readings, static checks and selected in-game evidence are recorded in the repository. Human proofreading and playtesting are welcome.

### Acknowledgements

- **Noto Sans**, © 2018 The Noto Project Authors, SIL Open Font License 1.1; font provenance and licence are in the repository.
- **PPSSPP**, used for native framebuffer captures, debugger checks and gameplay/UI verification.
- The original **Oreshika: Tainted Bloodlines** vital/element icon designs, adapted for this PSP patch. Original game artwork retains its owners' rights.
- [Macross Triangle Frontier](https://github.com/retro-trans/Macross-Triangle-Frontier), whose repository and release format served as the reference, and [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools) for verified packaging and automatic patch discovery.

### Source code

English translation exports, glossaries, UI metadata and tools are in the [project repository](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke). GitHub's source archives contain the tagged repository snapshot. Apply the `.xdelta` asset to patch the game; complete game images are not distributed.

### Contribute

Bug reports, proofreading and playtesting are welcome at **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)** or in repository issues. Include the patch version, steps and affected screen.

Apply the patch to your own disc image. No complete game images are included.

# Ore no Shikabane o Koete Yuke — English patch

English fan translation of the Japanese PSP game **Ore no Shikabane o Koete Yuke**
(**UCJS-10117**). Apply the xdelta patch to your own original disc image.
This repository contains translation text, glossaries, UI metadata and tools;
game images, extracted data, saves and Japanese working scripts remain local.

Current local test build: **0.2.38**, 2026-10-18; archive-text draft: **0.2.38**.

## Applying the patch

Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools/releases/latest) app:

1. Click **Refresh catalog**, open **Automatic**, and select your original Japanese ISO.
2. Select **Ore no Shikabane o Koete Yuke**, choose **0.2.38** or **Latest**, and select a new output filename.
3. Apply the patch. The app verifies the source and the complete resulting image.

For manual patching, download `OreNoShikabane-English-0.2.38.xdelta` from
[Releases](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke/releases/latest) and use xdelta3 or Delta Patcher:

```text
xdelta3 -d -s "Ore no Shikabane o Koete Yuke (Japan).iso" OreNoShikabane-English-0.2.38.xdelta "Ore no Shikabane o Koete Yuke English 0.2.38.iso"
```

Compare the source/output sizes and SHA-256 values with the release's
`BUILD-MANIFEST.json`. Only the supported original Japanese ISO is an input to
this first release. Boot the patched ISO fresh and load a normal save; older save
states retain old text and graphics in memory. The image has a decrypted EBOOT
and has been tested in PPSSPP. Physical PSP testing remains pending.

## Included content and status

- English drafts for all **8,027 distinct indexed main strings**, covering 11,026 Japanese-bearing archive records. This is indexed draft coverage, not full-game translation approval.
- Dialogue and narration, menus/help, character and item data, descriptions, credits and original subtitle text, plus separately tracked executable and graphic labels.
- An embedded proportional **Noto Sans** font with 4x rasters; no PPSSPP texture replacement pack is required.
- Latin name entry and Auto-name choices, translated native UI artwork, compact battle item names, wider menus, complete character traits, and clearer status/battle displays.
- Original Oreshika: Tainted Bloodlines vital/element icon designs adapted to native PSP UI slots.
- Wider story dialogue with a partly transparent background, and a wider home-menu description panel that keeps both Rest help lines inside its frame.

**This is an early draft build. Human proofreading and full-game playtesting are needed.**
Selected setup, inventory, shops, character/status, battle and home screens were
checked in PPSSPP; the whole game has not been played through. Some names/readings
are provisional, some decorative Japanese artwork remains, and other dynamic or
long text may still need layout work. Audio remains Japanese.

The translation was produced with large language models and edited using scene
context and a project glossary. Testing and uncertainty are recorded in
[the changelog](CHANGELOG.md), [progress](docs/translation_progress.json) and
[build evidence](docs/local_build_status.json). Fresh-boot UI checks and static
measurements are recorded separately.

## Repository layout and building

- `tools/`: extraction, translation/export, font, native layout, graphics, build and QA tools.
- `work/translation/en/`: source-free `*.en.json` exports.
- `work/glossary/`: names, readings and shared terminology; Japanese names/UI terms are permitted.
- `work/ui/`: coordinates, widths, IDs and selected QA metadata. Native screenshots stay local.
- `docs/`: format/investigation notes, build history and release metadata.
- `incoming/noto-sans/`: the font, its provenance and SIL OFL licence.
- `work/source/`, `work/output/`, and other `incoming/` files: ignored local extraction, test images and external game assets.

See [local build/development notes](docs/LOCAL_DEVELOPMENT.md) and the
[release guide](docs/RETRO_TRANS_RELEASES.md). Reproduction requires your own
original Japanese ISO, local extraction and intermediate build stages; icon
source extraction additionally needs your own Oreshika: Tainted Bloodlines files.
Run mutating tools as a dry run before adding `--write`.

## Credits and licence

Noto Sans © 2018 The Noto Project Authors, used under
[SIL Open Font License 1.1](incoming/noto-sans/LICENSE.txt). PPSSPP's debugger and
software renderer were used for native text/layout testing. Repository/release
presentation follows [Macross Triangle Frontier](https://github.com/retro-trans/Macross-Triangle-Frontier).

Original translation tools and English text: [MIT](LICENSE). The font retains
its own licence. The games, original artwork and other game assets retain their
respective owners' rights; the MIT licence does not cover them.

Bug reports, proofreading and playtesting are welcome at
**[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)** and in repository issues.
Read [CONTRIBUTING.md](CONTRIBUTING.md) before editing.

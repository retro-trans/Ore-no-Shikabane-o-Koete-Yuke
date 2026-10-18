"""Prepare the reference-style public README and first release notes. Dry run first."""
import argparse,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO='https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke';V='0.2.38'
README='''# Ore no Shikabane o Koete Yuke — English patch

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
[Releases](REPO/releases/latest) and use xdelta3 or Delta Patcher:

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
'''.replace('REPO',REPO)
NOTES='''English fan translation of **Ore no Shikabane o Koete Yuke** for PSP (**UCJS-10117**).

### Apply

**Recommended:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools/releases/latest) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO, choose **0.2.38** (or **Latest**), and select a new output filename. The app downloads the matching patch and verifies the result.

**Manual patching:** [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) and [xdelta3](https://github.com/jmacd/xdelta) accept the same asset:

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO (UCJS-10117) | `OreNoShikabane-English-0.2.38.xdelta` |

```text
xdelta3 -d -s "Ore no Shikabane o Koete Yuke (Japan).iso" OreNoShikabane-English-0.2.38.xdelta "Ore no Shikabane o Koete Yuke English 0.2.38.iso"
```

Original ISO: SOURCE_BYTES bytes; SHA-256 `SOURCE_SHA`.

Release output: 1,081,079,808 bytes; SHA-256 `c7a51ee07bf8f42d47d65c670c80e270eae9fe7743551b1ffe732e3efe6569f8`.

`BUILD-MANIFEST.json` records the exact source, output and patch identities. `VALIDATION.json` records the complete xdelta round trip, and `SHA256SUMS.txt` covers the downloads. This first public release provides a full patch from the original; it does not offer upgrade patches from unpublished local test builds.

### What's included

- English drafts for all **8,027 distinct indexed main strings**, covering 11,026 Japanese-bearing archive records: dialogue/narration, menus/help, descriptions, character/item text, credits and original subtitle text. Additional executable and native graphic labels are tracked separately.
- A proportional **Noto Sans** font with embedded 4x rasters, including UI/battle artwork and digits. Texture replacement is disabled in the verified build.
- Latin name entry and Auto-name pools; translated setup/date, shop, equipment, status, party, calendar, Chronicle and catalog interfaces, with selected overlap and clipping fixes.
- Full character creeds/sayings, clearer Potential labels, original Oreshika: Tainted Bloodlines vital/element icon designs, compact battle item names and wrapped battle descriptions.
- Wider story dialogue with a partly transparent background. Build 0.2.38 also widens the centered home help panel, retaining the complete Rest description.

See the [changelog](REPO/blob/main/CHANGELOG.md) for the accumulated local changes and selected runtime evidence.

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

English translation exports, glossaries, UI metadata and tools are in the [project repository](REPO). GitHub's source archives contain the tagged repository snapshot. Apply the `.xdelta` asset to patch the game; complete ISO files are not distributed.

### Contribute

Bug reports, proofreading and playtesting are welcome at **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)** or in repository issues. Include the patch version, steps and affected text/screen.

No complete game images are included. Apply the patch to your own disc image.
'''.replace('REPO',REPO)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();source=ROOT/'Ore no Shikabane o Koete Yuke (Japan).iso';h=hashlib.sha256()
 with source.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 notes=NOTES.replace('SOURCE_BYTES',format(source.stat().st_size,',')).replace('SOURCE_SHA',h.hexdigest())
 print('Public README, preserved local development notes and release notes for',V);print('Original ISO:',source.stat().st_size,h.hexdigest());print('Release note sections:',[line for line in notes.splitlines() if line.startswith('### ')])
 if not a.write:return
 archive=ROOT/'docs/LOCAL_DEVELOPMENT.md'
 if not archive.exists():
  old=(ROOT/'README.md').read_text(encoding='utf-8');old=old.replace('](docs/','](').replace('](work/','](../work/');archive.write_text(old,encoding='utf-8')
 (ROOT/'README.md').write_text(README,encoding='utf-8');out=ROOT/'docs/releases'/V;out.mkdir(parents=True,exist_ok=True);(out/'RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
if __name__=='__main__':main()

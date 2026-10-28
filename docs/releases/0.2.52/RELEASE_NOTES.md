English fan translation of **Ore no Shikabane o Koete Yuke** for PSP (**UCJS-10117**).

**PSP hardware tested:** 0.2.52 was confirmed working by the tester on a physical PSP running **6.61 ARK-5**, with the installed **PBOOT.PBP update disabled**. The same ISO was checked in PPSSPP. Full-game playtesting remains incomplete.

### Apply

**Recommended:** Use the latest [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools/releases/latest). Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or public English **0.2.48** ISO, choose **0.2.52** or **Latest**, and choose a new output filename. The app selects the matching patch and verifies the result.

For manual patching, use [Delta Patcher](https://github.com/marco-calautti/DeltaPatcher) or [xdelta3](https://github.com/jmacd/xdelta) with one matching patch:

| Input image | Patch |
| --- | --- |
| Original Japanese UCJS-10117 ISO | `OreNoShikabane-English-0.2.52-full.xdelta` |
| Public English 0.2.48 ISO | `OreNoShikabane-English-0.2.48-to-0.2.52.xdelta` |

```text
xdelta3 -d -s "Ore no Shikabane o Koete Yuke (Japan).iso" OreNoShikabane-English-0.2.52-full.xdelta "Oreshika-English-0.2.52.iso"
```

Original ISO: 847,937,536 bytes; SHA-256 `03791a833656ddebadff7848a6296fc1698b52dfd7052c91572dd8b800fd569a`.

English 0.2.48 input: 1,081,337,856 bytes; SHA-256 `43569c29fb58ece6ade5f02f4ac39ea8df86041ba6bce7fc461f7293e1dcc907`.

Release output: **1,077,544,960 bytes**; SHA-256 `5e821290c20f25f0642c4834f602e9fc7d46925d820f3ccfd83b78cc7f86590b`.

Both patches reproduce the same tested ISO. `BUILD-MANIFEST.json`, `VALIDATION.json` and `SHA256SUMS.txt` identify and verify the downloads. Earlier local test builds are not release-patch inputs. If you already have the working 0.2.52 test ISO, its bytes are identical and you do not need to repatch.

### Required PSP setup: disable the installed update

1. Fully close the game. Copy the new ISO into the PSP storage's `ISO` folder using a distinct filename.
2. Find **`PSP/GAME/UCJS10117/PBOOT.PBP`** on the storage. On PSP Go, check internal storage and any memory card containing the update.
3. Back up that file to your computer, then rename **only** `PBOOT.PBP` to **`PBOOT.PBP.disabled`**. If it is absent, skip this step. Leave `EBOOT.PBP` and `PSP/SAVEDATA` unchanged.
4. Fully power off/restart the PSP, launch the new ISO, and confirm **v0.2.52** on the title screen. Load a normal save; the home menu should have three separated columns and a wide description box.
5. If startup fails, restore the exact original `PBOOT.PBP` filename and report the PSP model, firmware and ISO hash. If the layout still looks old, check the ISO selected and look for another active update copy.

The installed update can launch its own original executable and bypass the translation's native layout/font changes, even while the text is English. Disabling it lets the patched executable run. No firmware change or plugin installation was part of the successful test. This patch does not port the official update's gameplay changes.

[Complete PSP setup and troubleshooting guide](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke/blob/main/docs/PSP_SETUP.md).

### What's changed since 0.2.48

- Resolved the reported startup failure on the tested PSP setup. The executable uses a contiguous loading layout that avoids erasing added translation code/data during loading, and clears the obsolete extra decryption request.
- Packaged the native executable in a compressed, authenticated PSP container while preserving the intended game code, data and addresses.
- Translated the commodity broker's native banner, Money/ryo labels, quantity/confirmation/retry prompts and graph labels; separated headings and added a contracts unit specific to trading.
- Preserved all earlier translation, native font, UI, dialogue wrapping and tournament fixes. The release contains the exact hardware-tested 0.2.52 ISO bytes.

See the [changelog](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke/blob/main/CHANGELOG.md) and [recorded hardware result](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke/blob/main/work/ui/psp-contiguous-0.2.52/hardware-report.json).

### What's included

- English drafts for all **8,027 distinct indexed main strings**, covering 11,026 Japanese-bearing archive records: dialogue/narration, menus/help, descriptions, character/item text, credits and original subtitle text. Executable and native graphic labels are tracked separately.
- A proportional **Noto Sans** font with embedded 4x rasters; no emulator texture replacement pack is required.
- Latin name entry and Auto-name pools; translated setup/date, shop, equipment, status, party, calendar, Chronicle and catalog interfaces, with selected overlap and clipping fixes.
- Full character creeds/sayings, clearer Potential labels, original Oreshika: Tainted Bloodlines vital/element icon designs, compact battle item names and wrapped battle descriptions.

### Release status

**This is an early draft build. Human proofreading and full-game playtesting are needed.** Indexed coverage does not certify meaning or visual fit throughout the game. Selected screens and fixes were checked in a cold-started PPSSPP instance; static measurements and actual in-game checks are recorded separately.

- **PSP hardware tested:** the tester confirmed 0.2.52 works on 6.61 ARK-5 with `PBOOT.PBP` disabled. This confirms startup/operation on that setup; full playthrough and broader model/firmware testing remain pending. The new-child class-description screen has not been visually verified.
- Some names/readings remain provisional, including 62 Auto-name readings and 23 credit readings. Some decorative Japanese artwork remains; other long/dynamic text may need layout changes.
- Japanese audio is retained. Voices without original text do not gain subtitles.
- The image uses a compressed native executable with a contiguous load layout. Native 1x rendering scales the embedded 4x glyph rasters down. The official 1.01 update's gameplay changes are not incorporated.

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

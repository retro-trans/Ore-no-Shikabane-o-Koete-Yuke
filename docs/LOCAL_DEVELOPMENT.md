# Ore no Shikabane o Koete Yuke — English translation

Current local test build: **0.2.38**, 2026-10-18; archive-text draft: **0.2.38**.
An experimental native VWF patch embeds
4× font rasters directly in the game executable, with texture replacement disabled.
The English draft covers **8,027/8,027 distinct main strings (100%)** and all
11,026 Japanese-bearing archive records. This is draft coverage, not full-game approval.
Eighteen executable records, six shop literals, two equipment literals, three result/pause literals, two Chronicle date formats, two Pack literals, and 70 native graphic assets/label groups are recorded separately.
Build 0.2.8 adds 14 previously uncatalogued standalone name-entry prompts.
Build 0.2.16 replaces the Auto-name pools with 180 curated Latin choices
(22 surnames, 85 female names and 73 male names), each at most eight letters.
The glossary marks 62 conventional kanji readings as provisional. The 1,735
original choices remain in the source archive; the earlier 100% figure refers
to the indexed EZBIND text draft.
Full-game translation, visual fit checks and real PSP testing remain incomplete.

Read [the investigation](translation-investigation.txt) for counts, scope,
known uncertainties and the next translation batch. [Progress](translation_progress.json)
and [the changelog](CHANGELOG.md) record the current state.

## Files

- `work/source/`: ignored local extraction, inventories and Japanese source corpus.
- `work/glossary/core.json`: names, terms, sources and translation policies.
- `work/translation/en/initial_batch.json`: ignored bilingual editorial working file.
- `work/translation/en/initial_batch.en.json`: English-only export suitable for Git.
- `work/translation/en/initial_draft_input.json`: ignored seed for the initial batch.
- `work/ui/`: native glyph metrics, runtime evidence and pending text-box measurements.
- `work/output/english-native-0.2.38.iso`: centered wider home-menu description box, including complete Rest help. See [QA evidence](../work/ui/home-help-0.2.38/verification.json).
- `work/output/english-native-0.2.37.iso`: wider translucent story dialogue and translated Pack confirmation/count. See [QA evidence](../work/ui/dialogue-window-0.2.37/verification.json).
- `work/output/english-native-0.2.36.iso`: clear battle commands, wide Equipment popup, wrapped descriptions and compact consumable names. See [QA evidence](../work/ui/battle-menu-0.2.36/verification.json).
- `work/output/english-native-0.2.35.iso`: extended Status/Abilities frame around character traits and separate Potential label/axis/icon columns. See [QA evidence](../work/ui/status-layout-0.2.35/verification.json).
- `work/output/english-native-0.2.34.iso`: Item Catalog overlap fixes, compact Acquired caption and Scrolls fraction without items. See [QA evidence](../work/ui/catalog-0.2.34/verification.json).
- `work/output/english-native-0.2.33.iso`: translated Chronicle date headings and compact navigation captions clear of button icons. See [QA evidence](../work/ui/chronicle-0.2.33/verification.json).
- `work/output/english-native-0.2.32.iso`: English herbal-medicine and all twelve calendar ribbons within the original memory budgets. See [QA evidence](../work/ui/left-banners-0.2.32/verification.json).
- `work/output/english-native-0.2.31.iso`: original native Oreshika HP/MP/HLTH and element icons, replacing the earlier screenshot copies. See [source and QA evidence](../work/ui/native-icons-0.2.31/verification.json).
- `work/output/english-native-0.2.30.iso`: complete character creeds/sayings, bounded formatting and two-line native placement. See [QA evidence](../work/ui/profile-traits-0.2.30/verification.json).
- `work/output/english-native-0.2.29.iso`: reused the reference HP/MP/HLTH symbols in compact and standard native badges; prior element icons and layout fixes retained. See [QA evidence](../work/ui/vital-icons-0.2.29/verification.json).
- `work/output/english-native-0.2.28.iso`: reused the four reference element icons in shared native sprites; all0.2.27 fixes retained. See [QA evidence](../work/ui/element-icons-0.2.28/verification.json).
- `work/output/english-native-0.2.27.iso`: translated battle/pause labels, compact headings, separated equipment rows and clearer Potential chart. See [QA evidence](../work/ui/six-screens-0.2.27/verification.json).
- `work/output/english-native-0.2.26.iso`: 83 native HD badge, heading, chart and combat-digit assets; selected remaining graphic translations. Battle visual QA pending. See [QA evidence](../work/ui/hd-fonts-0.2.26/verification.json).
- `work/output/english-native-0.2.25.iso`: English battle HP/MP badges and Genta/Orin display aliases. See [QA evidence](../work/ui/battle-hud-0.2.25/verification.json).
- `work/output/english-native-0.2.24.iso`: tighter English exclamation spacing, verified in the reported Orin dialogue; all earlier fixes retained.
- `work/output/english-native-0.2.23.iso`: English opening disclaimer in the project font; all earlier UI fixes retained. See [startup notes](startup-disclaimer.txt).
- `work/output/english-native-0.2.22.iso`: English status badges and separated detailed-roster equipment/status columns. See [layout notes](detailed-roster-layout.txt).
- `work/output/english-native-0.2.21.iso`: English character/spell labels, wider character submenu, full-height portrait selector, two-column spell grid and separated name/age/MP rows. See [layout notes](character-spells-layout.txt).
- `work/output/english-native-0.2.20.iso`: translated equipment/role/slot labels, gender text and Missing portraits; four equipment rows, wider Divine Union submenu, two-line deity list and complete offering requirements. See [equipment/deity layout notes](equipment-deities-layout.txt).
- `work/output/english-native-0.2.19.iso`: translated and rearranged native shop screen, separate ownership/funds, wider stock/prices, four-member comparison paging, complete restrictions and English Gear Stats popup. The two large background kanji remain unchanged; see [shop layout notes](shop-layout.txt).
- `work/output/english-native-0.2.18.iso`: wider shared inventory, category and shop windows. Two item columns, native paging, full descriptions, and adjacent shop menus verified in game. All 631 fixed item names and 232 descriptions fit the measured budgets without changing wording or font size; see [layout notes](inventory-window-layout.txt).
- `work/output/english-native-0.2.17.iso`: preserved curse-explanation and Itsuka dialogue reflow fixes; see [reflow notes](dialogue-reflow.txt).
- `work/output/english-native-0.2.16.iso`: preserved enlarged footer, Latin Auto names and native eight-character/HD font fixes. See [the build notes](latin-auto-and-controller.txt).
- `work/output/english-native-0.2.15.iso`: preserved eight-character name build. Long-name saves require 0.2.15 or newer; see [name-entry details](eight-character-names.txt).
- `work/output/english-native-0.2.12.iso`: preserved native English keyboard build with the original three-character limit.
- `work/output/english-native-0.2.11.iso`: preserved wider dungeon destination menu and English Mount Oe banner.
- `work/output/english-native-0.2.10.iso`: preserved translated overworld signs, seasonal copies and selected-destination banners.
- `work/output/english-native-0.2.9.iso`: preserved complete deity confirmation, wider character/home/studio menus and translated Portrait Studio artwork.
- `work/output/english-native-0.2.8.iso`: preserved setup fixes, Gregorian birth-date cursor and native-font percentage values.
- `work/output/english-native-0.2.7.iso`: preserved build before the setup fixes.
- `work/output/english-native-0.2.6.iso`: preserved build before the footer addition.
- `work/output/english-native-0.2.2.iso`: preserved archive-text build.
- `work/output/english-native-0.2.1.iso`: preserved earlier partial translation build.
- `work/output/english-native-0.2.0.iso`: preserved previous test build with runtime evidence.
- `work/output/native-vwf-0.2.0.iso`: native-font-only diagnostic build.
- `docs/`: research, counts, progress and workflow notes.
- `tools/`: extraction, catalog, export and verification utilities.
- `incoming/`: external files for investigation.

## Reproduce the research

Python 3.8+ and the standard library are sufficient. Run from this folder.
Mutating utilities default to a dry run: inspect their sample output before adding
`--write`. The input ISO must remain local and unmodified.

```text
python tools/extract_iso.py
python tools/extract_iso.py --write
python tools/catalog_text.py
python tools/catalog_text.py --write
python tools/prepare_translation.py
python tools/prepare_translation.py --write
python tools/strip_jp.py
python tools/strip_jp.py --write
python tools/check_translation.py
python tools/report_progress.py
python tools/report_progress.py --write
```

`prepare_translation.py --seed PATH --output PATH` joins later editorial seeds too.
It refuses to overwrite changed translations. Make editorial changes explicitly
in the bilingual working file, then regenerate that file's English-only copy with
`strip_jp.py PATH --write`. Check each batch with `check_translation.py --batch PATH`.
Progress aggregates all English-only batches and excludes readings and repeated
speaker labels from the main-string denominator.

## Local test build

See [native patch and build notes](native-vwf.txt) for prerequisites, binary
guards, memory details and validation limits. With the verified decrypted local
ELF and Noto Sans inputs present, inspect each dry run before writing:

```text
python tools/build_vwf.py
python tools/build_vwf.py --write
python tools/test_native_vwf.py
python tools/build_embedded_text.py
python tools/build_embedded_text.py --write
python tools/check_embedded_text.py
python tools/prepare_setup_fixes.py
python tools/prepare_setup_fixes.py --write
python tools/strip_jp.py work/translation/en/initial_batch.json
python tools/strip_jp.py work/translation/en/initial_batch.json --write
python tools/strip_jp.py work/translation/en/ui_batch_002.json
python tools/strip_jp.py work/translation/en/ui_batch_002.json --write
python tools/strip_jp.py work/translation/en/name_entry/prompts.json
python tools/strip_jp.py work/translation/en/name_entry/prompts.json --write
python tools/repack_text.py
python tools/repack_text.py --write
python tools/build_title_cards.py --version 0.2.8
python tools/build_title_cards.py --version 0.2.8 --write
python tools/build_localized_sfo.py
python tools/build_localized_sfo.py --write
python tools/build_title_branding.py --version 0.2.8 --source work/output/english-native-0.2.8/data.graphics.ore
python tools/build_title_branding.py --version 0.2.8 --source work/output/english-native-0.2.8/data.graphics.ore --write
python tools/build_setup_ui.py
python tools/build_setup_ui.py --write
python tools/test_setup_ui.py
python tools/build_iso.py --version 0.2.8 --elf work/output/english-native-0.2.8/EBOOT.setup.elf --ore work/output/english-native-0.2.8/data.setup.ore --sfo work/output/english-native-0.2.6/PARAM.SFO --output work/output/english-native-0.2.8.iso
python tools/build_iso.py --version 0.2.8 --elf work/output/english-native-0.2.8/EBOOT.setup.elf --ore work/output/english-native-0.2.8/data.setup.ore --sfo work/output/english-native-0.2.6/PARAM.SFO --output work/output/english-native-0.2.8.iso --write
```

The font atlas and metrics stay at 0.2.0; 0.2.8 extends its selector for numeric
non-breaking-space padding. The 0.2.3 executable adds two relocated system
message tables; 0.2.4 also translates six native menu-card graphics. Live checks
verify table loading and native-font execution. Actual display captures verify
the title cards, caption and gender setup. Other scenes still need layout review.
Build 0.2.7 adds the version and group to a native title foreground sprite;
see `work/ui/title-branding-0.2.7/` for placement and capture evidence.
Setup fixes and reproduction details are in `docs/setup-fixes.txt`; actual
screen and native-font evidence is under `work/ui/setup-fixes-0.2.8/`.

Build 0.2.9 applies the menu fixes to the verified 0.2.8 components. Inspect the
dry runs before writing; use a fresh output path if reproducing an existing ISO:

```text
python tools/build_menu_fixes.py
python tools/build_menu_fixes.py --previews
python tools/build_menu_fixes.py --write
python tools/test_menu_ui.py
python tools/build_iso.py --version 0.2.9 --elf work/output/english-native-0.2.9/EBOOT.menu.elf --ore work/output/english-native-0.2.9/data.menu.ore --sfo work/output/english-native-0.2.6/PARAM.SFO --output work/output/english-native-0.2.9.iso
python tools/build_iso.py --version 0.2.9 --elf work/output/english-native-0.2.9/EBOOT.menu.elf --ore work/output/english-native-0.2.9/data.menu.ore --sfo work/output/english-native-0.2.6/PARAM.SFO --output work/output/english-native-0.2.9.iso --write
```

See `docs/menu-fixes.txt` for native layout settings and verification scope.

Twenty-three staff-name romanizations remain provisional, as authorized by the
user after research; the glossary records the uncertain readings and alternatives.
The five neutral alternatives approved by the user are applied and marked as
adaptations. Draft coverage does not include unexamined
image lettering or executable text, and does not measure in-game approval.

The ISO builder preserves the source image and refuses to overwrite a previous
test ISO. Choose a new version/output name for another build. Generated game
binaries remain local and ignored. Python dependencies for font work are Pillow,
Keystone and Unicorn; the optional debugger client uses websockets.

## Translation and build requirements

Follow `AGENTS.md` and `BASE_RULES.md`. Draft the full meaning, preserve each
record and engine token, and use the glossary. Record ambiguity rather than
inventing context or gender. Observed Japanese lengths are not display limits.
Expanded text is relocated and pointers are rebuilt. The native font changes do
not enlarge text boxes or implement new wrapping. Run an in-game visual check
before claiming a fit. The 4× setting refers to font raster detail; PSP display
resolution remains 480×272. PPSSPP can separately render at 4× for inspection.

Run `tools/strip_jp.py --write` before committing English translation copies.
Never commit the ISO, extracted game data or Japanese dialogue working files.
Japanese names, UI terms and necessary engine tags are allowed. This folder was
not a Git repository when this snapshot was created.

Builds use `0.x.y` versions with a changelog. A future GitHub release requires an
explicit user request and compatibility with Retro Trans Tools.

# Changelog

## 0.2.38 (2026-10-18)

- Replaced the 189,434,623-byte patch with a 2,559,594-byte compact encoding and republished at the user's explicit request. Rebuilt the manifest, validation report and checksums; verified the exact same source/output ISO identities through Retro Trans Tools and all four uploaded asset hashes. The catalog retires the original patch record while preserving its history, and routes to the new compact filename. Scoped catalog validation passed.
- Temporarily unpublished the original release at the user's request before replacing its assets. The version, source commit and Git tag remain unchanged; the compact encoding produces the identical 0.2.38 ISO.
- Verified all four uploaded asset sizes/SHA-256 hashes against the local round-trip-verified bundle. Retro Trans catalog refresh succeeded, and its source recognition plus Latest/specific/next-version routes resolve the original ISO to 0.2.38. See `docs/releases/0.2.38/PUBLICATION.json`.
- Published the first public repository/release using Macross Triangle Frontier's repository and release conventions: English-only translation exports, source tools, MIT/SIL OFL notices, contributor/build instructions, and Retro Trans Tools xdelta/manifest/checksum/round-trip packaging. Original and translated game images remain local.
- Extended the home menu description panel from 288 to 432 native pixels and kept it centered, moving its left edge from 96 to 24. Both Rest description lines now sit inside the box with comfortable right-side clearance.
- Kept all wording, line breaks, vertical positions and visual styling. The shared native resize automatically expands each help line to 426 pixels. Prior story dialogue width/transparency and other fixes remain unchanged.
- Measured all 34 related fixed help entries; the widest line is 378.857 pixels. Verified Rest and Divine Union descriptions in the final ISO, complete Rest text using native 4x glyphs, actual panel/line geometry and both patched instructions.
- Restored the isolated test saves and verified the user save source unchanged. This version is the first requested public release. Full-playthrough and physical PSP testing remain pending.

## 0.2.37 (2026-10-18)

- Translated the Pack's executable-only item confirmation to "Use [item]?" and its quantity caption to "Left: [count]". Preserved the native item substitution and numeric count.
- Widened the shared bottom story dialogue panel from 288 to 432 native pixels (50%), keeping its left edge at 24 and its right edge at 456. All dialogue wording, line breaks and script data remain unchanged. The reported Hayate passage now fits its shared panel by measured native font advances.
- Set only that panel's background to 200/255 opacity (about 78%), allowing the character sprite to show through. Text, name labels, borders and other menus retain their original opacity. The native layout relocates the advance indicator to the wider panel's right corner.
- Added a placement check for scenes that size the panel before positioning it. Verified ten geometry cases and ten update cases in MIPS, including excluded menu/alert layouts, caller state and one-time native resize behavior.
- Verified actual story dialogue, complete native 4x text, background transparency, advance-icon placement, Pack item confirmation and remaining count in the final ISO. Isolated test saves restored; user save source unchanged. Local test build only; no release. Full-playthrough and physical PSP checks remain pending.

## 0.2.36 (2026-10-18)

- Shortened the battle command Skills / Other to Skills and updated translated references, so it fits beside Retreat in the existing two-column command menu.
- Widened the Items/Equipment popup to contain Equipment and aligned it with the main menu's left edge, keeping it clear of the party portraits.
- Added measured wrapping for battle item and Skills descriptions. The complete source text is split into owned native text children at 16-pixel spacing; plain newlines alone are ignored by this renderer. Grew tooltips upward to retain their existing bottom edge above the battle HUD.
- Audited all 66 consumable names against Young Leaf Pills' width. Shortened 47 overlong names, retaining distinct element/stat/material identities; updated translated references and the glossary consistently. Evergreen Elixir and other names already within the budget remain unchanged. Equipment and collectible names use their existing wider lists.
- Passed actual MIPS wrapping checks for all 223 item descriptions and three Skills descriptions: complete text, source buffers, line widths, up to three lines, child spacing, buffer guard and caller registers/stack. Verified the final ISO's battle menu, Equipment popup, full ring/Elixir tooltips and Div. Favor Orb slot, including native 4x font UV checks. Seven native hooks/coordinates, submenu width and wrap code read back correctly.
- Item IDs, effects, inventory, gameplay, saved data and earlier icons/profile/catalog fixes remain unchanged. Isolated QA saves restored and user source save verified unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

## 0.2.35 (2026-10-18)

- Extended the Status and Abilities frames to 108 pixels, matching Equipment, so the complete Creed/Saying text sits inside the box. Existing two-line formatting and Equipment trait visibility remain unchanged.
- Gave Potential's full Spirit, Skill and Body labels a separate column: inset labels, moved the gold axis and element icons right, and aligned the bars/grid beside them. Reduced only the display width scale to keep maximum bars inside the existing frame. Stat values, calculations and saved data are unchanged.
- Inspected supplied Oreshika US status, shared icon and common UI sheets. No dedicated pictograms for the three category names were identified in those sheets; retained readable full labels. Existing original Oreshika vital and element symbols remain unchanged. Additional sheet audit records unsupported layouts rather than claiming they were inspected.
- Kept the header and its owned trait text above the enlarged background through the native draw key in both character-screen constructors. Verified final-ISO character screens and switching between Status, Abilities and Equipment, including returning to Abilities. Native font UV checks cover the full group captions and reported traits. Readback verifies eight geometry/layer instructions, the display scale and embedded grid pixels/palette. Existing executable allocation, translations, catalog fixes and unrelated archive members are unchanged except the title version footer.
- Original isolated QA saves restored; user source save unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

## 0.2.34 (2026-10-18)

- Widened Item Catalog category cells so Weapons and Armor no longer overlap. Native tab navigation and selection frames remain aligned.
- Separated the Other tab's escape quantities from Total Value rows and moved the collection caption/bar down to fit. Counts, money totals and collection calculations are unchanged.
- Changed Curios Total Acquired to Acquired and separated its heading, caption and count. Scrolls now shows a single compact fraction such as 0/73; removed its items suffix locally, preserving other shared item labels.
- Final ISO screen captures and native 4x glyph-UV checks cover Other, Curios and Scrolls; runtime readback verifies 27 instruction edits, tab width and both tiny adapters. Twelve MIPS adapter cases verify counts from zero to all 73 and preserve caller registers/stack. Unrelated archive members and previous translations/icons remain unchanged, except the title version footer.
- Restored isolated QA saves and verified the user source save was unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

## 0.2.33 (2026-10-18)

- Translated both native Chronicle date headings to Events: year / month, including the existing unknown-month marker. Relocated the complete English formats and retained parameter types/order, date arithmetic and historical record selection.
- Shortened Chronicle navigation to Year Start, Prev and Next. Moved Year Start left to clear the L icon and date frame; Next Year and the original button bindings remain. Event descriptions and portraits are unchanged.
- Passed 18 actual MIPS date cases covering normal months, year transitions, four special historical indices, the 16-bit upper bound, adjacent object guards and caller registers/stack. Final-ISO captures and native 4x glyph-UV checks verify both date forms and navigation labels, including moving to April and back to Kirara's birth entry. Five native patches and both relocated formats read back correctly.
- Retained all 0.2.32 banners, original Oreshika icons, full-profile fix and other translations. Only the three selected Chronicle text rows and title version footer change in the archive. Original isolated test saves restored; user source save unchanged.
- Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

## 0.2.32 (2026-10-18)

- Translated the left medicine-shop ribbon as HERBAL MEDICINE and all twelve home calendar ribbons as JANUARY through DECEMBER, including the reported APRIL label. Retained their seasonal diamond patterns, original positions and logical dimensions.
- Rendered the English labels in Noto Sans. Each 96x264 four-bit texture retains the original 13,744-byte resource size; only 388 bytes of tagged image-renderer support are appended. This preserves startup and sound-thread memory while allowing twice the original horizontal sampling. Existing eight-bit HD assets and untagged images retain their original paths.
- Passed 112 actual MIPS crop/binding cases across four/eight-bit textures and ten existing icon descriptor proxies. Verified the final ISO's April and herbal-medicine ribbons by actual framebuffer captures, native palette/pixel matches and complete UV rectangles. All twelve calendar images were preview checked; status icons and the full creed were also checked for regressions.
- Retained 0.2.31's original Oreshika icons, full-profile fix and existing translations. Other archive resources, including the background shop sign, remain unchanged except the title version footer. Restored the isolated test saves and verified the user source save was unchanged.
- Local test build only; no GitHub release. Other calendar months still need live calendar progression checks; full-playthrough and physical PSP testing remain pending.

## 0.2.31 (2026-10-18)

- Replaced all seven screenshot-derived icon designs with original assets extracted locally from the supplied Oreshika Tainted Bloodlines (USA) folder. HP/MP/HLTH come from udtx_status_us.ppt; Fire/Water/Wind/Earth come from uitx_icon_us.ppt. Exact native crops and source hashes are recorded under incoming/oreshika-native-icons/ and work/ui/native-icons-0.2.31/.
- Decoded the native BC3 texture sheets and retained their alpha/outlines. Added an independent block-decoder check across all 5,824 icon pixels; recovered crops match the source sheets exactly. Resized and palette-converted those originals into ten existing PSP variants: six vital icons and four shared element icons.
- Retained original image descriptors, logical dimensions, renderer code and all 0.2.30 profile/layout fixes. Only ten embedded image payloads/palettes and the title version footer changed; scripts and translations remain byte-identical.
- Passed 48 actual MIPS crop cases and ten descriptor-proxy cases. Final-ISO status/abilities and roster captures verify the original designs; native memory readback verifies all ten payloads and selected draw UVs. Additional selected context evidence is in the verification report. Original isolated-profile saves restored; user source save left unchanged.
- Local test build only; no GitHub release. Full-playthrough and physical PSP testing remain pending.

## 0.2.30 (2026-10-18)

- Fixed the nine-character status-profile cutoff responsible for “Creed: An” and “Saying: K”. The native formatter now uses a bounded 1,024-byte display buffer instead of the 20-byte stack buffer; character records and save layout remain unchanged.
- Moved traits below the stats panel, retaining the native font size and removing eight empty pixels at the bottom of its frame. Measured word wrapping displays up to two lines using an owned native text child, since ordinary newlines are ignored by this label renderer. Character changes clear and rebuild both lines through the existing label lifecycle. Traits appear on Status/Abilities and hide on the taller equipment tab; its four item rows retain their space.
- Verified Hayate’s full “Creed: An iron heart and iron will” and Kirara’s “Saying: Knock on wood.” in the final ISO, including repeated switches and screen re-entry. A separate test-only executable displayed the longest trait; no character/save records were changed for that fixture.
- Passed actual MIPS formatting/wrapping checks for all 731 translated traits, dynamic name/city substitutions, five stress cases, buffer guards, original stack buffer preservation and three text-child/placement cases. Final ISO checksums, native hooks and original isolated saves verified. Existing translations, icons and unrelated archive members remain unchanged except the version footer.
- Local test build only; no GitHub release. Full-playthrough and physical PSP testing remain pending.

## 0.2.29 (2026-10-18)

- Reused the reference Oreshika symbols for HP (red flexed arm), MP (blue open hand), and HLTH (green heart/pulse). Replaced six shared image variants: 11/107.ppt, 12/108.ppt and 13/113.ppt.
- Removed the lettered badge artwork and centered each symbol within the original compact 24x16 or standard 32x16 bounds. Symbol aspect ratios, number/bar positions, native descriptors and renderer code are preserved.
- Changed only six existing embedded palette/pixel payloads and the title version footer. All scripts, text tables, previous element icons, unrelated archive members and earlier 0.2.28 fixes are byte-identical.
- Passed 48 actual MIPS crop cases and six descriptor-proxy cases. Verified standard HP/MP/HLTH in the final ISO's status/roster screens and compact HP/MP in battle, including native payloads and full UVs. The compact HLTH slot has payload/geometry checks; its live context was not encountered.
- Original isolated-profile saves restored and user profile left unchanged. Screenshot source detail, full-playthrough and physical PSP testing remain limitations. Local test build only; no GitHub release.

## 0.2.28 (2026-10-18)

- Reused the four element icon designs from the user's Oreshika reference: red flame (Fire), blue droplet (Water), green swirl (Wind), and yellow earth/rock hexagon (Earth).
- Replaced the shared 17.ppt–20.ppt resources as four embedded native sprites. Extracted reference pixels have transparent outer corners and retain their square aspect within the original 16x14 logical bounds. Status, ability/Potential charts, deity lists and other consumers reuse these shared resources.
- Preserved all 0.2.27 text, gameplay scripts, layouts, existing native renderer hooks and unrelated archive members. Original resource loader sizes are unchanged. Updated the title footer to 0.2.28; texture replacement remains disabled.
- Passed 48 actual MIPS crop cases and four descriptor-proxy cases. Verified all four icons in the final ISO's status/abilities/Potential screen and deity list, including native palettes, pixels and UV coordinates. Original isolated-profile saves restored and user profile left unchanged.
- Source detail is limited by the supplied screenshot. Full-playthrough and physical PSP checks remain pending. Local test build only; no GitHub release.

## 0.2.27 (2026-10-18)

- Translated the native battle growth caption to Next Growth and shared pause funds to Money / ryo. Added spacing before currency and item-count units.
- Shortened crowded text to Points Earned, Free Slots, Naginata, Now: and Mo. %d:. Separate Victory Points / Offering Points totals retain their meaning; full class wording remains in descriptions and dialogue.
- Rewrote formation help as two complete lines: Press Circle to change / front and back rows. Engine controls and placeholders are preserved.
- Separated equipment name/gender, age and class into three rows, extended the portrait band and moved comparison stats below it.
- Kept full-size Spirit / Skill / Body captions, shifted Potential icons/bars/grid right and removed duplicate decorative words. Maximum bars stay inside the original frame.
- Passed six actual MIPS row cases, 24 chart-coordinate cases, five translation batch checks, ISO checksums and 14 runtime patch readbacks. All six reported screens checked in the final ISO with texture replacement disabled. Original project-profile saves restored. Full-playthrough and physical PSP checks remain pending. Local test build only; no GitHub release.

## 0.2.26 (2026-10-18)

- Replaced 83 native image assets with Noto Sans artwork: 33 shared badges, headings and chart backgrounds, plus 50 white/green/purple combat digit images across both number packs. Badges and digits use 4x rasters; tall headings and the Potential chart respect the PSP 512-by-512 texture limit.
- Translated remaining selected graphic labels: STATUS, BATTLE RESULTS, ONI RECORDS, ITEM CATALOG, Defeated, Specialty, WINS, Growth, compact Spirit/Skill/Body labels and Study/Train/Command badges. Replaced the Japanese Potential watermarks with SPIRIT, SKILL and BODY. Existing unknown-enemy question marks remain intentional.
- Embedded 63 unique native images and added image binding/UV hooks. Archive resources retain exactly their original decompressed sizes, keeping within the shared loader budget. Original logical geometry, crop rectangles, selection borders, scripts and unrelated archive members are preserved. Texture replacement remains disabled.
- Passed 40 actual MIPS crop cases and 83 descriptor-proxy cases. Verified the final ISO title, status, roster, equipment and spell screens, including physical texture sizes and native UVs. Oni Records and dungeon traversal were also checked on a shared-image candidate whose 32 images are byte-identical in the final build.
- Combat digits and battle-results artwork are included; their live battle visual check remains pending. Full-playthrough and physical PSP checks remain pending. Evidence: work/ui/hd-fonts-0.2.26/. Original project-profile saves restored after QA. Local test build only; no GitHub release.

## 0.2.25 (2026-10-18)

- Translated the compact battle stat icons to HP and MP, inside their original 24-by-16-pixel sampled regions. Portrait artwork, gauges, values and HUD coordinates remain unchanged.
- Added exact display aliases for Genta and Orin after text formatting and before native line construction. The text setter borrows the English strings; character records, saved names and source buffers are unchanged. Other names, prefixes and sentences retain their original handling.
- Verified 13 MIPS trampoline cases and 13 complete native text-setter cases, including correct child-line strings/counts, null/empty inputs, nonmatching names, source-buffer identity, stack and saved registers. The title/prologue boot with the native 4x font. Scripts and unrelated archive members match 0.2.24; the exclamation-spacing fix is retained.
- Battle visual QA: PARTIAL: title/prologue boot and native MIPS name conversion pass; combat transition halts at PC 0 in isolated testing, also observed on base 0.2.24; battle visual check pending. Evidence: work/ui/battle-hud-0.2.25/. Saves unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP tests remain pending.

## 0.2.24 (2026-10-18)

- Moved English exclamation marks closer to the preceding text by removing the original renderer's special 14-quarter-unit horizontal offset for ASCII `!`. Both marks in `!!` move together. Text, line breaks, font artwork and character advances remain unchanged.
- Verified the exact reported Orin passage ("Tch!! / Not even time to catch our breath!!") before and after in PPSSPP. Each exclamation moves left by about 2.75 native pixels at this text size; every other glyph position and all native 4x font UVs match.
- Compared all 65,536 UTF-16 values through the actual original and patched MIPS helper. Only ASCII `!` changes; question marks, fullwidth punctuation, null behavior, stack and saved registers are preserved. Scripts and unrelated archive payloads remain byte-identical to 0.2.23.
- Updated title footer to v0.2.24. Evidence: work/ui/punctuation-0.2.24/. Saves unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP tests remain pending.

## 0.2.23 (2026-10-18)

- Translated the opening fiction disclaimer in Noto Sans, centered on three complete lines. The text retains the source references to actual people, places, organizations, product names and similar subjects, without adding a coincidence claim.
- Rebuilt and relocated the executable-embedded startup archive, preserving its four logo assets and original warning palette. Both archive accessors point to the relocated data; the original allocation, timing and startup flow remain.
- Verified both accessors in actual MIPS execution and all four pointer instructions in PPSSPP memory. The rendered English image matches the expected native bitmap mask exactly, and the game continues to the v0.2.23 title. Scripts and unrelated archive members remain byte-identical to 0.2.22; all 49 translation batches pass.
- Evidence: work/ui/startup-disclaimer-0.2.23/. Save files remain unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP tests remain pending.

## 0.2.22 (2026-10-18)

- Translated native HP, LOY (Loyalty), and HLTH (Health) badges. Retained the English MP, ATK/DEF/AGI, role and equipment-slot labels from earlier builds.
- Arranged detailed-roster equipment into four separate rows, with a 208-pixel name budget. All 463 fixed equipment names fit; item names remain unchanged. Moved status columns clear of longer character names.
- Verified four native coordinate tables and both characters in actual PPSSPP captures, plus equipment-name font atlas/UVs. All 49 translation batches pass. Native instructions, scripts and unrelated archive members remain unchanged from 0.2.21. The archive builder can now retain its finished buffer to avoid an extra large allocation on 32-bit Python.
- Evidence: work/ui/detailed-roster-0.2.22/. Original project-profile saves restored after QA. Local test build only; no GitHub release. Full-playthrough and real PSP checks remain pending.

## 0.2.21 (2026-10-18)

- Translated the remaining visible spell-screen labels: MP, Spirit Req./Now and Skill Req./Now. Kept the English Head/Leader/Party flags from 0.2.20. The complete colored availability legend now uses the native HD font.
- Widened both character submenu columns from 32 to 84 pixels. Extended the red portrait selection image by the same 12 pixels added to the name/age cards.
- Reorganized spells into two 108-pixel columns with matching backgrounds/highlights and native scrolling. All 96 fixed spell names fit the measured 107-pixel text budget. Separated long character names, age and MP into rows, and spaced the MP Required caption clear of the badge.
- Verified 28 guarded native instructions and nine appended wrappers, actual MIPS geometry/caller state, native font atlas/UVs, both character selectors and later spell pages in PPSSPP. All 49 translation batches pass; scripts and unrelated archive payloads match 0.2.20. Evidence: work/ui/character-spells-0.2.21/. Original project-profile saves restored after QA. Local test build; no GitHub release. Full-game and physical PSP QA remain pending.

## 0.2.20 — 2026-10-17

- Translated the native EQUIPMENT ribbon, Head/Leader/Party flags, WPN/HEAD/ARM/ACC slot labels, Male/Female text, DIVINE UNION ribbon, and both native Missing portrait copies. Original palettes and other artwork remain; texture replacement stays disabled.
- Changed equipped slots to four 248-pixel rows, with a 36-pixel label reserve. Candidate equipment uses a 240-pixel column with four visible rows and native scrolling. Repositioned the list, source caption and description to fit the taller slot frame. All 463 fixed equipment names fit the 212-pixel equipped-name budget.
- Widened the Divine Union submenu to 128 pixels of text space. Deity lists now show four two-line entries with separate cost, element and gender. Widened the details frame to 176 pixels, centered the portrait, and moved the element clear of the name. Offering Points Required fits in full; all 127 fixed deity names fit the measured detail-name budget.
- Verified 35 guarded runtime patches, appended Latin labels and the native geometry wrapper. Actual MIPS checks cover geometry, saved caller state and dirty-register coordinate setup. Selected runtime evidence includes both genders, equipment selection, the long submenu label, deity scrolling and the Missing portrait. All 49 translation batches pass; script payloads and unrelated archive members remain byte-identical to 0.2.19. Evidence: `work/ui/equipment-deities-0.2.20/`. Local test build only; no GitHub release. Dynamic generated names, the pre-existing low-offering warning, full-game and physical PSP checks remain pending.

## 0.2.19 — 2026-10-17

- Translated native Funds/currency, ATK/DEF/AGI comparison labels, BUY / SELL ribbon and Gear Stats popup. The two large helmet/armor background kanji remain byte-identical. English text uses the embedded native 4× font, with texture replacement disabled.
- Separated ownership and funds at the top; widened stock cells to 398 pixels with right-aligned prices. Rebuilt the lower comparison area with four 100-pixel member cells, names above markers/stat changes, signed ASCII deltas, and native paging to all members. Retained the fifth allocation for destructor compatibility.
- Expanded four equipment-description buffers to 128 bytes each in a 736-byte stack frame. Separated stat/value and type/restriction fields, and added spaces without dropping restriction terms. The shared formatter also improves inventory details.
- Verified final components in game: 71 guarded runtime patches, appended strings/wrapper, native atlas/UVs, armor restrictions, positive/negative comparisons, weapons, General Store and inventory details. Actual MIPS tests cover coordinate assignments, register/stack preservation, buffer canaries and 49 paging cases for parties of 0–12. All 49 translation batches pass; script payloads and unrelated archive members remain byte-identical to 0.2.18. Evidence: `work/ui/shop-layout-0.2.19/`. Local test build only; no GitHub release. Full-game and physical PSP testing remain pending.

## 0.2.18 — 2026-10-17

- Widened shared inventory and item-detail frames to 472 native pixels. Item lists use two 232-pixel cells and four visible rows, with original cursor paging to all entries. Moved the heading and capacity frame/digits clear of the actions. Kept the full descriptions, existing line breaks, and native HD font size.
- Widened inventory categories to two 200-pixel cells, retaining all eight choices through native scrolling. Enlarged the shop selector and sell-source cells to 100 pixels, armor cells to 92, and weapon category cells to 84. Weapon columns each reserve another 24 pixels for icons; the complete submenu stays on screen and follows the enlarged parent automatically.
- Measured all 631 fixed item names within a 220-pixel text budget and all 232 descriptions within 456 pixels, including conservative signed 32-bit numeric substitutions. Selected actual screenshots verify item/category scrolling, the full Firestorm description, capacity placement, shop names and both submenus. Recorded 28 additional selected-context record IDs, bringing accumulated visual-fit evidence to 64; this does not represent full-game QA.
- Preserved all script payloads and other archive members from 0.2.17; only the native footer asset changes to v0.2.18. Forty guarded instructions/data fields and a 20-byte inventory margin wrapper change layout. Actual MIPS geometry/register checks and ISO directory/component checksums pass. Evidence: `work/ui/menu-fit-0.2.18/`; notes: `docs/inventory-window-layout.txt`. Physical PSP and full-playthrough checks remain pending. Local test build only; no GitHub release.

## 0.2.17 — 2026-10-17

- Fixed the reported Curse of Short Life overflow by reflowing the full sentence across three English lines, keeping “ordinary people” together. Its longest line now measures about 254.6 native pixels instead of 315.4.
- Rebalanced Itsuka's equipment reminder so its final line fits clear of the advance icon. Combined “And please look over all the information, too.” into one line, followed by “A quick skim will do!” on the next. Every word in all three passages is retained.
- Recorded a source/target-hash-specific exception for the requested three-to-two-line change. Other row identities, controls, source hashes and line-count checks remain enforced. All 49 translation batches pass.
- Updated the native footer to v0.2.17. The executable, font, name support and all other archive text/assets are retained from 0.2.16; unrelated payloads/members remain byte-identical. Compression/MLT round trips and ISO component checksums pass. Runtime evidence is recorded under `work/ui/dialogue-reflow-0.2.17/`. Local test build only; no GitHub release.

## 0.2.16 — 2026-10-17

- Enlarged the native title version to 14 pixels and the group line to 12 pixels, using the full `github.com/retro-trans` URL. The footer draws above Itsuka and unregisters before title resources are freed. Moved the title-menu help window left to keep both areas clear. Original copyright pixels and palette are preserved; no texture replacement.
- Auto now uses 22 Latin surnames, 85 female names and 73 male names, each within the eight-letter limit. These are curated original choices, without truncation. Explicit kana supplies 96 readings; 22 are Kyoto place names, and 62 kanji readings are conventional project choices marked provisional in `work/glossary/latin_auto_names.json`. The remaining original candidates stay in the source archive.
- Preserved the internal fullwidth Latin convention in Auto tables, keeping the original duplicate-name comparison compatible with saved/decoded names. All 180 choices pass actual MIPS encoding, decoding, comparison and record-boundary checks; the native VWF displays normal Latin glyphs.
- Diagnosed the recorded controller Start signal as XInput Start plus DirectInput button 8, which the default PPSSPP mapping binds to R. Backed up both local profiles and enabled XInput alone. This emulator configuration correction is separate from the ISO. Physical controller confirmation after the change remains pending.
- Selected runtime checks cover the full footer on opening/title-menu screens, footer teardown, existing long-name save loading, Latin family/given Auto names, HD confirmation, reopening a generated name in the keyboard, and finishing with the native PSP Start signal. Native registration/teardown MIPS checks and ISO component checksums pass. Physical PSP and full-playthrough checks remain pending. Local test build only; no GitHub release.

## 0.2.15 — 2026-10-17

- Added the requested eight-character English names while retaining three Japanese characters, the original eight-byte name records, and legacy save names. Names of four to eight printable Latin characters use a length-marked compact record. Long-name saves require this build or newer.
- Fixed blurry fullwidth Latin in name confirmations. Glyph creation now maps fullwidth letters, numbers, punctuation and spaces to the existing native 4× font before measuring them; stored legacy names and Japanese fallback are retained. The PSP system keyboard retains its system font. No texture replacement.
- Added bounded decoding to name copies, comparisons, both game text formatters and legacy byte conversion. Decoded game strings use the original fullwidth conventions, preventing name punctuation from becoming formatting or control syntax. Enlarged the name-entry value window and updated its capacity/error prompts.
- Separated portrait-card names and ages into two rows, extending their frames by 12 native pixels. Preserved other archive payloads, name-generation pools, title members and prior fixes. Updated the native footer to v0.2.15.
- Actual MIPS checks cover 127 varied names, adjacent-record canaries, bounded/counted copies, comparisons including the last character, both literal/substitution formatters, original byte-conversion equivalence, invalid-input recovery, and saved registers. Runtime evidence is recorded under `work/ui/names-0.2.15/`. Physical PSP and full-playthrough checks remain pending. Local test build only; no GitHub release.

## 0.2.14 — 2026-10-17 (internal test)

- Corrected the legacy byte converter and verified entry of eight-character family, given and child names, mixed case, HD confirmations and an actual save. Subsequent review identified literal-format bounds and portrait-card spacing work, completed in 0.2.15. Superseded internal candidate; not a release.

## 0.2.13 — 2026-10-17 (rejected internal test)

- Initial compact-name and fullwidth-font candidate. Rejected after a helper classified as a wide-string copy was found to be a legacy byte converter. Its tests were corrected to compare the actual original conversion contract. This candidate must not be used.

## 0.2.12 — 2026-10-17

- Enabled native English name entry in the PSP system keyboard. Both Latin cases, digits and symbols are now allowed alongside the original Japanese sets, with English selected by default. The original three-character name limit and save format are retained.
- Changed the family-name reminder to “Please take care to spell it correctly,” matching the newly available English input. The instruction keeps its three original lines and all other title text is preserved.
- Updated the native footer to v0.2.12. Three guarded OSK-initialization instructions change; no new executable segment or font replacement is required. The game retains the native 4× VWF and all prior menu/artwork fixes. Unrelated payload/member preservation, compression round trips, ISO checksums, and actual MIPS field/stack/register comparisons pass. Local build only; no GitHub release.
- Verified lowercase, uppercase and Japanese switching in actual keyboard captures. The game accepts Latin family, given and child names, enforces the original three-character limit, and preserves letters/case through an actual save, restart and load. The original game stores these names as fullwidth Unicode internally. Runtime evidence: `work/ui/alphabet-0.2.12/verification.json`.

## 0.2.11 — 2026-10-17

- Fixed overlapping Enter / Oni Records / Treasures labels on the dungeon destination screen. Its dedicated three-column menu now uses 88-pixel cells instead of 30, preserving the original centering, navigation and highlights.
- Included the native English Mount Oe banner and the other destination banners from 0.2.10. The reported Japanese title is the location name Mount Oe; its matching English artwork is retained in this build.
- Updated the native title footer to v0.2.11. The executable changes only one guarded 16-bit menu-width field; executable code, 4× native VWF, earlier menu fixes and native map translations are retained. The archive changes only the footer. Payload preservation, compression round trips and ISO replacement checksums pass. Local test build only; no GitHub release.
- Verified the English Mount Oe banner, all three complete menu labels and their highlights in actual final-build framebuffer captures. Three additional core records now have selected-context fit evidence (33 total); draft coverage is unchanged. Evidence: `work/ui/destination-fixes-0.2.11/verification.json`.

## 0.2.10 — 2026-10-17

- Translated the native overworld signs and destination banners using the existing glossary: Kyoto, Soyokuin, Kujuro, Torii Senmangu, Mount Oe, White Bone Castle, Boga Aqueduct, Crimson Flame Shrine, Royal Requiem Tomb and Tour of Hell.
- Updated all 50 small map-sign copies across both map sets and their seasonal variants, plus ten selected-destination banners. Small signs retain their dimensions and scenery, with clean gold-to-purple panels. The large banners use fitted English plaques; Itsuka's portrait is retained. Translated all eight compass copies to KYO and N/E/S/W.
- Updated the title footer to v0.2.10. Preserved the 0.2.9 executable, native 4× font and all earlier menu fixes. Native palettes, unrelated pixels, unrelated archive members and root payloads pass byte-preservation checks. Compression round trips and ISO checksums pass. No texture replacement or GitHub release.
- Build-specific artwork coordinates, previews and actual game captures are recorded under `work/ui/map-fixes-0.2.10/`. Other seasons and late-game banners have asset-preview checks; they still need full playthrough verification.

## 0.2.9 — 2026-10-17

- Fixed the first-deity confirmation's runtime truncation. The intended second line is “Is that your choice?”; its allocation and formatter capacity now both allow 256 bytes instead of 64. The popup sizes itself around the complete text.
- Widened character-action menu cells from 64 to 112 native pixels, including the selection highlight, so Best Equipment fits.
- Widened all three home-menu columns from 48 to 96 native pixels. Clan, Sortie, Divine Union and the remaining rows keep their original navigation and separate columns. Raised this window above Itsuka's preview poses so her umbrella and SAVE sign cannot cover the right column.
- Widened the Portrait Studio's two choices from 128 to 248 native pixels and moved them below the heading. Translated its native banner to Family Photo and its vertical heading to Portrait Studio, matching the glossary. Added a clean title plaque while retaining the camera, projection beam and outer floral frame.
- Updated the native title footer to v0.2.9. Preserved the 4× native font, date cursor, name-entry prompts, original image palettes and every unrelated archive member/payload. No texture replacement or GitHub release.
- Guarded binary edits, archive/compression round trips, unchanged-payload checks, MIPS stack/register and contextual-position checks, and ISO replacement checksums pass. The new hooks add 84 bytes to the existing segment. In-game verification details are recorded under `work/ui/menu-fixes-0.2.9/`.

## 0.2.8 — 2026-10-17

- Corrected the overflowing family-name instruction while preserving all three lines and its request for the correct kanji.
- Removed redundant gender parentheses from the already gendered Japanese Lad / Japanese Maiden labels, preventing the unselected label from lingering at the right edge during setup.
- Found the standalone root name-entry resource omitted by the earlier EZBIND text catalog. Translated all 14 controls, labels, errors and confirmation prompts, including Input / Auto / OK. Preserved its 1,735 original Japanese player-name choices and three-character input limit.
- Changed the birth-date display to Gregorian YYYY/MM/DD. Updated native year forwarding and cursor character ranges so the year, month and day highlight their actual digits; retained the original stored date, input bounds and validation.
- Escaped ASCII percentage signs for the game's formatter and taught the native VWF selector to accept its non-breaking numeric padding. Both three-digit and padded two-digit values use the existing 4× atlas. Padding advances, glyph geometry and Japanese fallback are preserved. Abbreviated Battle Experience to Battle EXP for spacing.
- Updated the title footer to v0.2.8. Added 28 bytes to the native date patch; preserved earlier local builds. Translation checks, archive round trips and MIPS date tests pass. Actual screen verification is recorded separately; no GitHub release created.
- Verified the corrected family/given-name screens and confirmations, Gregorian year/month/day highlights and day increment in actual guest-framebuffer captures. Live glyph checks confirm all three Thorough-mode values (125%, padded 94%, 125%) use the native 4× atlas and matching UVs/ASCII advances.

## 0.2.7 — 2026-10-17

- Added two right-aligned title-screen footer lines, `v0.2.7` and `retro-trans`, styled with light gray lettering and a dark outline to match the supplied SRW Z reference. Used the group name to fit beside the title-menu portrait.
- Expanded the native copyright sprite to include the footer, preserving its original pixels and palette. A guarded title-only instruction change keeps it visible during the menu. Normal title teardown still removes and frees it. Texture replacement remains disabled.
- Kept the native T8 texture format and all other archive members unchanged. The expanded sprite adds 25,088 uncompressed bytes and fits within existing archive sector padding, so the ISO size stays unchanged. Preserved all earlier local builds.
- Verified native texture/compression round trips, unchanged archive members and the new ISO's directory entries and replacement checksums. Runtime placement evidence is recorded with the title-screen captures. No GitHub release created.
- Actual PSP framebuffer captures verify both footer lines on the opening title and title menu, clear of the portrait and caption. The native 4× font hook still executes with correct glyph geometry.
- Confirmed the footer disappears when title setup advances to the gender screen; no footer remains in that scene. The final archive and executable reproduce byte-for-byte from the builder.

## 0.2.6 — 2026-10-17

- Localized the PSP game-menu metadata title to Over My Dead Body, matching the translated save metadata. Preserved game/save compatibility IDs and every other metadata field.
- Built a separate local candidate containing the complete 0.2.5 archive draft, 18 executable messages and six native graphic labels. The main catalog is 100% drafted, with five approved neutral adaptations and 23 explicitly provisional staff readings.
- Reviewed 96 sampled frames from all eight movie files; found no baked-in Japanese dialogue/captions in those samples. Decorative title/sigil artwork is retained. Full frame-by-frame movie inspection, broad layout QA and real PSP tests remain incomplete.
- Measured data.bin: only its first 3,648 bytes contain nonzero data; the remaining 272,629,760 bytes are zero. Recorded the padding/filler inference and retained the original file.
- All translation/source/placeholder, archive round-trip, MIPS font and embedded table checks pass. No GitHub release created.

## 0.2.5 — in progress, 2026-10-17

- Resolved three more staff readings by matching the English sequel's credits to the same series, employer and production roles. Recorded which identity matches are inferred and the corroborating sources; excluded unrelated namesakes.
- Main working draft: 11,580 archive records, covering all 11,026 Japanese-bearing records and 8,027/8,027 distinct main strings (100% draft coverage).
- Applied 23 researched conventional staff-name romanizations after the user explicitly requested project romaji. All 23 are marked provisional, with alternatives and source limitations in the credit glossary; they are not presented as verified personal readings.
- Version 0.2.4 live checks confirm both relocated executable message tables are accepted by the game. Actual captures verify six native English title cards, the title caption and the complete gender setup prompt/labels. Four archive text records have visual-fit evidence; meaning approval and broad gameplay QA remain pending.

## 0.2.4 — in progress, 2026-10-17

- Applied the five neutral alternatives explicitly approved by the user, recording them as adaptations rather than faithful translations. All main dialogue and portrait captions now have English drafts.
- Translated six title-menu card labels directly in native PPT assets. Preserved their flower art, original palettes, image dimensions and geometry; emulator texture replacement remains disabled.
- Built a separate local 0.2.4 test ISO with 11,554 archive text records, 18 executable records and six graphic labels. Main archive draft coverage is 8,001/8,027 (99.68%); 26 unverified staff-name readings remain in Japanese.
- Added direct capture of the guest PSP display buffer through its display API. A 0.2.3 dialogue screen is visibly readable and fits its box; this does not approve other screens. Broad visual/gameplay checks and the remaining graphics audit are still pending. No GitHub release created.

## 0.2.3 — in progress, 2026-10-17

- Found two MLT tables embedded in the executable, outside the original archive catalog. Drafted all 18 records, including save-data labels, date/location formatting, screenshot-save failure and storage errors.
- Relocated both expanded tables into the added native segment and updated the two verified table-loader address pairs. Preserved the original table bytes and all source/previous builds. Added 1,196 bytes beyond the native font component.
- Verified both rebuilt tables, exact placeholders/newlines, source-free exports and actual MIPS address materialization. Built a separate local 0.2.3 ISO; runtime save/error scenarios remain unapproved.
- Captured the actual title-logo screen as a UI audit artifact. Japanese logo artwork remains an identified graphics task. Main archive draft coverage remains 99.61%; the 18 executable records are counted separately. No GitHub release created.

## 0.2.2 — in progress, 2026-10-17

Translation continuation toward full coverage. Native font component remains 0.2.0; local test build 0.2.2 includes the expanded text. Visual and gameplay approval remain pending.

- Drafted the entire 205-record battle table, including Hiruko and Kitsuto's combat remarks. Reviewed all 205 records through three 80-row windows with overlap at the end.
- Added all 96 spell labels, 83 nonempty spell descriptions, 33 secret-art labels and 33 descriptions. Invocation spellings follow the disc's pronunciation table; ordinary action labels are translated.
- Drafted all 530 help records: 174 headings, 304 body paragraphs and 52 alternate help entries, preserving twelve marker-only records. Kept Itsuka's uncertainty, jokes and continuation fragments explicit.
- Added all 631 item names, 223 nonempty item descriptions and 125 inventory labels/prompts. Preserved curse tags, inherited ownership, class restrictions, tone and cultural naming notes.
- Drafted the complete deity roster and all 547 deity-voice records, including 15 preserved empty records. Reviewed the voice table in seven 80-row windows with overlap at the end; each record stored once.
- Drafted all 176 dungeon-common records, 76 field-selection/statistics records and 60 exploration messages. The eighteen-part animated epitaph retains eighteen records and needs composed visual review.
- Drafted Divine Union menus, the full chronicle, equipment blessings/curses, Hiruko Challenge and all 81 family response records. Recorded the revival donor/recipient relationship and uncertain runtime kinship composition.
- Expanded the glossary to 1,308 entries, including deity and monster rosters, item names, spells, dungeons and the Rite of Revival. Gender follows explicit documented fields; unknown personality/biography remains blank. Automated copies remain flagged for contextual review.
- Added a compact all-batch validator and guarded repetition for identical descriptions. Corrected review-note scope so first-person exceptions apply only where the source actually names Itsuka.
- Drafted the complete monster roster, tournament and multiplayer menus, and all 876 last-word records, including empty separators. Retained threats, coarse jokes, ambiguous references and deliberate continuations with review notes.
- Linked 1,455 pronunciation/display records to their corresponding English names. Name-order behavior still requires runtime verification; no opaque event IDs were changed.
- Completed drafts for all event dialogue, movie subtitle tracks, ending narration, last words and Itsuka records except three explicitly excluded lines. Reviewed consecutive 80-row dialogue windows, with documented overlap at the ends; stored each record once.
- Added portrait captions and researched staff names. Five child-sexualizing lines remain explicitly untranslated; neutral alternatives are proposed separately, awaiting the user's choice. Twenty-six credit-name readings remain unverified and are not guessed.
- Working checkpoint: 11,549 draft records, comprising 9,029 manual drafts, 1,065 terminology copies and 1,455 derived name/readings. Distinct main-string draft coverage is 7,996/8,027 (99.61%). All 49 batches pass structural checks. This measures indexed MLT text, not complete game approval or image/executable coverage.
- Rebuilt 241 changed archives with all MLT records round-tripped and control codes checked. Preserved the original ISO and earlier builds. No GitHub release created.

## 0.2.1 — 2026-10-17

Translation continuation; native font component remains 0.2.0. New text has not received in-game layout approval.

- Added 349 manually drafted records: 273 Itsuka records (including four preserved empty records) and 76 Herbalist, Print Shop and Portrait Studio entries.
- Completed the consecutive Itsuka range 360–792. This pass examined 275 unique source records for 273 new drafts; the final two 80-row review windows overlap by 47 rows, stored once.
- Translated rebuilding and festival announcements, tournament invitations, Mount Oe notices, bounty reports, medicine names, photo prompts, memory-box warnings and frame titles.
- Expanded the glossary from 108 to 133 entries, including two deity names, medicines, festivals, places and investment sectors. Recorded the source's Ring/Bracelet discrepancy and standardized the English item name to Clan Head's Ring.
- Rebuilt terminology copies: 843 records remain marked as requiring contextual review. Combined drafts total 2,917 records, including 2,074 manual drafts; distinct main-string coverage is 2,046/8,027 (25.49%).
- Strengthened checks for escaped percent signs, the percent-bang engine marker, preserved empty records and complete declared dialogue ranges. Source-free exports retain unique-versus-overlapping review counts.
- Rebuilt relocated text for a separate local 0.2.1 test ISO, preserving the original ISO and 0.2.0 builds. Archive round trips, placeholders, line breaks, source hashes and export checks passed. Full translation, visual fit and a 0.2.1 playthrough remain pending. No GitHub release was created.

## 0.2.0 — 2026-10-17

Experimental native font and partial English test build. Full translation and visual QA remain incomplete.

- Confirmed the existing renderer uses variable glyph widths; patched Latin advances and embedded a native 512×512 T4 atlas with glyphs rasterized at 4× logical resolution. No texture replacement is used.
- Added a guarded MIPS selector for ASCII text, preserving the original Japanese/mixed-text font path. Added 135,168 bytes of executable data/code.
- Verified 95 widths and 103 glyph geometry cases by executing the MIPS selector. Verified a live native-font hook and Japanese fallback in PPSSPP with texture replacement disabled.
- Added MLT relocation, custom compression, EZBIND rebuilding, root archive offset relocation and ISO reinsertion with round-trip and checksum checks.
- Expanded to 2,564 draft records: 1,725 manually drafted records and 839 terminology copies, including 681 repeated speaker labels. Distinct main-string coverage is 1,701/8,027 (21.19%).
- Drafted title/setup, party/training controls, shared system labels, swordsmith, commodity trading, spell menus/effects, expedition schedules and all 732 Japanese profile traits.
- Added a second consecutive 80-record Itsuka slice; 86 records examined. Expanded the glossary to 108 entries and recorded uncertain idioms and readings.
- Kept every record, placeholder, engine tag and source line-break count. Text-box fit remains unverified; long English text is relocated rather than truncated.
- Built local font-only and combined partial-English ISOs. In-game screenshot capture is unresolved, and real PSP hardware is untested. No GitHub release was created.

## 0.1.0 — 2026-10-17

Initial research and translation snapshot; no playable game build.

- Identified the PSP input as UCJS10117 and preserved the source ISO.
- Added ISO extraction, EZBIND decompression, and UTF-16/ASCII MLT catalog tools.
- Cataloged all 734 message tables: 11,026 Japanese records / 8,984 distinct strings. Main workload excluding readings and speaker labels: 8,027 distinct strings.
- Added an 81-entry glossary with sources, character notes and provisional decisions.
- Drafted 207 English records covering home UI/help, settings, difficulty labels, opening narration and an 80-record Itsuka dialogue/tutorial slice.
- Added source hashes, context notes, exact placeholder/control checks and English-only exports.
- Recorded progress, extraction limits and pending in-game font/layout/relocation work.
- Ignored Japanese script working files and added the requested folder structure.

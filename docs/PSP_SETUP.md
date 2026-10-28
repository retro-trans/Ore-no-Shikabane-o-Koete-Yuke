# Running 0.2.52 on PSP hardware

**PSP hardware tested:** a tester confirmed that English **0.2.52** starts and
works on their PSP running **6.61 ARK-5**, after disabling the installed
`PBOOT.PBP` update. This confirms the reported startup problem is resolved on
that setup; it does not certify a full playthrough or every PSP/firmware model.

## 1. Apply the matching patch

Use the latest [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools/releases/latest).
Refresh the catalog, open **Automatic**, select your original Japanese
**UCJS-10117** ISO or public English **0.2.48** ISO, and choose **0.2.52** or
**Latest**. Save to a new ISO filename. The app checks the input and output hashes.

For manual patching, choose one asset from the
[0.2.52 release](https://github.com/retro-trans/Ore-no-Shikabane-o-Koete-Yuke/releases/tag/v0.2.52):

| Input ISO | Patch |
| --- | --- |
| Original Japanese UCJS-10117 | `OreNoShikabane-English-0.2.52-full.xdelta` |
| Public English 0.2.48 | `OreNoShikabane-English-0.2.48-to-0.2.52.xdelta` |

Apply only the patch matching your input. Earlier local test builds are not
inputs for these release patches. The existing 0.2.52 test ISO is byte-identical
to the release output and does not need repatching.

Expected output: **1,077,544,960 bytes**.
SHA-256: `5e821290c20f25f0642c4834f602e9fc7d46925d820f3ccfd83b78cc7f86590b`.

## 2. Disable the installed game update

1. Fully close the game, then connect the PSP storage to your computer.
2. Copy the patched ISO into the storage's `ISO` folder with a distinct name,
   for example `Oreshika-English-0.2.52.iso`.
3. Look for **`PSP/GAME/UCJS10117/PBOOT.PBP`** on the PSP storage. On a PSP Go,
   check the internal storage and any memory card that contains the game update.
4. Back up that file to your computer, then rename **only** `PBOOT.PBP` to
   **`PBOOT.PBP.disabled`**. If the file is absent, skip this step.
5. Leave `EBOOT.PBP` and everything under `PSP/SAVEDATA` unchanged. Enable file
   extensions in your computer's file browser so the rename is exact.
6. Disconnect storage normally, fully power off the PSP, and start it again.
   Launch the new patched ISO from the Game menu.

The installed update can launch its own executable instead of the patched
one inside the ISO. That produces English text with original narrow menus,
overlap, or missing native font/icon changes. Disabling the update lets the
0.2.52 executable run. The patch does not incorporate the official update's
gameplay changes.

## 3. Confirm the correct build is running

Check for **v0.2.52** at the title screen. Load a normal save and check that the
home menu has three separated columns and its description fits in the wider
box. Start fresh; emulator save states can restore an older executable's memory.

If the layout still looks old, check that you launched the new ISO and that no
active copy of `PBOOT.PBP` remains. If startup fails, restore the backed-up file
under its exact original name and report your PSP model, firmware, ISO hash and
what appears at startup. Keep the older ISO until the new one is working.

No firmware update or plugin installation was part of the successful test.
Do not use 0.2.48, 0.2.50 or 0.2.51 as the hardware startup fix; those builds
failed on the reported setup with the update disabled.

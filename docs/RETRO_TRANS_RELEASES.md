# Retro Trans release packaging

This repository follows the layout and release presentation of
[Macross Triangle Frontier](https://github.com/retro-trans/Macross-Triangle-Frontier)
and the [Retro Trans release standard](https://github.com/retro-trans/retro-trans-tools/blob/main/docs/RELEASE_STANDARD.md).
The reference repository is not marked as a GitHub template; its structure and
packaging conventions are adapted here without copying its game-specific files.

Stable identity: game ID `ore-no-shikabane-o-koete-yuke`, platform `PSP`,
edition `UCJS10117`, language `en`. Never reuse a published version for changed bytes.

## Prepare and verify

Keep the original Japanese ISO and every built image local. Build 0.2.38 is the
exact tested `work/output/english-native-0.2.38.iso`; packaging does not relayout
or otherwise change its bytes. Supported source and target hashes are recorded
in the release's `BUILD-MANIFEST.json`.

1. Export English-only text with `tools/export_public_text.py` (dry run, then
   `--write`). Review the Git staging list for source text and original binaries.
2. Commit the translation text, tools and documentation. The packaging manifest
   records this full source commit; a later metadata-only commit can add the
   generated release evidence without changing the source identity.
3. Check out Retro Trans Tools under ignored `work/source/retro-trans-tools/`.
   Its own release builder performs the xdelta encode/decode round trip and
   validates the complete resulting image against the tested ISO.
4. Run `py -3.11 tools/package_release.py` and inspect its source, target and
   output paths and hashes. Add `--write` to build and validate the bundle.
   The private configuration remains under ignored `work/source/`.
5. Copy only `BUILD-MANIFEST.json`, `VALIDATION.json` and `SHA256SUMS.txt` into
   `docs/releases/0.2.38/`. The `.xdelta` stays in ignored `work/output/` until upload.

The first release provides a full patch from the original ISO. Later releases
should also offer upgrade patches from earlier published versions. A local test
build is not a previously published upgrade source.

## Publish and confirm discovery

Use a `v0.x.y` tag. Create a draft with the tested patch, `VALIDATION.json` and
`SHA256SUMS.txt`, then upload `BUILD-MANIFEST.json` last. Check the uploaded sizes
and hashes against the local bundle before publishing. Do not replace published
assets or upload an ISO, executable, archive, save or private configuration.

Notes follow the reference's Apply, included content, release status, translation
method, acknowledgements, source code and contribution sections. Describe the
current draft and testing limits honestly.

After publishing, start **Refresh patch catalog** in Retro Trans Tools with
`repository=retro-trans/Ore-no-Shikabane-o-Koete-Yuke`. Confirm that the published
manifest and patch appear in the public catalog and that an original ISO has a
route to 0.2.38. Catalog checks verify patch application, not game behavior.

# Contributing

Bug reports, proofreading and playtesting are welcome at
[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB) or in this repository's issues.
Include the patch version, screen or row ID, reproduction steps and a screenshot
when useful. State whether you booted the ISO normally or loaded a save state.

Read [BASE_RULES.md](BASE_RULES.md) before editing translations. Keep terminology
in `work/glossary/`, layout metadata in `work/ui/`, and English translations in
`work/translation/en/`. Preserve IDs, placeholders, control codes and source hashes.
Read adjacent records for context and record uncertain interpretations.

Japanese script text is kept only in ignored local working files. Run
`python tools/export_public_text.py`, inspect the preview, then add `--write` to
regenerate the `*.en.json` exports through `tools/strip_jp.py`. Commit only those
exports. Japanese names, UI terms and the kana romanization alphabet are allowed;
dialogue source text is not. Never commit game images, extracted game data, saves,
incoming game artwork, private build configurations or local emulator profiles.

Record changes in `CHANGELOG.md`. Test from a fresh ISO boot and a normal save.
Distinguish measured/static checks from actual gameplay checks. Full-game meaning
review and physical PSP testing remain incomplete.

New binaries receive a new `0.x.y` version. A GitHub release requires an explicit
request and must follow [the release guide](docs/RETRO_TRANS_RELEASES.md).

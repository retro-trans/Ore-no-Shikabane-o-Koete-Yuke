"""Generate source-free progress and observed UI constraints. Dry run unless --write."""
import argparse
import collections
import json
from pathlib import Path

from check_translation import TOKEN

ROOT = Path(__file__).resolve().parents[1]


def reports():
    corpus = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    batches = [json.loads(p.read_text(encoding='utf-8')) for p in
               sorted((ROOT / 'work/translation/en').glob('*.en.json'))]
    versions = [b['version'] for b in batches]
    build_status = ROOT / 'docs/local_build_status.json'
    current_build = {}
    if build_status.exists():
        current_build = json.loads(build_status.read_text(encoding='utf-8'))
        versions.append(current_build['archive_translation_version'])
    version = max(versions, key=lambda v: tuple(map(int, v.split('.'))))
    glossary = json.loads((ROOT / 'work/glossary/core.json').read_text(encoding='utf-8'))
    core = [r for r in corpus if r['has_japanese'] and r['category'] not in
            {'pronunciation_readings', 'speaker_names', 'voice_or_event_metadata'}]
    translated = {}
    for batch in batches:
        for row in batch['rows']:
            if row['id'] in translated and translated[row['id']]['translation_en'] != row['translation_en']:
                raise ValueError('Conflicting translations: ' + row['id'])
            translated[row['id']] = row
    source = {r['id']: r for r in corpus}
    translated = {key: dict(source[key], **{k: v for k, v in row.items() if k not in source[key]})
                  for key, row in translated.items()}
    distinct = {r['source_jp'] for r in core}
    drafted = {r['source_jp'] for r in core if r['id'] in translated}
    unresolved = {r['id']: r for b in batches for r in b.get('untranslated_rows', [])}
    if set(unresolved) & set(translated):
        raise ValueError('An explicitly unresolved row has been translated elsewhere')
    qa_path = ROOT / 'work/ui/verified_screens.json'
    qa = json.loads(qa_path.read_text(encoding='utf-8')) if qa_path.exists() else {}
    visually_tested = set(qa.get('visual_fit_verified_record_ids', []))
    if visually_tested - set(translated):
        raise ValueError('Visual evidence references an unknown translated record')
    extra = {}
    for domain in ('executable', 'graphics', 'name_entry', 'shop', 'equipment', 'character'):
        extra[domain] = sum(len(json.loads(p.read_text(encoding='utf-8'))['rows'])
                            for p in (ROOT / 'work/translation/en' / domain).glob('*.en.json'))
    credits_path=ROOT/'work/glossary/credits.json'
    credits=json.loads(credits_path.read_text(encoding='utf-8')) if credits_path.exists() else {}
    progress = dict(version=version, date=current_build.get('build_date','2026-10-18'), language='en',
                    status=('Complete indexed text draft; native 4x VWF patch boots. Visual/gameplay QA incomplete.'
                            if drafted==distinct else 'Partial English draft; native 4x VWF patch boots. Visual/gameplay QA incomplete.'),
                    total_draft_records=len(translated),
                    drafted_japanese_records=sum(r['has_japanese'] for r in translated.values()),
                    retained_non_japanese_records=sum(not r['has_japanese'] for r in translated.values()),
                    distinct_main_strings_drafted=len(drafted),
                    distinct_main_strings_total=len(distinct),
                    distinct_main_strings_remaining=len(distinct - drafted),
                    main_record_ids_remaining=sum(r['id'] not in translated for r in core),
                    distinct_draft_coverage_percent=round(100 * len(drafted) / len(distinct), 2),
                    approved_or_game_tested_records=len(visually_tested),
                    visually_fit_checked_records=len(visually_tested),
                    meaning_approved_records=0,
                    additional_draft_records_by_domain=extra,
                    latin_auto_name_choices=current_build.get('latin_auto_name_pool_records',0),
                    provisional_auto_name_readings=current_build.get('provisional_auto_name_readings',0),
                    provisional_credit_readings=sum(e.get('reading_status')=='provisional_user_authorized' for e in credits.get('entries',[])),
                    approved_neutral_adaptations=sum(r.get('kind')=='approved_neutral_adaptation' for r in translated.values()),
                    explicitly_untranslated_records=len(unresolved),
                    untranslated_issues=list(unresolved.values()),
                    records_by_file=dict(collections.Counter(r['file'] for r in translated.values())),
                    records_by_category=dict(collections.Counter(r['category'] for r in translated.values())),
                    meaning_review=dict(collections.Counter(r['meaning_review'] for r in translated.values())),
                    glossary_entries=len(glossary['characters']) + len(glossary['terms']) + len(glossary['organizations']),
                    credit_glossary_entries=len(credits.get('entries',[])),
                    dialogue_batches=[dict(file='itsuka.mlb', source_row_range_zero_based=[360, 439],
                                        sections='4:0-39 and 5:0-39', rows_in_slice=80, rows_examined=86,
                                        adjacent_context='3:119-120 and 5:40-43',
                                        note='Indexed order; includes late-game events, not 80 chronological opening dialogue lines.')] +
                                    [s for b in batches for s in b.get('dialogue_slices', [])],
                    scope='Percentage measures the indexed EZBIND MLT draft only. Standalone name-entry UI, executable and graphic drafts are reported separately. Curated Latin Auto-name choices are tracked separately from the original source pools. Full graphics/binary audit and gameplay QA remain incomplete.')
    constraints = dict(version=version, measurement_status='Selected title/setup, character/home/Portrait Studio/dungeon destination menus, shared inventory/category/shop windows, equipment/Divine Union/deity menus and overworld labels measured from actual PSP display captures; build-specific evidence is linked separately. Other gameplay screens remain unverified.',
                       maximum_characters_allowed=None, text_box_coordinates=qa.get('screens', []),
                       additional_build_evidence=qa.get('additional_build_evidence',[]),
                       note='Observed source lengths are NOT display limits. Runtime placeholders have unknown expanded widths. '
                            'Drafts preserve row identity and controls. Requested line-count reflows are scoped by source/target hashes in UI layouts; remaining wrapping and display contexts still require QA.',
                       rows_exceeding_original_utf16_bytes=sum(len(r['translation_en'].encode('utf-16-le')) >
                                                              len(r['source_jp'].encode('utf-16-le')) for r in translated.values()),
                       required_build_strategy='Relocate expanded text and update pointers; never truncate to original byte slots.',
                       tables=[])
    for file in sorted({r['file'] for r in translated.values()}):
        rows = [r for r in translated.values() if r['file'] == file]
        def max_visible(field):
            return max(len(TOKEN.sub('', line)) for r in rows for line in r[field].split('\n'))
        constraints['tables'].append(dict(file=file, drafted_records=len(rows),
                                          source_observed_max_literal_line_characters=max_visible('source_jp'),
                                          english_observed_max_literal_line_characters=max_visible('translation_en'),
                                          source_observed_max_lines=max(r['source_jp'].count('\n') + 1 for r in rows),
                                          fit_status='unverified'))
    return progress, constraints


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()
    progress, constraints = reports()
    print(json.dumps(progress if args.verbose else {k: v for k, v in progress.items() if k != 'records_by_file'}, indent=2))
    print(json.dumps({'constraints_status': constraints['measurement_status'],
                      'rows_needing_larger_storage': constraints['rows_exceeding_original_utf16_bytes']}, indent=2))
    if args.write:
        for relative, obj in [('docs/translation_progress.json', progress), ('work/ui/text_constraints.json', constraints)]:
            dest = ROOT / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(obj, indent=2), encoding='utf-8')
    print('Reports written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

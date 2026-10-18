"""Read-only checks for source identity, placeholders, controls, rows and export safety."""
import collections
import hashlib
import json
import re
from pathlib import Path

from catalog_text import JP
from strip_jp import export

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'\[[^\]\r\n]+\]|%%|%!|%(?:\d+:)?(?:[-+ #0]*\d*(?:\.\d+)?[dsf]|[@$])')


def permitted_line_reflow(row):
    """Accept only exact source/target pairs documented for requested reflow."""
    for path in (ROOT/'work/ui').glob('dialogue-reflow-*/layout.json'):
        info=json.loads(path.read_text(encoding='utf-8'))
        for change in info.get('line_break_exceptions',[]):
            if (change.get('id')==row['id']
                and change.get('reason')=='User-requested English dialogue reflow'
                and change.get('source_sha256')==row['source_sha256']
                and change.get('translation_sha256')==hashlib.sha256(row['translation_en'].encode()).hexdigest()
                and change.get('target_lines')==row['translation_en'].count('\n')+1):
                return True
    return False


def tokens_equal(source, target):
    """Preserve controls, allowing full-width percent text to become printf %%.

    A full-width percent is visible text in the source, whereas an ASCII
    percent must be escaped before this game's formatter. Never relax actual
    argument/control tokens or existing percent escapes.
    """
    a, b = TOKEN.findall(source), TOKEN.findall(target)
    if a == b:
        return True
    return (source.count('％') > 0 and target.count('％') == 0
            and target.count('%%') == source.count('%%') + source.count('％')
            and [t for t in a if t != '%%'] == [t for t in b if t != '%%'])


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, default=ROOT / 'work/translation/en/initial_batch.json')
    args = parser.parse_args()
    source = args.batch
    batch = json.loads(source.read_text(encoding='utf-8'))
    corpus = {r['id']: r for r in json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']}
    glossary = json.loads((ROOT / 'work/glossary/core.json').read_text(encoding='utf-8'))
    errors = []
    if len({r['id'] for r in batch['rows']}) != len(batch['rows']):
        errors.append('Duplicate translation IDs')
    for row in batch['rows']:
        jp, en = row['source_jp'], row['translation_en']
        prefix = row['id']
        if jp.strip() and not en.strip():
            errors.append(prefix + ': blank English')
        if not jp and en:
            errors.append(prefix + ': inserted text into an empty source record')
        if row['source_sha256'] != hashlib.sha256(jp.encode()).hexdigest() or corpus[row['id']]['source_jp'] != jp:
            errors.append(prefix + ': source identity mismatch')
        if not tokens_equal(jp, en):
            errors.append(prefix + ': changed placeholders or control tags')
        if jp.count('\n') != en.count('\n') and not permitted_line_reflow(row):
            errors.append(prefix + ': changed line-break count')
        if jp.startswith('@') != en.startswith('@'):
            errors.append(prefix + ': changed leading runtime marker')
        if JP.search(TOKEN.sub('', en)):
            errors.append(prefix + ': untranslated Japanese outside engine controls')
        if '\x00' in en or '\ufffd' in en:
            errors.append(prefix + ': invalid translated character')
        for char in glossary['characters']:
            if char['id'] == 'itsuka' and 'Itsuka refers to herself by name; English uses I in this row.' in row.get('review_notes', []):
                continue
            variants = [char['jp']] + char.get('aliases_jp', [])
            if any(v in jp for v in variants) and not any(v in en for v in [char['en'], char.get('short_en', char['en'])]):
                errors.append(prefix + ': glossary name missing: ' + char['id'])
    translated_dialogue = [r for r in batch['rows'] if r['file'] == 'itsuka.mlb']
    source_dialogue = [r for r in corpus.values() if r['file'] == 'itsuka.mlb']
    if source.name == 'initial_batch.json' and [r['id'] for r in translated_dialogue] != [r['id'] for r in source_dialogue[360:440]]:
        errors.append('Itsuka batch is not the expected 80 consecutive records')
    declared = collections.defaultdict(set)
    actual_by_group = {}
    unresolved_ids = set()
    translated_ids = {r['id'] for r in batch['rows']}
    for issue in batch.get('untranslated_rows', []):
        original = corpus.get(issue['id'])
        if (not original or not issue.get('reason') or issue.get('status') != 'untranslated'
                or any(issue.get(k) != original[k] for k in ('file', 'section', 'index', 'source_sha256'))
                or issue['id'] in translated_ids or issue['id'] in unresolved_ids):
            errors.append('Invalid unresolved source record: ' + issue['id'])
        unresolved_ids.add(issue['id'])
    for slice_info in batch.get('dialogue_slices', []):
        prefix = slice_info.get('file_group_prefix')
        def belongs(r):
            return (r['file'].startswith(prefix) and r['category'] == 'dialogue_narration_subtitles'
                    and not any(r['file'].startswith(p) for p in slice_info.get('excluded_file_prefixes', []))) if prefix else r['file'] == slice_info['file']
        file_rows = [r for r in corpus.values() if belongs(r)]
        actual_by_group[slice_info['file']] = {r['id'] for r in batch['rows'] if belongs(r)}
        start, count = slice_info['start'], slice_info['rows_in_slice']
        expected = [r['id'] for r in file_rows[start:start + count]]
        declared[slice_info['file']].update(expected)
        if count != 80 or not all(key in translated_ids | unresolved_ids for key in expected):
            errors.append('Dialogue slice is incomplete: ' + str(slice_info))
    for file, expected_ids in declared.items():
        actual_ids = actual_by_group[file]
        if actual_ids != expected_ids - unresolved_ids:
            errors.append('Dialogue records do not match the union of declared slices: ' + file)
    english = export(source)
    actual = json.loads(source.with_suffix('.en.json').read_text(encoding='utf-8'))
    if english != actual:
        errors.append('English-only copy is stale or altered')
    if any('source_jp' in r for r in actual['rows']):
        errors.append('Japanese source leaked into English-only copy')
    print(json.dumps(dict(rows=len(batch['rows']),
                          explicitly_untranslated_rows=len(unresolved_ids),
                          japanese_source_rows=sum(corpus[r['id']]['has_japanese'] for r in batch['rows']),
                          distinct_japanese_sources=len({r['source_jp'] for r in batch['rows'] if r['has_japanese']}),
                          rows_by_file=dict(collections.Counter(r['file'] for r in batch['rows'])),
                          glossary_entries=len(glossary['characters']) + len(glossary['terms']) + len(glossary['organizations']),
                          dialogue_rows_in_slice=len(translated_dialogue),
                          dialogue_rows_examined=86 if source.name == 'initial_batch.json' else
                          batch.get('dialogue_rows_examined_unique',
                                    sum(s['rows_examined'] for s in batch.get('dialogue_slices', []))),
                          dialogue_slice_counts=[{k: s[k] for k in ('start', 'rows_in_slice', 'rows_examined')}
                                                 for s in batch.get('dialogue_slices', [])],
                          errors=errors), indent=2))
    if errors:
        raise SystemExit(1)
    print('PASS: source identity, declared dialogue slices, control tokens, line breaks, glossary names, and safe export.')


if __name__ == '__main__':
    main()

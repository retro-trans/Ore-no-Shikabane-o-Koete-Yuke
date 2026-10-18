"""Export English-only translation rows using an allowlist. Dry run unless --write."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('id', 'file', 'archive_offset', 'member_entry', 'section', 'index',
          'text_offset', 'source_sha256', 'category', 'translation_en', 'status',
          'kind', 'context', 'fit_status', 'meaning_review', 'review_notes')


def export(source):
    original = json.loads(source.read_text(encoding='utf-8'))
    result = {key: original[key] for key in ('schema_version', 'version', 'language', 'status')}
    if original.get('dialogue_slices'):
        result['dialogue_slices'] = original['dialogue_slices']
    if 'dialogue_rows_examined_unique' in original:
        result['dialogue_rows_examined_unique'] = original['dialogue_rows_examined_unique']
    if original.get('untranslated_rows'):
        fields = ('id', 'file', 'section', 'index', 'source_sha256', 'status', 'reason')
        result['untranslated_rows'] = [{k: row[k] for k in fields} for row in original['untranslated_rows']]
    result['rows'] = [{key: row[key] for key in FIELDS if key in row} for row in original['rows']]
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', nargs='?', type=Path, default=ROOT / 'work/translation/en/initial_batch.json')
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    result = export(args.source)
    dest = args.source.with_suffix('.en.json')
    print(json.dumps({'destination': str(dest), 'rows': len(result['rows']),
                      'removed_fields': ['source_jp', 'has_japanese', 'japanese_characters'],
                      'sample': result['rows'][0]}, ensure_ascii=True, indent=2))
    if args.write:
        dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('English-only copy written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

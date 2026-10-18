"""Apply unambiguous whole UI strings and glossary names; never replace dialogue substrings."""
import argparse
import collections
import json

from catalog_text import ROOT
from check_translation import TOKEN


def build():
    source = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    glossary = json.loads((ROOT / 'work/glossary/core.json').read_text(encoding='utf-8'))
    versions = [glossary['version']]
    choices, covered = collections.defaultdict(set), set()
    for file in sorted((ROOT / 'work/translation/en').glob('*.en.json')):
        if file.name == 'consistent_terms.en.json':
            continue
        batch = json.loads(file.read_text(encoding='utf-8'))
        versions.append(batch['version'])
        for row in batch['rows']:
            covered.add(row['id'])
            text = next((r['source_jp'] for r in source if r['id'] == row['id']), None)
            if text is not None:
                choices[text].add(row['translation_en'])
    known = {}
    for entry in glossary['terms'] + glossary['characters']:
        if entry.get('category') == 'speaker_label':
            continue
        known[entry['jp']] = entry['en']
        for alias in entry.get('aliases_jp', []):
            known[alias] = entry['en'] if alias.replace(' ', '') == entry['jp'].replace(' ', '') else entry.get('short_en', entry['en'])
    speaker_terms = {r['jp']: r['en'] for r in glossary['terms'] if r.get('category') == 'speaker_label'}
    results = []
    eligible = {'ui_system_help', 'names_and_terms', 'speaker_names'}
    for row in source:
        if row['id'] in covered or not row['has_japanese'] or row['category'] not in eligible:
            continue
        jp = row['source_jp']
        en = None
        origin = None
        if len(choices.get(jp, set())) == 1:
            en = next(iter(choices[jp]))
            origin = 'Exact previously translated UI string; context review still required.'
        else:
            prefix, text = ('@', jp[1:]) if jp.startswith('@') else ('', jp)
            if text in known:
                en = prefix + known[text]
            elif row['category'] == 'speaker_names' and text in speaker_terms:
                en = prefix + speaker_terms[text]
            elif row['category'] == 'speaker_names' and '\uff06' in text:
                parts = text.split('\uff06')
                if all(p in known for p in parts):
                    en = prefix + ' & '.join(known[p] for p in parts)
            if en is not None:
                origin = 'Whole glossary name or UI term; no substring rewriting.'
        if en is None or TOKEN.findall(jp) != TOKEN.findall(en):
            continue
        results.append(dict(**row, translation_en=en, status='draft', kind='consistent_term',
                            context='Exact complete UI/name record; dialogue is excluded from automatic propagation.',
                            fit_status='unverified_in_game', meaning_review='glossary_checked_context_pending',
                            review_notes=[origin]))
    version = max(versions, key=lambda v: tuple(map(int, v.split('.'))))
    return dict(schema_version=1, version=version, language='en',
                status='Terminology drafts; no meaning review is claimed for new contexts.', rows=results)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    result = build()
    print(json.dumps(dict(rows=len(result['rows']), categories=dict(collections.Counter(r['category'] for r in result['rows'])),
                          sample=[{k: r[k] for k in ('id', 'file', 'translation_en')} for r in result['rows'][:8]]), indent=2))
    if args.write:
        (ROOT / 'work/translation/en/consistent_terms.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Terminology batch written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

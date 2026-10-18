"""Apply the five neutral adaptations explicitly approved by the user.

The approved wording is kept separate from faithful translations. Dry run first.
"""
import argparse
import json

from catalog_text import ROOT
from check_translation import TOKEN


def prepare():
    proposal_path = ROOT / 'work/translation/en/safe_adaptations.proposed.json'
    proposal = json.loads(proposal_path.read_text(encoding='utf-8'))
    corpus = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    mapping = {'itsuka.mlb': 'dialogue_batch_014', 'eMltFacil.mlb': 'portraits_batch_001'}
    updates = {}
    for item in proposal['rows']:
        source = next(r for r in corpus if all(r[k] == item[k] for k in ('file', 'section', 'index')))
        en = item['translation_en']
        assert source['source_jp'].count('\n') == en.count('\n')
        assert TOKEN.findall(source['source_jp']) == TOKEN.findall(en)
        name = mapping[item['file']]
        path = ROOT / 'work/translation/en' / (name + '.json')
        if path not in updates:
            updates[path] = json.loads(path.read_text(encoding='utf-8'))
        batch = updates[path]
        existing = next((r for r in batch['rows'] if r['id'] == source['id']), None)
        if existing:
            assert existing['translation_en'] == en
            continue
        assert any(r['id'] == source['id'] for r in batch['untranslated_rows'])
        row = dict(source, translation_en=en, status='draft', kind='approved_neutral_adaptation',
                   context='Neutral nonsexual replacement approved by the user on 2026-10-17; deliberately adapted rather than a faithful translation.',
                   fit_status='unverified_in_game', meaning_review='adapted_with_user_approval',
                   review_notes=[item['change'], 'User explicitly selected: Use neutral alternatives.'])
        batch['rows'].append(row)
        batch['rows'].sort(key=lambda r: (r['archive_offset'], r['member_entry'], r['section'], r['index']))
        batch['untranslated_rows'] = [r for r in batch['untranslated_rows'] if r['id'] != source['id']]
        batch['version'] = '0.2.4'
    proposal['version'] = '0.2.4'
    proposal['status'] = 'Approved by the user on 2026-10-17; applied as neutral adaptations, pending in-game layout checks.'
    proposal['approval'] = 'Use neutral alternatives'
    updates[proposal_path] = proposal
    return updates


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    updates = prepare()
    for path, data in updates.items():
        print(path.name, 'rows:', len(data['rows']), 'untranslated:', len(data.get('untranslated_rows', [])))
    print('Sample:', updates[ROOT / 'work/translation/en/safe_adaptations.proposed.json']['rows'][0]['translation_en'])
    if args.write:
        for path, data in updates.items():
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Approved adaptations applied.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

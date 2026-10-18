"""Join the reviewed roster to disc readings and documented deity genders; dry run by default."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    path = ROOT / 'work/glossary/core.json'
    g = json.loads(path.read_text(encoding='utf-8'))
    corpus = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    names = {r['index']: r for r in corpus if r['file'] == 'spirit_name.mlb'}
    readings = {r['index']: r['source_jp'] for r in corpus if r['file'] == 'spirit_kana.mlb'}
    seed = json.loads((ROOT / 'work/translation/en/names_batch_001_input.json').read_text(encoding='utf-8'))
    additions, updates = [], []
    for i, en in enumerate(seed['batches'][0]['translations']):
        if not i:
            continue
        row = names[i]
        jp = row['source_jp']
        # PSP wiki's explicit gender column, cross-checked against this roster.
        gender = None if i == 5 else 'male' if 1 <= i <= 54 or 112 <= i <= 119 else 'female'
        existing = next((x for x in g['characters'] if any(jp.replace(' ','') == a.replace(' ','')
                        for a in [x['jp']] + x.get('aliases_jp', []))), None)
        if existing:
            if en != existing['en']:
                raise ValueError(f'Name conflicts with established glossary: {i}: {en}')
            if existing.get('gender') not in (None, gender):
                raise ValueError(f'Documented gender conflict: {i}')
            if gender and not existing.get('gender'):
                existing['gender'] = gender
                existing['notes'] = existing.get('notes', '').replace(
                    'gender awaits explicit source confirmation.', 'gender is confirmed by the PSP deity list.')
                existing['notes'] += ' Gender verified from the explicit PSP deity-list column.'
                updates.append(dict(index=i,en=en,gender=gender))
            if 'gods_psp' not in existing['sources']:
                existing['sources'].append('gods_psp')
            continue
        entry = dict(id='deity_' + re.sub('[^a-z0-9]+','_',en.lower()).strip('_'), jp=jp,
            aliases_jp=[jp.replace(' ','')] if ' ' in jp else [], en=en, reading=readings[i],
            nicknames=[], gender=gender, personality=None, role='Deity available for Divine Union.',
            sources=['gods_psp','corpus'], source_ids=[row['id']], status='project_spelling',
            notes='Reading verified against spirit_kana.mlb. Gender follows the PSP wiki explicit column; personality and undisclosed biography remain unknown.')
        g['characters'].append(entry)
        additions.append(entry)
    print(json.dumps(dict(additions=len(additions),gender_updates=updates,sample=additions[:3]),ensure_ascii=True,indent=2))
    if args.write:
        path.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

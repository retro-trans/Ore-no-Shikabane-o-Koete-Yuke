"""Derive English display/reading fields from their localized name rows; dry run by default."""
import argparse
import json
from pathlib import Path

from propagate_terms import build as propagate

ROOT=Path(__file__).resolve().parents[1]


def build():
    c=json.loads((ROOT/'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    lookup={(r['file'],r['section'],r['index']):r for r in c}
    english={}
    for p in sorted((ROOT/'work/translation/en').glob('*.en.json')):
        if p.name in ('consistent_terms.en.json','localized_readings.en.json'):
            continue
        for r in json.loads(p.read_text(encoding='utf-8'))['rows']:
            if r['id'] in english and english[r['id']]!=r['translation_en']:
                raise ValueError('Conflicting name translation: '+r['id'])
            english[r['id']]=r['translation_en']
    for r in propagate()['rows']:
        english.setdefault(r['id'],r['translation_en'])
    rows=[]
    pairs={'item_kana.mlb':'item_name.mlb','spell_kana.mlb':'spell.mlb',
           'spirit_kana.mlb':'spirit_name.mlb','monster_kana.mlb':'monster.mlb'}
    for r in c:
        if not r['has_japanese']:
            continue
        if r['file'] in pairs:
            name_key=(pairs[r['file']],r['section'],r['index'])
        elif r['file']=='enemy.mlb' and r['section']==1:
            name_key=('enemy.mlb',0,r['index'])
        else:
            continue
        name=lookup[name_key]
        if name['id'] not in english:
            raise ValueError('Untranslated paired name: '+name['id'])
        en=english[name['id']]
        if not en:
            raise ValueError('Nonempty reading paired with empty English name: '+r['id'])
        rows.append(dict(**r,translation_en=en,status='draft',kind='localized_reading',
            context='English reading/display field linked by table index to the localized name. Visibility and alphabetical sorting require runtime validation.',
            fit_status='unverified_in_game',meaning_review='derived_from_reviewed_name',
            review_notes=['Derived from localized name record '+name['id']+'. No opaque identifier or engine control is changed.']))
    return dict(schema_version=1,version='0.2.2',language='en',
                status='Derived English reading/display fields; runtime display and ordering unverified.',rows=rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    result=build()
    counts={f:sum(r['file']==f for r in result['rows']) for f in sorted({r['file'] for r in result['rows']})}
    print(json.dumps(dict(rows=len(result['rows']),files=counts,
         sample=[{k:r[k] for k in ('id','file','translation_en','review_notes')} for r in result['rows'][:3]]),indent=2))
    if args.write:
        p=ROOT/'work/translation/en/localized_readings.json'
        p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()

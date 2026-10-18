"""Import reviewed complete item names and readings into the glossary; dry run by default."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    p = ROOT / 'work/glossary/core.json'
    g = json.loads(p.read_text(encoding='utf-8'))
    c = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    readings = {(r['section'],r['index']):r['source_jp'] for r in c if r['file']=='item_kana.mlb'}
    rows = [r for n in ('items_batch_001.json','items_batch_002.json') for r in
            json.loads((ROOT/'work/translation/en'/n).read_text(encoding='utf-8'))['rows']]
    additions=[]
    for r in rows:
        if r['translation_en']=='This is a bug.' or r['kind']=='accessory_name' and r['index']>=51:
            continue
        existing=next((t for t in g['terms'] if t['jp']==r['source_jp']),None)
        if existing:
            if existing['en']!=r['translation_en']:
                raise ValueError('Glossary conflict: '+r['id'])
            continue
        t=dict(jp=r['source_jp'],en=r['translation_en'],category='item',
               reading=readings[(r['section'],r['index'])] or None,sources=['corpus'],
               source_ids=[r['id']],status='draft_translation',notes=r['review_notes'])
        additions.append(t)
        g['terms'].append(t)
    ritual_jp='\u53cd\u9b42\u306e\u5100'
    if not any(t['jp']==ritual_jp for t in g['terms']):
        t=dict(jp=ritual_jp,en='Rite of Revival',category='mechanic',sources=['corpus'],
               notes='Life-sacrifice resurrection ceremony, distinct from city rebuilding and Soul Union.')
        g['terms'].append(t)
        additions.append(t)
    g['sources']['weapons_psp']='https://w.atwiki.jp/oreshika_psp/pages/17.html'
    g['sources']['collectibles_psp']='https://w.atwiki.jp/oreshika_psp/pages/43.html'
    print(json.dumps(dict(additions=len(additions),sample=additions[:3]),ensure_ascii=True,indent=2))
    if args.write:
        p.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()

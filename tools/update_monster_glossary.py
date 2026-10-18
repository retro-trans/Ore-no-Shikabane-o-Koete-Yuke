"""Register reviewed monster names and named bosses; dry run by default."""
import argparse
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    p=ROOT/'work/glossary/core.json'
    g=json.loads(p.read_text(encoding='utf-8'))
    c=json.loads((ROOT/'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    readings={r['index']:r['source_jp'] for r in c if r['file']=='monster_kana.mlb'}
    rows=json.loads((ROOT/'work/translation/en/names_batch_002.json').read_text(encoding='utf-8'))['rows']
    by_index={r['index']:r for r in rows}
    g['sources']['tournament_psp']='https://w.atwiki.jp/oreshika_psp/pages/39.html'
    g['sources']['hell_psp']='https://w.atwiki.jp/oreshika_psp/pages/90.html'
    chars=[]
    for i in (240,241,242,243,244,245,246,247,248,252,256,262):
        r=by_index[i]
        if any(x['jp']==r['source_jp'] for x in g['characters']):
            continue
        en=r['translation_en'][10:] if r['translation_en'].startswith('Commander ') else r['translation_en']
        jp=r['source_jp']
        aliases=[]
        if i in (256,262):
            jp=jp[:-2]
            aliases=[r['source_jp']]
        ch=dict(id='boss_'+re.sub('[^a-z0-9]+','_',en.lower()).strip('_'),jp=jp,aliases_jp=aliases,
            en=en,reading=readings[i],nicknames=[],gender=None,personality=None,
            role='Named hair boss.' if i!=241 and i<252 else 'Final story boss.' if i==241 else 'Selection Tournament opponent.',
            sources=['corpus','hell_psp'] if i<252 else ['corpus','tournament_psp'],
            source_ids=[r['id']],status='project_spelling',
            notes='Pronunciation follows the disc. Gender and personality are not inferred from the name. Hair-boss names use gami as a deity/hair pun.' if i<252 and i!=241 else
                  'Pronunciation follows the disc; no identity with a historical person or unconfirmed biography is asserted.')
        g['characters'].append(ch)
        chars.append(ch)
    additions=[]
    for r in rows:
        if not r['source_jp']:
            continue
        known=[t for t in g['terms'] if t['jp']==r['source_jp']]
        if known:
            if any(t['en']!=r['translation_en'] for t in known):
                raise ValueError('Monster glossary conflict: '+r['id'])
            continue
        if any(r['source_jp'] in [x['jp']]+x.get('aliases_jp',[]) for x in g['characters']):
            continue
        term=dict(jp=r['source_jp'],en=r['translation_en'],category='monster',reading=readings[r['index']],
                  sources=['corpus'],source_ids=[r['id']],status='draft_translation',notes=r['review_notes'])
        additions.append(term)
        g['terms'].append(term)
    print(json.dumps(dict(characters_added=len(chars),terms_added=len(additions),
         sample=chars[:2]),ensure_ascii=True,indent=2))
    if args.write:
        p.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()

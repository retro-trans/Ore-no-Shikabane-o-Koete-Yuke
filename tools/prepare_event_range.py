"""Join a reviewed event-dialogue range to its original file/section coordinates."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    s=json.loads(args.seed.read_text(encoding='utf-8'))
    c=json.loads((ROOT/'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    rows=[r for r in c if r['file'].startswith('ev_') and not r['file'].startswith('ev_kitsuto_')
          and r['category']=='dialogue_narration_subtitles']
    start,end=s['start'],s['end']
    if len(s['translations'])!=end-start:
        raise ValueError('Reviewed event translation count does not match range')
    batches=[]
    reviewed={}
    for n,en in enumerate(s['translations'],start):
        r=rows[n]
        if isinstance(en,dict):
            reference=en['same_as']
            if reference not in reviewed or rows[reference]['source_jp']!=r['source_jp']:
                raise ValueError('Reviewed duplicate source differs or is not earlier in this range: '+str(n))
            en=reviewed[reference]
        if not isinstance(en,str):
            raise ValueError('English translation must be text')
        reviewed[n]=en
        if batches and batches[-1]['file']==r['file'] and batches[-1]['section']==r['section'] and batches[-1]['end']==r['index']:
            b=batches[-1]
            b['translations'].append(en)
            b['end']+=1
        else:
            b=dict(file=r['file'],section=r['section'],start=r['index'],end=r['index']+1,
                   kind='event_dialogue',context=s['context'],translations=[en],row_notes={})
            batches.append(b)
        if str(n) in s.get('row_notes',{}):
            b['row_notes'][str(r['index'])]=s['row_notes'][str(n)]
    result=dict(version=s['version'],batches=batches,dialogue_rows_examined_unique=s['dialogue_rows_examined_unique'],
                dialogue_slices=[dict(x,file='Opening and dungeon event dialogue group',file_group_prefix='ev_',
                                     excluded_file_prefixes=['ev_kitsuto_']) for x in s['dialogue_slices']])
    print(json.dumps(dict(rows=end-start,range=[start,end],files=len({b['file'] for b in batches}),
                          sample=[dict(file=b['file'],section=b['section'],translations=b['translations'][:2]) for b in batches[:2]]),indent=2))
    if args.write:
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Coordinate seed written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()

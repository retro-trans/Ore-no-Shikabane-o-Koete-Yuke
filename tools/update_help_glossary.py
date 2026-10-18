"""Add reviewed help terminology and Yuko's documented identity; dry run by default."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    path = ROOT / 'work/glossary/core.json'
    g = json.loads(path.read_text(encoding='utf-8'))
    c = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    titles = {r['index']: r for r in c if r['file'] == 'explane.mlb' and r['section'] == 0}
    seed = json.loads((ROOT / 'work/translation/en/ui_batch_006_input.json').read_text(encoding='utf-8'))
    labels = seed['batches'][0]['translations']
    additions = []
    for index in (34,54,80,81,82,83,85,86,87,88):
        row = titles[index]
        if any(t['jp'] == row['source_jp'] for t in g['terms']):
            continue
        term = dict(jp=row['source_jp'], en=labels[index], category='location' if 80<=index<=88 else 'mechanic',
                    sources=['corpus'], status='project_translation', source_ids=[row['id']])
        g['terms'].append(term)
        additions.append(term)
    char = dict(id='yuko', jp=titles[98]['source_jp'], aliases_jp=['太照天 夕子','夕子'],
                en='Yuko Taishoten', short_en='Yuko', reading='タイショウテン ユウコ', nicknames=[],
                gender='female', personality=None,
                role="Former ruler of heaven; Hiruko's adoptive parent and guardian.",
                sources=['gods_psp','corpus'], status='project_spelling',
                notes='Reading and gender verified against the PSP deity list. Role stated in explane.mlb 1:253-254. Personality not inferred.')
    if not any(t['id'] == char['id'] for t in g['characters']):
        g['characters'].append(char)
        additions.append(char)
    print(json.dumps(dict(additions=additions), ensure_ascii=True, indent=2))
    if args.write:
        path.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

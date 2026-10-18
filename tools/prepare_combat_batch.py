"""Split the reviewed combat seed and extend the glossary. Dry run by default."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    folder = ROOT / 'work/translation/en'
    seed = json.loads((folder / 'combat_batch_001_input.json').read_text(encoding='utf-8'))
    if not any(b['file'] == 'spell.mlb' for b in seed['batches']):
        saved_names = json.loads((folder / 'combat_names_001_input.json').read_text(encoding='utf-8'))
        seed['batches'] = saved_names['batches'] + seed['batches']
    spell_batch = next(b for b in seed['batches'] if b['file'] == 'spell.mlb')
    spell_batch['translations'][13] = 'Koruidan'
    spell_batch['translations'][56] = 'Tatekezuri'
    corpus = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    battle = [r for r in corpus if r['file'] == 'battle.mlb']
    assert len(battle) == 205
    result = dict(version=seed['version'], batches=[b for b in seed['batches'] if b['file'] == 'battle.mlb'],
                  dialogue_rows_examined_unique=205, dialogue_slices=[])
    for start in (0, 80, 125):
        result['dialogue_slices'].append(dict(file='battle.mlb', start=start, end=start+80,
            rows_in_slice=80, rows_examined=min(205,start+84)-max(0,start-2),
            context='Battle table reviewed in full: menu/result fragments, Hiruko and Kitsuto remarks, then action messages. Windows overlap at EOF; each row stored once.'))
    names = dict(version=seed['version'], batches=[b for b in seed['batches'] if b['file'] != 'battle.mlb'])
    glossary_path = ROOT / 'work/glossary/core.json'
    glossary = json.loads(glossary_path.read_text(encoding='utf-8'))
    glossary['version'] = seed['version']
    glossary['sources']['spells_psp'] = 'https://w.atwiki.jp/oreshika_psp/pages/23.html'
    spells = {r['index']: r for r in corpus if r['file'] == 'spell.mlb'}
    readings = {r['index']: r['source_jp'] for r in corpus if r['file'] == 'spell_kana.mlb'}
    additions = []
    for index, en in enumerate(names['batches'][0]['translations']):
        jp = spells[index]['source_jp']
        existing = next((t for t in glossary['terms'] if t['jp'] == jp), None)
        if existing:
            if existing['en'] != en:
                raise ValueError(f'Conflicting glossary term at spell {index}')
            continue
        additions.append(dict(jp=jp, en=en, category='spell', reading=readings.get(index) or None,
            sources=['corpus','spells_psp'] if 0 < index < 83 else ['corpus'],
            status='project_spelling' if index < 83 else 'draft_translation'))
    glossary['terms'].extend(additions)
    print(json.dumps(dict(battle_rows=len(battle), slices=result['dialogue_slices'],
        name_help_rows=sum(len(b['translations']) for b in names['batches']), glossary_additions=len(additions),
        sample=additions[:3]), ensure_ascii=True, indent=2))
    if args.write:
        (folder / 'combat_batch_001_input.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        (folder / 'combat_names_001_input.json').write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding='utf-8')
        glossary_path.write_text(json.dumps(glossary, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

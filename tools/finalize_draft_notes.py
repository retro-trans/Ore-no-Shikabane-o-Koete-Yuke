"""Apply narrowly reviewed 0.2.2 metadata and terminology corrections; dry run by default."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = 'Itsuka refers to herself by name; English uses I in this row.'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    folder = ROOT / 'work/translation/en'
    changed = []
    writes = {}
    corpus = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    lookup = {(r['file'], r['section'], r['index']): r for r in corpus}
    for name in ('ui_batch_006','ui_batch_007','ui_batch_008','ui_batch_009'):
        for suffix in ('_input.json','.json'):
            p = folder / (name + suffix)
            obj = json.loads(p.read_text(encoding='utf-8'))
            if suffix == '_input.json':
                for b in obj['batches']:
                    if NOTE not in b.get('review_notes', []):
                        continue
                    b['review_notes'].remove(NOTE)
                    for index, en in enumerate(b['translations'], b['start']):
                        jp = lookup[(b['file'], b['section'], index)]['source_jp']
                        if '\u30a4\u30c4\u82b1' in jp and 'Itsuka' not in en:
                            notes = b.setdefault('row_notes', {}).setdefault(str(index), [])
                            if NOTE not in notes:
                                notes.append(NOTE)
            else:
                for r in obj['rows']:
                    notes = r.get('review_notes', [])
                    needed = '\u30a4\u30c4\u82b1' in r['source_jp'] and 'Itsuka' not in r['translation_en']
                    if NOTE in notes and not needed:
                        r['review_notes'] = [n for n in notes if n != NOTE]
                        changed.append(r['id'])
            writes[p] = obj
    for suffix in ('_input.json','.json'):
        p = folder / ('ui_batch_010' + suffix)
        obj = json.loads(p.read_text(encoding='utf-8'))
        note = 'Subject-first inheritance announcement preserves the source token order: recipient %2:s, then sword %1:s.'
        if suffix == '_input.json':
            b = next(b for b in obj['batches'] if b['file']=='item_etc.mlb' and b['section']==4)
            b['row_notes']['32'] = [note]
        else:
            r = next(r for r in obj['rows'] if r['file']=='item_etc.mlb' and r['section']==4 and r['index']==32)
            r['review_notes'] = [note]
        writes[p] = obj
    for suffix in ('_input.json','.json'):
        p = folder / ('combat_names_001' + suffix)
        obj = json.loads(p.read_text(encoding='utf-8'))
        en = "Fully restores one ally's MP, exhausting you"
        if suffix == '_input.json':
            b = next(b for b in obj['batches'] if b['file']=='spell_help.mlb')
            b['translations'][46] = en
        else:
            r = next(r for r in obj['rows'] if r['file']=='spell_help.mlb' and r['index']==46)
            r['translation_en'] = en
        writes[p] = obj
    print(json.dumps(dict(note_corrections=len(changed), sample=changed[:4],
        wording_correction=dict(file='spell_help.mlb',index=46,en=en),
        inventory_note='Corrected subject/object description; translation text unchanged.'),indent=2))
    if args.write:
        for p,obj in writes.items():
            p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Written. Re-export affected batches.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

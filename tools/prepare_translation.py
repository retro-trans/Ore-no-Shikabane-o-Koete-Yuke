"""Join English drafts to local Japanese records by file/section/index; dry run by default."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def dialogue_context(section, index):
    groups = {
        4: [(10, 'First arrival: greeting the clan head and explaining sortie preparation.'),
            (16, 'After meeting Hiruko: Itsuka jokes about the resemblance; lines 12-13 are mock surprise.'),
            (23, 'After learning about the real Shutendoji: Itsuka defends the decision to free captive deities.'),
            (26, 'Report of three new oni lairs around the capital.'),
            (29, 'Report of a scarlet seal and rumored entrance to hell.'),
            (33, 'Late-game report: the capital and heavenly roster have changed; Mount Oe reopened.'),
            (39, 'After encountering Hiruko on Mount Oe: Itsuka acknowledges divided loyalties.')],
        5: [(5, 'Before meeting a child: Itsuka explains inherited potential.'),
            (11, 'Before a first battle: age affects Body differently from Skill and Spirit.'),
            (15, 'Training tutorial: ask a resting or elderly family member to teach a child.'),
            (19, 'Class manuals tutorial: different classes create more tactical options.'),
            (24, 'Family-size advice: avoid an irreplaceable elite party; large family meals are a joke.'),
            (29, 'Preparing for Mount Oe: select a party, rest older members, bring everyone home.'),
            (33, 'Gift tutorial: sell valuables or improve a family member\'s Loyalty.'),
            (38, 'Loyalty warning: being ignored can lead clan members to run away.'),
            (42, 'Selection Tournament congratulations; the next rows continue this speech.')]
    }
    return 'Itsuka speaks respectfully and conversationally to the player-selected clan head. ' + next(
        text for end, text in groups[section] if index <= end)


def review_notes(file, section, index):
    notes = []
    if file == 'itsuka.mlb':
        notes.append('No gender inferred for the clan head or runtime family members.')
        if (section, index) in {(4, 17), (4, 19), (4, 20), (4, 31), (4, 34), (4, 36), (5, 23)}:
            notes.append('Intentional source trailing fragment retained; inspect adjacent rows.')
        if (section, index) == (4, 20):
            notes.append('Sentence continues in 4:21; no rows merged. The decision belongs to Hiruko.')
        if (section, index) == (4, 12):
            notes.append('Itsuka voices an imagined reaction from the clan head; quotation marks clarify the shift.')
        if (section, index) == (4, 28):
            notes.append('Seal is provisional for the supernatural mark; appearance and terminology need a game capture.')
        if (section, index) == (5, 9):
            notes.append('Skill and Spirit are named stat groups; do not substitute MP or Health.')
        if (section, index) == (5, 35):
            notes.append('Three tactical proposals are imagined complaints; full subjects were restored where the speaker is clear.')
        if (section, index) == (5, 37):
            notes.append('Direct quotation is a hypothetical family member; no male pronoun inferred from Japanese first-person speech.')
        if (section, index) in {(4, 32), (4, 39)}:
            notes.append('Itsuka refers to herself by name; English uses I in this row.')
    if file == 'home.mlb' and section == 0 and index == 26:
        notes.append('Kenpuku is a provisional reading; check before finalizing the UI.')
    if file == 'home.mlb' and section == 4:
        notes.append('Class descriptions use conventional UI fragments; large armor is kept distinct from heavy armor.')
    return notes


def prepare(seed=None):
    corpus = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    seeds = json.loads((seed or ROOT / 'work/translation/en/initial_draft_input.json').read_text(encoding='utf-8'))
    lookup = {}
    for row in corpus:
        key = row['file'], row['section'], row['index']
        lookup.setdefault(key, []).append(row)
    translated = []
    for batch in seeds['batches']:
        repeat = batch.get('repeat', 1)
        if 'translations_by_index' in batch:
            if 'translations' in batch or repeat != 1 or 'end' not in batch:
                raise ValueError('Indexed translations require an end and cannot be mixed with repeat/list input')
            mapping = batch['translations_by_index']
            expected_keys = {str(i) for i in range(batch['start'], batch['end'])}
            if set(mapping) - expected_keys:
                raise ValueError('Indexed translation falls outside its declared range')
            translations = []
            for index in range(batch['start'], batch['end']):
                matches = lookup.get((batch['file'], batch['section'], index), [])
                if len(matches) != 1:
                    raise ValueError('Missing/ambiguous source in indexed range')
                jp = matches[0]['source_jp']
                if str(index) not in mapping and jp:
                    raise ValueError('Missing nonempty indexed translation: ' + str(index))
                translations.append(mapping.get(str(index), ''))
        else:
            translations = batch['translations']
        if type(repeat) is not int or repeat < 1 or (repeat != 1 and len(translations) != 1):
            raise ValueError('repeat must be positive and may only expand one reviewed translation')
        translations = translations * repeat
        if 'end' in batch and batch['start'] + len(translations) != batch['end']:
            raise ValueError('Translation count mismatch for ' + str((batch['file'], batch['start'], batch['end'])))
        repeated_source = None
        for index, en in enumerate(translations, batch['start']):
            en = batch.get('prefix', '') + en
            matches = lookup.get((batch['file'], batch['section'], index), [])
            if len(matches) != 1:
                raise ValueError(f'Ambiguous or missing source: {batch["file"]}:{batch["section"]}:{index}')
            source = matches[0]
            if repeat > 1:
                if repeated_source is not None and source['source_jp'] != repeated_source:
                    raise ValueError('Repeated translation range contains different source strings')
                repeated_source = source['source_jp']
            notes = review_notes(batch['file'], batch['section'], index)
            if batch['file'] == 'eMltTrain.mlb' and batch['section'] == 1 and index in (9, 10):
                notes.append('Itsuka refers to herself by name; English uses I in this row.')
            if batch['kind'] == 'history_fragment':
                notes.append('Chronicle UI fragments combine at runtime. Preserve row boundaries and review the composed result.')
            if batch['file'] == 'title.mlb' and batch['section'] == 6 and index < 4:
                notes.append('Japanese era year retained; no Gregorian conversion is inferred from the placeholders.')
            if batch['file'] == 'title.mlb' and batch['section'] == 3 and index == 24:
                notes.append('Intentional source trailing fragment retained; sentence continues in 3:25.')
            translated.append(dict(**source, translation_en=en, status='draft', kind=batch['kind'],
                                   context=batch['context'] if 'context' in batch else
                                   dialogue_context(batch['section'], index) if batch['file'] == 'itsuka.mlb'
                                   else 'Itsuka addresses the player-selected clan head.' if batch['kind'] == 'dialogue'
                                   else 'Title/setup, clan history, or service menu as identified by the complete source table.'
                                   if seed else 'Home menu/help, settings, or opening narration as identified by the source file.',
                                   fit_status='unverified_in_game', meaning_review='self_reviewed',
                                   review_notes=notes + batch.get('review_notes', []) + batch.get('row_notes', {}).get(str(index), [])))
    if len({r['id'] for r in translated}) != len(translated):
        raise ValueError('Duplicate translation row ID')
    result = dict(schema_version=1, version=seeds['version'], language='en',
                  status='Draft translation; not an installable patch.', rows=translated,
                  dialogue_slices=seeds.get('dialogue_slices', []))
    if 'dialogue_rows_examined_unique' in seeds:
        result['dialogue_rows_examined_unique'] = seeds['dialogue_rows_examined_unique']
    if seeds.get('untranslated_rows'):
        unresolved = []
        for issue in seeds['untranslated_rows']:
            matches = lookup.get((issue['file'], issue['section'], issue['index']), [])
            if len(matches) != 1 or not issue.get('reason'):
                raise ValueError('Unresolved row requires a unique source identity and reason')
            row = matches[0]
            if row['id'] in {r['id'] for r in translated}:
                raise ValueError('Unresolved row also has a translation')
            unresolved.append({k: row[k] for k in ('id', 'file', 'section', 'index', 'source_sha256')})
            unresolved[-1].update(status='untranslated', reason=issue['reason'])
        result['untranslated_rows'] = unresolved
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--seed', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = prepare(args.seed)
    print(json.dumps({'rows': len(result['rows']), 'sample': [
        {'id': r['id'], 'translation_en': r['translation_en']}
        for r in result['rows'][:3]]}, ensure_ascii=True, indent=2))
    if args.write:
        dest = args.output or ROOT / 'work/translation/en/initial_batch.json'
        # Do not silently replace editorial work on a later rerun.
        if dest.exists():
            old = json.loads(dest.read_text(encoding='utf-8'))
            def identities(batch):
                return {r['id']: (r['source_sha256'], r['translation_en']) for r in batch['rows']}
            if identities(old) != identities(result):
                raise ValueError('Existing translations differ; merge edits explicitly instead of overwriting them.')
        dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Batch written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

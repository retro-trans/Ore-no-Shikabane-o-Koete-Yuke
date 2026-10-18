"""Apply specific reviewed caption/grammar corrections. Dry run by default."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = [
    ('portraits_batch_001', 'Kahoru Fukaya', 'Kaoru Fukaya'),
    ('events_batch_002', "And that baby...?\nAsk anyone,\nand no one knows where it went...",
     "And that baby...? Ask anyone,\nand no one knows where it went..."),
    ('portraits_batch_001', '(Homare)\nEnjoy this\nreborn Oreshika\nto the fullest!\nHeh heh\nheh heh...',
     '(Homare)\nEnjoy this reborn\nOreshika\nto the fullest!\nHeh heh heh heh...'),
    ('portraits_batch_001', '(Tomomi Kobayashi)\nTo all\nthe players,\nplease keep\nenjoying Oreshika\nfor years to come.',
     '(Tomomi Kobayashi)\nTo all the players,\nplease keep\nenjoying Oreshika\nfor years to come.'),
    ('dialogue_batch_015', "Congratulations on becoming clan head\nand inheriting the name '%d: %@ %$'!!\nMy heartfelt best wishes!!",
     "Congratulations on becoming clan head.\nAs generation %d, you've inherited '%@ %$'.\nMy heartfelt best wishes!!"),
    ('dialogue_batch_013', "If you need to beat Shuten,\nuse even the gods as stepping stones.\nI don't care. You have my permission.",
     "For victory over Shuten,\nuse even the gods as stepping stones if you must.\nI don't care. You have my permission."),
]


def main():
    import json
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    changed = {}
    for batch, old, new in CORRECTIONS:
        paths = [ROOT / ('work/translation/en/' + batch + suffix) for suffix in ('_input.json', '.json')]
        if batch == 'portraits_batch_001':
            paths.append(ROOT / 'tools/prepare_portrait_draft.py')
        if batch.startswith('events_batch_'):
            paths.append(ROOT / ('work/translation/en/' + batch + '_range.json'))
        for path in paths:
            text = changed.get(path, path.read_text(encoding='utf-8'))
            # JSON encodes actual newlines; the seed generator uses single-quoted
            # Python literals with the same newline escaping for these captions.
            before, after = old.replace('\n', '\\n'), new.replace('\n', '\\n')
            count = text.count(before)
            if count == 0 and after not in text:
                raise ValueError('Expected reviewed text missing: ' + str(path))
            if count:
                text = text.replace(before, after)
                changed[path] = text
                print(path.name + ': ' + str(count) + ' reviewed replacements; ' + new.split('\n')[0])
    if args.write:
        for path, text in changed.items():
            if path.suffix == '.json':
                json.loads(text)
            path.write_text(text, encoding='utf-8')
    print('Corrections written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

"""Check live translated text and the native font hook in the isolated PPSSPP test.

Dry run by default. --execute sends Start and temporarily sets one breakpoint;
--write also saves the source-free runtime evidence. No screenshot is claimed.
"""
import argparse
import base64
import json
import struct
import time
from pathlib import Path

from ppsspp_debug import Session

ROOT = Path(__file__).resolve().parents[1]
BREAK = 0x089BA8BC
NATIVE = 0x09B5C010
TITLE_TEXT = {'New Game', 'Continue', 'Prologue', 'Adoption', 'Share Deity',
              'Begin a new game.', 'Continue from a saved game.',
              'The incident that set the story in motion.'}


def read(session, address, size):
    return base64.b64decode(session.call('memory.read', address=address, size=size)['base64'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--version', default='0.2.0', help='Test build version; used in the evidence filename')
    ap.add_argument('--no-input', action='store_true', help='Inspect the current title menu without sending Start')
    args = ap.parse_args()
    if not args.execute:
        print(json.dumps(dict(mode='dry run', target='local debugger port 19417, UCJS10117',
                              actions=['Verify native image signature'] + ([] if args.no_input else ['Press Start']) + [
                                       'Temporarily break after the native font selector',
                                       'Read English glyph descriptors and verify 4x UV sizes',
                                       'Remove breakpoint and resume'],
                              report='work/ui/english-runtime-' + args.version + '.json' if args.write else None), indent=2))
        return
    metrics = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    with Session() as session:
        if session.call('game.status')['game']['id'] != 'UCJS10117':
            raise ValueError('Unexpected game; no input sent')
        if read(session, NATIVE + 4, 6) != struct.pack('<3H', 512, 512, 4):
            raise ValueError('Native image signature absent; no input sent')
        if session.call('cpu.status')['stepping']:
            raise ValueError('Test game is already paused; preserve its state')
        if not args.no_input:
            session.call('input.buttons.send', buttons={'start': True})
            time.sleep(0.15)
            session.call('input.buttons.send', buttons={'start': False})
            time.sleep(1)
        captures, added = [], False
        try:
            session.call('cpu.breakpoint.add', address=BREAK, condition='v0 == 0x09b5c010')
            added = True
            for attempt in range(24):
                deadline = time.monotonic() + 8
                while not session.call('cpu.status')['stepping']:
                    if time.monotonic() > deadline:
                        raise TimeoutError('Native draw breakpoint did not fire')
                    time.sleep(0.05)
                regs = session.call('cpu.getAllRegs')['categories'][0]
                regs = dict(zip(regs['registerNames'], regs['uintValues']))
                if regs['pc'] != BREAK or regs['v0'] != NATIVE:
                    raise ValueError('Unexpected breakpoint; inspect before continuing')
                pointer = struct.unpack('<I', read(session, regs['s1'] + 0xd4, 4))[0]
                raw = read(session, pointer, 28 * 256)
                text, checked = [], 0
                for offset in range(0, len(raw), 28):
                    code, advance = struct.unpack_from('<2H', raw, offset + 4)
                    if code == 0:
                        break
                    x, y, right, bottom = struct.unpack_from('<4H', raw, offset + 16)
                    expected = metrics[str(code)]
                    assert right - x == expected['sample_width'] * 64
                    assert bottom - y == 80 * 64
                    assert advance == expected['advance']
                    text.append(chr(code))
                    checked += 1
                else:
                    raise ValueError('No glyph terminator within safe descriptor bound')
                label = ''.join(text)
                if label not in {c['text'] for c in captures}:
                    captures.append(dict(text=label, glyphs_checked=checked, image=hex(regs['v0'])))
                if any(c['text'] in TITLE_TEXT for c in captures):
                    break
                session.call('cpu.resume')
        finally:
            if added:
                session.call('cpu.breakpoint.remove', address=BREAK)
            if session.call('cpu.status')['stepping']:
                session.call('cpu.resume')
        translated = any(c['text'] in TITLE_TEXT for c in captures)
        report = dict(version=args.version, font_component_version='0.2.0', game='UCJS10117', combined_build_boot_verified=True,
                      translated_title_reached=translated, native_hook_executed=bool(captures),
                      source_sampling_scale=4, texture_replacement=False, captures=captures,
                      visual_verification='Pending; glyph descriptors are runtime evidence, not a screenshot.')
        print(json.dumps(report, indent=2))
        if args.write:
            (ROOT / ('work/ui/english-runtime-' + args.version + '.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
        if not translated:
            raise SystemExit('Translated title label not observed; inspect the captures')


if __name__ == '__main__':
    main()

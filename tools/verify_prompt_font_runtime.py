"""Read the live button-prompt font selection. Dry run before --execute."""
import argparse
import base64
import json
import struct
import time

from catalog_text import ROOT
from ppsspp_debug import Session
from capture_psp_frame import capture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--execute', action='store_true')
parser.add_argument('--write', action='store_true')
parser.add_argument('--shape', choices=('circle', 'triangle'), default='circle')
parser.add_argument('--ends-with', default='button.')
args = parser.parse_args()
folder = ROOT / 'work/ui/prompt-font-0.2.39'
report = json.loads((ROOT / 'work/output/english-native-0.2.39/prompt.report.json').read_text())
page = report['pages']['0x25cb' if args.shape == 'circle' else '0x25b3']
print(json.dumps(dict(execute=args.execute, image=hex(page['image']),
    actions=['Temporarily break after the font selector', 'Read actual glyph UVs and codepoints',
             'Remove breakpoint, resume and capture framebuffer'], game_memory_writes=False)))
if not args.execute:
    raise SystemExit
proof = None
with Session() as session:
    def read(address, size):
        return base64.b64decode(session.call('memory.read', address=address, size=size)['base64'])
    assert session.call('game.status')['game']['id'] == 'UCJS10117'
    assert not session.call('cpu.status')['stepping']
    hook = int(report['hook'], 16)
    assert struct.unpack('<I', read(hook, 4))[0] == 0x0c000000 | (int(report['selector'], 16) >> 2)
    pc = hook + 8
    session.call('cpu.breakpoint.add', address=pc, condition='v0 == ' + hex(page['image']))
    try:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            while not session.call('cpu.status')['stepping']:
                assert time.monotonic() < deadline, 'Button prompt was not rendered in the current scene'
                time.sleep(.02)
            cat = session.call('cpu.getAllRegs')['categories'][0]
            regs = dict(zip(cat['registerNames'], cat['uintValues']))
            assert regs['pc'] == pc and regs['v0'] == page['image']
            obj = regs['s1']
            pointer = struct.unpack('<I', read(obj + 0xd4, 4))[0]
            raw = read(pointer, 28 * 120)
            text, glyphs = '', []
            for offset in range(0, len(raw), 28):
                cp, advance = struct.unpack_from('<2H', raw, offset + 4)
                if not cp:
                    break
                expected_cp = 32 if cp == 160 else cp
                uv = list(struct.unpack_from('<4H', raw, offset + 16))
                expected = page['glyphs'][str(expected_cp)]
                assert uv == expected['uv']
                glyphs.append(dict(codepoint=hex(cp), advance=advance, uv=uv,
                    destination=list(struct.unpack_from('<4H', raw, offset + 8))))
                text += chr(cp)
            if text.endswith(args.ends_with):
                proof = dict(version='0.2.39', result='PASS', text=text, image=hex(page['image']),
                    glyphs=glyphs, source_sampling_scale=4, game_memory_writes=False,
                    texture_replacement=False, renderer='Actual final ISO native draw path')
                break
            session.call('cpu.resume')
    finally:
        session.call('cpu.breakpoint.remove', address=pc)
        if session.call('cpu.status')['stepping']:
            session.call('cpu.resume')
assert proof
print(json.dumps(proof, indent=2))
if args.write:
    (folder / ('runtime-' + args.shape + '.json')).write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    image, metadata = capture()
    image.save(folder / ('settings-' + args.shape + '.png'))
    (folder / ('settings-' + args.shape + '.json')).write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')

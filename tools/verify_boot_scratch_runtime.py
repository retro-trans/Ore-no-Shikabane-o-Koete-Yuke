"""Verify the actual prologue framebuffer copy and protected patch assets. Dry run first."""
import argparse
import base64
import json
import struct

from catalog_text import ROOT
from ppsspp_debug import Session

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--execute', action='store_true')
parser.add_argument('--write', action='store_true')
args = parser.parse_args()
print(json.dumps(dict(execute=args.execute,
    actions=['Read patched accessors and active scratch pointer', 'Read GPU write provenance',
             'Compare parent names and all ten vital/element payloads to the final executable'],
    game_memory_writes=False)))
if not args.execute:
    raise SystemExit
folder = ROOT / 'work/output/english-native-0.2.40'
report = json.loads((folder / 'scratch.report.json').read_text())
elf = (folder / 'EBOOT.scratch.elf').read_bytes()
po = struct.unpack_from('<I', elf, 28)[0]
ph = struct.unpack_from('<8I', elf, po + 32)
offset = lambda address: ph[1]+address-ph[2] if address >= ph[2] else address-0x08803000
icons = json.loads((ROOT / 'work/output/english-native-0.2.31/icons.report.json').read_text())['icons']
scratch = int(report['scratch']['address'], 16)
with Session() as session:
    assert session.call('game.status')['game']['id'] == 'UCJS10117'
    assert not session.call('cpu.status')['stepping']
    def read(address, size):
        return b''.join(base64.b64decode(session.call('memory.read', address=address+i,
            size=min(16384, size-i))['base64']) for i in range(0, size, 16384))
    for patch in report['patches']:
        address = int(patch['address'], 16)
        line = next(x for x in session.call('memory.disasm', address=address, count=2,
            displaySymbols=False)['lines'] if x['address'] <= address < x['address']+x['addressSize'])
        words = line.get('macroEncoding') or [line['encoding']]
        assert words[(address-line['address'])//4] == int(patch['after'], 16)
    active = struct.unpack('<I', read(0x09ae65ac, 4))[0]
    assert active == scratch, hex(active)
    rows = [x for x in session.call('memory.info.list', address=scratch,
        size=report['scratch']['bytes'], type='write')['extents'] if x['tag'].startswith('GPUBlockTransfer/')]
    assert len(rows) == 272 and rows[0]['address'] == scratch
    assert all(x['address'] == scratch+i*2048 and x['size'] == 1920 for i, x in enumerate(rows))
    assert rows[-1]['address']+rows[-1]['size'] <= int(report['scratch']['end'], 16)
    assert read(0x09b85a74, 24) == elf[offset(0x09b85a74):offset(0x09b85a74)+24]
    checked = []
    for icon in icons:
        for name, size in [('pixels', icon['pixel_bytes']), ('palette', 1040)]:
            address = int(icon[name], 16)
            assert read(address, size) == elf[offset(address):offset(address)+size], (icon['file'], name)
        checked.append(icon['file'])
proof = dict(version='0.2.40', result='PASS', active_scratch=hex(active), bytes=report['scratch']['bytes'],
    actual_gpu_transfer=dict(rows=len(rows), first=rows[0], last=rows[-1]),
    names='Genta and Orin source strings byte-identical to final executable',
    icon_payloads_verified=checked, palettes_and_pixels='All ten byte-identical after the actual GPU transfer',
    game_memory_writes=False, save_state_loaded=False, texture_replacement=False)
print(json.dumps(proof, indent=2))
if args.write:
    (ROOT / 'work/ui/boot-scratch-0.2.40/runtime.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')

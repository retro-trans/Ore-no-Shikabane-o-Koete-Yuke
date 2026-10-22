"""Read the final Divine Union layout in the isolated emulator. Dry run first."""
import argparse
import base64
import json
import struct

from catalog_text import ROOT
from ppsspp_debug import Session

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--execute',action='store_true')
args = ap.parse_args()
if not args.execute:
    print('DRY RUN: verify five live instructions, eight recorded sort cells, and current confirmation geometry; save runtime.json. No guest memory writes.')
    raise SystemExit
ui = ROOT / 'work/ui/union-layout-0.2.47'
report = json.loads((ROOT / 'work/output/english-native-0.2.47/union.report.json').read_text())
sort = json.loads((ui / 'sort-tree.json').read_text())
confirmation = json.loads((ui / 'confirmation-tree.json').read_text())
cells = {}
frames = {}
for row in sort:
    for parent in row['ancestors']:
        if parent['vtable'] == '0x8a20170':
            cells[parent['object']] = parent['geometry']
        if parent['vtable'] == '0x8a20018':
            frames[parent['object']] = parent['geometry']
assert len(cells) == 8
assert set(tuple(g) for g in cells.values()) == {(x,y,160,16) for x in [10,178] for y in [10,29,48,67]}
assert list(frames.values()) == [[66,90,348,91]]
caption = next(r for r in confirmation if r['text'] == 'Offering Points Required')
root = next(p for p in caption['ancestors'] if p['vtable'] == '0x8a42a48')
root_address = int(root['object'],16)
value = next(r for r in confirmation if r['text'].isdigit())
assert caption['ancestors'][1]['geometry'][:2] == [299,162]
assert value['ancestors'][1]['geometry'][:2] == [447,178]
patches = []
with Session() as s:
    assert not s.call('cpu.status')['stepping']
    s.call('cpu.stepping')
    try:
        for patch in report['patches']:
            pc = int(patch['address'],16)
            word = s.call('memory.disasm',address=pc,count=1,displaySymbols=False)['lines'][0]['encoding']
            assert word == int(patch['after'],16),patch
            patches.append(dict(address=hex(pc),word=hex(word)))
        raw = base64.b64decode(s.call('memory.read',address=root_address+0x1550+0x40,size=16)['base64'])
        frame = list(struct.unpack('<4I',raw))
        assert frame == [291,136,160,60]
    finally:
        s.call('cpu.resume')
proof = dict(version='0.2.47',result='PASS',native_patches=patches,
    sort_frame=list(frames.values())[0],sort_cells=cells,
    confirmation_card=frame,caption=caption['text'],caption_position=[299,162],
    value=value['text'],value_position=[447,178],
    guest_memory_writes=False,save_state_loaded=False,texture_replacement=False)
(ui / 'runtime.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))

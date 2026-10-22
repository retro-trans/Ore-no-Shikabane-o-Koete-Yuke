"""Read the live six-line Help geometry and opacity. Dry run by default."""
import argparse
import base64
import json
import struct

from catalog_text import ROOT
from ppsspp_debug import Session


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    ui = ROOT / 'work/ui/help-dialogue-0.2.45'
    if not args.execute:
        print('DRY RUN: read FAQ object from after-tree.json, verify frame and alpha, save runtime.json. No guest memory writes.')
        return
    tree = json.loads((ui / 'after-tree.json').read_text())
    row = next(r for r in tree if 'remember this' in r['text'])
    ancestors = row['ancestors']
    index = next(i for i, r in enumerate(ancestors) if r['vtable'] == '0x8a208b8')
    obj = int(ancestors[index]['object'], 16)
    with Session() as s:
        def read(p, n):
            return base64.b64decode(s.call('memory.read', address=p, size=n)['base64'])
        assert not s.call('cpu.status')['stepping']
        s.call('cpu.stepping')
        try:
            assert struct.unpack('<I', read(0x088fa718, 4))[0] == 0x24050150
            b = read(obj, 0x240)
            geometry = list(struct.unpack_from('<4I', b, 0x40))
            assert geometry == [8,144,336,120]
            colors = list(struct.unpack_from('<4I', b, 0x220))
            assert all(c >> 24 == 255 for c in colors)
            sprite_opacity = struct.unpack_from('<f', b, 0x14c)[0]
            assert sprite_opacity == 1.0
            opacity = []
            for parent in ancestors[index:]:
                p = int(parent['object'], 16)
                value = struct.unpack('<f', read(p+0x2c, 4))[0]
                assert value == 1.0
                opacity.append(dict(object=hex(p), value=value))
            desc = struct.unpack_from('<I', b, 0x1ec)[0]
            d = read(desc, 48)
            assert struct.unpack_from('<H', d, 8)[0] == 5
            palette = struct.unpack_from('<I', d, 0x24)[0]
            ph = read(palette, 16)
            assert struct.unpack_from('<H', ph, 4)[0] == 3
            pp = struct.unpack_from('<I', ph, 8)[0]
            alphas = sorted(set(read(pp, 1024)[3::4]))
            assert alphas == [255]
        finally:
            s.call('cpu.resume')
    proof = dict(version='0.2.45', result='PASS', geometry=geometry,
        background=dict(vertex_alpha=[c >> 24 for c in colors], palette_alpha=alphas,
            sprite_opacity=sprite_opacity, ancestor_opacities=opacity,
            conclusion='Fully opaque; existing native settings retained'),
        text=row['text'], guest_memory_writes=False, save_state_loaded=False,
        runtime_patch='0x24050150 at 0x088fa718', texture_replacement=False)
    (ui / 'runtime.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()

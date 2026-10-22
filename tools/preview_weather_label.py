"""Select Downpour text once for a QA banner preview, without changing weather or saves."""
import argparse
import base64
import json
import struct
import time

from catalog_text import ROOT
from ppsspp_debug import Session

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--execute', action='store_true')
args = ap.parse_args()
if not args.execute:
    print('DRY RUN: watch native weather-label lookup for 120 seconds; select text index 1 once. No PC/code/save/weather-state edits. Output: preview-label.json.')
    raise SystemExit
pc = 0x08815b10
proof = dict(version='0.2.46', diagnostic_only=True, result='NOT REACHED',
    purpose='Render Downpour wording in the real dungeon banner without requiring random weather',
    weather_state_changed=False, code_or_pc_changed=False, save_state_loaded=False)
with Session() as s:
    assert not s.call('cpu.status')['stepping']
    s.call('cpu.breakpoint.add', address=pc)
    try:
        deadline = time.monotonic()+120
        while time.monotonic() < deadline:
            state = s.call('cpu.status')
            if state['stepping'] and state['pc'] == pc:
                r = s.call('cpu.getAllRegs')['categories'][0]['uintValues']
                stack = base64.b64decode(s.call('memory.read', address=r[29], size=16)['base64'])
                caller = struct.unpack_from('<I', stack, 4)[0]
                assert caller == 0x08891080, hex(caller)
                assert 0 <= r[2] < 8
                s.call('cpu.setReg', name='v0', value=1)
                proof.update(result='LABEL SELECTED', original_text_index=r[2], preview_text_index=1,
                    caller=hex(caller), breakpoint=hex(pc))
                s.call('cpu.resume')
                break
            time.sleep(.03)
    finally:
        s.call('cpu.breakpoint.remove', address=pc)
        state = s.call('cpu.status')
        if state['stepping'] and state['pc'] == pc:
            s.call('cpu.resume')
(ROOT / 'work/ui/weather-spacing-0.2.46/preview-label.json').write_text(json.dumps(proof,indent=2)+'\n', encoding='utf-8')
print(json.dumps(proof,indent=2))

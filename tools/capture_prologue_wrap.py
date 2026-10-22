"""Watch naturally selected prologue MLT records; no game-memory edits. Dry run first."""
import argparse
import base64
import hashlib
import json
import time

from catalog_text import ROOT
from build_prologue_wrap import V, EDITS
from capture_psp_frame import capture
from ppsspp_debug import Session

GETTER = 0x0896f574
NAMES = dict(zip(EDITS, ['narration', 'after-fight', 'orin']))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--seconds', type=float, default=600)
    a = ap.parse_args()
    print(json.dumps(dict(action='Observe original MLT getter and return, verify exact selected translations, capture framebuffer',
        records=NAMES, game_memory_writes=False, save_state=False, execute=a.execute)), flush=True)
    if not a.execute:
        return
    folder = ROOT / ('work/ui/dialogue-reflow-' + V)
    targets = {new: rid for rid, (old, new) in EDITS.items()}
    found, ret = set(), None
    end = time.monotonic() + a.seconds
    with Session() as s:
        def arm():
            s.call('cpu.breakpoint.add', address=GETTER, enabled=True,
                condition='a1 == 0 && (a2 == 0 || a2 == 3 || a2 == 4)')
        arm()
        try:
            while time.monotonic() < end and len(found) < len(targets):
                status = s.call('cpu.status')
                if not status['stepping']:
                    time.sleep(.03)
                    continue
                # A separate read-only framebuffer capture briefly pauses at
                # sceDisplaySetFrameBuf. Let its owner finish and resume.
                if status['pc'] != GETTER:
                    time.sleep(.03)
                    continue
                regs = s.call('cpu.getAllRegs')['categories'][0]['uintValues']
                ret, resource, section, index = regs[31], regs[4], regs[5], regs[6]
                s.call('cpu.breakpoint.remove', address=GETTER)
                s.call('cpu.breakpoint.add', address=ret, enabled=True)
                s.call('cpu.resume')
                until = time.monotonic() + 5
                while not s.call('cpu.status')['stepping']:
                    assert time.monotonic() < until
                    time.sleep(.003)
                assert s.call('cpu.status')['pc'] == ret
                ptr = s.call('cpu.getAllRegs')['categories'][0]['uintValues'][2]
                text = ''
                if 0x08800000 <= ptr < 0x0a000000:
                    raw = base64.b64decode(s.call('memory.read', address=ptr, size=2048)['base64'])
                    n = next((i for i in range(0, len(raw), 2) if raw[i:i+2] == b'\0\0'), len(raw))
                    text = raw[:n].decode('utf-16-le', errors='replace')
                s.call('cpu.breakpoint.remove', address=ret)
                ret = None
                s.call('cpu.resume')
                if text in targets and text not in found:
                    rid = targets[text]
                    proof = dict(version=V, id=rid, translation=text,
                        translation_sha256=hashlib.sha256(text.encode()).hexdigest(),
                        naturally_selected=True, exact_final_build_text=True,
                        resource=hex(resource), section=section, index=index, text_address=hex(ptr),
                        register_or_memory_writes=False)
                    print('Selected ' + rid + ': ' + repr(text), flush=True)
                    # Scene dialogue reveals letters slowly. Narration is
                    # already complete; portrait speech needs a longer hold.
                    time.sleep(3 if rid.startswith('ore:00683000:') else 15)
                    im, meta = capture()
                    path = folder / (NAMES[rid] + '.png')
                    im.save(path)
                    path.with_suffix('.json').write_text(json.dumps(meta, indent=2) + '\n', encoding='utf-8')
                    path.with_suffix('.native.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
                    found.add(text)
                    print('Captured ' + str(path.relative_to(ROOT)), flush=True)
                arm()
            assert len(found) == len(targets), 'Not all naturally selected passages reached'
        finally:
            s.call('cpu.breakpoint.remove', address=GETTER)
            if ret is not None:
                s.call('cpu.breakpoint.remove', address=ret)
            if s.call('cpu.status')['stepping']:
                s.call('cpu.resume')
    print('PASS: all three actual translations observed and captured.', flush=True)


if __name__ == '__main__':
    main()

"""Capture the game's actual PSP display buffer through its display API call.

Use the isolated software-rendering test instance. Dry run unless --execute.
This reads guest framebuffer memory, avoiding unreliable host-window captures.
"""
import argparse
import base64
import json
import time

import numpy as np
from PIL import Image

from catalog_text import ROOT
from ppsspp_debug import Session

SET_FRAMEBUFFER = 0x08A18CF8  # sceDisplaySetFrameBuf, NID 0x289D82FE


def capture():
    with Session() as session:
        assert session.call('game.status')['game']['id'] == 'UCJS10117'
        assert not session.call('cpu.status')['stepping']
        added = False
        try:
            session.call('cpu.breakpoint.add', address=SET_FRAMEBUFFER, condition='a0 != 0')
            added = True
            deadline = time.monotonic() + 12
            while not session.call('cpu.status')['stepping']:
                if time.monotonic() > deadline:
                    raise TimeoutError('No display-buffer submission observed')
                time.sleep(0.05)
            category = session.call('cpu.getAllRegs')['categories'][0]
            regs = dict(zip(category['registerNames'], category['uintValues']))
            assert regs['pc'] == SET_FRAMEBUFFER
            address, stride, fmt = regs['a0'], regs['a1'], regs['a2']
            assert 0x04000000 <= address < 0x04200000 and 480 <= stride <= 1024 and fmt in (0,1,2,3)
            size = stride * 272 * (4 if fmt == 3 else 2)
            # Small responses avoid the debugger's large-frame websocket
            # fragmentation/close stalls while the guest buffer is frozen.
            raw = b''.join(base64.b64decode(session.call('memory.read',address=address+pos,size=min(16384,size-pos))['base64']) for pos in range(0,size,16384))
        finally:
            if added:
                session.call('cpu.breakpoint.remove',address=SET_FRAMEBUFFER)
            if session.call('cpu.status')['stepping']:
                session.call('cpu.resume')
    if fmt == 3:
        rgb = np.frombuffer(raw,dtype=np.uint8).reshape(272,stride,4)[:,:480,:3].copy()
    else:
        values = np.frombuffer(raw,dtype='<u2').reshape(272,stride)[:,:480].astype(np.uint32)
        if fmt == 0:
            rgb = np.stack([(values&31)*255//31,(values>>5&63)*255//63,(values>>11&31)*255//31],axis=2)
        elif fmt == 1:
            rgb = np.stack([(values&31)*255//31,(values>>5&31)*255//31,(values>>10&31)*255//31],axis=2)
        else:
            rgb = np.stack([(values&15)*17,(values>>4&15)*17,(values>>8&15)*17],axis=2)
        rgb = rgb.astype(np.uint8)
    return Image.fromarray(rgb,'RGB'), dict(game='UCJS10117',framebuffer=hex(address),stride=stride,format=fmt,
                                          dimensions=[480,272],capture='Actual guest display buffer at sceDisplaySetFrameBuf; software backend.',
                                          texture_replacement=False)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true')
    ap.add_argument('--output',default='work/source/psp-display-frame.png')
    args = ap.parse_args()
    if not args.execute:
        print(json.dumps(dict(mode='dry run',actions=['Temporarily break at the guest display submission','Read and decode its actual framebuffer','Remove breakpoint and resume'],output=args.output),indent=2))
        return
    image, report = capture()
    path = ROOT / args.output
    path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path)
    path.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()

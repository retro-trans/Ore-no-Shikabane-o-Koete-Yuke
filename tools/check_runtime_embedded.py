"""Check that both relocated message tables load in the isolated test game.

Dry run by default. --execute resets only the project debugger's game instance.
"""
import argparse
import base64
import json
import struct
import time

from build_embedded_text import ROOT, build
from ppsspp_debug import Session

BREAK = 0x0896F430


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true')
    ap.add_argument('--write',action='store_true')
    ap.add_argument('--version',default='0.2.4')
    args = ap.parse_args()
    native,_,_,expected = build()
    phoff=struct.unpack_from('<I',native,28)[0]
    segment_offset,segment_address=struct.unpack_from('<II',native,phoff+32+4)
    targets = {int(p['relocated_address'],16):p for p in expected['patches']}
    if not args.execute:
        print(json.dumps(dict(mode='dry run',actions=['Reset the isolated UCJS10117 test','Break after either relocated MLT table is accepted','Verify the loader object points to the complete rebuilt table','Remove breakpoint and resume']),indent=2))
        return
    with Session() as session:
        assert session.call('game.status')['game']['id']=='UCJS10117'
        assert not session.call('cpu.status')['stepping']
        captures = {}
        added = False
        try:
            condition = ' || '.join('a1 == '+hex(a) for a in targets)
            session.call('cpu.breakpoint.add',address=BREAK,condition=condition)
            added = True
            session.call('game.reset')
            deadline = time.monotonic()+25
            while set(captures)!=set(targets):
                if time.monotonic()>deadline:
                    raise TimeoutError('Did not observe both relocated table constructors: '+str(list(captures)))
                if not session.call('cpu.status')['stepping']:
                    time.sleep(.05)
                    continue
                category = session.call('cpu.getAllRegs')['categories'][0]
                regs = dict(zip(category['registerNames'],category['uintValues']))
                assert regs['pc']==BREAK and regs['a1'] in targets
                pointer = struct.unpack('<I',base64.b64decode(session.call('memory.read',address=regs['a0'],size=4)['base64']))[0]
                assert pointer==regs['a1']
                magic = base64.b64decode(session.call('memory.read',address=pointer,size=4)['base64'])
                assert magic[:3]==b'MLT'
                size=targets[pointer]['rebuilt_bytes']
                live=base64.b64decode(session.call('memory.read',address=pointer,size=size)['base64'])
                file_offset=segment_offset+pointer-segment_address
                assert live==native[file_offset:file_offset+size]
                captures[pointer]=dict(table=hex(pointer),loader_object=hex(regs['a0']),records=targets[pointer]['records'],accepted=True)
                session.call('cpu.resume')
        finally:
            if added:
                session.call('cpu.breakpoint.remove',address=BREAK)
            if session.call('cpu.status')['stepping']:
                session.call('cpu.resume')
    report=dict(version=args.version,status='PASS',runtime_tables_loaded=list(captures.values()),
                limitation='Loader acceptance is verified. Save-dialog and error-message display/layout scenarios remain separate tests.')
    print(json.dumps(report,indent=2))
    if args.write:
        (ROOT/('work/ui/embedded-runtime-'+args.version+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()

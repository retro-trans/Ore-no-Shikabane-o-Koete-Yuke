"""Read wide text calls while advancing one prologue dialogue. Dry run first."""
import argparse,base64,json,struct,time
from catalog_text import ROOT
from ppsspp_debug import Session
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
if not a.execute:print('DRY RUN: one PSP Circle tap, read-only text-call trace with temporary breakpoint, no memory edits.');raise SystemExit
calls=[];pc=0x0882b544;last=time.monotonic()
with Session() as s:
    assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
    s.call('cpu.breakpoint.add',address=pc)
    try:
        s.call('input.buttons.press',button='circle',duration=6)
        end=time.monotonic()+18
        while time.monotonic()<end and len(calls)<180:
            state=s.call('cpu.status')
            if not state['stepping']:time.sleep(.01);continue
            if state['pc']!=pc:
                calls.append(dict(other_breakpoint=state));break
            r=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];ptr=r[5]
            text=''
            if 0x08800000<=ptr<0x0a000000:
                b=base64.b64decode(s.call('memory.read',address=ptr,size=200)['base64'])
                for i in range(0,len(b),2):
                    c=struct.unpack_from('<H',b,i)[0]
                    if not c:break
                    text+=chr(c)
            calls.append(dict(caller=hex(r[31]),object=hex(r[4]),source=hex(ptr),text=text))
            s.call('cpu.resume')
    finally:
        s.call('cpu.breakpoint.remove',address=pc)
        state=s.call('cpu.status')
        if state['stepping'] and state['pc']==pc:s.call('cpu.resume')
proof=dict(calls=calls,memory_writes=False)
if a.write:(ROOT/'work/ui/battle-hud-0.2.25/text-trace.json').write_text(json.dumps(proof,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2,ensure_ascii=True))

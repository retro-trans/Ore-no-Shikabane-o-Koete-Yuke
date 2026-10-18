"""Advance natural dialogue, stopping before a selected message. Dry run unless --execute."""
import argparse,json,time
from ppsspp_debug import Session
from catalog_text import ROOT
from capture_psp_frame import capture
GETTER=0x0896f574
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--section',type=int,required=True);ap.add_argument('--index',type=int,required=True);ap.add_argument('--taps',type=int,default=20);ap.add_argument('--capture');ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    assert 1<=a.taps<=40
    condition='a1 == %d && a2 == %d'%(a.section,a.index);print(json.dumps(dict(condition=condition,max_taps=a.taps,button='circle',mutation='Input only; no registers, text, names, or save-memory writes',execute=a.execute)))
    if not a.execute:return
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117'
        bps=s.call('cpu.breakpoint.list')['breakpoints'];event='cpu.breakpoint.update' if any(p['address']==GETTER for p in bps) else 'cpu.breakpoint.add'
        s.call(event,address=GETTER,condition=condition,enabled=True)
        try:
            for i in range(a.taps):
                if s.call('cpu.status')['stepping']:break
                s.call('input.buttons.send',buttons={'circle':True});time.sleep(.12)
                s.call('input.buttons.send',buttons={'circle':False});time.sleep(.7)
        finally:s.call('input.buttons.send',buttons={'circle':False})
        status=s.call('cpu.status');print(json.dumps(status))
    if a.capture and not status['stepping']:
        im,meta=capture();p=ROOT/a.capture;p.parent.mkdir(parents=True,exist_ok=True);im.save(p);p.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

"""Send a bounded button sequence to the isolated test emulator; dry run by default."""
import argparse
import json
import time
from ppsspp_debug import Session
from capture_psp_frame import capture
from catalog_text import ROOT

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('steps',help='Comma-separated buttons, button*count, or wait:seconds')
    ap.add_argument('--execute',action='store_true');ap.add_argument('--capture')
    ap.add_argument('--delay',type=float,default=.45);args=ap.parse_args()
    print(json.dumps(vars(args)))
    if not args.execute:return
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117'
        assert not s.call('cpu.status')['stepping']
        for token in args.steps.split(','):
            if token.startswith('wait:'):
                time.sleep(min(30,float(token.split(':')[1])));continue
            parts=token.split('*');button=parts[0];n=int(parts[1]) if len(parts)>1 else 1
            assert 1<=n<=30
            for _ in range(n):
                # Count guest frames, so fast emulation cannot turn one tap
                # into a held button and unintentionally traverse dialogs.
                s.call('input.buttons.press',button=button,duration=6)
                time.sleep(args.delay)
    if args.capture:
        im,meta=capture();p=ROOT/args.capture;p.parent.mkdir(parents=True,exist_ok=True)
        im.save(p);p.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')

if __name__=='__main__':main()

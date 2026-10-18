"""Trace native menu constructors in the isolated emulator. Dry run by default."""
import argparse,base64,json,struct,time
from ppsspp_debug import Session

POINTS={0x088221e0:'descriptor',0x088222d4:'cell_width'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('steps');ap.add_argument('--execute',action='store_true')
    ap.add_argument('--output');ap.add_argument('--stop-first',action='store_true');args=ap.parse_args()
    print(json.dumps(vars(args)))
    if not args.execute:return
    rows=[]
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117'
        assert not s.call('cpu.status')['stepping']
        for pc in POINTS:s.call('cpu.breakpoint.add',address=pc,enabled=True)
        def drain(seconds):
            end=time.monotonic()+seconds
            while time.monotonic()<end:
                if args.stop_first and rows:return
                if s.call('cpu.status')['stepping']:
                    r=s.call('cpu.getAllRegs')['categories'][0]['uintValues']
                    pc=r[32];row=dict(kind=POINTS.get(pc,hex(pc)),object=hex(r[4]),argument=hex(r[5]),caller=hex(r[31]))
                    if pc==0x088221e0:
                        b=base64.b64decode(s.call('memory.read',address=r[5],size=22)['base64'])
                        row['descriptor']=list(struct.unpack('<11h',b))
                    rows.append(row);print(json.dumps(row),flush=True)
                    assert pc in POINTS
                    s.call('cpu.resume')
                time.sleep(.01)
        try:
            for key in args.steps.split(','):
                if args.stop_first and rows:break
                s.call('input.buttons.send',buttons={key:True});drain(.12)
                s.call('input.buttons.send',buttons={key:False});drain(3)
        finally:
            for key in args.steps.split(','):s.call('input.buttons.send',buttons={key:False})
            for pc in POINTS:s.call('cpu.breakpoint.remove',address=pc)
            if s.call('cpu.status')['stepping']:s.call('cpu.resume')
    if args.output:
        from pathlib import Path
        p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()

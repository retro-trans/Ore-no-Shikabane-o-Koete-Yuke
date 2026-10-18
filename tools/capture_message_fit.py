"""Capture a naturally reached message at its MLT breakpoint. Dry run unless --execute."""
import argparse,base64,hashlib,json,time
from catalog_text import ROOT
from build_dialogue_reflow import EDITS,VERSION
from ppsspp_debug import Session
from capture_psp_frame import capture
GETTER=0x0896f574
NAMES=['curse','equipment','information']
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('row',type=int,choices=range(3));ap.add_argument('--execute',action='store_true');ap.add_argument('--wait',type=float,default=30);a=ap.parse_args()
    _,rid,old,expected,_,_=EDITS[a.row];section,index=[int(x,16) for x in rid.split(':')[-2:]]
    print(json.dumps(dict(record=rid,expected=expected,actions=['Check paused natural MLT call','Run only to its original return address','Verify returned text against final build','Resume without register or memory writes','Capture actual guest framebuffer'],wait_seconds=a.wait),indent=2))
    if not a.execute:return
    with Session() as s:
        st=s.call('cpu.status');assert st['stepping'] and st['pc']==GETTER
        regs=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];assert regs[5:7]==[section,index]
        ra=regs[31];resource=regs[4]
        s.call('cpu.breakpoint.remove',address=GETTER);s.call('cpu.breakpoint.add',address=ra,enabled=True)
        try:
            s.call('cpu.resume')
            for _ in range(100):
                st=s.call('cpu.status')
                if st['stepping']:break
                time.sleep(.03)
            assert st['stepping'] and st['pc']==ra
            regs=s.call('cpu.getAllRegs')['categories'][0]['uintValues'];ptr=regs[2]
            raw=base64.b64decode(s.call('memory.read',address=ptr,size=2048)['base64']);end=next(i for i in range(0,len(raw),2) if raw[i:i+2]==b'\0\0');text=raw[:end].decode('utf-16-le')
            assert text==expected,'Returned a different MLT record; expected text was not substituted'
            proof=dict(version=VERSION,id=rid,section=section,index=index,natural_message_selection=True,register_or_memory_writes=False,resource=hex(resource),original_caller_return=hex(ra),text_address=hex(ptr),translation_sha256=hashlib.sha256(text.encode()).hexdigest(),exact_final_build_text=True)
        finally:
            s.call('cpu.breakpoint.remove',address=ra)
            if s.call('cpu.status')['stepping']:s.call('cpu.resume')
    time.sleep(min(30,max(0,a.wait)))
    im,meta=capture();ui=ROOT/('work/ui/dialogue-reflow-'+VERSION);path=ui/(NAMES[a.row]+'.png');im.save(path)
    path.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8');(ui/(NAMES[a.row]+'.native.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof,indent=2));print('Captured',str(path.relative_to(ROOT)))
if __name__=='__main__':main()

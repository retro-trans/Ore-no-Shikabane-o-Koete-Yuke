"""Preview public-works level 1 in the isolated QA instance; no save/code writes."""
import argparse,json,time,subprocess,sys
from catalog_text import ROOT
from ppsspp_debug import Session

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--execute',action='store_true');ap.add_argument('--seconds',type=int,default=45)
ap.add_argument('--steps',help='Optional normal controller input while the override is armed')
args=ap.parse_args()
assert 1<=args.seconds<=60
if not args.execute:
    print('DRY RUN: override only the public-works level getter return to 1 for bounded QA. No code, PC, text, price, money, investment-data or save-state edits.')
    raise SystemExit
pc=0x088d4b38;calls=[]
with Session() as s:
    assert s.call('game.status')['game']['id']=='UCJS10117'
    assert not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
    s.call('cpu.breakpoint.add',address=pc,condition='a1 == 3')
    inputs=None
    if args.steps:
        inputs=subprocess.Popen([sys.executable,str(ROOT/'tools/qa_buttons.py'),args.steps,'--delay','1','--execute'],
            cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        end=time.monotonic()+args.seconds
        while time.monotonic()<end:
            status=s.call('cpu.status')
            if status['stepping'] and status['pc']==pc:
                regs=s.call('cpu.getAllRegs')['categories'][0]['uintValues']
                assert regs[5]==3 and 0<=regs[3]<=15
                s.call('cpu.setReg',name='v1',value=1)
                calls.append(dict(original_level=regs[3],preview_level=1,caller=hex(regs[31])))
                s.call('cpu.resume')
            time.sleep(.02)
    finally:
        s.call('cpu.breakpoint.remove',address=pc)
        if s.call('cpu.status')['stepping']:s.call('cpu.resume')
    if inputs is not None:assert inputs.wait(timeout=5)==0
proof=dict(version='0.2.49',diagnostic_only=True,purpose='Expose locked commodity UI for visual QA',
    result='OVERRIDE APPLIED' if calls else 'NOT REACHED',calls=calls,
    actual_native_ui=True,gameplay_unlock_verified=False,code_or_pc_writes=False,
    game_memory_writes=False,register_override=True,save_state_loaded=False,
    money_price_investment_values_changed=False,delivered_image_modified=False)
(ROOT/'work/ui/market-ui-0.2.49/preview-unlock.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))

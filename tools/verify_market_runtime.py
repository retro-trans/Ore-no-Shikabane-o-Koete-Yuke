"""Verify final-build broker text, native fonts, pointers and literal bytes."""
import argparse,base64,json,struct
from catalog_text import ROOT
from build_market_ui import V,BASE
from build_vwf import IMAGE
from ppsspp_debug import Session


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');args=ap.parse_args()
    if not args.execute:
        print('DRY RUN: compare recorded final-build native text/fonts and live instructions/literals. No guest memory/register edits.')
        return
    ui=ROOT/('work/ui/market-ui-'+V);out=ROOT/('work/output/english-native-'+V)
    r=json.loads((out/'market.report.json').read_text())
    trees={n:json.loads((ui/(n+'-tree.json')).read_text()) for n in ['market','quantity-one','quantity-two','confirmation','retry','graph']}
    checks={'market':['Money','1052 ryo',r['literals'][5]['translation_en']],
        'quantity-one':['"Rice," then!','How many contracts?',' contracts','100 ryo'],
        'quantity-two':['"Rice," then!','How many contracts?',' contracts','200 ryo'],
        'confirmation':['"Rice": 2 contracts.','220 ryo, including fees.','Is that correct?','Yes','No'],
        'retry':['"Rice," then!','How many contracts?',' contracts','200 ryo'],
        'graph':['Month','(ryo)']}
    for context,texts in checks.items():
        for text in texts:
            row=next((row for row in trees[context] if row['text']==text),None)
            assert row is not None,(context,text,[z['text'] for z in trees[context]])
            assert row['font_image']==hex(IMAGE),(context,text,row['font_image'])
    live=[]
    with Session() as s:
        assert s.call('game.status')['game']['id']=='UCJS10117'
        assert not s.call('cpu.status')['stepping'] and not s.call('cpu.breakpoint.list')['breakpoints']
        def read(address,size):return base64.b64decode(s.call('memory.read',address=address,size=size)['base64'])
        s.call('cpu.stepping')
        try:
            for p in r['patches']:
                address=int(p['address'],16)
                if address==0x08b2b770:actual=struct.unpack('<I',read(address,4))[0]
                else:
                    line=s.call('memory.disasm',address=address,count=1,displaySymbols=False)['lines'][0]
                    # PPSSPP groups adjacent LUI/ADDIU as one eight-byte LI.
                    # Querying its second instruction returns that same macro.
                    if line.get('macroEncoding'):
                        actual=line['macroEncoding'][(address-line['address'])//4]
                    else:actual=line['encoding']
                assert actual==int(p['after'],16),p
                live.append(dict(address=hex(address),word=hex(actual)))
            for literal in r['literals']:
                raw=read(int(literal['address'],16),literal['bytes'])
                assert raw==literal['translation_en'].encode('ascii')+b'\0'
            assert read(int(r['unit_wrapper']['literal'],16),22)==' contracts\0'.encode('utf-16-le')
        finally:s.call('cpu.resume')
    proof=dict(version=V,result='PASS',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],
        live_patches=live,contexts=checks,font='Native embedded HD ASCII pages',
        quantity_and_fee_examples=[dict(contracts=1,base_price=100),dict(contracts=2,base_price=200,total_with_fees=220)],
        retry_after_decline=True,guest_memory_writes=False,register_edits_by_this_verifier=False,
        qa_unlock_override='Separately recorded in preview-market-entry.json and preview-graph-entry.json',
        texture_replacement=False,save_state_loaded=False,purchase_confirmed=False)
    print(json.dumps(proof,indent=2))
    if args.write:(ui/'runtime.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()

"""Translate native commodity-broker prompts and ribbon. Dry run before --write."""
import argparse,hashlib,json,re,struct
import keystone
from PIL import Image
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from build_hd_ui import ribbon_image
from hd_sprites import encode
from repack_text import align,root_entries,rebuild_ez,rebuild_root
from strip_jp import export

V='0.2.49'
BASE=0x08803000
sha=lambda b:hashlib.sha256(b).hexdigest()


def build():
    src=ROOT/'work/output/english-native-0.2.48'
    source=(src/'EBOOT.tournament.elf').read_bytes()
    data=(src/'data.tournament.ore').read_bytes()
    assert sha(source)=='ad5480bc8eb2d2185ef2e239bd3a681764b4c3e79ccfa8ae1dff360e11bbb88a'
    assert sha(data)=='6648dd31cb0c5fd7444ac2e1041994769be1f368cce27b412188b8ac43467202'
    elf=bytearray(source)
    po=struct.unpack_from('<I',elf,28)[0]
    ph=list(struct.unpack_from('<8I',elf,po+32))
    assert ph[1]+ph[4]==len(elf)
    patches=[];literals=[];allowed=set(range(po+48,po+56))
    def append(blob):
        elf.extend(bytes(align(len(elf),4)-len(elf)))
        address=ph[2]+len(elf)-ph[1];elf.extend(blob)
        return address
    def word(pc,old,new,purpose):
        off=pc-BASE
        assert struct.unpack_from('<I',elf,off)[0]==old,(hex(pc),hex(old))
        struct.pack_into('<I',elf,off,new);allowed.update(range(off,off+4))
        patches.append(dict(address=hex(pc),before=hex(old),after=hex(new),purpose=purpose))
    def relocate(address,text,highs,low):
        off=address-BASE;old=source[off:source.index(b'\0',off)]
        english=text.encode('ascii')+b'\0';target=append(english)
        # Narrow UI strings are converted by the original EUC-JP -> UTF-16 routine.
        for pc in highs:
            w=struct.unpack_from('<I',source,pc-BASE)[0]
            assert w>>26==15 and (w&65535)==((address+0x8000)>>16)
            word(pc,w,(w&0xffff0000)|((target+0x8000)>>16),'Market literal pointer high')
        w=struct.unpack_from('<I',source,low-BASE)[0]
        assert w>>26==9 and (w&65535)==(address&65535)
        word(low,w,(w&0xffff0000)|(target&65535),'Market literal pointer low')
        literals.append(dict(id='elf:market:'+hex(address),file='EBOOT market UI',
            original_address=hex(address),address=hex(target),source_sha256=sha(old),
            translation_en=text,bytes=len(english),source_encoding='euc_jp',
            format_arguments=re.findall(r'%[sd]',text)))
    relocate(0x08a43488,'"%s," then!\nHow many contracts?',
        [0x0893eb08,0x0893eb84],0x0893eb10)
    relocate(0x08a434b0,'"%s": %d contracts.\n%d ryo, including fees.\nIs that correct?',
        [0x0893ec34],0x0893ec38)
    relocate(0x08a432a0,'Month',[0x0893d4e8],0x0893d4f0)
    relocate(0x08a432a8,'(ryo)',[0x0893d538],0x0893d540)
    relocate(0x08a437f0,'Money',[0x089401d8],0x089401e8)
    heading='                Now    High   Low'
    header=append(heading.encode('ascii')+b'\0')
    word(0x08b2b770,0x08a43428,header,'Translated market column heading; padding aligns native proportional columns')
    old_header=source[0x08a43428-BASE:source.index(b'\0',0x08a43428-BASE)]
    literals.append(dict(id='elf:market:0x8a43428',file='EBOOT market UI',original_address='0x8a43428',
        address=hex(header),source_sha256=sha(old_header),translation_en=heading,bytes=len(heading)+1,
        source_encoding='euc_jp',format_arguments=[]))
    contracts=append(' contracts\0'.encode('utf-16-le'))
    # The quantity picker is shared with ordinary shops. Override its visible
    # unit only when its saved caller is the commodity-purchase routine.
    asm='''.set noreorder
    lw $t0,28($sp)
    li $t1,0x0893eb60
    bne $t0,$t1,original
    nop
    li $a1,CONTRACTS
    original:
    j 0x0882b49c
    nop
    '''.replace('CONTRACTS',hex(contracts))
    wrapper=append(b'')
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    code=bytes(ks.asm(asm,addr=wrapper)[0]);elf.extend(code)
    word(0x0894e728,0x0c000000|(0x0882b49c>>2),0x0c000000|(wrapper>>2),'Market contracts unit; other quantity pickers retain items')
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,po+32,*ph)
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);be,bend=root_entries(data)
    rootmap={o:next(r[3] for r in be if r[0]==i) for i,_,_,o in oe}
    rb=rootmap[0xb4a800];arc,en=container(data,rb);oa,oen=container(original,0xb4a800)
    old=member(arc,en,52);assert old==member(oa,oen,52)
    inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text())
    assert any(r['archive_offset']==0xb4a800 and r['entry']==52 and r['name']=='259.ppt' for r in inv)
    image,typography=ribbon_image(old,'COMMODITY BROKER')
    image=image.resize((96,264),Image.Resampling.LANCZOS)
    ppt,actual,hd=encode(old,image,pixel_format=4)
    assert len(ppt)==len(old)==13744
    graphics=[dict(archive_offset=0xb4a800,member_entry=52,file='259.ppt',
        translation_en='COMMODITY BROKER',resource_bytes=len(ppt),original_bytes=len(old),**typography,**hd)]
    tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000)
    title,preview,fr=footer(member(ot,ote,25),V)
    updates={rb:rebuild_ez(arc,{52:pack(ppt)}),tb:rebuild_ez(ta,{25:pack(title)})}
    changed={rb:{52},tb:{25}}
    ore=rebuild_root(data,updates,mutable=True);ae,aend=root_entries(ore)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047)
        sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047)
        aa,bb=data[a[3]:sa],ore[b[3]:sb]
        if a[3] not in updates:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in changed[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    measure=lambda s:sum(metrics[str(ord(c))]['advance'] for c in s)
    fit=dict(prompt_question=dict(text=literals[0]['translation_en'].split('\n')[1],advance=measure(literals[0]['translation_en'].split('\n')[1]),
        full_draft_advance=measure('How many contracts would you like?'),reason='Concise question keeps the complete meaning inside the existing two-line quantity prompt'))
    report=dict(version=V,source_version='0.2.48',elf_sha256=sha(elf),archive_sha256=sha(ore),
        elf_bytes=len(elf),archive_bytes=len(ore),added_resident_bytes=len(elf)-len(source),
        patches=patches,literals=literals,graphics=graphics,fit=fit,
        unit_wrapper=dict(address=hex(wrapper),bytes=len(code),literal=hex(contracts),
            caller='0x0893eb60',setter='0x0882b49c',original_stack_return_offset=28),
        checks=dict(quantity_price_fees='Native values, input bounds and arithmetic unchanged',
            argument_order='Original commodity/quantity/price argument order retained',
            retry_path='Both initial and retry prompt pointer highs relocated',
            other_quantity_pickers='Original unit retained by saved-caller guard',
            prior_fixes='All other executable bytes and archive members unchanged except segment size and title',
            money_header='Native Money caption explicitly relocated; existing spaced ryo currency retained',
            resource_loader='Ribbon retains original 13744-byte loader budget'),
        footer=fr,texture_replacement=False,runtime_verification='pending',github_release=False)
    return elf,ore,actual,preview,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    elf,ore,actual,preview,report=build()
    print(json.dumps({k:v for k,v in report.items() if k!='footer'},indent=2))
    if args.write:
        out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True)
        assert not (out/'EBOOT.market.elf').exists()
        (out/'EBOOT.market.elf').write_bytes(elf);(out/'data.market.ore').write_bytes(ore)
        (out/'market.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/market-ui-'+V);ui.mkdir(exist_ok=True)
        actual.save(ui/'market-ribbon.png');preview.save(ui/'native-footer.png')
        source=(ROOT/'work/output/english-native-0.2.48/EBOOT.tournament.elf').read_bytes();rows=[]
        for r in report['literals']:
            off=int(r['original_address'],16)-BASE
            jp=source[off:source.index(b'\0',off)].decode('euc_jp')
            rows.append(dict(id=r['id'],file=r['file'],source_jp=jp,source_sha256=sha(jp.encode()),translation_en=r['translation_en'],
                status='draft',kind='ui',category='native_market_literal',fit_status='pending_runtime_'+V,
                context='Commodity trading; native runtime placeholders retained. Original Japanese source stays local.'))
        path=ROOT/'work/translation/en/executable/market_prompts.json'
        path.write_text(json.dumps(dict(schema_version=1,version=V,language='en',status='draft',rows=rows),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        path.with_suffix('.en.json').write_text(json.dumps(export(path),indent=2)+'\n',encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()

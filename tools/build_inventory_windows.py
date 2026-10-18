"""Widen native inventory/shop windows for 0.2.18. Dry run unless --write."""
import argparse,hashlib,json,re,struct
import keystone
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root,align

VERSION='0.2.18';BASE=0x08803000
# Guard each original word. Source is the delivered 0.2.17 executable.
PATCHES=[
 (0x088db038,0x24050070,232,'Equipment item cell width'),
 (0x088db02c,0x24050080,232,'Other item cell width'),
 (0x088db338,0x24050008,2,'Shared list column gap'),
 (0x088db344,0x24050005,4,'Shared list visible rows'),
 (0x088db348,0x24060003,2,'Shared list columns'),
 (0x088db390,0x24060040,84,'Shared list top'),
 (0x088db45c,0x24050080,232,'Inherited weapon list cell width'),
 (0x088db470,0x2405000a,2,'Inherited weapon list column gap'),
 (0x088db47c,0x24050005,4,'Inherited weapon list visible rows'),
 (0x088db480,0x24060003,2,'Inherited weapon list columns'),
 (0x088db4c8,0x24060040,84,'Inherited weapon list top'),
 (0x088dbb34,0x24050040,132,'Pack/storehouse action cells'),
 (0x088dbd58,0x24060011,28,'Action menu top'),
 (0x088db548,0x24050040,132,'Three-way inventory category cells'),
 (0x088db638,0x24060011,28,'Three-way category top'),
 (0x088db6ac,0x24050040,200,'Equipment category cells'),
 (0x088db6d8,0x24060004,2,'Equipment category columns; native scrolling retains eight choices'),
 (0x088db878,0x24060008,28,'Equipment category top'),
 (0x088db8ec,0x24050040,200,'Item category cells'),
 (0x088db918,0x24060004,2,'Item category columns; native scrolling retains eight choices'),
 (0x088dbab8,0x24060008,28,'Item category top'),
 (0x08930a10,0x24060014,-4,'Heading ornament top'),
 (0x08930a14,0x24050017,85,'Heading ornament left'),
 (0x08930a60,0x24060018,0,'Breadcrumb top'),
 (0x08930a64,0x24050030,110,'Breadcrumb center; keep long category headings on screen'),
 (0x08930c58,0x2405016f,400,'Capacity frame left'),
 (0x08930c68,0x24060027,0,'Capacity frame top'),
 (0x08930ce0,0x240501a3,452,'Capacity digits right anchor'),
 (0x08930cf0,0x2406002b,4,'Capacity digits top'),
 (0x08930d9c,0x24050041,4,'Item detail window left'),
 (0x08930dac,0x240600ae,178,'Item detail window top'),
 (0x08930510,0x2405015e,472,'Shared item detail frame width'),
 (0x08930564,0x2405014e,456,'Shared item detail text region width'),
 (0x089304d8,0x24050041,4,'Default item detail left'),
]

def sha(b):return hashlib.sha256(b).hexdigest()

def build():
    src=ROOT/'work/output/english-native-0.2.17'
    source=(src/'EBOOT.reflow.elf').read_bytes();data=(src/'data.reflow.ore').read_bytes()
    assert sha(source)=='498dcae55831b40a4f3126d35c3b54ca926b3a3e65183bbefeef5c06beb46a3c'
    assert sha(data)=='3428746e95c867deda03b067ef5d0baf2edf738251d72fd60394a614b935eefa'
    elf=bytearray(source);changes=[];allowed=set()
    def patch(pc,old,new,note,size=4):
        fmt='<I' if size==4 else '<h';off=pc-BASE
        assert struct.unpack_from(fmt,elf,off)[0]==old,(hex(pc),hex(struct.unpack_from(fmt,elf,off)[0]),hex(old))
        struct.pack_into(fmt,elf,off,new);allowed.update(range(off,off+size))
        changes.append(dict(address=hex(pc),before=old,after=new,purpose=note))
    for pc,old,imm,note in PATCHES:patch(pc,old,(old&0xffff0000)|(imm&0xffff),note)
    for table,old,new,note in [
      (0x08a45efc,64,100,'Shop selector text width'),
      (0x08a45f14,48,100,'Sell inventory source menu width'),
      (0x08a45f2c,32,84,'Weapon shop category width; each column reserves 24px for icons'),
      (0x08a45f44,48,92,'Armor submenu text width')]:patch(table+8,old,new,note,2)
    # Dedicated inventory geometry calls use small edge margins so both
    # 232px cells fit on the native 480px display. Native source counts and
    # cursor paging are retained; this does not alter other menu classes.
    phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32))
    assert ph[1]+ph[4]==len(elf)
    elf.extend(bytes(align(len(elf),16)-len(elf)));cave=ph[2]+len(elf)-ph[1]
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    code=bytes(ks.asm('''.set noreorder
        addiu $t0, $zero, 3
        sw $t0, 0x2578($a0)
        sw $t0, 0x257c($a0)
        j 0x08821f50
        nop
    ''',addr=cave)[0]);elf.extend(code)
    for pc in (0x088db354,0x088db48c):patch(pc,0x0c000000|(0x08821f50//4),0x0c000000|(cave//4),'Inventory-only edge margins before native geometry')
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph)
    allowed.update(range(phoff+48,phoff+56))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    def width(t):return sum(metrics.get(str(ord(c)),{'advance':14})['advance'] for c in re.sub(r'\[[^\]\r\n]*\]','',t))*12/14
    allrows={r['id']:r for p in (ROOT/'work/translation/en').glob('*.en.json') for r in json.loads(p.read_text(encoding='utf-8')).get('rows',[])}
    names=[r for r in allrows.values() if r.get('archive_offset')==0x28000 and r.get('member_entry')==0]
    helpkinds={'item_help','accessory_help','treasure_help','field_item_effect'}
    descriptions=[r for r in allrows.values() if r.get('archive_offset')==0x28000 and r.get('kind') in helpkinds]
    name_widths=sorted([(width(r['translation_en']),r['id'],r['translation_en']) for r in names],reverse=True)
    help_widths=sorted([(max(width(line) for line in r['translation_en'].split('\n')),r['id'],r['translation_en']) for r in descriptions],reverse=True)
    expanded_help_widths=[max(width(re.sub(r'%[1-9]:d','-2147483648',line)) for line in r['translation_en'].split('\n')) for r in descriptions]
    assert len(names)==631 and name_widths[0][0]<=220,name_widths[:5]
    assert len(descriptions)==232 and help_widths[0][0]<=456,help_widths[:5]
    assert max(expanded_help_widths)<=456,'Description numeric substitutions exceed the text region'
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);be,bend=root_entries(data)
    ti=next(i for i,_,_,o in oe if o==0x1e8000);tb=next(o for i,_,_,o in be if i==ti)
    ta,te=container(data,tb);ot,ote=container(original,0x1e8000)
    ppt,preview,footer_report=footer(member(ot,ote,25),VERSION)
    output=rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(ppt)})});ae,aend=root_entries(output)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047)
        aa=data[a[3]:sa];bb=output[b[3]:sb]
        if a[3]!=tb:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j!=25:assert aa[p:p+z]==bb[pp:pp+zz]
    layout=dict(version=VERSION,font_logical_size=12,texture_replacement=False,
       inventory=dict(frame=[4,84,476,174],columns=2,visible_rows=4,cell_width=232,column_gap=2,edge_margins=3,item_icon_reserve=12,name_advance_budget=220),
       descriptions=dict(frame=[4,178,476,242],advance_budget=456,records_audited=len(descriptions),longest_advance=round(help_widths[0][0],3),signed_32bit_substitution_max_advance=round(max(expanded_help_widths),3),text_changes=0),
       categories=dict(columns=2,visible_rows=2,cell_width=200,top=28,source_choices=8,paging='Native menu cursor paging'),
       names=dict(records_audited=len(names),longest_advance=round(name_widths[0][0],3),longest_examples=[dict(advance=round(w,3),id=k,text=t) for w,k,t in name_widths[:5]],dynamic_names='Not included in fixed-name audit'),
       capacity=dict(frame_origin=[400,0],digits_anchor=[452,4]),
       shops=dict(selector_text_width=100,armor_text_width=92,weapon_category_text_width=84,weapon_icon_reserve_per_column=24,submenu_position='Original code derives x from the enlarged parent width'),
       wrapper=dict(address=hex(cave),bytes=len(code),tail_target='0x08821f50',fields=['0x2578','0x257c']),runtime_verification='pending')
    report=dict(version=VERSION,source_version='0.2.17',texture_replacement=False,font_raster_scale=4,patches=changes,extra_code_bytes=len(code),wrapper=layout['wrapper'],script_text_changes=0,
       checks=dict(executable_diff='Guarded dimensions and inventory-only margin wrapper; no font changes',all_script_payloads='byte-identical',other_root_payloads='byte-identical',other_title_members='byte-identical',all_631_fixed_item_names='Measured within 220px',all_232_item_descriptions='Measured within 456px'),
       elf_sha256=sha(elf),archive_sha256=sha(output),elf_bytes=len(elf),archive_bytes=len(output),runtime_verification='pending',footer=footer_report)
    return bytes(elf),output,preview,report,layout

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    elf,ore,preview,report,layout=build();print(json.dumps(report,indent=2,ensure_ascii=True));print(json.dumps(layout,indent=2,ensure_ascii=True))
    if a.write:
        out=ROOT/('work/output/english-native-'+VERSION);out.mkdir(parents=True,exist_ok=True)
        assert not (out/'EBOOT.inventory.elf').exists() and not (out/'data.inventory.ore').exists()
        (out/'EBOOT.inventory.elf').write_bytes(elf);(out/'data.inventory.ore').write_bytes(ore)
        (out/'inventory.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/menu-fit-'+VERSION);ui.mkdir(parents=True,exist_ok=True)
        (ui/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8');preview.save(ui/'native-footer.png')
    print('Build written.' if a.write else 'DRY RUN: no files written.')

if __name__=='__main__':main()

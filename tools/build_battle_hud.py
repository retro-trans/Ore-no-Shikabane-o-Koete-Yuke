"""Translate compact battle stat badges and fixed parent display names. Dry run first."""
import argparse,hashlib,json,struct
import keystone
from catalog_text import ROOT
from build_equipment_deities import badge
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root,align
VERSION='0.2.25';BASE=0x08803000;HOOK=0x0882B544
def sha(b):return hashlib.sha256(b).hexdigest()

def patch_names(source):
    elf=bytearray(source);p=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,p+32));assert ph[1]+ph[4]==len(elf)
    def append(b):
        elf.extend(bytes(align(len(elf),4)-len(elf)));a=ph[2]+len(elf)-ph[1];elf.extend(b);return a
    names={s:append((s+'\0').encode('utf-16-le')) for s in ('Genta','Orin')}
    cave=ph[2]+align(len(elf),4)-ph[1]
    # Only exact, terminated display names match. Never modify name records,
    # source strings, formatter arguments, or other names/prefixed sentences.
    code=f'''.set noreorder
        beqz $a1, original
        nop
        lhu $v0, 0($a1)
        ori $v1, $zero, 0x6e90
        beq $v0, $v1, genta
        nop
        ori $v1, $zero, 0x304a
        bne $v0, $v1, original
        nop
        lhu $v0, 2($a1)
        ori $v1, $zero, 0x8f2a
        bne $v0, $v1, original
        nop
        lhu $v0, 4($a1)
        bnez $v0, original
        nop
        li $a1, {names['Orin']}
        b original
        nop
    genta:
        lhu $v0, 2($a1)
        ori $v1, $zero, 0x592a
        bne $v0, $v1, original
        nop
        lhu $v0, 4($a1)
        bnez $v0, original
        nop
        li $a1, {names['Genta']}
    original:
        addiu $sp, $sp, -64
        j {HOOK+8}
        sw $s3, 44($sp)
    '''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    blob=bytes(ks.asm(code,addr=cave)[0]);assert append(blob)==cave
    assert struct.unpack_from('<2I',elf,HOOK-BASE)==(0x27bdffc0,0xafb3002c)
    struct.pack_into('<2I',elf,HOOK-BASE,0x08000000|(cave>>2),0)
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,p+32,*ph)
    allowed=set(range(HOOK-BASE,HOOK-BASE+8))|set(range(p+48,p+56))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    return elf,dict(hook=hex(HOOK),wrapper=hex(cave),wrapper_bytes=len(blob),names={k:hex(v) for k,v in names.items()},source_records='unchanged',match='Exact two-character parent name followed by UTF-16 NUL only')

def build():
    src=ROOT/'work/output/english-native-0.2.24';source=(src/'EBOOT.spacing.elf').read_bytes();data=(src/'data.spacing.ore').read_bytes()
    assert sha(source)=='eba90cb5795f10d13da6baa1c8061ceefa558ce4a8164aa252b28c8da7d464f8'
    assert sha(data)=='1b113126dd10cd11e8c0a4e37b4f06fe1a2fff27ece8654bc9a80709b1b33d71'
    elf,names=patch_names(source)
    orig=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(orig);be,bend=root_entries(data);rootmap={o:next(r[3] for r in be if r[0]==i) for i,_,_,o in oe}
    base=rootmap[0x36000];a,e=container(data,base);assets={};previews={};graphics=[]
    for entry,label in [(13,'HP'),(24,'MP')]:
        b,im=badge(member(a,e,entry),label);assets[entry]=pack(b);previews[label]=im
        graphics.append(dict(archive_offset=0x36000,member_entry=entry,file={13:'11.ppt',24:'12.ppt'}[entry],translation_en=label,label_rectangle=[0,0,24,16]))
    changed={base:rebuild_ez(a,assets)};members={base:set(assets)}
    tb=rootmap[0x1e8000];a,e=container(data,tb);ot,ote=container(orig,0x1e8000);ppt,im,fr=footer(member(ot,ote,25),VERSION)
    changed[tb]=rebuild_ez(a,{25:pack(ppt)});members[tb]={25};previews['footer']=im;del orig
    ore=rebuild_root(data,changed,mutable=True);ae,aend=root_entries(ore)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
        if a[3] not in changed:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in members[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,source_version='0.2.24',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),names=names,graphics=graphics,footer=fr,texture_replacement=False,checks=dict(unrelated_executable_bytes='byte-identical',all_scripts='byte-identical',unrelated_archive_members='byte-identical',save_records='unchanged',compression_roundtrips='pass'),runtime_verification='pending')
    return elf,ore,previews,report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--tag',default='');a=ap.parse_args();elf,ore,previews,r=build();print(json.dumps(r,indent=2))
    if a.write:
        out=ROOT/('work/output/english-native-'+VERSION+a.tag);out.mkdir(parents=True,exist_ok=True);assert not (out/'EBOOT.battle.elf').exists()
        (out/'EBOOT.battle.elf').write_bytes(elf);(out/'data.battle.ore').write_bytes(ore);(out/'battle.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/battle-hud-'+VERSION);ui.mkdir(parents=True,exist_ok=True)
        for n,im in previews.items():im.save(ui/('native-'+n+'.png'))
    print('Written.' if a.write else 'DRY RUN: no game changes.')
if __name__=='__main__':main()

"""Localize and rearrange the native shop screen. Dry run unless --write."""
import argparse,hashlib,json,struct
import keystone
from PIL import Image,ImageDraw,ImageFont
from catalog_text import ROOT
from build_menu_fixes import container,member,pack,encode_native
from build_latin_auto import footer
from inspect_native_textures import decode
from repack_text import root_entries,rebuild_ez,rebuild_root,align

VERSION='0.2.19';BASE=0x08803000
SOURCE_ELF='4d6c14133931715cab38dd088aa7eb58415be89b87abaaf0876b0a12a702f6fb'
SOURCE_ORE='ccfc45b592f5150d7f6ca4d1934ba3d61a0b9d06600f178b4c9673c01fc74ff7'
# Immediate operands guarded against delivered 0.2.18. Native dimensions.
PATCHES=[
 (0x08951830,0x24050080,56,'Stock list left'),
 (0x08950014,0x24050064,152,'Ownership frame width'),
 (0x08950034,0x2406008c,8,'Ownership frame top'),
 (0x08950038,0x24050177,56,'Ownership frame left'),
 (0x08950074,0x24050050,50,'Comparison frame left'),
 (0x08950078,0x240600b0,174,'Comparison frame top'),
 (0x08950094,0x24060042,68,'Comparison frame height'),
 (0x08950098,0x2405017c,424,'Comparison frame width'),
 (0x0894f3e8,0x2414000a,6,'First comparison cell left'),
 (0x0894f3f0,0x24120004,3,'Attach four visible character cells; retain fifth allocation for destructor compatibility'),
 (0x0894f428,0x24060007,4,'Comparison cells top'),
 (0x0894f430,0x2694004a,104,'Comparison cell pitch'),
 (0x0894f43c,0x24050040,100,'Comparison cell width'),
 (0x0894f444,0x24060034,40,'Comparison cell height'),
 (0x0894f45c,0x28420006,5,'Show comparison paging beyond four members'),
 (0x0894fb18,0x28420006,5,'Previous-page threshold'),
 (0x0894fb64,0x28a20006,5,'Next-page threshold'),
 (0x0894fb78,0x24a7fffb,-4,'Last valid comparison offset'),
 (0x0894fb80,0x24430006,5,'Clamp next offset for four visible members'),
 (0x0894fbb4,0x24020005,4,'Number of comparison cells refreshed'),
 (0x0894fc90,0x24420005,4,'Next-arrow visibility'),
 (0x0894ea4c,0x00003021,20,'Move equipped marker below the name'),
 (0x0894ea84,0x24050010,0,'Full-width character name'),
 (0x0894eaa4,0x24060012,20,'Stat label row'),
 (0x0894eab0,0x00002821,20,'Stat label after equipped marker'),
 (0x0894ead0,0x24060012,20,'Signed comparison value row'),
 (0x0894f948,0x2405000a,6,'Equipment details left'),
 (0x0894f94c,0x2406002b,44,'Equipment details below character comparisons'),
 (0x0894f354,0x24050028,412,'Equipment detail text width'),
 (0x0892f85c,0x24050050,96,'Separated item stat/value region'),
 (0x0892f87c,0x24050055,112,'Separate armor type/restrictions from stat/value'),
]

def sha(b):return hashlib.sha256(b).hexdigest()

def heading(blob):
    original,_=decode(blob);assert original.size==(48,264)
    edited=original.copy();edited.paste(original.crop((0,128,48,240)),(0,0))
    scale=4;layer=Image.new('RGBA',(48*scale,112*scale));d=ImageDraw.Draw(layer)
    font=ImageFont.truetype(str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf'),16*scale)
    for text,y in [('BUY',24),('/',48),('SELL',72)]:
        d.text((24*scale,y*scale),text,font=font,anchor='mm',fill='white',stroke_width=scale+1,stroke_fill=(12,12,18,255))
    edited.alpha_composite(layer.resize((48,112),Image.Resampling.LANCZOS))
    return encode_native(blob,edited,(0,0,48,112))

def stat_icon(blob,label):
    original,_=decode(blob);assert original.size==(32,16)
    scale=4;layer=Image.new('RGBA',(32*scale,16*scale));d=ImageDraw.Draw(layer)
    d.rounded_rectangle((scale,scale,31*scale,15*scale),radius=3*scale,fill=(8,8,12,255),outline=(230,201,118,255),width=scale)
    font=ImageFont.truetype(str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf'),9*scale)
    d.text((16*scale,8*scale),label,font=font,anchor='mm',fill='white')
    return encode_native(blob,layer.resize((32,16),Image.Resampling.LANCZOS),(0,0,32,16))

def build():
    source=(ROOT/'work/output/english-native-0.2.18/EBOOT.inventory.elf').read_bytes()
    data=(ROOT/'work/output/english-native-0.2.18/data.inventory.ore').read_bytes()
    assert sha(source)==SOURCE_ELF and sha(data)==SOURCE_ORE
    elf=bytearray(source);allowed=set();changes=[]
    def raw(addr,old,new,note):
        off=addr-BASE;assert elf[off:off+len(old)]==old,(hex(addr),elf[off:off+len(old)].hex(),old.hex())
        assert len(old)==len(new);elf[off:off+len(old)]=new;allowed.update(range(off,off+len(old)))
        changes.append(dict(address=hex(addr),before=old.hex(),after=new.hex(),purpose=note))
    def word(addr,old,new,note):raw(addr,struct.pack('<I',old),struct.pack('<I',new),note)
    def imm(addr,old,new,note):word(addr,old,(old&0xffff0000)|(new&0xffff),note)
    for a,b,c,n in PATCHES:
        if b in (0x00003021,0x00002821):
            # These two original operands are MOVE instructions. Replacing
            # only their low bits would not produce an immediate assignment.
            word(a,b,0x24000000|(((b>>11)&31)<<16)|(c&0xffff),n)
        else:imm(a,b,c,n)
    raw(0x08a45f5c+8,struct.pack('<h',224),struct.pack('<h',398),'Stock list cell: wider name and right-aligned price')
    literals=[]
    for addr,old,new,name in [
       (0x08a437f0,bytes.fromhex('bdeabbfdb6e20000'),b'Funds:\0\0','Funds caption'),
       (0x08a459b4,b'\xb9\xb6'+bytes(30),b'ATK\0'+bytes(28),'Attack comparison'),
       (0x08a459d4,b'\xcb\xc9'+bytes(30),b'DEF\0'+bytes(28),'Defense comparison'),
       (0x08a459f4,b'\xc9\xd2'+bytes(30),b'AGI\0'+bytes(28),'Agility comparison'),
       (0x08a3ad8c,bytes.fromhex('c1f5c8f7c0adc7bd00000000'),b'Gear Stats\0\0','Equipment statistics popup heading')]:
        raw(addr,old,new,name);literals.append(dict(address=hex(addr),translation=new.split(b'\0')[0].decode(),context=name))
    raw(0x08a45a18,b'%d%s\0\0\0\0',b'%+d\0\0\0\0\0','ASCII signed delta; retains original positive/negative colors')
    raw(0x08a443a8,'%s%s\0\0'.encode('utf-16-le'),'%s %s\0'.encode('utf-16-le'),'Separate quantity and item unit')
    raw(0x08a411f4,'%s%s%s%s\0\0'.encode('utf-16-le'),'%s%s%s %s\0'.encode('utf-16-le'),'Space before equipment restriction term')
    # Dedicated stack storage for each intermediate English descriptor.
    # Existing saved registers and all engine input records retain their offsets.
    reloc={0x10:0xe0,0x30:0x160,0x40:0x1e0,0x50:0x260};relocated=[];stack_changes=[]
    for pc in range(0x0892f990,0x089300c0,4):
        w=struct.unpack_from('<I',source,pc-BASE)[0];op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31;n=w&0xffff
        if op!=9 or rs!=29:continue
        if rt==29 and n in (0xff20,0xe0):
            imm(pc,w,-0x2e0 if n==0xff20 else 0x2e0,'Expanded English equipment formatter stack');stack_changes.append(hex(pc))
        elif rt!=29 and n in reloc:
            imm(pc,w,reloc[n],'Private expanded English equipment descriptor buffer');relocated.append(hex(pc))
    assert len(relocated)==11,(len(relocated),relocated)
    assert stack_changes==['0x892f998','0x89300bc'],stack_changes
    caps={0x0892f9fc:0x20,0x0892fa10:0x10,0x0892fa20:0x10,0x0892fa30:0x40,0x0892fb78:0x20,0x0892fc54:0x20,0x0892fc9c:0x10,0x0892fd28:0x40,0x0892fe68:0x10,0x0892fe9c:0x10,0x0892fedc:0x40}
    for a,n in caps.items():imm(a,0x24060000|n if a in (0x0892f9fc,0x0892fa10,0x0892fa20,0x0892fa30) else 0x24050000|n,128,'English descriptor capacity: 128 bytes')
    phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
    def append(blob):
        elf.extend(bytes(align(len(elf),4)-len(elf)));addr=ph[2]+len(elf)-ph[1];elf.extend(blob);return addr
    unit=append(b' ryo\0');bodyfmt=append('%s %s\0'.encode('utf-16-le'))
    ownedfmt=append('%s:\t%d\0'.encode('utf-16-le'));bothfmt=append('%s%s %s %s\0'.encode('utf-16-le'))
    literals.append(dict(address=hex(unit),translation=' ryo',context='Funds currency unit'))
    def ptr(hi,lo,oldh,oldl,addr,note):
        word(hi,oldh,(oldh&0xffff0000)|((addr+0x8000)>>16),note+' high')
        word(lo,oldl,(oldl&0xffff0000)|(addr&0xffff),note+' low')
    ptr(0x089401dc,0x089401f4,0x3c0808a4,0x250837f8,unit,'Spaced Latin currency unit')
    ptr(0x0892fc44,0x0892fc4c,0x3c0608a4,0x24c611e0,bodyfmt,'Spaced armor location/type formatter')
    ptr(0x08944718,0x08944728,0x3c0608a4,0x24c6439c,ownedfmt,'Ownership caption colon')
    # Use an extra separator only when gender AND class are present. This
    # preserves all four original substitutions and avoids double spaces.
    elf.extend(bytes(align(len(elf),16)-len(elf)));cave=ph[2]+len(elf)-ph[1]
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    code=bytes(ks.asm(f'''.set noreorder
        lhu $t3, 0($t0)
        beqz $t3, tail
        nop
        lhu $t3, 0($t1)
        beqz $t3, tail
        nop
        li $a2, {bothfmt}
    tail:
        j 0x089aa7ac
        nop
    ''',addr=cave)[0]);elf.extend(code)
    word(0x0892fed8,0x0c000000|(0x089aa7ac//4),0x0c000000|(cave//4),'Restriction spacing wrapper')
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph);allowed.update(range(phoff+48,phoff+56))
    assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(source,elf)))
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data)
    rootmap={o:next(n[3] for n in be if n[0]==i) for i,_,_,o in oe};updates={}
    artbase=rootmap[0xb4a800];art,ent=container(data,artbase)
    sprite,preview=heading(member(art,ent,16));updates[artbase]=rebuild_ez(art,{16:pack(sprite)})
    cb=rootmap[0x36000];ca,ce=container(data,cb);icons={};icon_previews={}
    for i,label in [(12,'ATK'),(14,'DEF'),(15,'AGI')]:
        ib,ip=stat_icon(member(ca,ce,i),label);icons[i]=pack(ib);icon_previews[label]=ip
    updates[cb]=rebuild_ez(ca,icons)
    tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000)
    ppt,fp,footer_report=footer(member(ot,ote,25),VERSION);updates[tb]=rebuild_ez(ta,{25:pack(ppt)})
    ore=rebuild_root(data,updates);ae,aend=root_entries(ore)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047)
        aa=data[a[3]:sa];bb=ore[b[3]:sb]
        if a[3] not in updates:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                allowed_members={16} if a[3]==artbase else ({12,14,15} if a[3]==cb else {25})
                if j not in allowed_members:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,source_version='0.2.18',texture_replacement=False,font_raster_scale=4,patches=changes,literals=literals,
      buffers=dict(frame_before=224,frame_after=736,private_buffers=[224,352,480,608],bytes_each=128,relocated_operands=relocated),
      spacing_wrapper=dict(address=hex(cave),bytes=len(code),both_format=hex(bothfmt),original_target='0x089aa7ac'),
      elf_bytes=len(elf),archive_bytes=len(ore),elf_sha256=sha(elf),archive_sha256=sha(ore),runtime_verification='pending',
      checks=dict(unrelated_executable_bytes='unchanged',script_payloads='byte-identical',background_helmet_and_armor_art='byte-identical',other_archive_members='byte-identical',new_graphic_labels=['BUY / SELL','ATK','DEF','AGI']),footer=footer_report)
    layout=dict(version=VERSION,stock=[56,42,474,168],owned=[56,8,208,34],funds=[290,10,470,34],comparison_frame=[50,174,474,242],
       comparison_cells=dict(visible=4,width=100,pitch=104,left=6,top=4,name=[0,0],equipped_marker=[0,20],stat_label=[20,20],delta='right-aligned; signed ASCII, original color retained',paging='Original controls; clamped to four visible members'),
       equipment_details=dict(left=6,top=44,width=412,stat_region=96,type_left=112),background_art='Two large background kanji preserved byte-for-byte',runtime_verification='pending')
    return bytes(elf),ore,preview,fp,icon_previews,report,layout

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    elf,ore,preview,fp,icon_previews,report,layout=build();print(json.dumps(report,indent=2));print(json.dumps(layout,indent=2))
    if a.write:
        out=ROOT/('work/output/english-native-'+VERSION);out.mkdir(parents=True,exist_ok=True)
        assert not (out/'EBOOT.shop.elf').exists() and not (out/'data.shop.ore').exists()
        (out/'EBOOT.shop.elf').write_bytes(elf);(out/'data.shop.ore').write_bytes(ore)
        (out/'shop.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/shop-layout-'+VERSION);ui.mkdir(parents=True,exist_ok=True)
        (ui/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8');preview.save(ui/'native-buy-sell.png');fp.save(ui/'native-footer.png')
        for label,im in icon_previews.items():im.save(ui/('native-'+label.lower()+'.png'))
        p=ROOT/'work/translation/en/shop';p.mkdir(parents=True,exist_ok=True)
        (p/'literals.en.json').write_text(json.dumps(dict(version=VERSION,rows=report['literals'],status='Native UI literals; runtime review pending'),indent=2)+'\n',encoding='utf-8')
    print('Build written.' if a.write else 'DRY RUN: no files written.')

if __name__=='__main__':main()

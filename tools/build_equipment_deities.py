"""Translate equipment/deity graphics and repair native menus. Dry run unless --write."""
import argparse,hashlib,json,struct
import keystone
from PIL import Image,ImageDraw,ImageFont
from catalog_text import ROOT
from build_menu_fixes import container,member,pack,encode_native
from build_latin_auto import footer
from inspect_native_textures import decode
from repack_text import root_entries,rebuild_ez,rebuild_root,align

VERSION='0.2.20';BASE=0x08803000;FONT=str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf')
SOURCE_ELF='bb5c934d084824041df0a74a939156ece421fb38678a40ff4134e45250320bac'
SOURCE_ORE='952c2ccce5f496f36aa8c84abc1fad80924923449ffeec314ab9c828414944bf'
PATCHES=[
 (0x0893a8a8,0x2405004a,128,'Divine Union submenu text width'),
 (0x088f72d0,0x24050078,248,'Equipped item cell width'),
 (0x088f6fb0,0x2405001a,36,'Separate equipment slot badge and full item name'),
 (0x088f72e8,0x24050002,4,'Four equipped item rows'),
 (0x088f72f0,0x24060002,1,'One equipped item column'),
 (0x088f638c,0x24050070,240,'Available equipment cell width'),
 (0x088f63b0,0x24050006,4,'Four visible equipment choices; native paging retained'),
 (0x088f63b8,0x24060002,1,'One available equipment column'),
 (0x0895c2f4,0x24060058,126,'Equipment list below taller slot panel and source caption'),
 (0x0895c2c4,0x2406003e,100,'Equipment source caption below taller slot panel'),
 (0x0895c33c,0x240600d8,218,'Equipment description clear of the taller list'),
 (0x0895b40c,0x24050008,4,'Four visible deity rows with native paging'),
 (0x0895bb08,0x00003021,16,'Deity offering value second row'),
 (0x0895bb14,0x240500a4,90,'Deity offering value right anchor'),
 (0x0895bb3c,0x24060002,18,'Deity element second row'),
 (0x0895bb48,0x240500aa,106,'Deity element clear of cost'),
 (0x0895bb7c,0x00003021,16,'Deity gender second row'),
 (0x0895bb88,0x240500ca,162,'Deity gender clear of element'),
 (0x08959324,0x24050085,176,'Wider deity detail frame'),
 (0x08959354,0x24050150,300,'Deity detail frame left'),
 (0x08959388,0x24050152,324,'Center deity portrait inside wider frame'),
 (0x0895946c,0x24050156,306,'Deity pronunciation left'),
 (0x089594ac,0x240501bd,456,'Element beside pronunciation instead of long name'),
 (0x089594a0,0x240600a1,148,'Deity element above name'),
 (0x089594dc,0x24050012,16,'Deity name size matches list'),
 (0x089594ec,0x24050156,306,'Deity name left'),
 (0x0895952c,0x24050166,306,'Divine Unions caption left'),
 (0x08959594,0x240501ca,468,'Divine Unions count right anchor'),
 (0x089595e0,0x24050166,306,'Full Offering Points Required caption left'),
 (0x08959648,0x240501ca,468,'Required offering value right anchor'),
]

def sha(b):return hashlib.sha256(b).hexdigest()

def badge(blob,label):
    im,_=decode(blob);assert im.size==(32,16)
    scale=4;layer=Image.new('RGBA',(128,64));d=ImageDraw.Draw(layer)
    # Slot widgets sample only the first 24 pixels of these 32-pixel textures.
    # Keep the entire caption and rim inside that original sprite rectangle.
    slot=label in ('WPN','HEAD','ARM','ACC');w=24 if slot else 32
    d.rounded_rectangle((4,4,(w-1)*4,60),radius=10,fill=(8,8,16,255),outline=(224,199,117,255),width=4)
    size=9
    while ImageFont.truetype(FONT,round(size*4)).getlength(label)>(w-4)*4:size-=.25
    assert size>=7
    d.text((w*2,32),label,font=ImageFont.truetype(FONT,round(size*4)),anchor='mm',fill='white')
    return encode_native(blob,layer.resize((32,16),Image.Resampling.LANCZOS),(0,0,32,16))

def ribbon(blob,label):
    im,_=decode(blob);assert im.size==(48,264)
    edited=im.copy()
    # Reuse a clean 64-pixel repeat from the lower native diamond pattern.
    for y in (0,64,128):edited.paste(im.crop((0,192,48,256)),(0,y))
    layer=Image.new('RGBA',(192*4,48*4));d=ImageDraw.Draw(layer)
    font=ImageFont.truetype(FONT,19*4);assert font.getlength(label)<184*4
    d.text((96*4,24*4),label,font=font,anchor='mm',fill='white',stroke_width=4,stroke_fill=(10,10,20,255))
    edited.alpha_composite(layer.resize((192,48),Image.Resampling.LANCZOS).transpose(Image.Transpose.ROTATE_270),(0,0))
    return encode_native(blob,edited,(0,0,48,192))

def missing(blob):
    im,_=decode(blob);assert im.size==(128,128);edit=im.copy();scale=4
    layer=Image.new('RGBA',(32*scale,108*scale));d=ImageDraw.Draw(layer)
    for y in range(108*scale):
        q=y/(108*scale);d.line((0,y,32*scale,y),fill=(round(52+24*q),round(15+5*q),round(119+15*q),255))
    d.line((0,0,0,108*scale),fill=(32,19,75,255),width=4)
    font=ImageFont.truetype(FONT,13*scale)
    for i,c in enumerate('MISSING'):d.text((16*scale,(12+i*14)*scale),c,font=font,anchor='mm',fill='white',stroke_width=2,stroke_fill=(20,8,50,255))
    edit.alpha_composite(layer.resize((32,108),Image.Resampling.LANCZOS),(48,11))
    return encode_native(blob,edit,(48,11,80,119))

def build():
    source=(ROOT/'work/output/english-native-0.2.19/EBOOT.shop.elf').read_bytes();data=(ROOT/'work/output/english-native-0.2.19/data.shop.ore').read_bytes()
    assert sha(source)==SOURCE_ELF and sha(data)==SOURCE_ORE
    elf=bytearray(source);allowed=set();changes=[]
    def raw(a,old,new,n):
        off=a-BASE;assert elf[off:off+len(old)]==old,(hex(a),elf[off:off+len(old)].hex());assert len(old)==len(new)
        elf[off:off+len(old)]=new;allowed.update(range(off,off+len(old)));changes.append(dict(address=hex(a),before=old.hex(),after=new.hex(),purpose=n))
    def word(a,old,new,n):raw(a,struct.pack('<I',old),struct.pack('<I',new),n)
    for a,old,value,note in PATCHES:
        if old in (0x00003021,0x00002821):new=0x24000000|(((old>>11)&31)<<16)|(value&0xffff)
        else:new=(old&0xffff0000)|(value&0xffff)
        word(a,old,new,note)
    phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
    def append(b):
        elf.extend(bytes(align(len(elf),4)-len(elf)));a=ph[2]+len(elf)-ph[1];elf.extend(b);return a
    male=append(b'Male\0');female=append(b'Female\0')
    for hi,lo,oldh,oldl,addr in [(0x088f68e8,0x088f68f4,0x3c0308a4,0x2465a648,male),(0x088f68f8,0x088f68fc,0x3c0208a4,0x2445a64c,female)]:
        word(hi,oldh,(oldh&0xffff0000)|((addr+0x8000)>>16),'Latin gender label high')
        word(lo,oldl,(oldl&0xffff0000)|(addr&0xffff),'Latin gender label low')
    elf.extend(bytes(align(len(elf),16)-len(elf)));cave=ph[2]+len(elf)-ph[1]
    code=bytes(keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN).asm('''.set noreorder
        li $t0, 32
        sw $t0, 0x2580($a0)
        j 0x08821f50
        nop
    ''',addr=cave)[0]);elf.extend(code)
    word(0x0895b418,0x0c000000|(0x08821f50//4),0x0c000000|(cave//4),'Two-line deity cells before native geometry')
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph);allowed.update(range(phoff+48,phoff+56))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data)
    rootmap={o:next(n[3] for n in be if n[0]==i) for i,_,_,o in oe};updates={};changed={};previews={};graphics=[]
    plans={0x36000:[(25,'Head',badge),(26,'Leader',badge),(27,'Party',badge),(33,'WPN',badge),(34,'HEAD',badge),(36,'ARM',badge),(37,'ACC',badge),(40,'EQUIPMENT',ribbon)],0xb4a800:[(17,'DIVINE UNION',ribbon)],0x75a000:[(0,'MISSING',None)],0xb3cc800:[(0,'MISSING',None)]}
    inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text());names={(r['archive_offset'],r['entry']):r['name'] for r in inv}
    for old,plan in plans.items():
        base=rootmap[old];a,e=container(data,base);assets={}
        for entry,label,fn in plan:
            blob=member(a,e,entry);nb,im=fn(blob,label) if fn else missing(blob);assets[entry]=pack(nb)
            key=f'{old:08x}-{entry:04d}';previews[key]=im
            graphics.append(dict(file=names[old,entry],archive_offset=old,member_entry=entry,translation_en=label,preview='native-'+key+'.png',status='draft'))
        updates[base]=rebuild_ez(a,assets);changed[base]=set(assets)
    tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000)
    ppt,fp,fr=footer(member(ot,ote,25),VERSION);updates[tb]=rebuild_ez(ta,{25:pack(ppt)});changed[tb]={25};previews['footer']=fp
    ore=rebuild_root(data,updates);ae,aend=root_entries(ore)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047)
        aa=data[a[3]:sa];bb=ore[b[3]:sb]
        if a[3] not in updates:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in changed[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,source_version='0.2.19',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=changes,literals=[dict(address=hex(male),translation_en='Male'),dict(address=hex(female),translation_en='Female')],graphics=graphics,wrapper=dict(address=hex(cave),bytes=len(code),native_target='0x08821f50'),texture_replacement=False,font_raster_scale=4,runtime_verification='pending',checks=dict(unrelated_executable_bytes='byte-identical',all_script_payloads='byte-identical',other_archive_members='byte-identical',archive_compression_round_trip='pass'),footer=fr)
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    def width(t):return sum(metrics.get(str(ord(c)),{'advance':14})['advance'] for c in t)*12/14
    rows=[r for p in (ROOT/'work/translation/en').glob('*.en.json') for r in json.loads(p.read_text(encoding='utf-8')).get('rows',[])]
    equipment=[r for r in rows if r.get('archive_offset')==0x28000 and r.get('member_entry')==0 and r.get('section',0)>=2]
    deity=[r for r in rows if r.get('kind')=='deity_name']
    assert len(equipment)==463 and max(width(r['translation_en']) for r in equipment)<=212
    assert max(width(r['translation_en']) for r in deity)<=160
    report['static_names']=dict(equipment=len(equipment),equipped_name_budget=212,max_equipment_width=max(width(r['translation_en']) for r in equipment),deities=len(deity),deity_detail_name_budget=160,max_deity_width=max(width(r['translation_en']) for r in deity),generated_deity_names='Require separate dynamic-name review')
    layout=dict(version=VERSION,equipment_slots=dict(columns=1,rows=4,cell_width=248,name_left=36,name_budget=212),equipment_choices=dict(columns=1,visible_rows=4,cell_width=240,top=126,ownership_top=100,description_top=218,paging='native'),union_submenu=dict(text_width=128),deity_list=dict(columns=1,visible_rows=4,cell_height=32,cell_width=216,name=[20,0],offering_anchor=[90,16],element=[106,18],gender=[162,16],paging='native'),deity_details=dict(frame=[300,16,476,228],portrait=[324,18,452,146],name=[306,158],element=[456,148],unions_caption=[306,179],required_caption=[306,195],required_anchor=[468,211]),runtime_verification='pending')
    return bytes(elf),ore,previews,report,layout

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,previews,report,layout=build();print(json.dumps(report,indent=2));print(json.dumps(layout,indent=2))
    if a.write:
        out=ROOT/'work/output/english-native-0.2.20';out.mkdir(parents=True,exist_ok=True);assert not (out/'EBOOT.equipment.elf').exists()
        (out/'EBOOT.equipment.elf').write_bytes(elf);(out/'data.equipment.ore').write_bytes(ore);(out/'equipment.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/'work/ui/equipment-deities-0.2.20';ui.mkdir(parents=True,exist_ok=True);(ui/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
        for name,im in previews.items():im.save(ui/('native-'+name+'.png'))
    print('Build written.' if a.write else 'DRY RUN: no game files written.')

if __name__=='__main__':main()

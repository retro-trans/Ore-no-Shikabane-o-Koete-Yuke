"""Render shared UI labels at native HD texture resolution. Dry run before writing."""
import argparse,hashlib,json,struct,functools
from PIL import Image,ImageDraw,ImageFont
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root
from inspect_native_textures import decode
from hd_sprites import encode,patch,proxy
VERSION='0.2.26';FONT=str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf')
BADGES={11:'HP',12:'MP',13:'Body',107:'HP',108:'MP',109:'ATK',110:'DEF',111:'AGI',112:'WINS',113:'HLTH',114:'LOY',120:'Head',121:'Leader',122:'Party',123:'Study',124:'Train',125:'Cmd',128:'WPN',129:'HEAD',130:'ARM',131:'ACC',21:'SPR',22:'SKL',23:'BOD',86:'Growth'}
RIBBONS={132:'STATUS',134:'EQUIPMENT',84:'BATTLE RESULTS'}
def sha(b):return hashlib.sha256(b).hexdigest()

def badge_image(blob,text):
    im,info=decode(blob);w,h=im.size;lw,lh=info['logical_width'],info['logical_height'];s=4
    layer=Image.new('RGBA',(w*s,h*s));d=ImageDraw.Draw(layer)
    rim=(185,188,199,255) if text in ('Head','Party') else (224,199,117,255)
    d.rounded_rectangle((s,s,(lw-1)*s,(lh-1)*s),radius=3*s,fill=(8,8,13,255),outline=rim,width=s)
    size=11
    while ImageFont.truetype(FONT,round(size*s)).getlength(text)>(lw-4)*s:size-=.25
    assert size>=6.5,(text,lw,size)
    font=ImageFont.truetype(FONT,round(size*s));d.text((lw*s/2,lh*s/2),text,font=font,anchor='mm',fill='white')
    return layer,dict(font='Noto Sans',font_size=size,text=text,ink_budget=lw-4)

def ribbon_image(blob,text):
    im,info=decode(blob);w,h=im.size;assert (w,h)==(48,264)
    # Reuse the clear lower diamond repeat to remove the source lettering.
    clean=Image.new('RGBA',im.size)
    for y in range(0,h,32):clean.paste(im.crop((0,224,48,256)),(0,y))
    s=4;layer=clean.resize((w*s,h*s),Image.Resampling.NEAREST)
    word=Image.new('RGBA',(h*s,w*s));d=ImageDraw.Draw(word);font=ImageFont.truetype(FONT,20*s)
    assert font.getlength(text)<(h-24)*s
    d.text((h*s/2,w*s/2),text,font=font,anchor='mm',fill='white',stroke_width=s,stroke_fill=(12,12,22,255))
    layer.alpha_composite(word.transpose(Image.Transpose.ROTATE_270))
    # PSP textures are at most512x512. Preserve the entire original264px
    # logical strip, with4x horizontal and~1.94x vertical physical sampling.
    layer=layer.resize((192,512),Image.Resampling.LANCZOS)
    return layer,dict(font='Noto Sans',font_size=20,text=text,hardware_limit=512)

def potential_image(blob,text):
    im,info=decode(blob);w,h=im.size;assert (w,h)==(144,256)
    s=4;layer=im.resize((w*s,h*s),Image.Resampling.NEAREST);d=ImageDraw.Draw(layer)
    # Preserve the frame, then rebuild the three graph cells without bitmap
    # Japanese watermarks. Bars and English row labels are separate widgets.
    d.rectangle((4*s,14*s,137*s,247*s),fill=(0,0,0,255))
    for x in (44,66,87,108,129):d.line((x*s,30*s,x*s,244*s),fill=(46,46,46,255),width=s)
    for y in (99,173):d.line((36*s,y*s,135*s,y*s),fill=(46,46,46,255),width=s)
    font=ImageFont.truetype(FONT,10*s)
    for y,label in ((70,'SPIRIT'),(145,'SKILL'),(218,'BODY')):
        d.text((101*s,y*s),label,font=font,anchor='mm',fill=(62,62,62,255))
    return layer.resize((512,512),Image.Resampling.LANCZOS),dict(font='Noto Sans',font_size=10,text=text,hardware_limit=512)

def digit_image(blob,text,color):
    im,info=decode(blob);w,h=im.size;lw,lh=info['logical_width'],info['logical_height'];s=4
    layer=Image.new('RGBA',(w*s,h*s));d=ImageDraw.Draw(layer);font=ImageFont.truetype(FONT,22*s)
    assert font.getlength(text)<(lw-2)*s
    d.text((lw*s/2,lh*s/2),text,font=font,anchor='mm',fill=color,stroke_width=2,stroke_fill=(0,0,0,255))
    return layer,dict(font='Noto Sans',font_size=22,text=text,color=color,category='native combat digit')

def build(prototype=False):
    src=ROOT/'work/output/english-native-0.2.25-c';source=(src/'EBOOT.battle.elf').read_bytes();data=(src/'data.battle.ore').read_bytes()
    assert sha(source)=='8620a2b0986a3cc90489748aa9aa99bd6dec262af6536aedcbd44a34c4d23a1b'
    assert sha(data)=='02f48e0ea579dc0daeff258bc7dcf761dacb95a169419d1ed00980d8554106bb'
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data)
    rootmap={o:next(r[3] for r in be if r[0]==i) for i,_,_,o in oe}
    inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text());lookup={(r['archive_offset'],r['name']):r['entry'] for r in inv}
    plans=[(0x36000,str(i)+'.ppt',t,badge_image) for i,t in BADGES.items()]
    plans += [(0x36000,str(i)+'.ppt',t,ribbon_image) for i,t in RIBBONS.items()]
    plans += [(0x36000,'115.ppt','SPIRIT / SKILL / BODY',potential_image)]
    plans += [(0x4eaf000,'286.ppt','ONI RECORDS',ribbon_image),(0x4eaf000,'287.ppt','ITEM CATALOG',ribbon_image),(0x4eaf000,'288.ppt','Defeated',badge_image),(0x4eaf000,'289.ppt','Specialty',badge_image)]
    for old,prefixes in [(0x660d800,('','green','purple')),(0xa92f800,('','green'))]:
        for prefix in prefixes:
            color={'':(255,255,255,255),'green':(72,245,0,255),'purple':(190,72,230,255)}[prefix]
            for digit in range(10):
                plans.append((old,'num'+('_'+prefix if prefix else '')+str(digit)+'.ppt',str(digit),functools.partial(digit_image,color=color)))
    if prototype:plans=[plans[3]] # Shared HP badge107.ppt
    changes={};changed_members={};previews={};graphics=[];assets=[];originals=[]
    for old,name,text,draw in plans:
        base=rootmap[old]
        if base not in changes:changes[base]={}
        arc,entries=container(data,base);entry=lookup[old,name];blob=member(arc,entries,entry)
        image,typography=draw(blob,text);new,actual,hd=encode(blob,image)
        assets.append(new);originals.append((base,entry,blob))
        key='%08x-%04d'%(old,entry);previews[key]=actual
        graphics.append(dict(archive_offset=old,member_entry=entry,file=name,translation_en=text,**typography,**hd))
    elf,renderer=patch(source,assets)
    for (base,entry,blob),address in zip(originals,renderer['embedded_descriptors']):
        replacement=proxy(blob,address)
        assert len(replacement)==len(blob),(base,entry,len(blob),len(replacement))
        changes[base][entry]=pack(replacement)
    updates={}
    for base,assets in changes.items():
        arc,_=container(data,base);updates[base]=rebuild_ez(arc,assets);changed_members[base]=set(assets)
    tb=rootmap[0x1e8000];arc,en=container(data,tb);oa,oe2=container(original,0x1e8000);ppt,im,fr=footer(member(oa,oe2,25),VERSION)
    updates[tb]=rebuild_ez(arc,{25:pack(ppt)});changed_members[tb]={25};previews['footer']=im;del original
    ore=rebuild_root(data,updates,mutable=True);ae,aend=root_entries(ore)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
        if a[3] not in updates:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in changed_members[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,prototype=prototype,source_version='0.2.25',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),renderer=renderer,graphics=graphics,footer=fr,texture_replacement=False,checks=dict(all_scripts='byte-identical',unrelated_archive_members='byte-identical',archive_decompressed_resource_sizes='exactly preserved',source_logical_geometry='preserved',crop_rectangles='mapped to physical HD coordinates'),runtime_verification='pending')
    return elf,ore,previews,report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--prototype',action='store_true');ap.add_argument('--tag',default='');a=ap.parse_args()
    elf,ore,previews,r=build(a.prototype);print(json.dumps(r,indent=2))
    if a.write:
        out=ROOT/('work/output/english-native-'+VERSION+a.tag);out.mkdir(parents=True,exist_ok=True);assert not (out/'EBOOT.hd.elf').exists()
        (out/'EBOOT.hd.elf').write_bytes(elf);(out/'data.hd.ore').write_bytes(ore);(out/'hd.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/hd-fonts-'+VERSION);ui.mkdir(parents=True,exist_ok=True)
        for key,im in previews.items():im.save(ui/('native-'+key+'.png'))
    print('Written.' if a.write else 'DRY RUN: no game changes.')
if __name__=='__main__':main()

"""Native overworld labels for 0.2.10. Dry run unless --write."""
import argparse
import hashlib
import json
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

from catalog_text import ROOT, unpack_member
from inspect_native_textures import decode
from build_menu_fixes import container, member, pack, encode_native
from build_title_branding import footer
from repack_text import rebuild_ez, rebuild_root, root_entries

VERSION = '0.2.10'
FONT = str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf')
# Native atlas sign bounds: scenery remains untouched.
SIGNS = {
 '01': ('Mount Oe', (485,3,511,80)),
 '02': ('Soyokuin', (213,3,254,81)),
 '03': ('Kujuro', (99,3,126,83)),
 '04': ('Torii Senmangu', (223,5,254,181)),
 '05': ('Boga Aqueduct', (218,3,254,117)),
 '06': ('White Bone\nCastle', (199,3,253,85)),
 '07': ('Crimson Flame\nShrine', (221,4,254,112)),
 '08': ('Royal Requiem\nTomb', (223,3,255,103)),
}
DESTINATIONS = ['Soyokuin','Kujuro','White Bone Castle','Mount Oe',
                'Crimson Flame Shrine','Tour of Hell','Royal Requiem Tomb',
                'Boga Aqueduct','Torii Senmangu','Kyoto']


def lettering(size, text, maximum=22, dark=False):
    """Four-times raster, fitted to a vertical native sign before reduction."""
    w,h = size
    layer = Image.new('RGBA',(h*4,w*4))
    d = ImageDraw.Draw(layer)
    for fs in range(maximum*4,19,-1):
        font = ImageFont.truetype(FONT,fs)
        box = d.multiline_textbbox((0,0),text,font=font,spacing=0,stroke_width=2)
        if box[2]-box[0] <= (h-4)*4 and box[3]-box[1] <= (w-3)*4:break
    assert box[2]-box[0] <= (h-4)*4 and box[3]-box[1] <= (w-3)*4
    x=(h*4-(box[2]-box[0]))/2-box[0]
    y=(w*4-(box[3]-box[1]))/2-box[1]
    d.multiline_text((x,y),text,font=font,align='center',spacing=0,
                     fill=(29,15,30,255) if dark else 'white',
                     stroke_width=0 if dark else 3,stroke_fill=(10,7,20,255))
    return layer.resize((h,w),Image.Resampling.LANCZOS).transpose(Image.Transpose.ROTATE_270),fs/4


def small_sign(blob, label, rect):
    im,_=decode(blob);x0,y0,x1,y1=rect
    edit=im.copy()
    # Match the original gold-to-purple sign with a clean rim and inset.
    d=ImageDraw.Draw(edit)
    for y in range(y0,y1):
        t=(y-y0)/max(1,y1-y0-1)
        a,b=((248,204,81),(246,234,218)) if t<.5 else ((246,234,218),(163,99,211))
        t=t*2 if t<.5 else (t-.5)*2
        color=tuple(round(a[i]*(1-t)+b[i]*t) for i in range(3))+(255,)
        d.line((x0,y,x1-1,y),fill=color)
    d.rectangle((x0,y0,x1-1,y1-1),outline=(25,16,33,255),width=1)
    d.rectangle((x0+2,y0+2,x1-3,y1-3),outline=(185,139,65,255),width=1)
    d.line((x0+3,y0+3,x0+3,y1-4),fill=(249,225,155,255),width=1)
    text,fs=lettering((x1-x0-8,y1-y0-8),label,18,True)
    edit.alpha_composite(text,(x0+4,y0+4))
    out,preview=encode_native(blob,edit,rect)
    return out,preview,fs


def compass(blob):
    im,_=decode(blob);edit=im.copy();d=ImageDraw.Draw(edit)
    d.ellipse((190,194,252,254),fill=(42,48,130,255),outline=(210,191,158,255),width=1)
    d.ellipse((208,209,235,239),fill=(210,191,158,255))
    places=[('KYO',(209,219,235,230),8,(210,191,158,255)),
            ('N',(215,193,230,207),10,(42,48,130,255)),
            ('W',(190,216,205,233),10,(42,48,130,255)),
            ('E',(237,216,253,233),10,(42,48,130,255)),
            ('S',(215,240,230,256),10,(42,48,130,255))]
    for label,box,fs,color in places:
        x0,y0,x1,y1=box;d.rectangle((x0,y0,x1-1,y1-1),fill=color)
        layer=Image.new('RGBA',((x1-x0)*4,(y1-y0)*4));ld=ImageDraw.Draw(layer)
        font=ImageFont.truetype(FONT,fs*4)
        ld.text((layer.width/2,layer.height/2),label,font=font,anchor='mm',fill=(27,16,35,255) if label=='KYO' else (236,219,166,255))
        edit.alpha_composite(layer.resize((x1-x0,y1-y0),Image.Resampling.LANCZOS),(x0,y0))
    out,preview=encode_native(blob,edit,(190,193,253,256))
    return out,preview


def destination(blob,label):
    im,_=decode(blob);w,h=im.size
    if label=='Kyoto':
        edit=im.copy();rect=(109,27,176,192)
        # This area contains the plaque and its reading. Itsuka's pixels
        # left of the plaque and below it remain exactly as in the source.
        edit.paste((0,0,0,0),(161,27,176,192))
        d=ImageDraw.Draw(edit)
        d.rectangle((109,27,160,190),fill=(31,29,83,255),outline=(113,74,180,255),width=2)
        d.rectangle((114,32,155,185),outline=(48,88,157,255),width=2)
        text,fs=lettering((39,149),label.upper(),27)
        edit.alpha_composite(text,(116,35))
    else:
        edit=Image.new('RGBA',im.size)
        rect=(0,0,w,h)
        d=ImageDraw.Draw(edit)
        d.rounded_rectangle((3,2,w-6,h-4),radius=5,fill=(45,22,49,255),outline=(195,161,86,255),width=2)
        text,fs=lettering((w-16,h-18),label.upper(),25)
        edit.alpha_composite(text,(7,8))
    out,preview=encode_native(blob,edit,rect)
    return out,preview,fs,rect


def build():
    data=(ROOT/'work/output/english-native-0.2.9/data.menu.ore').read_bytes()
    assert hashlib.sha256(data).hexdigest()=='3999a61344b47e1699ef4bfd90ad641a056fef3b90b4eabfd22e68d1423c95fe'
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);ne,_=root_entries(data)
    old_index={off:i for i,_,_,off in oe};current={i:off for i,_,_,off in ne}
    relocated=lambda b:current[old_index[b]]
    inventory=json.loads((ROOT/'work/source/archive_inventory.json').read_text())
    changes=defaultdict(dict);previews={};assets=[]
    for row in inventory:
        name=row['name']
        if not (name.startswith('d14_wm_') and name.endswith('.ppt') and name[7:9] in SIGNS):continue
        label,rect=SIGNS[name[7:9]]
        base=relocated(row['archive_offset'])
        archive,entries=container(data,base)
        blob=member(archive,entries,row['entry'])
        out,preview,fs=small_sign(blob,label,rect)
        changes[base][row['entry']]=pack(out)
        key=f'{row["archive_offset"]:08x}-{row["entry"]:04d}-{name}'
        previews[key]=preview
        assets.append(dict(asset=name,original_archive=hex(row['archive_offset']),entry=row['entry'],translation=label.replace('\n',' '),rectangle=rect,font_pixels=fs,kind='map_sign'))
    for row in inventory:
        name=row['name']
        if not (name.startswith('d14_wm_0a_') and name.endswith('.ppt')):continue
        base=relocated(row['archive_offset']);archive,entries=container(data,base)
        out,preview=compass(member(archive,entries,row['entry']))
        changes[base][row['entry']]=pack(out)
        previews[f'{row["archive_offset"]:08x}-compass']=preview
        assets.append(dict(asset=name,original_archive=hex(row['archive_offset']),entry=row['entry'],translation='KYO / N / E / S / W',rectangle=(190,193,253,256),kind='compass'))
    base=relocated(0x4eaf000);archive,entries=container(data,base)
    for entry,label in enumerate(DESTINATIONS):
        blob=member(archive,entries,entry)
        out,preview,fs,rect=destination(blob,label)
        changes[base][entry]=pack(out);previews[f'destination-{entry:02d}']=preview
        assets.append(dict(asset=f'{276+entry}.ppt',entry=entry,original_archive='0x4eaf000',translation=label,rectangle=rect,font_pixels=fs,kind='destination_banner'))
    base=relocated(0x1e8000);orig,entries=container(original,0x1e8000)
    out,preview,_=footer(member(orig,entries,25),VERSION)
    changes[base][25]=pack(out);previews['title-footer']=preview
    updates={}
    for base,members in changes.items():
        archive,_=container(data,base);updates[base]=rebuild_ez(archive,members)
    result=rebuild_root(data,updates)
    # Verify unrelated root payloads and individual archive members byte for byte.
    after,after_end=root_entries(result);before,before_end=root_entries(data)
    for n,(a,b) in enumerate(zip(before,after)):
        sa=before[n+1][3] if n+1<len(before) else before_end
        sb=after[n+1][3] if n+1<len(after) else after_end
        aa=data[a[3]:sa-(a[2]&2047)];bb=result[b[3]:sb-(b[2]&2047)]
        if a[3] not in updates:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in changes[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
                else:assert unpack_member(bb[pp:pp+zz])[0][:4]==b'ppt\0'
    report=dict(version=VERSION,source_version='0.2.9',texture_replacement=False,
                unique_location_labels=10,map_sign_copies=sum(x['kind']=='map_sign' for x in assets),compass_copies=sum(x['kind']=='compass' for x in assets),
                assets=assets,archive_bytes=len(result),archive_sha256=hashlib.sha256(result).hexdigest(),
                checks=dict(unrelated_root_payloads='byte-identical',unrelated_members='byte-identical',
                            original_palettes='preserved',unmodified_pixels='byte-identical outside recorded rectangles',
                            executable='0.2.9 unchanged',compression_round_trips='pass'),runtime_verification='pending')
    return result,previews,report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--previews',action='store_true');args=ap.parse_args()
    ore,previews,report=build()
    print(json.dumps({k:v for k,v in report.items() if k!='assets'},indent=2))
    print('Labels: '+', '.join(DESTINATIONS))
    if args.previews or args.write:
        dest=ROOT/'work/ui/map-fixes-0.2.10';dest.mkdir(parents=True,exist_ok=True)
        for name,im in previews.items():im.save(dest/('native-'+name+'.png'))
        sheet=Image.new('RGB',(1000,((len(previews)+4)//5)*300),(45,45,45));d=ImageDraw.Draw(sheet)
        for i,(name,im) in enumerate(previews.items()):
            im=im.copy();im.thumbnail((194,270));x=i%5*200;y=i//5*300
            sheet.paste(im,(x,y+22),im);d.text((x,y),name[:29],fill='white')
        sheet.save(dest/'native-contact-sheet.png')
    if args.write:
        dest=ROOT/'work/output/english-native-0.2.10';dest.mkdir(parents=True,exist_ok=True)
        if (dest/'data.map.ore').exists():
            assert hashlib.sha256((dest/'data.map.ore').read_bytes()).hexdigest() in ('13230bf9fe0c79153e366dff62ba8effcc223c61916043d97fb64c64b39a8f44',report['archive_sha256']), 'Refusing to overwrite an unknown build'
        (dest/'data.map.ore').write_bytes(ore)
        (dest/'map.report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Build written.' if args.write else 'DRY RUN: game files unchanged.')


if __name__=='__main__':main()

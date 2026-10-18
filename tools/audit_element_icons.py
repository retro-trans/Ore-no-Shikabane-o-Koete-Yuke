"""Inspect the original shared element sprites; dry run before --write."""
import argparse,json
from PIL import Image,ImageDraw
from catalog_text import ROOT
from build_menu_fixes import container,member
from inspect_native_textures import decode
from repack_text import root_entries
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
data=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();arc,en=container(data,0x36000)
inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text());rows=[r for r in inv if r['archive_offset']==0x36000]
images=[];report=[]
for r in rows:
 im,info=decode(member(arc,en,r['entry']))
 if info['logical_width']<=40 and info['logical_height']<=40:
  images.append((r,im,info));report.append(dict(file=r['name'],entry=r['entry'],**info))
print(json.dumps(dict(write=a.write,count=len(images),output='work/source/element-audit/shared.png',element_candidates=[r for r in report if r['file'] in ('17.ppt','18.ppt','19.ppt','20.ppt')]),indent=2))
if a.write:
 out=ROOT/'work/source/element-audit';out.mkdir(exist_ok=True)
 sheet=Image.new('RGB',(800,((len(images)+7)//8)*110),(45,45,50));d=ImageDraw.Draw(sheet)
 for i,(r,im,info) in enumerate(images):
  x=i%8*100;y=i//8*110;d.text((x+3,y+3),r['name'],fill='white');im=im.crop((0,0,info['logical_width'],info['logical_height']));im.thumbnail((76,76));im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST) if max(im.size)<38 else im
  sheet.paste(im,(x+5,y+24),im)
 sheet.save(out/'shared.png');(out/'inventory.json').write_text(json.dumps(report,indent=2))

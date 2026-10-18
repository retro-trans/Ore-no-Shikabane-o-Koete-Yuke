"""Recover seven exact icon crops from the supplied Vita game's native UI sheets."""
import argparse,hashlib,json
from PIL import Image,ImageDraw
from catalog_text import ROOT,unpack_member
from decode_vita_gxt import decode
SOURCE=ROOT/'work/source/vita3k-icons-profile/ux0/app/PCSA00155/data.img'
SPECS=[('HP','udtx_status_us.ppt',(0,16,24,40)),('MP','udtx_status_us.ppt',(24,16,48,40)),('HLTH','udtx_status_us.ppt',(48,16,72,40)),('Fire','uitx_icon_us.ppt',(444,0,476,32)),('Water','uitx_icon_us.ppt',(444,32,476,64)),('Wind','uitx_icon_us.ppt',(444,64,476,96)),('Earth','uitx_icon_us.ppt',(444,96,476,128))]
sha=lambda b:hashlib.sha256(b).hexdigest()
def extract():
 rows=json.loads((ROOT/'work/source/oreshika-textures/inventory.json').read_text());sheets={};sources={};glyphs={};crops=[]
 with SOURCE.open('rb') as f:
  for stat,file,box in SPECS:
   if file not in sheets:
    row=next(x for x in rows if x['name']==file);f.seek(row['member_offset']);packed=f.read(row['size']);gxt,compression=unpack_member(packed);im,info=decode(gxt);sheets[file]=im
    sources[file]=dict(**row,packed_sha256=sha(packed),gxt_sha256=sha(gxt),decoded_rgba_sha256=sha(im.tobytes()),archive_compression=compression,**info)
   glyph=sheets[file].crop(box);glyphs[stat]=glyph
   crops.append(dict(symbol=stat,sheet=file,crop=list(box),width=glyph.width,height=glyph.height,rgba_sha256=sha(glyph.tobytes()),alpha='Original native BC3 alpha, no screenshot mask or redraw',resampled=False))
 return glyphs,sheets,dict(source='User-supplied Oreshika Tainted Bloodlines (USA), PCSA00155',archive_bytes=SOURCE.stat().st_size,source_archive='work/source/vita3k-icons-profile/ux0/app/PCSA00155/data.img',native_sheets=sources,icons=crops)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();glyphs,sheets,r=extract();print(json.dumps(dict(write=a.write,**r),indent=2))
 if not a.write:return
 out=ROOT/'incoming/oreshika-native-icons';out.mkdir(exist_ok=True);ui=ROOT/'work/ui/native-icons-0.2.31';ui.mkdir(parents=True,exist_ok=True)
 sheet=Image.new('RGBA',(7*144,176),(45,45,50,255));d=ImageDraw.Draw(sheet)
 for i,(stat,im) in enumerate(glyphs.items()):
  im.save(out/(stat.lower()+'.png'));large=im.resize((112,112),Image.Resampling.NEAREST);sheet.alpha_composite(large,(i*144+16,12));d.text((i*144+48,140),stat,fill='white')
 sheet.save(ui/'source-icons.png');(out/'provenance.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');(ui/'source.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 print('Native crops written; game builds unchanged.')
if __name__=='__main__':main()

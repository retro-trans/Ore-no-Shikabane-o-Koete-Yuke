"""Inspect supplied Oreshika UI sheets for category symbols; dry run first."""
import argparse,json,hashlib
from PIL import Image,ImageDraw
from catalog_text import ROOT,unpack_member
from decode_vita_gxt import decode
from extract_oreshika_icon_sheets import SOURCE
NAMES=['uitx_common0_us.ppt','uitx_show_us.ppt','uitx_show2_us.ppt','uitx_kochin_us.ppt','uitx_kochin2_us.ppt','uitx_window_spirit.ppt']
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();rows=json.loads((ROOT/'work/source/oreshika-textures/inventory.json').read_text());report=[];images=[]
with SOURCE.open('rb') as f:
 for name in NAMES:
  row=next(x for x in rows if x['name']==name);f.seek(row['member_offset']);b=f.read(row['size']);gxt,_=unpack_member(b)
  try:im,meta=decode(gxt)
  except (AssertionError,KeyError) as error:report.append(dict(name=name,not_decoded=str(error)));continue
  report.append(dict(name=name,packed_sha256=hashlib.sha256(b).hexdigest(),**meta));images.append((name,im))
print(json.dumps(dict(write=a.write,sheets=report),indent=2))
if a.write:
 out=ROOT/'work/ui/status-layout-0.2.35';out.mkdir(parents=True,exist_ok=True);canvas=Image.new('RGBA',(3*360,2*390),(35,35,40,255));d=ImageDraw.Draw(canvas)
 for i,(name,im) in enumerate(images):
  x,y=(i%3)*360,(i//3)*390;d.text((x+6,y+4),name,fill='white');im.thumbnail((350,355));canvas.alpha_composite(im,(x+4,y+25))
 canvas.save(out/'oreshika-additional-sheets.png');(out/'oreshika-audit.json').write_text(json.dumps(report,indent=2)+'\n')

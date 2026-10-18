"""Find native UI artwork requiring HD text. Read-only unless --write."""
import argparse,json,re
from PIL import Image,ImageDraw
from catalog_text import ROOT,unpack_member
from inspect_native_textures import decode
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
rows=[];images=[]
with (ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').open('rb') as f:
    for r in json.loads((ROOT/'work/source/archive_inventory.json').read_text()):
        name=r['name']
        if not name.endswith('.ppt') or name.startswith(('ps_','pm_','pb_','pj_')):continue
        f.seek(r['member_offset']);b,_=unpack_member(f.read(r['size']))
        try:im,info=decode(b)
        except (ValueError,AssertionError):continue
        w,h=im.size;ribbon=(w,h)==(48,264)
        small=(h<=48 and w>=32 and not re.match(r'^[FMS]\d',name))
        if not (ribbon or small):continue
        key='%08x-%04d'%(r['archive_offset'],r['entry'])
        rows.append(dict(key=key,name=name,archive_offset=r['archive_offset'],entry=r['entry'],**info));images.append(im)
print(json.dumps(dict(selected=len(rows),ribbons=sum(r['height']==264 for r in rows),samples=rows[:8],write=a.write),indent=2))
if a.write:
    out=ROOT/'work/ui/hd-fonts-0.2.26/source-audit';out.mkdir(parents=True,exist_ok=True)
    (out/'inventory.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    for n in range(0,len(rows),60):
        sheet=Image.new('RGB',(1100,((min(60,len(rows)-n)+3)//4)*94),(42,42,42));d=ImageDraw.Draw(sheet)
        for j,(r,im) in enumerate(zip(rows[n:n+60],images[n:n+60])):
            im.save(out/(r['key']+'.png'));thumb=im.copy()
            if r['height']==264:thumb=thumb.transpose(Image.Transpose.ROTATE_90)
            thumb.thumbnail((265,66));x=(j%4)*275;y=(j//4)*94
            d.text((x+2,y+2),r['key']+' '+r['name'][:19],fill='white');sheet.paste(thumb,(x,y+23),thumb)
        sheet.save(out/('sheet-%03d.png'%n))

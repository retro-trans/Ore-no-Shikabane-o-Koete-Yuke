"""Translate the shop and twelve month ribbons within their original loader budgets."""
import argparse,calendar,hashlib,json,struct
from PIL import Image,ImageDraw
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from build_hd_ui import ribbon_image
from repack_text import root_entries,rebuild_ez,rebuild_root
from hd_sprites import encode,patch,BIND,RECT

V='0.2.32'
SPECS=[(51,'258.ppt','HERBAL MEDICINE','Medicine shop')]+[(34+n,str(241+n)+'.ppt',calendar.month_name[n].upper(),'Calendar month '+str(n)) for n in range(1,13)]
sha=lambda b:hashlib.sha256(b).hexdigest()

def build():
 src=ROOT/'work/output/english-native-0.2.31';source=(src/'EBOOT.icons.elf').read_bytes();data=(src/'data.icons.ore').read_bytes()
 assert sha(source)=='332a8bf34497de3bf64bf0680e271507f42a52515ba985e08e0fe0b6e699416f'
 assert sha(data)=='4214f181273374ce6be74c3143fb764b87795a4ee5f4cbd127b8472de7a4797c'
 # Add tagged 4-bit support so the original resource slots can hold 2x-wide
 # pixels. Existing 8-bit images retain the same binding and crop semantics.
 hd=json.loads((ROOT/'work/output/english-native-0.2.26/hd.report.json').read_text());reset=bytearray(source)
 for h in hd['renderer']['hooks']:
  addr=int(h['address'],16);off=addr-0x08803000;target=int(h['wrapper'],16)
  assert struct.unpack_from('<2I',source,off)==(0x08000000|(target>>2),0)
  struct.pack_into('<2I',reset,off,*h['before'])
 elf,renderer=patch(bytes(reset));phoff=struct.unpack_from('<I',source,28)[0];allowed=set(range(phoff+48,phoff+56))
 for addr in (BIND,RECT):allowed.update(range(addr-0x08803000,addr-0x08803000+8))
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data)
 rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe};base=rootmap[0xb4a800];arc,en=container(data,base);oa,oen=container(original,0xb4a800)
 inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text());assets={};images={};rows=[]
 for entry,name,text,context in SPECS:
  assert any(r['archive_offset']==0xb4a800 and r['entry']==entry and r['name']==name for r in inv)
  old=member(arc,en,entry);assert old==member(oa,oen,entry)
  image,typography=ribbon_image(old,text);image=image.resize((96,264),Image.Resampling.LANCZOS)
  ppt,actual,hd=encode(old,image,pixel_format=4);assert len(ppt)==len(old)==13744
  assert hd['logical_size']==[44,260] and hd['physical_visible_size']==[88,260]
  assets[entry]=pack(ppt);images[name]=actual
  rows.append(dict(file=name,archive_offset=0xb4a800,member_entry=entry,translation_en=text,context=context,pixel_format=4,palette_colors=16,resource_bytes=len(ppt),original_bytes=len(old),**typography,**hd))
 updates={base:rebuild_ez(arc,assets)};changed={base:set(assets)}
 tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000);f,fp,fr=footer(member(ot,ote,25),V);updates[tb]=rebuild_ez(ta,{25:pack(f)});changed[tb]={25};del original
 ore=rebuild_root(data,updates,mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in updates:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j not in changed[a[3]]:assert aa[x:x+z]==bb[xx:xx+zz]
 report=dict(version=V,source_version='0.2.31',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),resident_added_bytes=len(elf)-len(source),graphics=rows,renderer=renderer,footer=fr,checks=dict(existing_executable_bytes='Only two renderer redirects and appended segment size change; small replacement wrappers appended',existing_icons_and_profile_fix='Byte-identical to 0.2.31',other_archive_members='Byte-identical except title version footer',translations_and_scripts='Byte-identical to 0.2.31',resource_loader_sizes='All thirteen retain exactly 13744 decompressed bytes',calendar_logic='Unchanged; all twelve existing month images translated',background_shop_sign='Unchanged'),texture_replacement=False,runtime_verification='pending')
 return elf,ore,images,fp,report

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,images,fp,r=build()
 summary={k:v for k,v in r.items() if k not in ('footer','graphics')};summary['graphics']=[{k:x[k] for k in ('file','translation_en','logical_size','physical_storage_size','resource_bytes')} for x in r['graphics']];print(json.dumps(summary,indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.banners.elf').exists();(out/'EBOOT.banners.elf').write_bytes(elf);(out/'data.banners.ore').write_bytes(ore);(out/'banners.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/('work/ui/left-banners-'+V);ui.mkdir(parents=True,exist_ok=True)
  sheet=Image.new('RGB',(13*106,532),(40,40,45));d=ImageDraw.Draw(sheet)
  for i,(name,im) in enumerate(images.items()):
   im.save(ui/(name+'.png'));small=im.resize((96,512),Image.Resampling.NEAREST);sheet.paste(small,(i*106,20),small);d.text((i*106+1,2),r['graphics'][i]['translation_en'][:15],fill='white')
  sheet.save(ui/'banners-preview.png');fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 print('Written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

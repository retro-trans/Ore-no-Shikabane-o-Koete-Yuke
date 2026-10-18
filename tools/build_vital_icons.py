"""Reuse the user's HP/MP/HLTH artwork in both native badge sizes. Dry run first."""
import argparse,hashlib,json,shutil,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root
from inspect_native_textures import decode
from hd_sprites import encode
V='0.2.29';REF=ROOT/'incoming/vital-icons-reference.png'
CROPS={'HP':(69,209,92,233),'MP':(69,231,92,251),'HLTH':(68,249,93,273)}
FILES={'11.ppt':'HP','107.ppt':'HP','12.ppt':'MP','108.ppt':'MP','13.ppt':'HLTH','113.ppt':'HLTH'}
sha=lambda b:hashlib.sha256(b).hexdigest()

def extract(ref,stat):
 box=CROPS[stat];raw=ref.crop(box).convert('RGBA');a=np.array(raw).astype(float);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
 key=((r>85)&(r>g*1.3)&(r>b*1.3)) if stat=='HP' else (((b>80)&(g>65)&(b>r*1.3)&(b>g*.9)) if stat=='MP' else ((g>90)&(g>r*1.3)&(g>b*1.15)))
 seen=set();components=[]
 for y,x in zip(*np.where(key)):
  if (int(y),int(x)) in seen:continue
  todo=[(int(y),int(x))];group=[];seen.add(todo[0])
  while todo:
   yy,xx=todo.pop();group.append((yy,xx))
   for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
    ny,nx=yy+dy,xx+dx
    if 0<=ny<key.shape[0] and 0<=nx<key.shape[1] and key[ny,nx] and (ny,nx) not in seen:seen.add((ny,nx));todo.append((ny,nx))
  components.append(group)
 group=max(components,key=len);assert len(group)>35,(stat,len(group));mask=np.zeros(key.shape,dtype=np.uint8)
 for y,x in group:mask[y,x]=255
 mask=Image.fromarray(mask).filter(ImageFilter.MaxFilter(3));padded=Image.new('L',(mask.width+4,mask.height+4));padded.paste(mask,(2,2));ImageDraw.floodfill(padded,(0,0),128)
 z=np.array(padded);z[z==0]=255;z[z==128]=0;mask=Image.fromarray(z).crop((2,2,mask.width+2,mask.height+2))
 # Retain the matching symbol and its dark outline, excluding adjacent skin
 # or hair reached by the one-pixel outline expansion.
 opacity=np.array(mask);opacity[(~key)&(a[:,:,:3].max(axis=2)>=85)]=0;mask=Image.fromarray(opacity);raw.putalpha(mask)
 bounds=mask.getbbox();assert bounds;glyph=raw.crop(bounds)
 return glyph,dict(source_region=box,source_ink_bounds=[box[0]+bounds[0],box[1]+bounds[1],box[0]+bounds[2],box[1]+bounds[3]],source_glyph_size=glyph.size,colored_pixels=len(group))

def build(reference):
 src=ROOT/'work/output/english-native-0.2.28';source=(src/'EBOOT.elements.elf').read_bytes();data=(src/'data.elements.ore').read_bytes()
 assert sha(source)=='dc9d35f8f17ccaa7e09a553925db7064f5eaf14b2bdc6a17384378ae169a3cef'
 assert sha(data)=='21c29baa28c2ffcc106948a68425a4d47f4211d43bb34ee345caa78cbebb06ab'
 assert sha(reference.read_bytes())=='0864dbb2a2cadeb3bd3f822f074b1336c5fc365d5fb3f78a8fa60cf80e0ac734'
 ref=Image.open(reference).convert('RGB');assert ref.size==(960,544);glyphs={};extraction={}
 for stat in CROPS:glyphs[stat],extraction[stat]=extract(ref,stat)
 oldhd=json.loads((ROOT/'work/output/english-native-0.2.26/hd.report.json').read_text());lookup={g['file']:(g,d) for g,d in zip(oldhd['graphics'],oldhd['renderer']['embedded_descriptors']) if g['archive_offset']==0x36000}
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();arc,en=container(original,0x36000);inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text())
 elf=bytearray(source);p=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,p+32);offset=lambda a:ph[1]+a-ph[2]
 rows=[];allowed=set();previews={}
 for file,stat in FILES.items():
  entry=next(r['entry'] for r in inv if r['archive_offset']==0x36000 and r['name']==file);old=member(arc,en,entry);_,info=decode(old);lw,lh=info['logical_width'],info['logical_height'];assert lw in (24,32) and lh==16
  layer=Image.new('RGBA',(info['width']*4,info['height']*4))
  scale=56/max(glyphs[stat].size);size=tuple(max(1,round(x*scale)) for x in glyphs[stat].size);glyph=glyphs[stat].resize(size,Image.Resampling.LANCZOS)
  layer.alpha_composite(glyph,((lw*4-glyph.width)//2,(lh*4-glyph.height)//2));ppt,actual,hd=encode(old,layer);po=struct.unpack_from('<I',ppt,24)[0]
  oldrow,desc=lookup[file];off=offset(desc);pixels,palette=struct.unpack_from('<2I',source,off+32);assert source[off+4:off+20]==ppt[4:20]
  for addr,new in [(pixels,ppt[32:po]),(palette+16,ppt[po+16:po+1040])]:
   at=offset(addr);elf[at:at+len(new)]=new;allowed.update(range(at,at+len(new)))
  rows.append(dict(stat=stat,file=file,archive_offset=0x36000,member_entry=entry,descriptor=hex(desc),pixels=hex(pixels),palette=hex(palette),pixel_bytes=po-32,**hd))
  previews[file]=actual
 assert len(elf)==len(source) and all(x==y or i in allowed for i,(x,y) in enumerate(zip(source,elf)))
 oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe};tb=rootmap[0x1e8000];ta,te=container(data,tb);oa,ote=container(original,0x1e8000);f,fp,fr=footer(member(oa,ote,25),V)
 ore=rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(f)})},mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3]!=tb:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j!=25:assert aa[x:x+z]==bb[xx:xx+zz]
 report=dict(version=V,source_version='0.2.28',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),reference=dict(file='incoming/vital-icons-reference.png',sha256=sha(reference.read_bytes()),dimensions=ref.size,source='User-provided Oreshika screenshot; exact symbol pixels reused'),extraction=extraction,icons=rows,footer=fr,checks=dict(existing_code_and_descriptors='Byte-identical',other_executable_bytes='Only six embedded palettes/pixel payloads changed',archive_members='Byte-identical except version footer',scripts_and_text_tables='Byte-identical to 0.2.28',geometry='Original 24x16 and32x16 logical bounds; symbol aspect preserved',native_renderer='Existing hooks reused',previous_element_icons='Byte-identical'),texture_replacement=False,runtime_verification='pending')
 return elf,ore,previews,glyphs,fp,report

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reference',default=str(REF));ap.add_argument('--preview',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args();reference=ROOT/a.reference;elf,ore,images,glyphs,fp,r=build(reference)
 print(json.dumps({k:v for k,v in r.items() if k!='footer'},indent=2))
 if a.preview or a.write:
  ui=ROOT/('work/ui/vital-icons-'+V);ui.mkdir(parents=True,exist_ok=True);sheet=Image.new('RGB',(384,128),(45,45,50));d=ImageDraw.Draw(sheet)
  for i,stat in enumerate(CROPS):
   im=images[{'HP':'107.ppt','MP':'108.ppt','HLTH':'113.ppt'}[stat]];sheet.paste(im,(i*128,8),im);d.text((i*128+54,92),stat,fill='white');glyphs[stat].save(ui/(stat.lower()+'-source.png'))
  for file,im in images.items():im.save(ui/(file+'.png'))
  sheet.save(ui/'icons-preview.png');fp.save(ui/'native-footer.png')
  if not REF.exists():shutil.copyfile(reference,REF)
  assert sha(REF.read_bytes())==r['reference']['sha256'];(ui/'layout.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.vitals.elf').exists();(out/'EBOOT.vitals.elf').write_bytes(elf);(out/'data.vitals.ore').write_bytes(ore);(out/'vitals.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 print('Build written.' if a.write else ('Previews written; game files unchanged.' if a.preview else 'DRY RUN: no files written.'))
if __name__=='__main__':main()

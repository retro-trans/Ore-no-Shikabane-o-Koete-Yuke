"""Reuse the user's four reference element icons in native shared sprites. Dry run first."""
import argparse,hashlib,json,shutil,struct
import numpy as np
from PIL import Image,ImageDraw
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root,align
from inspect_native_textures import decode
from hd_sprites import encode,proxy
V='0.2.28';REF=ROOT/'incoming/element-icons-reference.png'
SPECS=[('Fire','17.ppt',(75,280,107,312)),('Water','18.ppt',(75,348,107,380)),('Wind','19.ppt',(75,382,107,414)),('Earth','20.ppt',(75,314,107,346))]
sha=lambda b:hashlib.sha256(b).hexdigest()

def build(reference):
 source=(ROOT/'work/output/english-native-0.2.27/EBOOT.screens.elf').read_bytes();data=(ROOT/'work/output/english-native-0.2.27/data.screens.ore').read_bytes()
 assert sha(source)=='a26d9e355a5055ec8dd9c8cb7fdde724b5b47900b423564d08c20dbf471fd03f'
 assert sha(data)=='2b4a5ab7cb64132d489afc2f47015f23d6df8d560f1d24198625d0dd488aa6bd'
 ref=Image.open(reference).convert('RGB');assert ref.size==(960,544)
 assert sha(reference.read_bytes())=='6811954156be6632cd41bc19ee796c2119ed331fdc6d64fcd99e4f1fef35ffd6'
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe}
 inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text());base=rootmap[0x36000];arc,en=container(data,base);assets={};images={};rows=[]
 elf=bytearray(source);p=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,p+32));assert ph[1]+ph[4]==len(elf)
 def reserve(b):
  elf.extend(bytes(align(len(elf),16)-len(elf)));addr=ph[2]+len(elf)-ph[1];elf.extend(b);return addr
 for name,file,box in SPECS:
  row=next(r for r in inv if r['archive_offset']==0x36000 and r['name']==file);old=member(arc,en,row['entry']);_,info=decode(old);assert (info['logical_width'],info['logical_height'])==(16,14)
  crop=ref.crop(box).convert('RGBA');mask=Image.new('L',(128,128));d=ImageDraw.Draw(mask)
  d.polygon([(x*4,y*4) for x,y in [(8,1),(24,1),(32,16),(24,31),(8,31),(0,16)]],fill=255)
  crop.putalpha(mask.resize((32,32),Image.Resampling.LANCZOS))
  sprite=Image.new('RGBA',(64,64));sprite.alpha_composite(crop.resize((56,56),Image.Resampling.LANCZOS),(4,0));ppt,actual,hd=encode(old,sprite);po=struct.unpack_from('<I',ppt,24)[0]
  desc=reserve(bytes(48));palette=reserve(ppt[po:po+1040]);pixels=reserve(ppt[32:po]);off=desc-ph[2]+ph[1];head=bytearray(32);head[4:20]=ppt[4:20];tw,th=struct.unpack_from('<2H',head,4);head[28:30]=bytes([tw.bit_length()-1,th.bit_length()-1]);elf[off:off+32]=head
  struct.pack_into('<III',elf,off+32,pixels,palette,pixels);struct.pack_into('<I',elf,palette-ph[2]+ph[1]+8,palette+16)
  replacement=proxy(old,desc);assert len(replacement)==len(old);assets[row['entry']]=pack(replacement)
  a=np.array(ref.crop(box)).astype(float);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
  color=((r>110)&(r>g*1.5)&(r>b*1.5)) if name=='Fire' else (((g>85)&(b>110)&(r<g*.7)) if name=='Water' else (((g>110)&(g>r*1.5)&(g>b*1.2)) if name=='Wind' else ((r>120)&(g>100)&(b<g*.5))))
  yy,xx=np.where(color);bounds=[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())];assert color.sum()>50
  rows.append(dict(element=name,file=file,archive_offset=0x36000,member_entry=row['entry'],source_crop=box,source_ink_bounds=bounds,descriptor=hex(desc),palette=hex(palette),pixels=hex(pixels),proxy_bytes=len(replacement),source_bytes=len(old),**hd))
  images[name.lower()]=actual
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,p+32,*ph)
 allowed=set(range(p+48,p+56));assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 updates={base:rebuild_ez(arc,assets)};changed={base:set(assets)}
 tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000);f,fp,fr=footer(member(ot,ote,25),V);updates[tb]=rebuild_ez(ta,{25:pack(f)});changed[tb]={25}
 ore=rebuild_root(data,updates,mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in updates:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j not in changed[a[3]]:assert aa[x:x+z]==bb[xx:xx+zz]
 report=dict(version=V,source_version='0.2.27',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),reference=dict(file='incoming/element-icons-reference.png',sha256=sha(reference.read_bytes()),dimensions=ref.size,source='User-provided Oreshika reference screenshot; icon pixels reused'),elements=rows,footer=fr,checks=dict(existing_executable_bytes='Byte-identical except appended segment size',other_archive_members='Byte-identical',scripts_and_text='Byte-identical to 0.2.27',proxy_loader_sizes='Original byte size retained',geometry='Original 16x14 logical bounds retained; square artwork fits without distortion',existing_native_hooks='Reused without code changes'),texture_replacement=False,runtime_verification='pending')
 return elf,ore,images,fp,report

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reference',type=str,default=str(REF));ap.add_argument('--preview',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args();reference=ROOT/a.reference;elf,ore,images,fp,r=build(reference)
 print(json.dumps({k:v for k,v in r.items() if k!='footer'},indent=2))
 if a.preview or a.write:
  ui=ROOT/('work/ui/element-icons-'+V);ui.mkdir(parents=True,exist_ok=True);sheet=Image.new('RGB',(512,150),(45,45,50));d=ImageDraw.Draw(sheet)
  for i,(name,im) in enumerate(images.items()):
   im.save(ui/(name+'.png'));sheet.paste(im,(i*128+32,30),im);d.text((i*128+44,108),name.title(),fill='white')
  sheet.save(ui/'icons-preview.png');fp.save(ui/'native-footer.png')
  if not REF.exists():shutil.copyfile(reference,REF)
  assert sha(REF.read_bytes())==r['reference']['sha256']
  (ui/'layout.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.elements.elf').exists()
  (out/'EBOOT.elements.elf').write_bytes(elf);(out/'data.elements.ore').write_bytes(ore);(out/'elements.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 print('Build written.' if a.write else ('Previews written; game files unchanged.' if a.preview else 'DRY RUN: no files written.'))
if __name__=='__main__':main()

"""Enclose profile traits and give Potential labels their own column. Dry run first."""
import argparse,hashlib,json,struct
from PIL import Image,ImageDraw
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root
from inspect_native_textures import decode
from hd_sprites import encode
V='0.2.35';BASE=0x08803000
sha=lambda b:hashlib.sha256(b).hexdigest()
def build():
 src=ROOT/'work/output/english-native-0.2.34';source=(src/'EBOOT.catalog.elf').read_bytes();data=(src/'data.catalog.ore').read_bytes()
 assert sha(source)=='81ecabe4a711085e0aa9ab23e87afa1153fda66c226b836380f4686c846ce737'
 assert sha(data)=='34ce60c416a63d8a3240189eaf63ab786d132fd89e3d7f979e30b107998ef443'
 elf=bytearray(source);po=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,po+32);allowed=set();patches=[]
 def off(addr):return addr-BASE if addr<ph[2] else ph[1]+addr-ph[2]
 def raw(addr,old,new,note):
  p=off(addr);assert elf[p:p+len(old)]==old,hex(addr);assert len(old)==len(new);elf[p:p+len(new)]=new;allowed.update(range(p,p+len(new)));patches.append(dict(address=hex(addr),before=old.hex(),after=new.hex(),purpose=note))
 def word(addr,old,new,note):raw(addr,struct.pack('<I',old),struct.pack('<I',new),note)
 for addr in (0x089476ac,0x08947fd0):word(addr,0x24060050,0x2406006c,'Status and Abilities use the 108-pixel equipment frame, enclosing both trait lines')
 word(0x08946044,0x34068000,0x34068001,'Draw character header and its owned trait above the enlarged stats background')
 word(0x0894649c,0x34068000,0x34068001,'Use the same header layer in the second character-screen constructor')
 word(0x088f1d8c,0x24050016,0x24050028,'Potential gold axis x22 to x40, beyond group captions')
 word(0x088f1f5c,0x24050002,0x24050004,'Potential captions inset four pixels inside the frame')
 word(0x088f1ed0,0x24050024,0x2405002c,'Element column x44 beyond caption/axis')
 word(0x088f1e90,0x24050036,0x2405003e,'Potential bars begin at x62 beside element icons')
 raw(0x08a39b30,struct.pack('<f',86),struct.pack('<f',76),'Display-only maximum bar width: 76 pixels, right edge x138 inside frame')
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();arc,en=container(original,0x36000);blob=member(arc,en,19);im,info=decode(blob);layer=im.resize((576,1024),Image.Resampling.NEAREST);d=ImageDraw.Draw(layer);s=4
 d.rectangle((4*s,14*s,137*s,247*s),fill=(0,0,0,255))
 for x in (61,80,99,118,138):d.line((x*s,30*s,x*s,244*s),fill=(46,46,46,255),width=s)
 for y in (99,173):d.line((61*s,y*s,138*s,y*s),fill=(46,46,46,255),width=s)
 ppt,preview,hd=encode(blob,layer.resize((512,512),Image.Resampling.LANCZOS));paloff=struct.unpack_from('<I',ppt,24)[0];oldr=json.loads((ROOT/'work/output/english-native-0.2.27/screens.report.json').read_text());desc=int(oldr['potential_image']['descriptor'],16);pixels,palette=struct.unpack_from('<2I',source,off(desc)+32)
 assert source[off(desc)+4:off(desc)+20]==ppt[4:20]
 for addr,b in [(pixels,ppt[32:paloff]),(palette+16,ppt[paloff+16:paloff+1040])]:raw(addr,source[off(addr):off(addr)+len(b)],b,'Align native Potential grid with the shifted bar origin; preserve sprite allocation and descriptor')
 assert len(elf)==len(source) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe};tb=rootmap[0x1e8000];ta,te=container(data,tb);oa,ote=container(original,0x1e8000);f,fp,fr=footer(member(oa,ote,25),V);del original
 ore=rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(f)})},mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3]!=tb:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j!=25:assert aa[x:x+z]==bb[xx:xx+zz]
 r=dict(version=V,source_version='0.2.34',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,grid=dict(descriptor=hex(desc),pixels=hex(pixels),palette=hex(palette),**hd),layout=dict(stats_frame=[60,142,260,108],trait=[70,229],trait_second_line_y=243,equipment_frame_height=108,potential=dict(frame_width=142,caption_x=4,axis_x=40,element_x=44,bar_x=62,bar_max_width=76,right_edge=138,grid_x=[61,80,99,118,138])),source_icons='No dedicated Spirit/Skill/Body pictograms identified in inspected Oreshika US common/status/icon sheets; readable full category captions retained',checks=dict(other_executable_bytes='Only guarded frame/layout coordinates, display scale and existing grid pixels/palette',archive_members='Byte-identical except version footer',traits_and_stat_values='Byte-identical; formatting, wrapping, getters and save data unchanged',previous_icons_and_catalog_fixes='Byte-identical',elf_memory_footprint='Unchanged'),footer=fr,texture_replacement=False,runtime_verification='pending')
 return elf,ore,preview,fp,r
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,preview,fp,r=build();brief={k:v for k,v in r.items() if k!='footer'};brief['patches']=[{k:v for k,v in p.items() if k not in ('before','after')} for p in r['patches']];print(json.dumps(brief,indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.status.elf').exists();(out/'EBOOT.status.elf').write_bytes(elf);(out/'data.status.ore').write_bytes(ore);(out/'status.report.json').write_text(json.dumps(r,indent=2)+'\n');ui=ROOT/('work/ui/status-layout-'+V);ui.mkdir(exist_ok=True);preview.save(ui/'native-potential.png');fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r['layout'],indent=2)+'\n')
 print('Written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

"""Replace screenshot copies with seven native Oreshika icon designs. Dry run first."""
import argparse,hashlib,json,struct
from PIL import Image,ImageDraw
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root
from inspect_native_textures import decode
from hd_sprites import encode
from extract_oreshika_icon_sheets import extract
V='0.2.31';FILES={'11.ppt':'HP','107.ppt':'HP','12.ppt':'MP','108.ppt':'MP','13.ppt':'HLTH','113.ppt':'HLTH','17.ppt':'Fire','18.ppt':'Water','19.ppt':'Wind','20.ppt':'Earth'}
sha=lambda b:hashlib.sha256(b).hexdigest()
def build():
 src=ROOT/'work/output/english-native-0.2.30';source=(src/'EBOOT.traits.elf').read_bytes();data=(src/'data.traits.ore').read_bytes()
 assert sha(source)=='9f303fd005662bd157a9c88e9c28da642646bca66b3adfe5feb6e82b9f79f04b'
 assert sha(data)=='be62c63473110ac34a2a693b3da0692bf459b28d17b0dbdc6af2bd07fe2777c4'
 glyphs,sheets,provenance=extract();stored=json.loads((ROOT/'incoming/oreshika-native-icons/provenance.json').read_text());assert provenance==stored
 for stat,im in glyphs.items():assert Image.open(ROOT/('incoming/oreshika-native-icons/'+stat.lower()+'.png')).tobytes()==im.tobytes()
 oldhd=json.loads((ROOT/'work/output/english-native-0.2.26/hd.report.json').read_text());lookup={g['file']:d for g,d in zip(oldhd['graphics'],oldhd['renderer']['embedded_descriptors']) if g['archive_offset']==0x36000}
 oldel=json.loads((ROOT/'work/output/english-native-0.2.28/elements.report.json').read_text());lookup.update({g['file']:int(g['descriptor'],16) for g in oldel['elements']})
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();arc,en=container(original,0x36000);inv=json.loads((ROOT/'work/source/archive_inventory.json').read_text())
 elf=bytearray(source);p=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,p+32);offset=lambda a:ph[1]+a-ph[2];allowed=set();rows=[];previews={}
 for file,stat in FILES.items():
  entry=next(r['entry'] for r in inv if r['archive_offset']==0x36000 and r['name']==file);old=member(arc,en,entry);_,info=decode(old);lw,lh=info['logical_width'],info['logical_height'];assert (lw,lh) in [(24,16),(32,16),(16,14)]
  layer=Image.new('RGBA',(info['width']*4,info['height']*4));glyph=glyphs[stat].resize((56,56),Image.Resampling.LANCZOS);xy=((lw*4-56)//2,(lh*4-56)//2);layer.alpha_composite(glyph,xy)
  ppt,actual,hd=encode(old,layer);po=struct.unpack_from('<I',ppt,24)[0];desc=lookup[file];off=offset(desc);pixels,palette=struct.unpack_from('<2I',source,off+32);assert source[off+4:off+20]==ppt[4:20]
  for addr,new in [(pixels,ppt[32:po]),(palette+16,ppt[po+16:po+1040])]:
   at=offset(addr);elf[at:at+len(new)]=new;allowed.update(range(at,at+len(new)))
  rows.append(dict(stat=stat,file=file,archive_offset=0x36000,member_entry=entry,descriptor=hex(desc),pixels=hex(pixels),palette=hex(palette),pixel_bytes=po-32,source_sheet=next(x['sheet'] for x in provenance['icons'] if x['symbol']==stat),native_crop=next(x['crop'] for x in provenance['icons'] if x['symbol']==stat),physical_icon_box=[xy[0],xy[1],xy[0]+56,xy[1]+56],**hd));previews[file]=actual
 assert len(elf)==len(source) and all(x==y or i in allowed for i,(x,y) in enumerate(zip(source,elf)))
 oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe};tb=rootmap[0x1e8000];ta,te=container(data,tb);oa,ote=container(original,0x1e8000);f,fp,fr=footer(member(oa,ote,25),V);del original
 ore=rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(f)})},mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3]!=tb:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j!=25:assert aa[x:x+z]==bb[xx:xx+zz]
 report=dict(version=V,source_version='0.2.30',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),source=provenance,icons=rows,footer=fr,checks=dict(native_code_and_descriptors='Byte-identical',other_executable_bytes='Only ten embedded palette/pixel payloads changed',archive_members='Byte-identical except version footer',translations_and_scripts='Byte-identical to 0.2.30',profile_trait_fix='Byte-identical to 0.2.30',logical_geometry='Original compact, standard and element bounds retained'),texture_replacement=False,runtime_verification='pending')
 return elf,ore,previews,fp,report
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,images,fp,r=build();print(json.dumps({k:v for k,v in r.items() if k not in ('footer','source')},indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.icons.elf').exists();(out/'EBOOT.icons.elf').write_bytes(elf);(out/'data.icons.ore').write_bytes(ore);(out/'icons.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/('work/ui/native-icons-'+V);ui.mkdir(parents=True,exist_ok=True)
  for file,im in images.items():im.save(ui/(file+'.png'))
  fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 print('Written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

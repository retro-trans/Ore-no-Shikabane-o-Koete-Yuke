"""Translate status badges and separate detailed-roster equipment. Dry run unless --write."""
import argparse,hashlib,json,struct
from catalog_text import ROOT
from build_shop_layout import stat_icon
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root
VERSION='0.2.22';BASE=0x08803000
TEXT_BEFORE=[(155,5),(155,23),(290,5),(290,23)]
TEXT_AFTER=[(192,1),(192,16),(192,31),(192,46)]
ICONS_BEFORE=[(128,125,5),(129,125,23),(130,260,5),(131,260,23)]
ICONS_AFTER=[(128,160,0),(129,160,15),(130,160,30),(131,160,45)]
STATS_TEXT_BEFORE=[(198,5),(231,5),(198,23),(231,23),(308,5),(308,23),(383,5),(383,23),(383,41),(248,41),(308,41)]
STATS_TEXT_AFTER=[(225,5),(260,5),(225,23),(260,23),(325,5),(325,23),(392,5),(392,23),(392,41),(248,41),(325,41)]
STATS_ICONS_BEFORE=[(107,125,5),(108,125,23),(114,240,5),(113,240,23),(109,315,5),(110,315,23),(111,315,41)]
STATS_ICONS_AFTER=[(107,154,5),(108,154,23),(114,267,5),(113,267,23),(109,332,5),(110,332,23),(111,332,41)]
def sha(b):return hashlib.sha256(b).hexdigest()
def build():
 source=(ROOT/'work/output/english-native-0.2.21/EBOOT.character.elf').read_bytes();data=(ROOT/'work/output/english-native-0.2.21/data.character.ore').read_bytes()
 assert sha(source)=='136e36198be6364d30c7f4553ffe20e492919ef1e8b4096c9059000bbe8a2ed8'
 assert sha(data)=='ff32d7a24f18693ae82749ad7d2de096ca8e5c673922fd002b805837867da615'
 elf=bytearray(source);patches=[];allowed=set()
 for addr,old,new,label in [(0x08b2a348,TEXT_BEFORE,TEXT_AFTER,'Four separate full-name equipment rows'),(0x08b2a368,ICONS_BEFORE,ICONS_AFTER,'Slot labels aligned with their equipment names'),(0x08b2a188,STATS_TEXT_BEFORE,STATS_TEXT_AFTER,'Status values clear of eight-character names'),(0x08b2a1e0,STATS_ICONS_BEFORE,STATS_ICONS_AFTER,'Separate status badge columns')]:
  a=struct.pack('<'+'i'*sum(map(len,old)),*(x for row in old for x in row));b=struct.pack('<'+'i'*sum(map(len,new)),*(x for row in new for x in row));off=addr-BASE
  assert elf[off:off+len(a)]==a,(hex(addr),elf[off:off+len(a)].hex());elf[off:off+len(a)]=b;allowed.update(range(off,off+len(a)));patches.append(dict(address=hex(addr),before=a.hex(),after=b.hex(),purpose=label))
 assert len(elf)==len(source) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(n[3] for n in be if n[0]==i) for i,_,_,o in oe}
 base=rootmap[0x36000];a,e=container(data,base);updates={};assets={};graphics=[];previews={}
 for i,label in [(10,'HP'),(17,'HLTH'),(18,'LOY')]:
  b,im=stat_icon(member(a,e,i),label);assets[i]=pack(b);previews[label]=im;graphics.append(dict(archive_offset=0x36000,member_entry=i,file={10:'107.ppt',17:'113.ppt',18:'114.ppt'}[i],translation_en=label,label_rectangle=[0,0,32,16]))
 updates[base]=rebuild_ez(a,assets);changed={base:set(assets)}
 tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000);ppt,im,fr=footer(member(ot,ote,25),VERSION);updates[tb]=rebuild_ez(ta,{25:pack(ppt)});changed[tb]={25};previews['footer']=im
 del original
 ore=rebuild_root(data,updates,mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in updates:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
    if j not in changed[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
 metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];width=lambda t:sum(metrics.get(str(ord(c)),{'advance':14})['advance'] for c in t)*12/14
 rows=[r for p in (ROOT/'work/translation/en').glob('*.en.json') for r in json.loads(p.read_text(encoding='utf-8')).get('rows',[])];equipment=[r for r in rows if r.get('archive_offset')==0x28000 and r.get('member_entry')==0 and r.get('section',0)>=2]
 assert len(equipment)==463 and max(width(r['translation_en']) for r in equipment)<=202.286
 layout=dict(version=VERSION,native_resolution=[480,272],card=dict(width=400,height=61,left=40,name_left=70,name_font_size=14),equipment=dict(text_positions=TEXT_AFTER,slot_positions=ICONS_AFTER,name_budget=208,fixed_names=463,max_fixed_name_width=max(width(r['translation_en']) for r in equipment),row_pitch=15,paging='native; unchanged'),status=dict(text_positions=STATS_TEXT_AFTER,slot_positions=STATS_ICONS_AFTER),badges=dict(HP='Hit points',HLTH='Health',LOY='Loyalty'),retained_labels=['MP','ATK','DEF','AGI','Head','Leader','Party','WPN','HEAD','ARM','ACC'])
 report=dict(version=VERSION,source_version='0.2.21',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,graphics=graphics,layout=layout,footer=fr,checks=dict(native_instructions='unchanged',unrelated_executable_bytes='byte-identical',all_script_payloads='byte-identical',other_archive_members='byte-identical',compression_round_trips='pass'),texture_replacement=False,runtime_verification='pending')
 return bytes(elf),ore,previews,report
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--tag',default='');a=ap.parse_args();elf,ore,previews,r=build();print(json.dumps(r,indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-0.2.22'+a.tag);out.mkdir(parents=True,exist_ok=True);assert not (out/'EBOOT.roster.elf').exists()
  (out/'EBOOT.roster.elf').write_bytes(elf);(out/'data.roster.ore').write_bytes(ore);(out/'roster.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');ui=ROOT/'work/ui/detailed-roster-0.2.22';ui.mkdir(parents=True,exist_ok=True)
  for n,im in previews.items():im.save(ui/('native-'+n+'.png'))
 print('Written.' if a.write else 'DRY RUN: no game changes.')
if __name__=='__main__':main()

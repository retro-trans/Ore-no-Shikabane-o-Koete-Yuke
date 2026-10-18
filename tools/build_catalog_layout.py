"""Fit Item Catalog tabs and totals; dry run before --write."""
import argparse,hashlib,json,struct
from catalog_text import ROOT,parse_mlt
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_mlt,rebuild_root,align
from strip_jp import export
V='0.2.34';BASE=0x08803000
sha=lambda b:hashlib.sha256(b).hexdigest()

def build():
 src=ROOT/'work/output/english-native-0.2.33';source=(src/'EBOOT.chronicle.elf').read_bytes();data=(src/'data.chronicle.ore').read_bytes()
 assert sha(source)=='83677056891403cf743bfef2133b6b1ef3cb9805a9c5f0720ade20b15a40dabb'
 assert sha(data)=='91674c37ee5f284e85371e489b950cd814ed6f933ecddcc69d39571769b4d28a'
 elf=bytearray(source);po=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,po+32));assert ph[1]+ph[4]==len(elf)
 patches=[];allowed=set();literals=[];wrappers=[]
 def word(addr,old,new,note):
  p=addr-BASE;assert struct.unpack_from('<I',elf,p)[0]==old,hex(addr)
  struct.pack_into('<I',elf,p,new);allowed.update(range(p,p+4));patches.append(dict(address=hex(addr),before=hex(old),after=hex(new),purpose=note))
 def imm(addr,reg,old,new,note):word(addr,0x24000000|(reg<<16)|old,0x24000000|(reg<<16)|new,note)
 def append(b):
  elf.extend(bytes(align(len(elf),16)-len(elf)));addr=ph[2]+len(elf)-ph[1];elf.extend(b);return addr
 # Local cText setter: discard only these two Scrolls units, retaining shared item labels.
 empty=append(b'\0\0');fmt=append(b'%d/%d\0')
 def thunk(name,words):
  addr=append(struct.pack('<%dI'%len(words),*words));wrappers.append(dict(name=name,address=hex(addr),words=[hex(w) for w in words]));return addr
 hide=thunk('empty_scrolls_unit',[0x3c050000|((empty+0x8000)>>16),0x24a50000|(empty&65535),0x08000000|(0x0882b49c>>2),0])
 fraction=thunk('scrolls_fraction',[0x3c050000|((fmt+0x8000)>>16),0x24a50000|(fmt&65535),0x08000000|(0x0882b2e0>>2),0x24070049])
 literals=[dict(address=hex(empty),hex_bytes='0000',purpose='Empty localized Scrolls suffix'),dict(address=hex(fmt),hex_bytes=(b'%d/%d\0').hex(),purpose='Current count / total, no spaces or unit')]
 for addr in (0x0894dfbc,):word(addr,0x0c000000|(0x0882b2e0>>2),0x0c000000|(hide>>2),'Hide separate denominator object; fraction is rendered by current-count object')
 word(0x0894e02c,0x0c000000|(0x0882b49c>>2),0x0c000000|(hide>>2),'Remove items only from Scrolls')
 word(0x0894e280,0x0c000000|(0x0882b2e0>>2),0x0c000000|(fraction>>2),'Render acquired and total together as %d/%d, preserving actual acquired count')
 imm(0x0894e298,5,365,400,'Right-align complete Scrolls fraction at x400')
 # This constructor is selected by 0x08963a8c; the other similar constructor is the Sword view.
 for addr,old,new,note in [(0x088e351c,20,16,'Curios heading size'),(0x088e354c,130,120,'Curios heading x'),(0x088e35b0,290,304,'Acquired caption x'),(0x088e3620,390,432,'Curios count right edge'),(0x088e3680,400,442,'Curios items unit x')]:imm(addr,5,old,new,note)
 for addr,old,new in [(0x08943d90,195,375),(0x08943e10,200,380),(0x08944068,195,375),(0x089440d0,200,380)]:imm(addr,5,old,new,'Escape quantity and items column')
 for addr,old,new in [(0x08943e9c,155,174),(0x08943f0c,155,174),(0x08943f74,155,174),(0x08943fec,180,187),(0x0894405c,180,187),(0x089440c4,180,187),(0x08944138,180,206),(0x089441a4,180,206),(0x0894420c,180,206),(0x08944284,205,224),(0x089442e4,230,248),(0x0894433c,232,250),(0x089443c8,233,251),(0x08944424,230,248)]:imm(addr,6,old,new,'Separate escape value rows and fit collection bar')
 table=0x08a49790;assert struct.unpack_from('<11h',elf,table-BASE)==(1,5,15,4,30,16,10,10,15,15,0)
 p=table-BASE+8;struct.pack_into('<h',elf,p,60);allowed.update((p,p+1))
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,po+32,*ph);allowed.update(range(po+48,po+56));assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe}
 base=rootmap[0x27000];arc,en=container(data,base);mlt=member(arc,en,1);oldrows={(s,i):t for s,i,_,t in parse_mlt(mlt)};assert oldrows[0,26]=='Total Acquired'
 edits={(0,26):'Acquired'};rebuilt=rebuild_mlt(mlt,edits);assert {(s,i):t for s,i,_,t in parse_mlt(rebuilt)}=={k:edits.get(k,v) for k,v in oldrows.items()}
 path=ROOT/'work/translation/en/ui_batch_011.json';batch=json.loads(path.read_text(encoding='utf-8'));row=next(x for x in batch['rows'] if x['id']=='ore:00027000:0001:00:0026');assert row['translation_en'] in ('Total Acquired','Acquired');row['translation_en']='Acquired';row['fit_status']='pending_runtime_'+V;batch['version']=V
 updates={base:rebuild_ez(arc,{1:pack(rebuilt)})};changed={base:{1}}
 tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000);f,fp,fr=footer(member(ot,ote,25),V);updates[tb]=rebuild_ez(ta,{25:pack(f)});changed[tb]={25};del original
 ore=rebuild_root(data,updates,mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in updates:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j not in changed[a[3]]:assert aa[x:x+z]==bb[xx:xx+zz]
 report=dict(version=V,source_version='0.2.33',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,literals=literals,wrappers=wrappers,tab_geometry=dict(address=hex(table+8),before=30,after=60,columns=5),text_edit=dict(id=row['id'],before='Total Acquired',after='Acquired'),layout=dict(curios=dict(heading=[120,78,16],caption=[304,80],count_right=432,unit_x=442),other=dict(main_y=[80,105,130,155,187],escape_value_y=[174,206],collection_y=224,bar_y=248,bar_bottom=264),scrolls=dict(format='%d/%d',right=400,unit='')),checks=dict(unrelated_archive_members='Byte-identical except title footer',other_executable_bytes='Only guarded layout/call patches, one menu width and segment size',counter_getters_totals_and_scroll_paging='Byte-identical',prior_translations_icons_and_profile_fix='Preserved',shared_items_unit='Preserved'),footer=fr,runtime_verification='pending',texture_replacement=False)
 return elf,ore,fp,report,path,batch

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,fp,r,path,batch=build();print(json.dumps({k:v for k,v in r.items() if k!='footer'},indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.catalog.elf').exists();(out/'EBOOT.catalog.elf').write_bytes(elf);(out/'data.catalog.ore').write_bytes(ore);(out/'catalog.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/('work/ui/catalog-'+V);ui.mkdir(exist_ok=True);fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');path.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');path.with_suffix('.en.json').write_text(json.dumps(export(path),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

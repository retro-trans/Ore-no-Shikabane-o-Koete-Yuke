"""Translate native Chronicle date formats and fit navigation captions. Dry run first."""
import argparse,hashlib,json,struct
from catalog_text import ROOT,parse_mlt
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_mlt,rebuild_root,align
from check_translation import tokens_equal
from strip_jp import export
V='0.2.33';BASE=0x08803000
EDITS=[(66,'@Start of the Year','@Year Start'),(68,'@Last Month','@Prev'),(69,'@Next Month','@Next')]
sha=lambda b:hashlib.sha256(b).hexdigest()

def build():
 src=ROOT/'work/output/english-native-0.2.32';source=(src/'EBOOT.banners.elf').read_bytes();data=(src/'data.banners.ore').read_bytes()
 assert sha(source)=='e06a8d06a9c49684ba7755b5f3d44d5b34b5d6c6cc1edddbcf5144337132f44b'
 assert sha(data)=='57c75624a2a125ff69a2a4ad2179279821236d09f63edc6ee4724aed2c559845'
 elf=bytearray(source);phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
 patches=[];literals=[];allowed=set()
 def word(addr,old,new,note):
  p=addr-BASE;assert struct.unpack_from('<I',elf,p)[0]==old,(hex(addr),hex(struct.unpack_from('<I',elf,p)[0]));struct.pack_into('<I',elf,p,new);allowed.update(range(p,p+4));patches.append(dict(address=hex(addr),before=hex(old),after=hex(new),purpose=note))
 def append(b):
  elf.extend(bytes(align(len(elf),16)-len(elf)));addr=ph[2]+len(elf)-ph[1];elf.extend(b);return addr
 for off,hi,lo,new in [(0x23bf80,0x0891900c,0x08919014,'Events: %4d / %s'),(0x23bf98,0x0891903c,0x08919040,'Events: %4d / %2d')]:
  old=source[off:source.index(0,off)];assert old.endswith(bytes.fromhex('bdd0cde8bbf6'))
  assert old[:3]==b'%4d' and new.count('%')==2
  addr=append(new.encode('ascii')+b'\0');oldaddr=BASE+off
  word(hi,0x3c050000|((oldaddr+0x8000)>>16),0x3c050000|((addr+0x8000)>>16),'Relocated English Chronicle heading: high pointer')
  word(lo,0x24a50000|(oldaddr&65535),0x24a50000|(addr&65535),'Relocated English Chronicle heading: low pointer')
  literals.append(dict(context='Chronicle unknown month' if new.endswith('%s') else 'Chronicle numbered month',original_address=hex(oldaddr),address=hex(addr),translation_en=new,placeholders=['%4d','%s' if new.endswith('%s') else '%2d']))
 word(0x0891b73c,0x24050020,0x24050008,'Year Start label at x8, clear of L icon at x88 and heading at x96')
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph);allowed.update(range(phoff+48,phoff+56));assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe}
 base=rootmap[0xc000];arc,en=container(data,base);mlt=member(arc,en,13);oldrows={(s,i):t for s,i,_,t in parse_mlt(mlt)}
 batchpath=ROOT/'work/translation/en/ui_batch_012.json';batch=json.loads(batchpath.read_text(encoding='utf-8'));edits={};fit=[];metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
 for index,old,new in EDITS:
  assert oldrows[0,index]==old;row=next(x for x in batch['rows'] if x['id']=='ore:0000c000:0013:00:%04d'%index);assert row['translation_en'] in (old,new) and tokens_equal(row['source_jp'],new)
  row['translation_en']=new;row['fit_status']='pending_runtime_'+V;note='Compact Chronicle navigation caption clears its native controller icon; leading control marker and row identity preserved.'
  if note not in row.setdefault('review_notes',[]):row['review_notes'].append(note)
  edits[0,index]=new;width=sum(metrics[str(ord(c))]['advance'] for c in new[1:])*12/14;budget=68 if index==66 else (36 if index==68 else 44);assert width<=budget
  fit.append(dict(id=row['id'],old=old,translation_en=new,width_at_size12=width,width_budget=budget))
 rebuilt=rebuild_mlt(mlt,edits);actual={(s,i):t for s,i,_,t in parse_mlt(rebuilt)};assert actual=={k:edits.get(k,v) for k,v in oldrows.items()}
 updates={base:rebuild_ez(arc,{13:pack(rebuilt)})};changed={base:{13}}
 tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000);f,fp,fr=footer(member(ot,ote,25),V);updates[tb]=rebuild_ez(ta,{25:pack(f)});changed[tb]={25};del original
 ore=rebuild_root(data,updates,mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in updates:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j not in changed[a[3]]:assert aa[x:x+z]==bb[xx:xx+zz]
 report=dict(version=V,source_version='0.2.32',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,literals=literals,text_edits=fit,layout=dict(heading=[96,8,288,32],year_start=[8,8],next_year=[400,8],prev_month=[8,128],next_month=[424,128],year_icons=[[88,24],[392,24]],month_icons=[[56,144],[424,144]]),footer=fr,checks=dict(calendar_math_and_record_lookup='Byte-identical',unknown_month_marker='Preserved',placeholder_types_and_order='Preserved',history_event_rows='Byte-identical',other_archive_members='Byte-identical except title footer',renderer_icons_banners_and_profile_fix='Byte-identical to 0.2.32',other_executable_bytes='Only four format-pointer instructions, one label position and segment size change'),texture_replacement=False,runtime_verification='pending')
 batch['version']=V
 return elf,ore,fp,report,batchpath,batch

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,fp,r,path,batch=build();print(json.dumps({k:v for k,v in r.items() if k!='footer'},indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.chronicle.elf').exists();(out/'EBOOT.chronicle.elf').write_bytes(elf);(out/'data.chronicle.ore').write_bytes(ore);(out/'chronicle.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/('work/ui/chronicle-'+V);ui.mkdir(parents=True,exist_ok=True);fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  path.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');path.with_suffix('.en.json').write_text(json.dumps(export(path),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

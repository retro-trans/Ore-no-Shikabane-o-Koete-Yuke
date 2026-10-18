"""Translate and fit the six reported result/party screens. Dry run before --write."""
import argparse,hashlib,json,struct
import keystone
from PIL import Image,ImageDraw
from catalog_text import ROOT,parse_mlt
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from inspect_native_textures import decode
from hd_sprites import encode
from repack_text import root_entries,rebuild_ez,rebuild_mlt,rebuild_root,align
from check_translation import tokens_equal
from strip_jp import export
V='0.2.27';BASE=0x08803000
EDITS=[
 ('combat_batch_001','ore:00023800:0000:01:0001','Until Next Growth','Next Growth'),
 ('combat_batch_001','ore:00023800:0000:01:0017','Victory Points / Offering Points Earned','Points Earned'),
 ('combat_batch_001','ore:00023800:0000:01:0019','Free Pack Slots','Free Slots'),
 ('consistent_terms','ore:00022800:0000:03:0002','Naginata Wielder','Naginata'),
 ('ui_batch_004','ore:0000c000:0009:00:0058','@Use the \u25cb button\nto switch between front and back rows.','@Press Circle to change\nfront and back rows.'),
 ('ui_batch_003','ore:00027000:0003:02:0016','This Month:','Now:'),
 ('ui_batch_003','ore:00027000:0003:02:0017','Month %d:','Mo. %d:'),
 ('ui_batch_010','ore:00028000:0003:00:0002','Free Pack Slots','Free Slots'),
 ('ui_batch_010','ore:00028000:0003:02:0000','items',' items'),
 ('ui_batch_010','ore:00028000:0003:02:0001','prints',' prints'),
]
sha=lambda b:hashlib.sha256(b).hexdigest()
def build():
 src=ROOT/'work/output/english-native-0.2.26';source=(src/'EBOOT.hd.elf').read_bytes();data=(src/'data.hd.ore').read_bytes()
 assert sha(source)=='1b56631724291d08c5f493006ad34f421973959a8b3e24f8f5c7681e4a16660e'
 assert sha(data)=='826980ba9c6de91e244f4e9336fee94173c9710f3f8b0d03850eaffded37412f'
 elf=bytearray(source);phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
 changes=[];allowed=set();wrappers=[];literals=[]
 def offset(a):return a-BASE if a<ph[2] else a-ph[2]+ph[1]
 def raw(a,old,new,note):
  p=offset(a);assert elf[p:p+len(old)]==old,(hex(a),elf[p:p+len(old)].hex(),old.hex());assert len(old)==len(new)
  elf[p:p+len(new)]=new;allowed.update(range(p,p+len(new)));changes.append(dict(address=hex(a),before=old.hex(),after=new.hex(),purpose=note))
 def word(a,old,new,note):raw(a,struct.pack('<I',old),struct.pack('<I',new),note)
 def append(b):
  elf.extend(bytes(align(len(elf),16)-len(elf)));a=ph[2]+len(elf)-ph[1];elf.extend(b);return a
 ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
 def code(t,note):
  a=ph[2]+align(len(elf),16)-ph[1];b=bytes(ks.asm('.set noreorder\n'+t,addr=a)[0]);assert append(b)==a;wrappers.append(dict(address=hex(a),bytes=len(b),purpose=note));return a
 def ptr(hi,lo,oldh,oldl,a,note):
  word(hi,oldh,(oldh&0xffff0000)|((a+0x8000)>>16),note+' high');word(lo,oldl,(oldl&0xffff0000)|(a&65535),note+' low')
 for a,old,new,note in [(0x08a3b198,bytes.fromhex('bca1a4cec0aec4b9a4dea4c700000000'),b'Next Growth\0'+bytes(4),'Native battle growth caption'),(0x08a443dc,bytes.fromhex('bdeabbfdb6e20000'),b'Money\0\0\0','Shared pause-menu money caption'),(0x08a443e4,bytes.fromhex('cebe0000'),b'ryo\0','Shared pause-menu currency')]:
  raw(a,old,new,note);literals.append(dict(address=hex(a),translation_en=new.split(b'\0')[0].decode(),context=note))
 money=append(b'%s\t%d %s\0');ptr(0x08944a28,0x08944a38,0x3c0508a4,0x24a543d4,money,'Space between money and currency')
 # The shared unit supplies its English space. Both the pause formatter and
 # battle-result number widget use this table; the latter has no formatter.
 word(0x088f6748,0x2406002c,0x24060040,'Portrait band height: room for separate class row')
 word(0x0895c174,0x24060084,0x2406009c,'Equipment comparison stats below separate age/class rows')
 position=code('''lw $v0, 0x78($v0)
  li $t0,4
  bne $s7,$t0,done
  move $a2,$s3
  li $a2,128
 done:
  jr $ra
  nop
 ''','Only the equipment class uses its own third text row')
 word(0x088f67c0,0x8c420078,0x0c000000|(position>>2),'Separate equipment class row helper')
 word(0x088f67c4,0x02603021,0,'Helper supplies the row coordinate')
 word(0x088f1f5c,0x24050006,0x24050002,'Full Potential labels at their original text size')
 word(0x088f1ed0,0x2405001b,0x24050024,'Potential element icons clear of full English captions')
 word(0x088f1e90,0x2405002d,0x24050036,'Potential bars beside their shifted element icons')
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe}
 # The Potential image is already embedded natively in26. Edit only that
 # image's palette and pixel payload; its descriptor, proxy and size stay.
 oa,en=container(original,0x36000);blob=member(oa,en,19);im,info=decode(blob);s=4;layer=im.resize((576,1024),Image.Resampling.NEAREST);d=ImageDraw.Draw(layer)
 d.rectangle((4*s,14*s,137*s,247*s),fill=(0,0,0,255))
 for x in (53,75,96,117,138):d.line((x*s,30*s,x*s,244*s),fill=(46,46,46,255),width=s)
 for y in (99,173):d.line((45*s,y*s,138*s,y*s),fill=(46,46,46,255),width=s)
 image,preview,hd=encode(blob,layer.resize((512,512),Image.Resampling.LANCZOS));po=struct.unpack_from('<I',image,24)[0]
 oldr=json.loads((src/'hd.report.json').read_text());idx=next(i for i,g in enumerate(oldr['graphics']) if g['file']=='115.ppt');desc=oldr['renderer']['embedded_descriptors'][idx];pixels,palette=struct.unpack_from('<2I',source,offset(desc)+32)
 for a,new in [(pixels,image[32:po]),(palette+16,image[po+16:po+1040])]:raw(a,source[offset(a):offset(a)+len(new)],new,'Remove decorative words from Potential graph; retain clean grid')
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph);allowed.update(range(phoff+48,phoff+56));assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(source,elf)))
 batches={};updates={};fit=[];metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
 for batch,rid,old,new in EDITS:
  path=ROOT/('work/translation/en/'+batch+'.json');b=batches.setdefault(path,json.loads(path.read_text(encoding='utf-8')));row=next(z for z in b['rows'] if z['id']==rid);assert row['translation_en'] in (old,new)
  assert tokens_equal(row['source_jp'],new) and old.count('\n')==new.count('\n') and old.startswith('@')==new.startswith('@')
  row['translation_en']=new;row['fit_status']='pending_runtime_'+V;b['version']=V
  note='User-requested compact English for the six reported party/result screens; source meaning, row identity and engine controls retained.'
  if note not in row.setdefault('review_notes',[]):row['review_notes'].append(note)
  base=rootmap[row['archive_offset']];updates.setdefault(base,{}).setdefault(row['member_entry'],{})[(row['section'],row['index'])]=(old,new)
  widths=[sum(metrics.get(str(ord(c)),{'advance':14})['advance'] for c in line.lstrip('@'))*12/14 for line in new.split('\n')]
  fit.append(dict(id=rid,old=old,translation_en=new,widths_at_size12=widths))
 changed={};changed_members={}
 for base,members in updates.items():
  arc,entries=container(data,base);assets={}
  for entry,rows in members.items():
   mlt=member(arc,entries,entry);lookup={(s,i):t for s,i,_,t in parse_mlt(mlt)};assert all(lookup[k]==old for k,(old,new) in rows.items());rebuilt=rebuild_mlt(mlt,{k:new for k,(old,new) in rows.items()});actual={(s,i):t for s,i,_,t in parse_mlt(rebuilt)}
   assert all(actual[k]==(rows[k][1] if k in rows else t) for k,t in lookup.items());assets[entry]=pack(rebuilt)
  changed[base]=rebuild_ez(arc,assets);changed_members[base]=set(assets)
 tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000);f,fp,fr=footer(member(ot,ote,25),V);changed[tb]=rebuild_ez(ta,{25:pack(f)});changed_members[tb]={25};del original
 ore=rebuild_root(data,changed,mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in changed:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
    if j not in changed_members[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
 report=dict(version=V,source_version='0.2.26',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=changes,literals=literals,wrappers=wrappers,potential_labels=dict(text=['Spirit','Skill','Body'],font_size='Original size retained',left=2,icons_left=36,bars_left=54,bar_max_width=84,right_edge=138,frame_width=142),text_edits=fit,potential_image=dict(descriptor=hex(desc),pixels=hex(pixels),palette=hex(palette),**hd),footer=fr,checks=dict(other_text_rows='byte-identical',other_archive_members='byte-identical',other_executable_bytes='byte-identical',tokens_and_row_ids='preserved',mlt_roundtrips='pass'),texture_replacement=False,runtime_verification='pending')
 return elf,ore,preview,fp,report,batches
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--tag',default='');a=ap.parse_args();elf,ore,im,fp,r,batches=build()
 concise={k:v for k,v in r.items() if k not in ('patches','footer')};concise['patches']=[{k:v for k,v in x.items() if k not in ('before','after')} for x in r['patches']];print(json.dumps(concise,indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V+a.tag);out.mkdir(parents=True,exist_ok=True);assert not (out/'EBOOT.screens.elf').exists();(out/'EBOOT.screens.elf').write_bytes(elf);(out/'data.screens.ore').write_bytes(ore);(out/'screens.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/('work/ui/six-screens-'+V);ui.mkdir(parents=True,exist_ok=True);im.save(ui/'native-potential.png');fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(concise,indent=2)+'\n',encoding='utf-8')
  for p,b in batches.items():p.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');p.with_suffix('.en.json').write_text(json.dumps(export(p),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Written.' if a.write else 'DRY RUN: no game changes.')
if __name__=='__main__':main()

"""Widen the home menu description panel. Dry run before --write."""
import argparse,hashlib,json,re,struct
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root
V='0.2.38';BASE=0x08803000
sha=lambda b:hashlib.sha256(b).hexdigest()
def build():
 src=ROOT/'work/output/english-native-0.2.37';source=(src/'EBOOT.dialogue.elf').read_bytes();data=(src/'data.dialogue.ore').read_bytes()
 assert sha(source)=='815308f8d8ef3691bfa70c44cd5645f12f1051ee7a4ee09e6cd9f977dd8d7582'
 assert sha(data)=='15489cc5f9007462b157a6f4ece0dd6b8c38f33d757d87afff256974d99f55b0'
 elf=bytearray(source);patches=[];allowed=set()
 for addr,old,new,note in [(0x088dc480,0x24050120,0x240501b0,'Home help width: 288 to 432'),(0x088dc498,0x24050060,0x24050018,'Keep wider home help centered: x=24')]:
  p=addr-BASE;assert struct.unpack_from('<I',elf,p)[0]==old;struct.pack_into('<I',elf,p,new);allowed.update(range(p,p+4));patches.append(dict(address=hex(addr),before=hex(old),after=hex(new),purpose=note))
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 g=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];rows=[r for p in (ROOT/'work/translation/en').glob('*.en.json') for r in json.loads(p.read_text(encoding='utf-8')).get('rows',[]) if r.get('id','').startswith('ore:0000c000:0000:03:')]
 fit=[]
 for r in rows:
  widths=[round(sum(g.get(str(ord(c)),{'advance':14})['advance'] for c in t)*12/14,3) for t in re.sub(r'\[[^]]*\]','',r['translation_en']).splitlines()]
  assert all(w<=426 for w in widths);fit.append(dict(id=r['id'],translation_en=r['translation_en'],line_advances=widths))
 assert len(fit)==34
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);ti=next(i for i,_,_,o in oe if o==0x1e8000);tb=next(o for i,_,_,o in be if i==ti);ta,te=container(data,tb);ot,ote=container(original,0x1e8000)
 f,fp,fr=footer(member(ot,ote,25),V);ore=rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(f)})},mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3]!=tb:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
    if j!=25:assert aa[p:p+z]==bb[pp:pp+zz]
 r=dict(version=V,source_version='0.2.37',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,layout=dict(before=[96,214,288,50],after=[24,214,432,50],text_width=426,text_left_inset=6,right_edge=456),measured_rows=fit,checks=dict(dialogue_and_ui_wording='Unchanged',other_executable_bytes='Byte-identical',archive_payloads='Byte-identical except title version',previous_dialogue_transparency='Unchanged'),footer=fr,texture_replacement=False,runtime_verification='pending')
 return elf,ore,fp,r
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,fp,r=build();print(json.dumps({k:v for k,v in r.items() if k not in ('footer','measured_rows')},indent=2));print('Measured 34 home help entries; longest line:',max(max(x['line_advances']) for x in r['measured_rows']))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.home.elf').exists();(out/'EBOOT.home.elf').write_bytes(elf);(out/'data.home.ore').write_bytes(ore);(out/'home.report.json').write_text(json.dumps(r,indent=2)+'\n');ui=ROOT/('work/ui/home-help-'+V);ui.mkdir(exist_ok=True);fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r['layout'],indent=2)+'\n')
 print('Written.' if a.write else 'DRY RUN: no files written.')

"""Translate the embedded startup disclaimer. Dry run unless --write."""
import argparse,hashlib,json,struct
from PIL import Image,ImageDraw,ImageFont
from catalog_text import ROOT
from build_menu_fixes import container,member,pack,encode_native
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root,align
VERSION='0.2.23';BASE=0x08803000;EMBEDDED=0x275230
LINES=['This story is entirely fictional.',
       'It has no connection to real people, places,',
       'organizations, product names, or the like.']
def sha(b):return hashlib.sha256(b).hexdigest()
def build():
 source=(ROOT/'work/output/english-native-0.2.22/EBOOT.roster.elf').read_bytes();data=(ROOT/'work/output/english-native-0.2.22/data.roster.ore').read_bytes()
 assert sha(source)=='3155612fb59643b4cc751cff838ce910ab30590fd222bae03c9c94f7d1d87ad3'
 assert sha(data)=='7063d39e56a5c4861ed645811f8e889fec25c8ab44680cb0a2fee7cf70bdb474'
 old,e=container(source,EMBEDDED);blob=member(old,e,4);original,info=__import__('inspect_native_textures').decode(blob);assert original.size==(480,272)
 scale=4;layer=Image.new('RGBA',(480*scale,272*scale),(0,0,0,255));draw=ImageDraw.Draw(layer);font=ImageFont.truetype(str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf'),14*scale);bounds=[]
 for line,y in zip(LINES,(116,136,156)):
  box=draw.textbbox((240*scale,y*scale),line,font=font,anchor='mm');assert box[0]>=24*scale and box[2]<=456*scale
  bounds.append([n/scale for n in box]);draw.text((240*scale,y*scale),line,font=font,anchor='mm',fill='white')
 edited=layer.resize((480,272),Image.Resampling.LANCZOS);new,preview=encode_native(blob,edited,(0,0,480,272));rebuilt=rebuild_ez(old,{4:pack(new)});_,ne=container(rebuilt,0)
 for i in range(4):assert member(old,e,i)==member(rebuilt,ne,i)
 elf=bytearray(source);phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
 elf.extend(bytes(align(len(elf),16)-len(elf)));address=ph[2]+len(elf)-ph[1];offset=len(elf);elf.extend(rebuilt);patches=[];allowed=set(range(phoff+48,phoff+56))
 for hi,lo in [(0x0881ad40,0x0881ad48),(0x0881ad4c,0x0881ad54)]:
  for pc,expected,value in [(hi,0x3c0208a8,0x3c020000|((address+0x8000)>>16)),(lo,0x24428230,0x24420000|(address&65535))]:
   p=pc-BASE;assert struct.unpack_from('<I',elf,p)[0]==expected;struct.pack_into('<I',elf,p,value);allowed.update(range(p,p+4));patches.append(dict(address=hex(pc),before=struct.pack('<I',expected).hex(),after=struct.pack('<I',value).hex()))
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph)
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)));assert elf[EMBEDDED:EMBEDDED+len(old)]==old
 orig=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(orig);be,bend=root_entries(data);idx=next(i for i,_,_,o in oe if o==0x1e8000);tb=next(o for i,_,_,o in be if i==idx)
 ta,te=container(data,tb);ot,ote=container(orig,0x1e8000);fppt,fpreview,fr=footer(member(ot,ote,25),VERSION);changed=rebuild_ez(ta,{25:pack(fppt)});del orig
 ore=rebuild_root(data,{tb:changed},mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3]!=tb:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for i,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
    if i!=25:assert aa[p:p+z]==bb[pp:pp+zz]
 report=dict(version=VERSION,source_version='0.2.22',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,embedded_archive=dict(original_offset=hex(EMBEDDED),new_file_offset=hex(offset),new_address=hex(address),bytes=len(rebuilt),sha256=sha(rebuilt),original_logos='All four decoded logo assets byte-identical',warning_member=4,warning_name='warning.ppt',warning_sha256=sha(new)),graphics=[dict(file='EBOOT:warning.ppt',member_entry=4,translation_en='\n'.join(LINES),native_size=[480,272],font='Noto Sans',font_size=14,line_bounds=bounds)],checks=dict(unrelated_executable_bytes='byte-identical; original embedded archive retained',all_script_payloads='byte-identical',other_archive_members='byte-identical',original_warning_palette='unchanged',compression_round_trip='pass'),footer=fr,texture_replacement=False,runtime_verification='pending')
 return bytes(elf),ore,preview,fpreview,report
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,preview,footer,r=build();print(json.dumps(r,indent=2))
 if a.write:
  out=ROOT/'work/output/english-native-0.2.23';out.mkdir(parents=True,exist_ok=True);assert not (out/'EBOOT.disclaimer.elf').exists();(out/'EBOOT.disclaimer.elf').write_bytes(elf);(out/'data.disclaimer.ore').write_bytes(ore);(out/'disclaimer.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/'work/ui/startup-disclaimer-0.2.23';ui.mkdir(parents=True,exist_ok=True);preview.save(ui/'native-warning.png');footer.save(ui/'native-footer.png')
 print('Written.' if a.write else 'DRY RUN: no game changes.')
if __name__=='__main__':main()

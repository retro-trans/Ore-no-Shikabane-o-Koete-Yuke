"""Native character popup, portrait selector and spell labels. Dry run unless --write."""
import argparse,hashlib,json,struct
import keystone
from catalog_text import ROOT
from build_equipment_deities import badge
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root,align

VERSION='0.2.21';BASE=0x08803000
PATCHES=[
 (0x088ff920,0x24050020,84,'Character submenu cell width'),
 (0x089547a4,0x24060004,2,'Two spell columns with native paging'),
 (0x089547d8,0x24050032,108,'Spell name cell width'),
 (0x08958d60,0x8c4200e8,0xe4,'Hide obsolete Spirit/Skill pictograms beside full English captions'),
 (0x08958da8,0x24050014,0,'Full stat captions start at the left of their panel'),
 (0x08955d48,0x2442004e,70,'Evenly space complete English spell legend labels'),
 (0x08955f60,0x2405008c,120,'Separate full MP Required caption from its MP badge'),
 (0x08955120,0x24060054,82,'Spell portrait name band top'),
 (0x08955138,0x2406002c,56,'Spell portrait band contains separate name age and MP rows'),
 (0x0895518c,0x24060058,82,'Spell portrait full English name on its own row'),
 (0x0895519c,0x24060058,98,'Spell portrait age on its own row'),
 (0x089551d0,0x2406006a,114,'Spell portrait current MP row'),
 (0x089551ec,0x2406006a,114,'Spell portrait MP separator row'),
 (0x089551fc,0x2406006a,114,'Spell portrait maximum MP row'),
 (0x08955280,0x2406006c,116,'Spell portrait MP badge row'),
 (0x089552dc,0x2406007c,132,'Spell portrait MP bar background below numeric row'),
 (0x0895532c,0x2406007c,132,'Spell portrait MP bar foreground below numeric row'),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def build():
 source=(ROOT/'work/output/english-native-0.2.20/EBOOT.equipment.elf').read_bytes()
 data=(ROOT/'work/output/english-native-0.2.20/data.equipment.ore').read_bytes()
 assert sha(source)=='b8e6fbe75efa36ed2112b581075740d5ef920ccffff3c821a7e18434aae0394a'
 assert sha(data)=='affbd83b412074d458164002b13a36879fe252ed090a95f09a9e8f33b92a499b'
 elf=bytearray(source);changes=[];allowed=set();wrappers=[];literals=[]
 def word(a,old,new,note):
  off=a-BASE;assert struct.unpack_from('<I',elf,off)[0]==old,(hex(a),hex(struct.unpack_from('<I',elf,off)[0]),hex(old))
  struct.pack_into('<I',elf,off,new);allowed.update(range(off,off+4));changes.append(dict(address=hex(a),before=struct.pack('<I',old).hex(),after=struct.pack('<I',new).hex(),purpose=note))
 for a,old,value,n in PATCHES:word(a,old,(old&0xffff0000)|(value&0xffff),n)
 phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
 def append(b):
  elf.extend(bytes(align(len(elf),4)-len(elf)));a=ph[2]+len(elf)-ph[1];elf.extend(b);return a
 ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
 def code(s,note):
  a=ph[2]+align(len(elf),4)-ph[1];b=bytes(ks.asm('.set noreorder\n'+s,addr=a)[0]);assert append(b)==a;wrappers.append(dict(address=hex(a),bytes=len(b),purpose=note));return a
 def jal(pc,target,old,note):word(pc,0x0c000000|(old//4),0x0c000000|(target//4),note)
 def text_wrapper(pc,old,label,size):
  p=append(label.encode('ascii')+b'\0');literals.append(dict(address=hex(p),translation_en=label))
  a=code('''addiu $sp,$sp,-32
   sw $ra,28($sp)
   sw $s0,24($sp)
   move $s0,$a0
   jal 0x0882b12c
   li $a1,%d
   move $a0,$s0
   lui $a1,0x%x
   jal 0x0882b2e0
   addiu $a1,$a1,%d
   lw $s0,24($sp)
   lw $ra,28($sp)
   jr $ra
   addiu $sp,$sp,32
  '''%(size,(p+0x8000)>>16,((p&65535)^32768)-32768),'English caption: '+label)
  jal(pc,a,old,'Full native-font caption: '+label)
 for pc,old,t in [(0x08958eb4,0x0882b2e0,'Spirit Req.'),(0x08958ec0,0x0882b2e0,'Spirit Now'),(0x08958ecc,0x0882b2e0,'Skill Req.'),(0x08958ed8,0x0882b2e0,'Skill Now'),(0x08955d68,0x0882b49c,'Usable'),(0x08955d80,0x0882b49c,'Unusable'),(0x08955d9c,0x0882b49c,'Not Learned')]:text_wrapper(pc,old,t,16)
 selector=code('''addiu $sp,$sp,-32
   sw $ra,28($sp)
   sw $s0,24($sp)
   jal 0x0882afac
   move $s0,$a0
   lw $v0,0($s0)
   lw $a1,0x38($s0)
   lw $a2,0x3c($s0)
   addiu $a2,$a2,12
   lw $v0,0x88($v0)
   jalr $v0
   move $a0,$s0
   lw $s0,24($sp)
   lw $ra,28($sp)
   jr $ra
   addiu $sp,$sp,32
 ''','Portrait selection image height follows the additional age row')
 jal(0x0892c154,selector,0x0882afac,'Extend roster selector by the same twelve pixels as cards')
 cell=code('''addiu $sp,$sp,-32
   sw $ra,28($sp)
   sw $s0,24($sp)
   jal 0x0882afac
   move $s0,$a0
   lw $v0,0($s0)
   li $a1,108
   lw $a2,0x3c($s0)
   lw $v0,0x88($v0)
   jalr $v0
   move $a0,$s0
   lw $s0,24($sp)
   lw $ra,28($sp)
   jr $ra
   addiu $sp,$sp,32
 ''','Spell cell background width follows the wider native cell')
 for pc in (0x08954cb8,0x08954f2c,0x08954f74):jal(pc,cell,0x0882afac,'Spell cell background matches text and selector width')
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph);allowed.update(range(phoff+48,phoff+56))
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data)
 rootmap={o:next(n[3] for n in be if n[0]==i) for i,_,_,o in oe};updates={};changed={};previews={};graphics=[]
 base=rootmap[0x36000];a,e=container(data,base);b,im=badge(member(a,e,11),'MP');updates[base]=rebuild_ez(a,{11:pack(b)});changed[base]={11};previews['mp']=im
 graphics.append(dict(archive_offset=0x36000,member_entry=11,file='108.ppt',translation_en='MP'))
 tb=rootmap[0x1e8000];ta,te=container(data,tb);ot,ote=container(original,0x1e8000);ppt,fp,fr=footer(member(ot,ote,25),VERSION)
 updates[tb]=rebuild_ez(ta,{25:pack(ppt)});changed[tb]={25};previews['footer']=fp
 del original
 ore=rebuild_root(data,updates);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047)
  aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in updates:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
    if j not in changed[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
 metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
 width=lambda t:sum(metrics.get(str(ord(c)),{'advance':14})['advance'] for c in t)*12/14
 spells=[r for p in (ROOT/'work/translation/en').glob('*.en.json') for r in json.loads(p.read_text(encoding='utf-8')).get('rows',[]) if r.get('kind')=='spell_name']
 assert len(spells)==96 and max(width(r['translation_en']) for r in spells)<107
 report=dict(version=VERSION,source_version='0.2.20',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=changes,literals=literals,wrappers=wrappers,graphics=graphics,texture_replacement=False,font_raster_scale=4,checks=dict(unrelated_executable_bytes='byte-identical',all_script_payloads='byte-identical',other_archive_members='byte-identical'),static_spell_names=dict(records=96,max_width=max(width(r['translation_en']) for r in spells),text_budget=107),footer=fr,runtime_verification='pending')
 return bytes(elf),ore,previews,report
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--tag',default='');a=ap.parse_args();elf,ore,previews,r=build();print(json.dumps(r,indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-0.2.21'+a.tag);out.mkdir(parents=True,exist_ok=True)
  assert not (out/'EBOOT.character.elf').exists()
  (out/'EBOOT.character.elf').write_bytes(elf);(out/'data.character.ore').write_bytes(ore);(out/'character.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/'work/ui/character-spells-0.2.21';ui.mkdir(parents=True,exist_ok=True)
  for n,im in previews.items():im.save(ui/('native-'+n+'.png'))
 print('Written.' if a.write else 'DRY RUN: no game changes.')
if __name__=='__main__':main()

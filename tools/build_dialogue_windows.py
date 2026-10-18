"""Translate Pack literals and widen bottom dialogue panels. Dry run before --write."""
import argparse,hashlib,json,struct
import keystone
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root,align
V='0.2.37';BASE=0x08803000
sha=lambda b:hashlib.sha256(b).hexdigest()

def build():
 src=ROOT/'work/output/english-native-0.2.36';source=(src/'EBOOT.bmenu.elf').read_bytes();data=(src/'data.bmenu.ore').read_bytes()
 assert sha(source)=='0c25f5ffc34a8fc8a43788034400730c67bfb5ee2451144aff953fa00690ab23'
 assert sha(data)=='b935c586538a9219e28a4e401071d8367515748e0a08290088e1f9abe6ebe5b6'
 elf=bytearray(source);po=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,po+32));assert ph[1]+ph[4]==len(elf);patches=[];allowed=set()
 def raw(addr,old,new,note):
  p=addr-BASE;assert elf[p:p+len(old)]==old,(hex(addr),elf[p:p+len(old)].hex());assert len(old)==len(new)
  elf[p:p+len(new)]=new;allowed.update(range(p,p+len(new)));patches.append(dict(address=hex(addr),before=old.hex(),after=new.hex(),purpose=note))
 literals=[]
 for addr,jp,en in [(0x08a4155c,'残り[w5]%2d[w5]個','Left: %2d'),(0x08a41570,'『%s』を使いますか？','Use %s?')]:
  old=jp.encode('euc_jp')+b'\0';new=en.encode()+b'\0';assert len(new)<=len(old)
  raw(addr,old,new+bytes(len(old)-len(new)),'Pack '+en);literals.append(dict(address=hex(addr),translation_en=en,format_arguments=['%2d' if '2d' in en else '%s']))
 # The story/help window is its own native class. Extend only its left-aligned
 # bottom panels; centered alerts, title help, battle tooltips and menus retain
 # their geometry. The inherited layout moves frame pieces and the advance icon.
 asm='''.set noreorder
 lw $t0,0x40($a0)
 li $t1,24
 bne $t0,$t1,original
 nop
 lw $t0,0x44($a0)
 slti $t0,$t0,180
 bnez $t0,original
 nop
 lw $t0,0x48($a0)
 li $t1,288
 beq $t0,$t1,extend
 li $t1,432
 bne $t0,$t1,original
 nop
 extend:
 li $t0,432
 sw $t0,0x48($a0)
 li $t0,412
 sw $t0,0xb88($a0)
 sw $t0,0xde8($a0)
 sw $t0,0x1048($a0)
 li $t0,0xc8ffffff
 sw $t0,0x220($a0)
 sw $t0,0x224($a0)
 li $t0,0xc8808080
 sw $t0,0x228($a0)
 sw $t0,0x22c($a0)
 li $t0,1
 sb $t0,0x1fc($a0)
 original:
 j 0x08823610
 nop
 '''
 elf.extend(bytes(align(len(elf),16)-len(elf)));addr=ph[2]+len(elf)-ph[1]
 ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN);code=bytes(ks.asm(asm,addr=addr)[0]);elf.extend(code)
 raw(0x0882f5e4,struct.pack('<I',0x0c000000|(0x08823610>>2)),struct.pack('<I',0x0c000000|(addr>>2)),'Bottom dialogue layout and background opacity')
 # Some scenes size first and place afterward. Check the final placement in
 # the class's normal update, then use its real resize entry point exactly once.
 elf.extend(bytes(align(len(elf),16)-len(elf)));update=ph[2]+len(elf)-ph[1]
 update_code=bytes(ks.asm('''.set noreorder
 addiu $sp,$sp,-32
 sw $ra,28($sp)
 sw $s0,24($sp)
 move $s0,$a0
 jal 0x08823c90
 nop
 sw $v0,20($sp)
 sw $v1,16($sp)
 lw $t0,0x40($s0)
 li $t1,24
 bne $t0,$t1,done
 nop
 lw $t0,0x44($s0)
 slti $t0,$t0,180
 bnez $t0,done
 nop
 lw $t0,0x48($s0)
 li $t1,288
 bne $t0,$t1,done
 nop
 move $a0,$s0
 li $a1,432
 lw $a2,0x4c($s0)
 jal 0x0881e3f0
 nop
 done:
 lw $v1,16($sp)
 lw $v0,20($sp)
 lw $s0,24($sp)
 lw $ra,28($sp)
 jr $ra
 addiu $sp,$sp,32
 ''',addr=update)[0]);elf.extend(update_code)
 raw(0x0882f5b8,struct.pack('<I',0x0c000000|(0x08823c90>>2)),struct.pack('<I',0x0c000000|(update>>2)),'Apply wider dialogue after final scene placement')
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,po+32,*ph);allowed.update(range(po+48,po+56))
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data)
 ti=next(i for i,_,_,o in oe if o==0x1e8000);tb=next(o for i,_,_,o in be if i==ti);ta,te=container(data,tb);ot,ote=container(original,0x1e8000)
 f,fp,fr=footer(member(ot,ote,25),V);ore=rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(f)})},mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3]!=tb:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
    if j!=25:assert aa[p:p+z]==bb[pp:pp+zz]
 r=dict(version=V,source_version='0.2.36',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,literals=literals,wrapper=dict(address=hex(addr),bytes=len(code),tail_target='0x08823610'),update_wrapper=dict(address=hex(update),bytes=len(update_code)),layout=dict(native_class='0x08a22ba8',selection='x=24, y>=180, width=288 or already extended 432',before_width=288,after_width=432,frame_right=456,text_width=412,background_alpha=200,background_opacity=round(200/255,3),border_and_text_alpha='Unchanged'),checks=dict(dialogue_words='All unchanged',script_payloads='Byte-identical',unrelated_archive_payloads='Byte-identical except title version',unrelated_executable_bytes='Byte-identical',format_arguments='Preserved; obsolete visual spacer tags removed'),footer=fr,texture_replacement=False,runtime_verification='pending')
 return elf,ore,fp,r

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,fp,r=build();print(json.dumps({k:v for k,v in r.items() if k!='footer'},indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.dialogue.elf').exists()
  (out/'EBOOT.dialogue.elf').write_bytes(elf);(out/'data.dialogue.ore').write_bytes(ore);(out/'dialogue.report.json').write_text(json.dumps(r,indent=2)+'\n')
  ui=ROOT/('work/ui/dialogue-window-'+V);ui.mkdir(exist_ok=True);fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r['layout'],indent=2)+'\n')
 print('Written.' if a.write else 'DRY RUN: no files written.')

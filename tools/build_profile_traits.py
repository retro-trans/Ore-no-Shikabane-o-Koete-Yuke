"""Remove the status-only nine-character trait limit. Dry run before --write."""
import argparse,hashlib,json,struct
import keystone
from catalog_text import ROOT
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_root,align
V='0.2.30';BASE=0x08803000
sha=lambda b:hashlib.sha256(b).hexdigest()

def build():
 src=ROOT/'work/output/english-native-0.2.29';source=(src/'EBOOT.vitals.elf').read_bytes();data=(src/'data.vitals.ore').read_bytes()
 assert sha(source)=='6ce2eaf6da4bb998ebb7e2756d50dbe5d4c6d3268b83aee0e5e156b5e278de95'
 assert sha(data)=='bd1de4e47235a348f62354639f9221bd977cddd0c8e67ebb3ddf829ee6453045'
 elf=bytearray(source);phoff=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
 changes=[];wrappers=[];allowed=set()
 def append(b):
  elf.extend(bytes(align(len(elf),16)-len(elf)));a=ph[2]+len(elf)-ph[1];elf.extend(b);return a
 def word(a,old,new,note):
  p=a-BASE;assert struct.unpack_from('<I',elf,p)[0]==old,(hex(a),hex(struct.unpack_from('<I',elf,p)[0]));struct.pack_into('<I',elf,p,new);allowed.update(range(p,p+4));changes.append(dict(address=hex(a),before=hex(old),after=hex(new),purpose=note))
 ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
 def code(t,note):
  a=ph[2]+align(len(elf),16)-ph[1];b=bytes(ks.asm('.set noreorder\n'+t,addr=a)[0]);assert append(b)==a;wrappers.append(dict(address=hex(a),bytes=len(b),purpose=note));return a
 def load(reg,a):return 'lui $%s,0x%x\n addiu $%s,$%s,%d'%(reg,(a+0x8000)>>16,reg,reg,((a&65535)^32768)-32768)
 metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];adv=append(bytes(metrics.get(str(i),{'advance':14})['advance'] for i in range(128)))
 buffer=append(bytes(1024));guard=append(b'TRAIT_BUFFER_END!')
 fmt=code('''addiu $sp,$sp,-32
 sw $ra,28($sp)
 %s
 jal 0x08969a00
 li $a1,1024
 %s
 %s
 move $t2,$zero
 move $t3,$zero
 scan:
 lhu $t4,0($t0)
 beqz $t4,done
 nop
 li $t5,10
 beq $t4,$t5,reset
 nop
 li $t5,32
 bne $t4,$t5,measure
 nop
 move $t3,$t0
 measure:
 sltiu $t5,$t4,128
 beqz $t5,fallback
 li $t6,14
 addu $t5,$t1,$t4
 lbu $t6,0($t5)
 fallback:
 addu $t2,$t2,$t6
 sltiu $t5,$t2,281
 bnez $t5,next
 nop
 beqz $t3,next
 nop
 li $t5,10
 sh $t5,0($t3)
 move $t0,$t3
 reset:
 move $t2,$zero
 move $t3,$zero
 next:
 b scan
 addiu $t0,$t0,2
 done:
 lw $ra,28($sp)
 jr $ra
 addiu $sp,$sp,32
 '''%(load('a0',buffer),load('t0',buffer),load('t1',adv)),'Bounded 1024-byte native formatting and measured word wrap')
 second=code('''addiu $sp,$sp,-48
 sw $ra,44($sp)
 sw $s0,40($sp)
 sw $s1,36($sp)
 sw $s2,32($sp)
 sw $s3,28($sp)
 move $s0,$a0
 move $s1,$a1
 move $s2,$a2
 move $s3,$a3
 lui $v0,0x08b3
 lw $v0,0x4a90($v0)
 lw $v0,0($v0)
 li $a0,0x110
 jalr $v0
 li $a1,16
 beqz $v0,append_done
 nop
 move $a0,$v0
 jal 0x089ba188
 sw $v0,16($sp)
 move $a0,$s0
 jal 0x089b8050
 lw $a1,16($sp)
 lw $a0,16($sp)
 lw $v0,0($a0)
 lw $v0,0xe8($v0)
 jalr $v0
 nop
 lw $a0,16($sp)
 jal 0x089bb080
 move $a1,$s3
 lw $a0,16($sp)
 move $a1,$s1
 jal 0x089bb00c
 move $a2,$s2
 lw $a0,16($sp)
 lw $v0,0($a0)
 lw $v0,0x6c($v0)
 move $a1,$zero
 jalr $v0
 li $a2,14
 lw $v0,16($sp)
 append_done:
 lw $s3,28($sp)
 lw $s2,32($sp)
 lw $s1,36($sp)
 lw $s0,40($sp)
 lw $ra,44($sp)
 jr $ra
 addiu $sp,$sp,48
 ''','Append an owned native text child for the second line, 14 pixels below the first')
 setter=code('''addiu $sp,$sp,-80
 sw $ra,76($sp)
 sw $s0,72($sp)
 sw $s1,68($sp)
 sw $s2,64($sp)
 move $s0,$a0
 %s
 move $s1,$a1
 move $s2,$a1
 find_line:
 lhu $t0,0($s2)
 beqz $t0,one_line
 li $t1,10
 beq $t0,$t1,split_line
 nop
 b find_line
 addiu $s2,$s2,2
 one_line:
 move $s2,$zero
 b set_first
 nop
 split_line:
 sh $zero,0($s2)
 set_first:
 jal 0x0882b544
 move $a0,$s0
 beqz $s2,set_done
 li $t0,10
 sh $t0,0($s2)
 addiu $a0,$sp,16
 jal 0x089bba6c
 addiu $a1,$s0,0x124
 jal 0x089aa690
 addiu $a0,$s2,2
 move $a2,$v0
 move $a0,$s0
 addiu $a1,$s2,2
 jal 0x%x
 addiu $a3,$sp,16
 jal 0x089bba88
 addiu $a0,$sp,16
 set_done:
 lw $s2,64($sp)
 lw $s1,68($sp)
 lw $s0,72($sp)
 lw $ra,76($sp)
 jr $ra
 addiu $sp,$sp,80
 '''%(load('a1',buffer),second),'Set full first line and append the optional second line with native ownership')
 word(0x08948e0c,0x0c000000|(0x08969a00>>2),0x0c000000|(fmt>>2),'Format trait outside the original 20-byte stack buffer')
 word(0x08948fe0,0x0c000000|(0x0882b49c>>2),0x0c000000|(setter>>2),'Display full wrapped trait through native wide setter')
 word(0x0894841c,0x24060028,0x240600d3,'Trait below the abilities panel: local y211, screen y229')
 word(0x089476ac,0x24060058,0x24060050,'Remove eight empty pixels below the stats rows for the two-line trait area')
 word(0x08947fd0,0x24060058,0x24060050,'Keep the shorter frame when selecting Status or Abilities')
 tab=code('''addiu $sp,$sp,-32
 sw $ra,28($sp)
 sw $s0,24($sp)
 sw $s1,20($sp)
 move $s0,$a0
 jal 0x08947e84
 move $s1,$a1
 addiu $a0,$s0,-7920
 lw $v0,0($a0)
 li $t0,2
 beq $s1,$t0,hide_trait
 nop
 b apply_trait
 lw $v0,0xe8($v0)
 hide_trait:
 lw $v0,0xe4($v0)
 apply_trait:
 jalr $v0
 nop
 lw $s1,20($sp)
 lw $s0,24($sp)
 lw $ra,28($sp)
 jr $ra
 addiu $sp,$sp,32
 ''','Show traits on Status and Abilities; hide them behind the taller equipment tab')
 for pc in (0x089460d0,0x08946528,0x08947434,0x089474dc):
  word(pc,0x0c000000|(0x08947e84>>2),0x0c000000|(tab>>2),'Update profile visibility with the selected tab')
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph);allowed.update(range(phoff+48,phoff+56));assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(source,elf)))
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe};tb=rootmap[0x1e8000];ta,te=container(data,tb);oa,ote=container(original,0x1e8000);f,fp,fr=footer(member(oa,ote,25),V);del original
 ore=rebuild_root(data,{tb:rebuild_ez(ta,{25:pack(f)})},mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3]!=tb:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j!=25:assert aa[x:x+z]==bb[xx:xx+zz]
 report=dict(version=V,source_version='0.2.29',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=changes,wrappers=wrappers,buffer=hex(buffer),buffer_bytes=1024,guard=hex(guard),advance_table=hex(adv),wrap_metric_budget=280,position=[70,229],stats_frame_height=80,font_size=16,footer=fr,checks=dict(save_format='unchanged',translations='byte-identical',archive_members='byte-identical except version footer',other_executable_bytes='byte-identical'),texture_replacement=False,runtime_verification='pending')
 return elf,ore,fp,report

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,fp,r=build();print(json.dumps({k:v for k,v in r.items() if k!='footer'},indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.traits.elf').exists();(out/'EBOOT.traits.elf').write_bytes(elf);(out/'data.traits.ore').write_bytes(ore);(out/'traits.report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
  ui=ROOT/('work/ui/profile-traits-'+V);ui.mkdir(parents=True,exist_ok=True);fp.save(ui/'native-footer.png')
 print('Written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

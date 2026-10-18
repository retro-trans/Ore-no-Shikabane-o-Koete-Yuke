"""Fit battle choices, descriptions and consumable names. Dry run before --write."""
import argparse,hashlib,json,re,struct
import keystone
from catalog_text import ROOT,parse_mlt
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_mlt,rebuild_root,align
from strip_jp import export
from check_translation import tokens_equal
V='0.2.36';BASE=0x08803000
sha=lambda b:hashlib.sha256(b).hexdigest()
# Only over-budget consumable names change. Equipment/collectible names have different lists.
SHORT={2:'Firestorm Tsl.',3:'Oni Venom Tsl.',5:'Water-Up Tsl.',6:'Fire-Up Charm',7:'Wind-Up Charm',8:'Earth-Up Charm',11:'Swift Wind Tsl.',12:'Shadow Needle',13:'Flame Wind Tsl.',14:'Catfish Tsl.',15:'Spellseal Tsl.',16:'Thunder Drum Tsl.',17:'Sea God Tsl.',18:'Reversal Tsl.',19:'Firewalk Stone',21:'Water SPR Tnc.',22:'Wind SPR Tonic',23:'Earth SPR Tonic',25:'Water BOD Tnc.',26:'Wind BOD Tnc.',27:'Earth BOD Tnc.',29:'Water SKL Tnc.',35:'Spring Sleep P.',36:'Dark Delus. P.',37:"Arisu's Mirror",38:'Demonward Tsl.',53:'Div. Favor Orb',55:'Longlife Water',57:'Time-Climb Flute',58:'Sword Manual',59:'Naginata Man.',61:'Spear Manual',62:'Fist Manual',63:'Hammer Man.',64:'Gunnery Man.'}
SHORT.update({16:'Thunder Drum',38:'Demonward Tsl',57:'Timeclimb Flute'})
for g,first in [('SPR',41),('BOD',45),('SKL',49)]:
 for i,(e,p) in enumerate([('F','Liver'),('W','Milk'),('Wi','Ess.'),('E','Root')]):SHORT[first+i]='Prl. '+e+'-'+g+' '+p

def build():
 src=ROOT/'work/output/english-native-0.2.35';source=(src/'EBOOT.status.elf').read_bytes();data=(src/'data.status.ore').read_bytes()
 assert sha(source)=='487695396e0bb232ff0c37b76fab91513ef3ee40bace6b027fb530afd3f775a9';assert sha(data)=='f18bce8636930f9edc31332f9a743e19a93860e3060492d35953e43711a4057a'
 elf=bytearray(source);po=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,po+32));assert ph[1]+ph[4]==len(elf);patches=[];allowed=set();wrappers=[]
 def word(addr,old,new,note):
  p=addr-BASE;assert struct.unpack_from('<I',elf,p)[0]==old,hex(addr);struct.pack_into('<I',elf,p,new);allowed.update(range(p,p+4));patches.append(dict(address=hex(addr),before=hex(old),after=hex(new),purpose=note))
 def append(b):
  elf.extend(bytes(align(len(elf),16)-len(elf)));addr=ph[2]+len(elf)-ph[1];elf.extend(b);return addr
 def load(reg,a):return 'lui $%s,0x%x\n addiu $%s,$%s,%d'%(reg,(a+0x8000)>>16,reg,reg,((a&65535)^32768)-32768)
 metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];measure=lambda t:sum(metrics.get(str(ord(c)),{'advance':14})['advance'] for c in t)
 adv=append(bytes(metrics.get(str(i),{'advance':14})['advance'] for i in range(128)));buffer=append(bytes(2048));guard=append(b'BATTLE_HELP_END!')
 ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
 def code(t,note):
  addr=ph[2]+align(len(elf),16)-ph[1];b=bytes(ks.asm('.set noreorder\n'+t,addr=addr)[0]);assert append(b)==addr;wrappers.append(dict(address=hex(addr),bytes=len(b),purpose=note));return addr
 # Native cLabel does not honor LF. Split measured lines into owned native text
 # children, using the already verified trait helper and inherited font state.
 wrap=code('''addiu $sp,$sp,-96
 sw $ra,92($sp)
 sw $s0,88($sp)
 sw $s1,84($sp)
 sw $s2,80($sp)
 sw $s3,76($sp)
 move $s0,$a0
 %s
 move $t0,$s1
 li $t1,1023
 copy:
 beqz $a1,copy_done
 nop
 lhu $t2,0($a1)
 beqz $t2,copy_done
 nop
 sh $t2,0($t0)
 addiu $t0,$t0,2
 addiu $t1,$t1,-1
 bnez $t1,copy
 addiu $a1,$a1,2
 copy_done:
 sh $zero,0($t0)
 move $t0,$s1
 %s
 move $t2,$zero
 move $t3,$zero
 scan:
 lhu $t4,0($t0)
 beqz $t4,wrapped
 li $t5,10
 beq $t4,$t5,reset
 li $t5,32
 bne $t4,$t5,measure
 nop
 move $t3,$t0
 measure:
 sltiu $t5,$t4,128
 beqz $t5,add_width
 li $t6,14
 addu $t5,$t1,$t4
 lbu $t6,0($t5)
 add_width:
 addu $t2,$t2,$t6
 sltiu $t5,$t2,281
 bnez $t5,next
 nop
 beqz $t3,next
 li $t5,10
 sh $t5,0($t3)
 move $t0,$t3
 reset:
 move $t2,$zero
 move $t3,$zero
 next:
 b scan
 addiu $t0,$t0,2
 wrapped:
 move $s3,$zero
 line:
 move $s2,$s1
 find_end:
 lhu $t0,0($s2)
 beqz $t0,end_found
 li $t1,10
 beq $t0,$t1,break_found
 nop
 b find_end
 addiu $s2,$s2,2
 break_found:
 sh $zero,0($s2)
 b render
 nop
 end_found:
 move $s2,$zero
 render:
 bnez $s3,child
 move $a0,$s0
 jal 0x0882b544
 move $a1,$s1
 b rendered
 nop
 child:
 addiu $a0,$sp,16
 jal 0x089bba6c
 addiu $a1,$s0,0x124
 jal 0x089aa690
 move $a0,$s1
 move $a2,$v0
 move $a0,$s0
 move $a1,$s1
 jal 0x09cbb6c0
 addiu $a3,$sp,16
 beqz $v0,child_done
 move $a0,$v0
 lw $t9,0($a0)
 lw $t9,0x6c($t9)
 sll $a2,$s3,4
 jalr $t9
 move $a1,$zero
 child_done:
 jal 0x089bba88
 addiu $a0,$sp,16
 rendered:
 beqz $s2,done
 addiu $s3,$s3,1
 b line
 addiu $s1,$s2,2
 done:
 lw $s3,76($sp)
 lw $s2,80($sp)
 lw $s1,84($sp)
 lw $s0,88($sp)
 lw $ra,92($sp)
 jr $ra
 addiu $sp,$sp,96
 '''%(load('s1',buffer),load('t1',adv)),'Bounded display-only measured word wrap; owned text lines at 16-pixel pitch')
 for pc in (0x08868a04,0x0886b9b8):word(pc,0x0c000000|(0x0882b49c>>2),0x0c000000|(wrap>>2),'Wrap battle item/Skills descriptions without modifying their source text')
 for pc,old,new in [(0x08868c8c,48,84),(0x08868cb4,150,114),(0x0886b73c,48,64),(0x0886b76c,150,134)]:word(pc,0x24060000|old,0x24060000|new,'Grow tooltip upward while retaining bottom y198 above the battle HUD')
 table=0x08a2c538;assert struct.unpack_from('<11h',elf,table-BASE)==(2,1,0,2,32,16,8,8,8,8,0)
 p=table-BASE+8;struct.pack_into('<h',elf,p,84);allowed.update((p,p+1));word(0x0886f3c4,0x24a50018,0x24a50000,'Wide Items/Equipment submenu starts at main-menu left, clear of portraits')
 ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,po+32,*ph);allowed.update(range(po+48,po+56));assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
 # Canonical compact names and every translated reference use the same aliases.
 previous_report=ROOT/('work/output/english-native-'+V+'/battle-menu.report.json')
 before_rows={(x['batch'],x['id']):x['before'] for x in json.loads(previous_report.read_text()).get('text_edits',[])} if previous_report.exists() else {}
 def working_batch(path):
  b=json.loads(path.read_text(encoding='utf-8'))
  for row in b.get('rows',[]):
   if (path.stem,row.get('id')) in before_rows:row['translation_en']=before_rows[path.stem,row['id']]
  return b
 canonical=working_batch(ROOT/'work/translation/en/items_batch_001.json');names=[r for r in canonical['rows'] if r['kind']=='item_name'];assert len(names)==66
 aliases={};nameproof=[];budget=measure('Young Leaf Pills')
 for row in names:
  old=row['translation_en'];new=SHORT.get(row['index'],old) if measure(old)>budget else old
  assert measure(new)<=budget,(row['index'],new,measure(new),budget)
  if new!=old:aliases[old]=new
  nameproof.append(dict(id=row['id'],before=old,after=new,metric_width=measure(new),reference_budget=budget))
 assert len(set(x['after'] for x in nameproof))==66
 aliases['Skills / Other']='Skills';pattern=re.compile('|'.join(re.escape(s) for s in sorted(aliases,key=len,reverse=True)))
 batches={};updates={};edits=[]
 for path in (ROOT/'work/translation/en').glob('*.json'):
  if path.name.endswith('.en.json'):continue
  b=working_batch(path);changed=False
  for row in b.get('rows',[]):
   old=row.get('translation_en','');new=pattern.sub(lambda m:aliases[m.group()],old)
   if new==old:continue
   assert tokens_equal(row['source_jp'],new)
   key=(row['section'],row['index']);memberkey=(row['archive_offset'],row['member_entry']);previous=updates.setdefault(memberkey,{})
   if key in previous:assert previous[key]==(old,new)
   previous[key]=(old,new);row['translation_en']=new;row['fit_status']='pending_selected_context_'+V;row.setdefault('review_notes',[]).append('Compact battle UI alias; retains item identity. Previous English: '+old);changed=True;edits.append(dict(id=row['id'],before=old,after=new,batch=path.stem))
  if changed:b['version']=V;batches[path]=b
 original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(z[3] for z in be if z[0]==i) for i,_,_,o in oe};replacements={};changed_members={}
 for (oldbase,entry),rows in updates.items():
  base=rootmap[oldbase];arc,en=container(data,base);mlt=member(arc,en,entry);lookup={(s,i):t for s,i,_,t in parse_mlt(mlt)};assert all(lookup[k]==old for k,(old,new) in rows.items()),(hex(oldbase),entry)
  rebuilt=rebuild_mlt(mlt,{k:new for k,(old,new) in rows.items()});assert {(s,i):t for s,i,_,t in parse_mlt(rebuilt)}=={k:rows[k][1] if k in rows else t for k,t in lookup.items()};replacements.setdefault(base,{})[entry]=pack(rebuilt);changed_members.setdefault(base,set()).add(entry)
 tb=rootmap[0x1e8000];ot,ote=container(original,0x1e8000);f,fp,fr=footer(member(ot,ote,25),V);replacements.setdefault(tb,{})[25]=pack(f);changed_members.setdefault(tb,set()).add(25);del original
 rootupdates={base:rebuild_ez(container(data,base)[0],members) for base,members in replacements.items()};ore=rebuild_root(data,rootupdates,mutable=True);ae,aend=root_entries(ore)
 for n,(a,b) in enumerate(zip(be,ae)):
  sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047);aa=data[a[3]:sa];bb=ore[b[3]:sb]
  if a[3] not in replacements:assert aa==bb
  else:
   _,ar=container(aa,0);_,br=container(bb,0)
   for j,((_,z,x,_),(_,zz,xx,_)) in enumerate(zip(ar,br)):
    if j not in changed_members[a[3]]:assert aa[x:x+z]==bb[xx:xx+zz]
 glossary=json.loads((ROOT/'work/glossary/core.json').read_text(encoding='utf-8'))
 for term in glossary['terms']:
  if term['en'] in aliases:term['full_english_before_compact_alias']=term['en'];term['en']=aliases[term['en']]
 r=dict(version=V,source_version='0.2.35',elf_sha256=sha(elf),archive_sha256=sha(ore),elf_bytes=len(elf),archive_bytes=len(ore),patches=patches,wrappers=wrappers,buffer=hex(buffer),guard=hex(guard),advance_table=hex(adv),buffer_bytes=2048,wrap_metric_budget=280,line_pitch=16,existing_child_helper='0x09cbb6c0',names=nameproof,aliases=aliases,text_edits=edits,submenu=dict(table=hex(table),cell_before=32,cell_after=84,x_offset=0),layout=dict(item_tooltip=[206,114,266,84],skills_tooltip=[206,134,264,64]),checks=dict(item_ids_effects_and_inventory='Byte-identical',source_descriptions='Unchanged except consistent item-name references',unrelated_members='Byte-identical except footer',prior_icons_profiles_and_catalog='Preserved',gameplay_and_save_format='Unchanged'),footer=fr,texture_replacement=False,runtime_verification='pending')
 return elf,ore,fp,r,batches,glossary
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();elf,ore,fp,r,batches,g=build();print(json.dumps(dict(version=V,elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],patches=r['patches'],submenu=r['submenu'],names_changed=[x for x in r['names'] if x['before']!=x['after']],translated_reference_rows=len(r['text_edits']),layout=r['layout']),indent=2))
 if a.write:
  out=ROOT/('work/output/english-native-'+V);out.mkdir(exist_ok=True);assert not (out/'EBOOT.bmenu.elf').exists();(out/'EBOOT.bmenu.elf').write_bytes(elf);(out/'data.bmenu.ore').write_bytes(ore);(out/'battle-menu.report.json').write_text(json.dumps(r,indent=2)+'\n');ui=ROOT/('work/ui/battle-menu-'+V);ui.mkdir(exist_ok=True);fp.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(r['layout'],indent=2)+'\n')
  for path,b in batches.items():path.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');path.with_suffix('.en.json').write_text(json.dumps(export(path),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  (ROOT/'work/glossary/core.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(ROOT/'work/glossary/battle_abbreviations.json').write_text(json.dumps(dict(version=V,abbreviations={'Tsl.':'Talisman','Tnc.':'Tonic','Prl.':'Peerless','F':'Fire','W':'Water','Wi':'Wind','E':'Earth','SPR':'Spirit','BOD':'Body','SKL':'Skill','Ess.':'Essence','P.':'Powder','Man.':'Manual','Div.':'Divine'},aliases=r['aliases']),indent=2)+'\n')
 print('Written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

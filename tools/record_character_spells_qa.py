"""Package verified 0.2.21 and record the selected UI checks. Dry run unless --write."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image
from catalog_text import ROOT
VERSION='0.2.21';UI=ROOT/'work/ui/character-spells-0.2.21'
SCREENS={
 'title.png':'Version 0.2.21 and full project URL',
 'clan-actions.png':'English Head, Leader and Party role flags retained',
 'selector-first.png':'Red portrait selector covers the name and age rows',
 'selector-second.png':'Selector follows the second portrait and its full height',
 'mini-equipment.png':'Equipment and its selection outline fit inside the wider submenu',
 'mini-training.png':'Both rows and columns of the wider submenu fit',
 'spells-after.png':'English Spirit/Skill requirements, MP and complete colored legend; two wide spell columns',
 'spells-scrolled.png':'Native paging reaches later spells; full selection and cell backgrounds stay aligned',
 'spells-second.png':'Second character, eight-letter name and separate age/MP rows'}
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 source=ROOT/'work/output/english-native-0.2.21d';stable=ROOT/'work/output/english-native-0.2.21';backup=ROOT/'work/source/qa-character-components-0.2.21a'
 if not source.exists():source=stable
 r=json.loads((source/'character.report.json').read_text());proof=json.loads((UI/'runtime-patches.json').read_text())
 assert len(proof['native_patches_verified'])==28 and proof['elf_sha256']==r['elf_sha256'] and proof['iso']=='work/source/qa-character-0.2.21d.iso'
 assert sha(source/'EBOOT.character.elf')==r['elf_sha256'] and sha(source/'data.character.ore')==r['archive_sha256']
 screens=[]
 for n,scope in SCREENS.items():
  p=UI/n;assert Image.open(p).size==(480,272) and json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False
  screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p),observed=scope,fit='pass'))
 assert json.loads((UI/'font-spells.json').read_text())['result']=='PASS'
 assert 'PASS:' in (ROOT/'work/source/test-character-0.2.21.txt').read_text()
 assert 'ALL 49 BATCHES PASS' in (ROOT/'work/source/check-translations-0.2.21.txt').read_text()
 candidate=ROOT/'work/source/qa-character-0.2.21d.iso';final=ROOT/'work/output/english-native-0.2.21.iso'
 identity=dict(version=VERSION,tested_iso=candidate.relative_to(ROOT).as_posix(),delivered_iso=final.relative_to(ROOT).as_posix(),bytes=candidate.stat().st_size,sha256=sha(candidate))
 print(json.dumps(dict(write=a.write,screens=len(screens),new_graphics=r['graphics'],new_captions=r['literals'],iso=identity,component_promotion=[str(source),str(stable)],preserve_first_candidate_components=str(backup)),indent=2))
 if not a.write:return
 if source!=stable:
  for p in (source,stable,backup):assert ROOT.resolve() in p.resolve().parents
  assert not backup.exists();shutil.move(str(stable),str(backup));shutil.move(str(source),str(stable))
 if not final.exists():shutil.copyfile(candidate,final)
 assert sha(final)==identity['sha256'] and final.stat().st_size==identity['bytes']
 manifest=json.loads(candidate.with_suffix('.manifest.json').read_text())
 for f in manifest['files']:
  if 'english-native-0.2.21d' in f['replacement']:f['replacement']=f['replacement'].replace('english-native-0.2.21d','english-native-0.2.21')
 dump(final.with_suffix('.manifest.json'),manifest);dump(UI/'image-identity.json',identity)
 layout=dict(version=VERSION,native_resolution=[480,272],character_submenu=dict(rows=2,columns=2,text_cell_width=84),portrait_card_height=116,portrait_selector=dict(additional_height=12,old_image_height=110,new_image_height=122),spells=dict(rows=7,columns=2,cell_width=108,background_width=108,text_budget=107,fixed_names=96,max_fixed_name_width=94.28571428571429,paging='native',name_y=82,age_y=98,mp_y=114,mp_bar_y=132,legend_font_size=16,legend_pitch=70,stat_caption_font_size=16,mp_required_caption_x=120),role_badges='Head / Leader / Party retained from 0.2.20',texture_replacement=False)
 dump(UI/'layout.json',layout)
 verification=dict(version=VERSION,result='PASS: selected requested character and spell screens',component_sha256=dict(elf=r['elf_sha256'],archive=r['archive_sha256']),screens=screens,native_mips=(ROOT/'work/source/test-character-0.2.21.txt').read_text().strip(),runtime_patches=28,appended_wrappers=9,native_font='Actual dynamic caption glyphs checked against embedded 4x atlas and UVs',layout=layout,checks=r['checks'],github_release=False,limits=['Selected two-character test save and native spell scrolling; full-playthrough and real PSP testing remain pending'])
 dump(UI/'verification.json',verification);r['runtime_verification']='PASS: work/ui/character-spells-0.2.21/verification.json';r['static_spell_names']=dict(records=96,max_width=94.28571428571429,text_budget=107);dump(stable/'character.report.json',r)
 dump(ROOT/'work/translation/en/character/literals.en.json',dict(version=VERSION,rows=r['literals'],status='Draft; selected native font and fit verified',evidence='work/ui/character-spells-0.2.21/verification.json'))
 dump(ROOT/'work/translation/en/graphics/character_spells.en.json',dict(version=VERSION,rows=[dict(**x,label_rectangle=[0,0,32,16],fit_evidence='work/ui/character-spells-0.2.21/spells-after.png') for x in r['graphics']]))
 dump(ROOT/'work/glossary/character_ui.json',dict(version=VERSION,scope='Compact spell requirement captions; Spirit and Skill follow core glossary',terms=[dict(jp='\u5fc3\u4fee\u5f97',en='Spirit Req.',context='Spirit stats required to learn the selected spell'),dict(jp='\u5fc3\u73fe\u5728',en='Spirit Now',context='Current Spirit stats'),dict(jp='\u6280\u4fee\u5f97',en='Skill Req.',context='Skill stats required to learn the selected spell'),dict(jp='\u6280\u73fe\u5728',en='Skill Now',context='Current Skill stats'),dict(jp='\u6280\u529b',en='MP',context='Magic points badge')]))
 p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text(encoding='utf-8'));q['latest_evidence_version']=VERSION;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/character-spells-0.2.21/verification.json',scope='Character submenu, full portrait selector, English spell labels and paging; core fit count unchanged')];dump(p,q)
 p=ROOT/'docs/local_build_status.json';s=json.loads(p.read_text(encoding='utf-8'));s.update(latest_local_build=VERSION,archive_translation_version=VERSION,build_date='2026-10-18',file=identity['delivered_iso'],bytes=identity['bytes'],sha256=identity['sha256'],native_graphic_labels=35,additional_character_native_literals=7,character_spells_ui_evidence='work/ui/character-spells-0.2.21/verification.json');s['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/character-spells-0.2.21/title.png');s['checks']['character_submenu_and_selector']='PASS: wider 2x2 submenu; twelve-pixel taller selector covers both portrait cards';s['checks']['spell_screen']='PASS: English MP/Spirit/Skill and complete native-font legend; two-column cell/background geometry; separate eight-letter name/age/MP rows; native paging retained';dump(p,s)
 p=ROOT/'CHANGELOG.md';text=p.read_text(encoding='utf-8');entry='''## 0.2.21 (2026-10-18)

- Translated the remaining visible spell-screen labels: MP, Spirit Req./Now and Skill Req./Now. Kept the English Head/Leader/Party flags from 0.2.20. The complete colored availability legend now uses the native HD font.
- Widened both character submenu columns from 32 to 84 pixels. Extended the red portrait selection image by the same 12 pixels added to the name/age cards.
- Reorganized spells into two 108-pixel columns with matching backgrounds/highlights and native scrolling. All 96 fixed spell names fit the measured 107-pixel text budget. Separated long character names, age and MP into rows, and spaced the MP Required caption clear of the badge.
- Verified 28 guarded native instructions and nine appended wrappers, actual MIPS geometry/caller state, native font atlas/UVs, both character selectors and later spell pages in PPSSPP. All 49 translation batches pass; scripts and unrelated archive payloads match 0.2.20. Evidence: work/ui/character-spells-0.2.21/. Original project-profile saves restored after QA. Local test build; no GitHub release. Full-game and physical PSP QA remain pending.

'''
 if '## 0.2.21 ' not in text:text=text.replace('# Changelog\n\n','# Changelog\n\n'+entry)
 p.write_text(text,encoding='utf-8')
 p=ROOT/'README.md';text=p.read_text(encoding='utf-8');line='- `work/output/english-native-0.2.21.iso`: English character/spell labels, wider character submenu, full-height portrait selector, two-column spell grid and separated name/age/MP rows. See [layout notes](docs/character-spells-layout.txt).\n'
 if line not in text:text=text.replace('- `work/output/english-native-0.2.20.iso`',line+'- `work/output/english-native-0.2.20.iso`',1)
 p.write_text(text,encoding='utf-8')
 (ROOT/'docs/character-spells-layout.txt').write_text('''Character and spell UI — local build 0.2.21

Input: delivered 0.2.20 components, pinned hashes in build_character_spells.py.
Native 480x272 coordinates are recorded in work/ui/character-spells-0.2.21/layout.json.
Popup text cells: two rows/columns, width84. Red roster selector: original
110-pixel image height plus12, matching the extended cards and age row.
Spells: two columns, seven visible rows, width108; all three paths assigning
the native cell background apply the same width. Native ordering, filtering,
scrolling and controls remain. All96 fixed spell names measure at most94.286
pixels inside a107-pixel budget. Character name/age/MP rows are separated.
The colored legend uses complete ASCII labels and the embedded4x VWF.
Spirit/Skill captions replace the obsolete Japanese pictogram plus text;
Req. identifies learning requirements and Now identifies current stats.
The MP graphic uses the existing native palette. Role flags retain0.2.20.

Build: build_character_spells.py (dry run, then --write); build_iso.py.
Checks: test_character_spells.py, verify_character_runtime.py,
check_shop_font.py, all49 translation batches and actual framebuffer captures.
Final ISO matches the tested qa-character-0.2.21d.iso byte-for-byte.
Script payloads, original save record structures and unrelated archive members
remain unchanged. Temporary project QA saves are restored after testing.
Selected contexts are verified; full-playthrough and real PSP QA remain pending.
''',encoding='utf-8')
if __name__=='__main__':main()

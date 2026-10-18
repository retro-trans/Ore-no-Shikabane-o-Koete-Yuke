"""Record four battle-menu fixes and local build identity. Dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.36';UI=ROOT/('work/ui/battle-menu-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();r=json.loads((OUT/'battle-menu.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
assert sha(OUT/'EBOOT.bmenu.elf')==r['elf_sha256'] and sha(OUT/'data.bmenu.ore')==r['archive_sha256']
runtime=json.loads((UI/'runtime-patches.json').read_text());mips=json.loads((UI/'mips-tests.json').read_text());assert runtime['result']==mips['result']=='PASS' and runtime['elf_sha256']==mips['elf_sha256']==r['elf_sha256'] and mips['description_cases']==226
for context in ('main-menu','submenu','evergreen-help','divine-orb','ring-help'):
 f=json.loads((UI/('font-'+context+'.json')).read_text());assert f['result']=='PASS' and f['version']==V
save=json.loads((UI/'save-preservation.json').read_text());assert save['result']=='PASS' and save['user_source_unchanged'] and save['original_project_hashes']==save['restored_project_hashes']
screens=[]
for name in ('title','main-menu','equipment-submenu','evergreen-help','divine-orb','ring-help'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
assert len(r['names'])==66 and all(x['metric_width']<=x['reference_budget'] for x in r['names']);changed=sum(x['before']!=x['after'] for x in r['names']);assert changed==47
identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso));proof=dict(version=V,result='PASS: separate battle commands, full Equipment submenu, complete wrapped tooltips and compact consumable names',iso=identity,screens=screens,runtime=runtime,mips=mips,names_checked=66,names_shortened=changed,reference='Young Leaf Pills',layout=r['layout'],checks=r['checks'],texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=['Visual battle checks cover the reported menus, ring tooltip, Evergreen Elixir and Div. Favor Orb. Other descriptions/names passed measured MIPS/static checks.','Full playthrough and physical PSP testing remain pending.'])
print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],names_shortened=changed,names_checked=66,description_cases=226,screens=len(screens)),indent=2))
if not a.write:raise SystemExit
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'battle-menu.report.json',r)
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],battle_menu_evidence='work/ui/battle-menu-0.2.36/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/battle-menu-0.2.36/title.png');q['checks']['battle_command_items_and_help']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,battle_menu_evidence='work/ui/battle-menu-0.2.36/verification.json');dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/battle-menu-0.2.36/verification.json',scope=proof['result']+'; accumulated indexed fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.36 (2026-10-18)

- Shortened the battle command Skills / Other to Skills and updated translated references, so it fits beside Retreat in the existing two-column command menu.
- Widened the Items/Equipment popup to contain Equipment and aligned it with the main menu's left edge, keeping it clear of the party portraits.
- Added measured wrapping for battle item and Skills descriptions. The complete source text is split into owned native text children at 16-pixel spacing; plain newlines alone are ignored by this renderer. Grew tooltips upward to retain their existing bottom edge above the battle HUD.
- Audited all 66 consumable names against Young Leaf Pills' width. Shortened 47 overlong names, retaining distinct element/stat/material identities; updated translated references and the glossary consistently. Evergreen Elixir and other names already within the budget remain unchanged. Equipment and collectible names use their existing wider lists.
- Passed actual MIPS wrapping checks for all 223 item descriptions and three Skills descriptions: complete text, source buffers, line widths, up to three lines, child spacing, buffer guard and caller registers/stack. Verified the final ISO's battle menu, Equipment popup, full ring/Elixir tooltips and Div. Favor Orb slot, including native 4x font UV checks. Seven native hooks/coordinates, submenu width and wrap code read back correctly.
- Item IDs, effects, inventory, gameplay, saved data and earlier icons/profile/catalog fixes remain unchanged. Isolated QA saves restored and user source save verified unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

'''
if '## 0.2.36 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.35**, 2026-10-18; archive-text draft: **0.2.34**.','Current local test build: **0.2.36**, 2026-10-18; archive-text draft: **0.2.36**.');line='- `work/output/english-native-0.2.36.iso`: clear battle commands, wide Equipment popup, wrapped descriptions and compact consumable names. See [QA evidence](work/ui/battle-menu-0.2.36/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.35.iso`',line+'- `work/output/english-native-0.2.35.iso`',1)
p.write_text(s,encoding='utf-8')
dump(ROOT/'work/translation/en/executable/battle_tooltip.en.json',dict(version=V,scope='Native battle tooltip layout and measured wrapping',layout=r['layout'],name_budget=dict(reference='Young Leaf Pills',metric_units=110,consumables=66,shortened=47),abbreviations='work/glossary/battle_abbreviations.json'))

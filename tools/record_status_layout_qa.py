"""Record status frame and Potential spacing checks; dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.35';UI=ROOT/('work/ui/status-layout-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();r=json.loads((OUT/'status.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
assert sha(OUT/'EBOOT.status.elf')==r['elf_sha256'] and sha(OUT/'data.status.ore')==r['archive_sha256']
runtime=json.loads((UI/'runtime-patches.json').read_text());assert runtime['result']=='PASS' and runtime['elf_sha256']==r['elf_sha256'] and len(runtime['patches'])==11
for name in ('hayate','kirara'):
 f=json.loads((UI/('font-'+name+'.json')).read_text());assert f['result']=='PASS' and f['version']==V and {'Spirit','Skill','Body'}<={x['text'] for x in f['objects']}
save=json.loads((UI/'save-preservation.json').read_text());assert save['result']=='PASS' and save['user_source_unchanged'] and save['original_project_hashes']==save['restored_project_hashes']
screens=[]
for name in ('title','hayate','kirara','abilities','equipment','returned-abilities','reentered'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
proof=dict(version=V,result='PASS: traits enclosed by full-height Status/Abilities frame; Potential group names clear of gold axis and elements',iso=identity,screens=screens,runtime_patch_proof=runtime,layout=r['layout'],checks=r['checks'],oreshika_symbols=r['source_icons'],texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=['Icon search covers the inspected common/status/icon sheets; no claim of an exhaustive search of every game resource.','Full playthrough and physical PSP testing remain pending.'])
print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],screens=len(screens)),indent=2))
if not a.write:raise SystemExit
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'status.report.json',r)
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],status_layout_evidence='work/ui/status-layout-0.2.35/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/status-layout-0.2.35/title.png');q['checks']['status_frame_and_potential']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,status_layout_evidence='work/ui/status-layout-0.2.35/verification.json');dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/status-layout-0.2.35/verification.json',scope=proof['result']+'; text coverage counts unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.35 (2026-10-18)

- Extended the Status and Abilities frames to 108 pixels, matching Equipment, so the complete Creed/Saying text sits inside the box. Existing two-line formatting and Equipment trait visibility remain unchanged.
- Gave Potential's full Spirit, Skill and Body labels a separate column: inset labels, moved the gold axis and element icons right, and aligned the bars/grid beside them. Reduced only the display width scale to keep maximum bars inside the existing frame. Stat values, calculations and saved data are unchanged.
- Inspected supplied Oreshika US status, shared icon and common UI sheets. No dedicated pictograms for the three category names were identified in those sheets; retained readable full labels. Existing original Oreshika vital and element symbols remain unchanged. Additional sheet audit records unsupported layouts rather than claiming they were inspected.
- Kept the header and its owned trait text above the enlarged background through the native draw key in both character-screen constructors. Verified final-ISO character screens and switching between Status, Abilities and Equipment, including returning to Abilities. Native font UV checks cover the full group captions and reported traits. Readback verifies eight geometry/layer instructions, the display scale and embedded grid pixels/palette. Existing executable allocation, translations, catalog fixes and unrelated archive members are unchanged except the title version footer.
- Original isolated QA saves restored; user source save unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

'''
if '## 0.2.35 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8')
p=ROOT/'docs/status-layout.txt';p.write_text('''Status layout — local build 0.2.35

Status and Abilities share Equipment's 108-pixel frame height. The trait
remains at (70,229), with an optional second line at y243. Both character
constructors register the header at native draw key 0x8001, above the
stats background. Native removal uses the existing object registration;
trait ownership, tab visibility and text wrapping are unchanged.

Within the 142-pixel Potential panel: labels x4; gold axis x40; elements
x44; bars x62 with a display maximum of 76 pixels, ending at x138.
The existing grid image is updated in place. Stat values and save records
are unchanged. No new resident texture memory is allocated.

Original Oreshika HP/MP/Health and element sprites remain. No dedicated
Spirit/Skill/Body pictograms were identified in the inspected US status,
common and icon sheets. The additional sheet audit lists undecoded layouts
explicitly; this is not an exhaustive absence claim for the entire game.

Screenshots, native font checks, runtime patch readback and save preservation:
work/ui/status-layout-0.2.35/verification.json
''',encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.34**,','Current local test build: **0.2.35**,');line='- `work/output/english-native-0.2.35.iso`: extended Status/Abilities frame around character traits and separate Potential label/axis/icon columns. See [QA evidence](work/ui/status-layout-0.2.35/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.34.iso`',line+'- `work/output/english-native-0.2.34.iso`',1)
p.write_text(s,encoding='utf-8')

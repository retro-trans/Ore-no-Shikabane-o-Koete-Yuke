"""Record widened home-menu help and local build identity. Dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.38';UI=ROOT/('work/ui/home-help-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((OUT/'home.report.json').read_text());assert sha(OUT/'EBOOT.home.elf')==r['elf_sha256'] and sha(OUT/'data.home.ore')==r['archive_sha256'];runtime=json.loads((UI/'runtime-patches.json').read_text());assert runtime['result']=='PASS' and runtime['elf_sha256']==r['elf_sha256']
font=json.loads((UI/'font-rest.json').read_text());assert font['result']=='PASS' and font['version']==V
lines=["Rest for one month to restore everyone's Health.",'You cannot go on a sortie or perform Divine Union.'];tree=json.loads((UI/'rest-text.json').read_text());assert set(lines)<={x['text'] for x in tree}
for line in lines:
 t=next(x for x in tree if x['text']==line);assert any(x['vtable']=='0x8a208b8' and x['geometry']==[24,214,432,50] for x in t['ancestors']);assert t['ancestors'][1]['geometry'][2]==426
assert len(r['measured_rows'])==34 and all(max(x['line_advances'])<=426 for x in r['measured_rows'])
save=json.loads((UI/'save-preservation.json').read_text());assert save['result']=='PASS' and save['user_source_unchanged'] and save['original_project_hashes']==save['restored_project_hashes']
screens=[]
for name in ('title','rest','divine-union'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
iso=ROOT/('work/output/english-native-'+V+'.iso');identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso));proof=dict(version=V,result='PASS: centered wider home description box; complete Rest text',iso=identity,screens=screens,runtime=runtime,layout=r['layout'],measured_entries=34,longest_measured_line=max(max(x['line_advances']) for x in r['measured_rows']),wording='All unchanged',texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=['Rest and Divine Union descriptions checked on the final ISO; all 34 related fixed help entries measured against the width.','Full playthrough and physical PSP testing pending.'])
print(json.dumps(dict(write=a.write,result=proof['result'],iso=identity,layout=r['layout'],measured_entries=34),indent=2))
if not a.write:raise SystemExit
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'home.report.json',r)
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],home_help_evidence='work/ui/home-help-0.2.38/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/home-help-0.2.38/title.png');q['checks']['home_description_box']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,home_help_evidence='work/ui/home-help-0.2.38/verification.json');dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/home-help-0.2.38/verification.json',scope=proof['result']+'; accumulated indexed fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.38 (2026-10-18)

- Extended the home menu description panel from 288 to 432 native pixels and kept it centered, moving its left edge from 96 to 24. Both Rest description lines now sit inside the box with comfortable right-side clearance.
- Kept all wording, line breaks, vertical positions and visual styling. The shared native resize automatically expands each help line to 426 pixels. Prior story dialogue width/transparency and other fixes remain unchanged.
- Measured all 34 related fixed help entries; the widest line is 378.857 pixels. Verified Rest and Divine Union descriptions in the final ISO, complete Rest text using native 4x glyphs, actual panel/line geometry and both patched instructions.
- Restored the isolated test saves and verified the user save source unchanged. Local test build only; no release. Full-playthrough and physical PSP testing remain pending.

'''
if '## 0.2.38 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.37**, 2026-10-18; archive-text draft: **0.2.37**.','Current local test build: **0.2.38**, 2026-10-18; archive-text draft: **0.2.38**.');line='- `work/output/english-native-0.2.38.iso`: centered wider home-menu description box, including complete Rest help. See [QA evidence](work/ui/home-help-0.2.38/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.37.iso`',line+'- `work/output/english-native-0.2.37.iso`',1)
p.write_text(s,encoding='utf-8')

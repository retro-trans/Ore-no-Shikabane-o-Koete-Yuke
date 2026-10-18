"""Record final native Item Catalog screen checks; dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
from strip_jp import export
V='0.2.34';UI=ROOT/('work/ui/catalog-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((OUT/'catalog.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
assert sha(OUT/'EBOOT.catalog.elf')==r['elf_sha256'] and sha(OUT/'data.catalog.ore')==r['archive_sha256']
runtime=json.loads((UI/'runtime-patches.json').read_text());mips=json.loads((UI/'mips-tests.json').read_text());assert runtime['result']==mips['result']=='PASS' and mips['cases']==12 and runtime['elf_sha256']==mips['elf_sha256']==r['elf_sha256']
for name in ('other','curios','scrolls'):
 f=json.loads((UI/('font-'+name+'.json')).read_text());assert f['result']=='PASS' and f['version']==V
 if name=='scrolls':assert '0/73' in {x['text'] for x in f['objects']} and 'items' not in {x['text'] for x in f['objects']}
 if name=='curios':assert 'Acquired' in {x['text'] for x in f['objects']} and 'Total Acquired' not in {x['text'] for x in f['objects']}
saves=json.loads((UI/'save-preservation.json').read_text());assert saves['result']=='PASS' and saves['user_source_unchanged'] and saves['original_project_hashes']==saves['restored_project_hashes']
screens=[]
for name in ('weapons','other','curios','scrolls'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
proof=dict(version=V,result='PASS: clear catalog tabs and escape statistics; Acquired caption; Scrolls 0/73 without items',iso=identity,screens=screens,runtime_patch_proof=runtime,mips=mips,native_font='Changed captions and fraction verified against native 4x glyph UVs',layout=r['layout'],checks=r['checks'],texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=['Full playthrough and physical PSP testing remain pending.'])
print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],screens=len(screens)),indent=2))
if not a.write:raise SystemExit
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'catalog.report.json',r)
dump(ROOT/'work/glossary/catalog.json',dict(version=V,terms=[dict(translation_en='Acquired',context='Item Catalog quantity caption',replaces='Total Acquired')],scrolls_fraction='%d/%d',shared_items_suffix='Retained outside Scrolls'))
p=ROOT/'work/translation/en/ui_batch_011.json';q=json.loads(p.read_text(encoding='utf-8'))
for x in q['rows']:
 if x['id']==r['text_edit']['id']:x['fit_status']='verified_selected_context_'+V
p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');dump(p.with_suffix('.en.json'),export(p))
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],catalog_evidence='work/ui/catalog-0.2.34/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/catalog-0.2.34/native-footer.png');q['checks']['item_catalog_layout']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,catalog_evidence='work/ui/catalog-0.2.34/verification.json');dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/catalog-0.2.34/verification.json',scope=proof['result']+'; indexed text fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.34 (2026-10-18)

- Widened Item Catalog category cells so Weapons and Armor no longer overlap. Native tab navigation and selection frames remain aligned.
- Separated the Other tab's escape quantities from Total Value rows and moved the collection caption/bar down to fit. Counts, money totals and collection calculations are unchanged.
- Changed Curios Total Acquired to Acquired and separated its heading, caption and count. Scrolls now shows a single compact fraction such as 0/73; removed its items suffix locally, preserving other shared item labels.
- Final ISO screen captures and native 4x glyph-UV checks cover Other, Curios and Scrolls; runtime readback verifies 27 instruction edits, tab width and both tiny adapters. Twelve MIPS adapter cases verify counts from zero to all 73 and preserve caller registers/stack. Unrelated archive members and previous translations/icons remain unchanged, except the title version footer.
- Restored isolated QA saves and verified the user source save was unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

'''
if '## 0.2.34 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.33**, 2026-10-18; archive-text draft: **0.2.33**.','Current local test build: **0.2.34**, 2026-10-18; archive-text draft: **0.2.34**.');line='- `work/output/english-native-0.2.34.iso`: Item Catalog overlap fixes, compact Acquired caption and Scrolls fraction without items. See [QA evidence](work/ui/catalog-0.2.34/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.33.iso`',line+'- `work/output/english-native-0.2.33.iso`',1)
p.write_text(s,encoding='utf-8')

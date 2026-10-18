"""Record translated Chronicle dates, navigation fit and local build identity."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
from strip_jp import export
V='0.2.33';UI=ROOT/('work/ui/chronicle-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((OUT/'chronicle.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
assert sha(OUT/'EBOOT.chronicle.elf')==r['elf_sha256'] and sha(OUT/'data.chronicle.ore')==r['archive_sha256']
runtime=json.loads((UI/'runtime-patches.json').read_text());mips=json.loads((UI/'mips-tests.json').read_text())
assert runtime['result']=='PASS' and runtime['elf_sha256']==r['elf_sha256'] and mips['result']=='PASS' and mips['elf_sha256']==r['elf_sha256'] and mips['cases']==18
fonts=[];headings=[]
for context in ('chronicle','chronicle-next','chronicle-prev'):
 f=json.loads((UI/('font-'+context+'.json')).read_text());assert f['result']=='PASS' and f['version']==V
 heading=[x['text'] for x in f['objects'] if x['text'].startswith('Events: ')];assert len(heading)==1;headings.append(heading[0]);fonts.append(f)
assert headings==['Events: 1018 / ?','Events: 1018 /  4','Events: 1018 / ?']
assert {'Year Start','Prev','Next','Next Year'}<={x['text'] for x in fonts[0]['objects']}
saves=json.loads((UI/'save-preservation.json').read_text());assert saves['result']=='PASS' and saves['user_source_unchanged'] and saves['original_project_hashes']==saves['restored_project_hashes']
screens=[]
for name in ('title','chronicle','chronicle-next','chronicle-prev'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
proof=dict(version=V,result='PASS: English Chronicle heading, clear navigation labels and month changes',iso=identity,screens=screens,runtime_patch_proof=runtime,mips=mips,native_font='Both date forms and visible navigation captions use the embedded 4x English atlas; glyph UVs verified',paging_headings=headings,layout=r['layout'],checks=r['checks'],texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=['Full playthrough and physical PSP testing remain pending.'])
print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],translated_native_formats=2,compact_navigation_captions=3,paging_headings=headings),indent=2))
if not a.write:raise SystemExit
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'chronicle.report.json',r)
dump(ROOT/'work/translation/en/executable/chronicle.en.json',dict(version=V,rows=r['literals'],layout=r['layout'],source='Native Chronicle heading formatter; both parameter sequences retained'))
dump(ROOT/'work/glossary/chronicle.json',dict(version=V,terms=[dict(source_jp='\u51fa\u6765\u4e8b',translation_en='Events',context='Chronicle date heading'),dict(source_jp='\u5e74\u982d',translation_en='Year Start',context='Chronicle L navigation'),dict(source_jp='\u7fcc\u5e74',translation_en='Next Year',context='Chronicle R navigation'),dict(source_jp='\u5148\u6708',translation_en='Prev',context='Previous Chronicle month'),dict(source_jp='\u7fcc\u6708',translation_en='Next',context='Next Chronicle month')]))
p=ROOT/'work/translation/en/ui_batch_012.json';q=json.loads(p.read_text(encoding='utf-8'));ids={x['id'] for x in r['text_edits']}
for x in q['rows']:
 if x['id'] in ids:x['fit_status']='verified_selected_context_'+V
p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');dump(p.with_suffix('.en.json'),export(p))
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],additional_chronicle_native_literals=2,chronicle_evidence='work/ui/chronicle-0.2.33/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/chronicle-0.2.33/title.png');q['checks']['chronicle_date_and_navigation']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,chronicle_evidence='work/ui/chronicle-0.2.33/verification.json');q['additional_draft_records_by_domain']['chronicle']=2;dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/chronicle-0.2.33/verification.json',scope=proof['result']+'; indexed text fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.33 (2026-10-18)

- Translated both native Chronicle date headings to Events: year / month, including the existing unknown-month marker. Relocated the complete English formats and retained parameter types/order, date arithmetic and historical record selection.
- Shortened Chronicle navigation to Year Start, Prev and Next. Moved Year Start left to clear the L icon and date frame; Next Year and the original button bindings remain. Event descriptions and portraits are unchanged.
- Passed 18 actual MIPS date cases covering normal months, year transitions, four special historical indices, the 16-bit upper bound, adjacent object guards and caller registers/stack. Final-ISO captures and native 4x glyph-UV checks verify both date forms and navigation labels, including moving to April and back to Kirara's birth entry. Five native patches and both relocated formats read back correctly.
- Retained all 0.2.32 banners, original Oreshika icons, full-profile fix and other translations. Only the three selected Chronicle text rows and title version footer change in the archive. Original isolated test saves restored; user source save unchanged.
- Local test build only; no GitHub release. Full-playthrough and physical PSP checks remain pending.

'''
if '## 0.2.33 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.32**, 2026-10-18; archive-text draft: **0.2.27**.','Current local test build: **0.2.33**, 2026-10-18; archive-text draft: **0.2.33**.').replace('three result/pause literals, and 70 native graphic assets/label groups','three result/pause literals, two Chronicle date formats, and 70 native graphic assets/label groups');line='- `work/output/english-native-0.2.33.iso`: translated Chronicle date headings and compact navigation captions clear of button icons. See [QA evidence](work/ui/chronicle-0.2.33/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.32.iso`',line+'- `work/output/english-native-0.2.32.iso`',1)
p.write_text(s,encoding='utf-8')

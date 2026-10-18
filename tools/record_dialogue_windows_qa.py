"""Record translated Pack prompts and widened dialogue build. Dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.37';UI=ROOT/('work/ui/dialogue-window-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((OUT/'dialogue.report.json').read_text());assert sha(OUT/'EBOOT.dialogue.elf')==r['elf_sha256'] and sha(OUT/'data.dialogue.ore')==r['archive_sha256']
runtime=json.loads((UI/'runtime-patches.json').read_text());mips=json.loads((UI/'mips-tests.json').read_text());assert runtime['result']==mips['result']=='PASS' and runtime['elf_sha256']==mips['elf_sha256']==r['elf_sha256'] and len(mips['cases'])==len(mips['update_cases'])==10
for ctx in ('story','pack-confirm'):
 f=json.loads((UI/('font-'+ctx+'.json')).read_text());assert f['result']=='PASS' and f['version']==V
save=json.loads((UI/'save-preservation.json').read_text());assert save['result']=='PASS' and save['user_source_unchanged'] and save['original_project_hashes']==save['restored_project_hashes']
pack=json.loads((UI/'pack-text.json').read_text());assert any(x['text'].startswith('Left:') for x in pack) and any(x['text'].startswith('Use ') and x['text'].endswith('?') for x in pack)
screens=[]
for name in ('title','story-first','story-long','pack-confirm'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
row=next(x for x in json.loads((ROOT/'work/translation/en/dialogue_batch_015.en.json').read_text(encoding='utf-8'))['rows'] if x['id']=='ore:0000c000:0015:02:0018');text=row['translation_en'].replace('%$','Hayate');g=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs'];widths=[round(sum(g[str(ord(c))]['advance'] for c in line)*12/14,3) for line in text.splitlines()];assert widths[0]>268 and all(w<=412 for w in widths)
iso=ROOT/('work/output/english-native-'+V+'.iso');identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso));proof=dict(version=V,result='PASS: translated Pack confirmation/count; wider translucent story dialogue',iso=identity,screens=screens,runtime=runtime,mips=mips,layout=r['layout'],reported_line=dict(id=row['id'],runtime_name_example='Hayate',line_advances=widths,old_text_budget=268,new_text_budget=412,words='Unchanged',validation='Measured against shared native geometry; representative story dialogue verified live'),texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=['Selected natural story and Pack screens checked; full playthrough and physical PSP testing pending.','Widening applies to the shared left-aligned bottom story panel. Menu help and centered alerts retain their existing layouts.'])
print(json.dumps(dict(write=a.write,result=proof['result'],iso=identity,reported_line_widths=widths,screens=len(screens),mips_cases=20),indent=2))
if not a.write:raise SystemExit
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'dialogue.report.json',r)
dump(ROOT/'work/translation/en/executable/pack_prompts.en.json',dict(version=V,scope='Native Pack literals',rows=r['literals']))
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],additional_pack_native_literals=2,dialogue_window_evidence='work/ui/dialogue-window-0.2.37/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/dialogue-window-0.2.37/title.png');q['checks']['wider_story_dialogue_and_pack_prompts']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,dialogue_window_evidence='work/ui/dialogue-window-0.2.37/verification.json');q.setdefault('additional_draft_records_by_domain',{})['native_pack']=2;dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/dialogue-window-0.2.37/verification.json',scope=proof['result']+'; accumulated indexed fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.37 (2026-10-18)

- Translated the Pack's executable-only item confirmation to "Use [item]?" and its quantity caption to "Left: [count]". Preserved the native item substitution and numeric count.
- Widened the shared bottom story dialogue panel from 288 to 432 native pixels (50%), keeping its left edge at 24 and its right edge at 456. All dialogue wording, line breaks and script data remain unchanged. The reported Hayate passage now fits its shared panel by measured native font advances.
- Set only that panel's background to 200/255 opacity (about 78%), allowing the character sprite to show through. Text, name labels, borders and other menus retain their original opacity. The native layout relocates the advance indicator to the wider panel's right corner.
- Added a placement check for scenes that size the panel before positioning it. Verified ten geometry cases and ten update cases in MIPS, including excluded menu/alert layouts, caller state and one-time native resize behavior.
- Verified actual story dialogue, complete native 4x text, background transparency, advance-icon placement, Pack item confirmation and remaining count in the final ISO. Isolated test saves restored; user save source unchanged. Local test build only; no release. Full-playthrough and physical PSP checks remain pending.

'''
if '## 0.2.37 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.36**, 2026-10-18; archive-text draft: **0.2.36**.','Current local test build: **0.2.37**, 2026-10-18; archive-text draft: **0.2.37**.').replace('two Chronicle date formats, and 70 native graphic','two Chronicle date formats, two Pack literals, and 70 native graphic');line='- `work/output/english-native-0.2.37.iso`: wider translucent story dialogue and translated Pack confirmation/count. See [QA evidence](work/ui/dialogue-window-0.2.37/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.36.iso`',line+'- `work/output/english-native-0.2.36.iso`',1)
p.write_text(s,encoding='utf-8')

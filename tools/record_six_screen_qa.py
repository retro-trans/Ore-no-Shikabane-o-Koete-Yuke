"""Record six-screen fixes and local build evidence; dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
from build_six_screen_fixes import EDITS
from strip_jp import export
V='0.2.27';UI=ROOT/('work/ui/six-screens-'+V);OUT=ROOT/('work/output/english-native-'+V)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 r=json.loads((OUT/'screens.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
 assert sha(OUT/'EBOOT.screens.elf')==r['elf_sha256'] and sha(OUT/'data.screens.ore')==r['archive_sha256']
 rt=json.loads((UI/'runtime-patches.json').read_text());assert rt['result']=='PASS' and rt['elf_sha256']==r['elf_sha256'] and len(rt['patches'])==14
 assert json.loads((UI/'save-preservation.json').read_text())['result']=='PASS'
 assert json.loads((UI/'font-potential.json').read_text())['required']==['Spirit','Skill','Body','Naginata']
 assert json.loads((UI/'font-results.json').read_text())['required']==['Next Growth','Points Earned','Free Slots',' items']
 assert Image.open(UI/'final-title.png').size==(480,272)
 mips=(UI/'mips-tests.txt').read_text(encoding='utf-8-sig').strip();assert '24 native chart-coordinate cases' in mips
 assert (UI/'translation-checks.txt').read_text().count('PASS:')==5
 screens=[]
 for name in ('final-status-female','final-equipment-female','final-pause','final-formation','final-schedule','final-results'):
  p=UI/(name+'.png');assert Image.open(p).size==(480,272)
  assert json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False
  screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
 identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
 limits=['Full-playthrough and physical PSP testing remain pending.','This pass covers the six reported screens; unrelated remaining text is not declared complete.']
 proof=dict(version=V,result='PASS: six reported screens checked in the final ISO',iso=identity,screens=screens,native_patch_count=14,actual_mips=mips,translation_batches=5,text_rows_changed=10,native_literals=r['literals'],checks=r['checks'],texture_replacement=False,github_release=False,save_record_writes=False,limits=limits)
 print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],changes=['Build identity and six framebuffer captures','English native-literal ledger and compact class alias','README, CHANGELOG and progress'],limits=limits),indent=2))
 if not a.write:return
 dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity)
 r['runtime_verification']=proof['result'];dump(OUT/'screens.report.json',r)
 dump(ROOT/'work/translation/en/six_screen_literals.en.json',dict(version=V,encoding='Original EUC-JP literals replaced with ASCII English',rows=r['literals']))
 dump(ROOT/'work/glossary/compact_character_ui.json',dict(version=V,terms=[dict(en='Naginata Wielder',compact_en='Naginata',context='Character class field in status/equipment; full term retained in descriptions and dialogue')]))
 for batch in sorted(set(x[0] for x in EDITS)):
  p=ROOT/('work/translation/en/'+batch+'.json');b=json.loads(p.read_text(encoding='utf-8'))
  for _,rid,old,new in (x for x in EDITS if x[0]==batch):
   row=next(z for z in b['rows'] if z['id']==rid)
   row['fit_status']=('measured_width_pass_' if rid in ('ore:00023800:0000:01:0001','ore:00028000:0003:02:0001') else 'fits_selected_context_')+V
  p.write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');dump(p.with_suffix('.en.json'),export(p))
 p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],additional_result_pause_native_literals=3,six_screen_evidence='work/ui/six-screens-0.2.27/verification.json')
 q['title_branding']['version']='v'+V;q['title_branding']['visual_evidence']='work/ui/six-screens-0.2.27/final-title.png';q['checks']['six_reported_screens']=proof['result'];dump(p,q)
 p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q['version']=V;q['additional_draft_records_by_domain']['result_pause']=3;q['six_screen_evidence']='work/ui/six-screens-0.2.27/verification.json';dump(p,q)
 p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/six-screens-0.2.27/verification.json',scope=proof['result']+'; indexed fit count unchanged')];dump(p,q)
 p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry="""## 0.2.27 (2026-10-18)

- Translated the native battle growth caption to Next Growth and shared pause funds to Money / ryo. Added spacing before currency and item-count units.
- Shortened crowded text to Points Earned, Free Slots, Naginata, Now: and Mo. %d:. Separate Victory Points / Offering Points totals retain their meaning; full class wording remains in descriptions and dialogue.
- Rewrote formation help as two complete lines: Press Circle to change / front and back rows. Engine controls and placeholders are preserved.
- Separated equipment name/gender, age and class into three rows, extended the portrait band and moved comparison stats below it.
- Kept full-size Spirit / Skill / Body captions, shifted Potential icons/bars/grid right and removed duplicate decorative words. Maximum bars stay inside the original frame.
- Passed six actual MIPS row cases, 24 chart-coordinate cases, five translation batch checks, ISO checksums and 14 runtime patch readbacks. All six reported screens checked in the final ISO with texture replacement disabled. Original project-profile saves restored. Full-playthrough and physical PSP checks remain pending. Local test build only; no GitHub release.

"""
 if '## 0.2.27 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
 p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('**0.2.26**, 2026-10-18; archive-text draft: **0.2.26**.','**0.2.27**, 2026-10-18; archive-text draft: **0.2.27**.')
 line='- '+chr(96)+'work/output/english-native-0.2.27.iso'+chr(96)+': translated battle/pause labels, compact headings, separated equipment rows and clearer Potential chart. See [QA evidence](work/ui/six-screens-0.2.27/verification.json).\n'
 if line not in s:s=s.replace('- '+chr(96)+'work/output/english-native-0.2.26.iso'+chr(96),line+'- '+chr(96)+'work/output/english-native-0.2.26.iso'+chr(96),1)
 s=s.replace('two equipment literals, and 57 native graphic','two equipment literals, three result/pause literals, and 57 native graphic');p.write_text(s,encoding='utf-8')

if __name__=='__main__':main()

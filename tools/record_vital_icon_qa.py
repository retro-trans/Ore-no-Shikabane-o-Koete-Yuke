"""Record the HP/MP/HLTH symbol replacement and local QA; dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.29';UI=ROOT/('work/ui/vital-icons-'+V);OUT=ROOT/('work/output/english-native-'+V)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 r=json.loads((OUT/'vitals.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
 assert sha(OUT/'EBOOT.vitals.elf')==r['elf_sha256'] and sha(OUT/'data.vitals.ore')==r['archive_sha256']
 assert len(r['icons'])==6 and {x['stat'] for x in r['icons']}=={'HP','MP','HLTH'}
 assert sha(ROOT/r['reference']['file'])==r['reference']['sha256']
 assert json.loads((UI/'save-preservation.json').read_text())['result']=='PASS'
 mips=(UI/'mips-tests.txt').read_text(encoding='utf-8-sig').strip();assert '48 actual MIPS crop cases and 6 embedded descriptor proxies' in mips
 runtime=[]
 for context,required in [('status',{'HP','MP','HLTH'}),('roster',{'HP','MP','HLTH'}),('battle',{'HP','MP'})]:
  q=json.loads((UI/('runtime-'+context+'.json')).read_text());assert q['result']=='PASS' and q['elf_sha256']==r['elf_sha256'];assert required<={x['stat'] for x in q['draws']};runtime.append(q)
 observed={x['file'] for q in runtime for x in q['draws']};assert {'11.ppt','12.ppt','107.ppt','108.ppt','113.ppt'}<=observed
 screens=[]
 for name in ('title','status','roster','battle'):
  p=UI/(name+'.png');assert Image.open(p).size==(480,272) and json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False;screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
 identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
 limits=['Source detail is limited by the supplied screenshot.','Compact HLTH (13.ppt) payload and bounds verified; this slot was not visible in the selected live contexts.','Full-playthrough and physical PSP testing remain pending.']
 proof=dict(version=V,result='PASS: HP/MP/HLTH reference symbols verified in status/roster and compact HP/MP in battle',iso=identity,screens=screens,reference=r['reference'],icons=r['icons'],observed_files=sorted(observed),all_six_payloads='Native memory matches executable',mips=mips,checks=r['checks'],texture_replacement=False,github_release=False,limits=limits)
 print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],changes=['Build identity and native image evidence','Asset ledger and vital-symbol glossary','README, CHANGELOG, build status and progress'],limits=limits),indent=2))
 if not a.write:return
 dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'vitals.report.json',r)
 dump(ROOT/'work/translation/en/graphics/vital_icons.en.json',dict(version=V,category='User-requested non-text HP/MP/HLTH symbols',reference=r['reference'],rows=r['icons']))
 dump(ROOT/'work/glossary/vital_icons.json',dict(version=V,source=r['reference'],terms=[dict(stat=stat,color=color,shape=shape,files=[x['file'] for x in r['icons'] if x['stat']==stat]) for stat,color,shape in [('HP','red','flexed arm'),('MP','blue','open hand'),('HLTH','green','heart with pulse line')]]))
 p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],native_vital_icon_assets=6,vital_icon_evidence='work/ui/vital-icons-0.2.29/verification.json')
 q['title_branding'].update(version='v'+V,visual_evidence='work/ui/vital-icons-0.2.29/title.png');q['checks']['reference_vital_icons']=proof['result'];dump(p,q)
 p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,native_vital_icon_assets=6,vital_icon_evidence='work/ui/vital-icons-0.2.29/verification.json');dump(p,q)
 p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/vital-icons-0.2.29/verification.json',scope=proof['result']+'; indexed text fit count unchanged')];dump(p,q)
 p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry="""## 0.2.29 (2026-10-18)

- Reused the reference Oreshika symbols for HP (red flexed arm), MP (blue open hand), and HLTH (green heart/pulse). Replaced six shared image variants: 11/107.ppt, 12/108.ppt and 13/113.ppt.
- Removed the lettered badge artwork and centered each symbol within the original compact 24x16 or standard 32x16 bounds. Symbol aspect ratios, number/bar positions, native descriptors and renderer code are preserved.
- Changed only six existing embedded palette/pixel payloads and the title version footer. All scripts, text tables, previous element icons, unrelated archive members and earlier 0.2.28 fixes are byte-identical.
- Passed 48 actual MIPS crop cases and six descriptor-proxy cases. Verified standard HP/MP/HLTH in the final ISO's status/roster screens and compact HP/MP in battle, including native payloads and full UVs. The compact HLTH slot has payload/geometry checks; its live context was not encountered.
- Original isolated-profile saves restored and user profile left unchanged. Screenshot source detail, full-playthrough and physical PSP testing remain limitations. Local test build only; no GitHub release.

"""
 if '## 0.2.29 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
 p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('Current local test build: **0.2.28**,','Current local test build: **0.2.29**,')
 line='- '+chr(96)+'work/output/english-native-0.2.29.iso'+chr(96)+': reused the reference HP/MP/HLTH symbols in compact and standard native badges; prior element icons and layout fixes retained. See [QA evidence](work/ui/vital-icons-0.2.29/verification.json).\n'
 if line not in s:s=s.replace('- '+chr(96)+'work/output/english-native-0.2.28.iso'+chr(96),line+'- '+chr(96)+'work/output/english-native-0.2.28.iso'+chr(96),1)
 p.write_text(s,encoding='utf-8')
 (ROOT/'docs/vital-icons.txt').write_text('HP / MP / HLTH reference symbols — local build0.2.29\n\nThe red arm, blue open hand and green pulse-heart reuse the supplied screenshot\npixels. Source coordinates, masks and SHA256 are documented in the build tool\nand work/ui/vital-icons-0.2.29/layout.json. Only existing native image palettes\nand pixels are replaced. Both24x16 and32x16 slots keep their original bounds.\nAll six assets retain their original descriptors, source crops and rendering\ncode. Numbers, bars, previous element icons, scripts and text tables are unchanged.\n\nActual status/roster/battle captures and native image payload/UV readbacks:\nwork/ui/vital-icons-0.2.29/. Compact HLTH13.ppt was verified as data/geometry;\nits live context was not encountered. Original isolated-profile saves restored.\nTexture replacement disabled. No GitHub release. Full-playthrough and physical\nPSP testing remain pending; source detail is limited by the screenshot.\n',encoding='utf-8')
if __name__=='__main__':main()

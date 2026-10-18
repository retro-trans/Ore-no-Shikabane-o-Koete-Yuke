"""Record native reference icon evidence and update local build notes; dry run first."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.28';UI=ROOT/('work/ui/element-icons-'+V);OUT=ROOT/('work/output/english-native-'+V)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
 r=json.loads((OUT/'elements.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
 assert sha(OUT/'EBOOT.elements.elf')==r['elf_sha256'] and sha(OUT/'data.elements.ore')==r['archive_sha256']
 assert len(r['elements'])==4 and all(x['logical_size']==[16,14] and x['proxy_bytes']==x['source_bytes'] for x in r['elements'])
 assert sha(ROOT/r['reference']['file'])==r['reference']['sha256']
 assert json.loads((UI/'save-preservation.json').read_text())['result']=='PASS'
 mips=(UI/'mips-tests.txt').read_text(encoding='utf-8-sig').strip();assert '48 actual MIPS crop cases and 4 embedded descriptor proxies' in mips
 runtime=[]
 for context,minimum in [('status',24),('deities',4)]:
  q=json.loads((UI/('runtime-'+context+'.json')).read_text());assert q['result']=='PASS' and q['elf_sha256']==r['elf_sha256'] and len(q['draws'])>=minimum
  assert {x['element'] for x in q['draws']}=={'Fire','Water','Wind','Earth'};runtime.append(q)
 screens=[]
 for name in ('title','status-abilities','deities'):
  p=UI/(name+'.png');assert Image.open(p).size==(480,272) and json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False
  screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
 identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
 limits=['Reference artwork is reused from the supplied screenshot; resolution is limited by that source.','Full-playthrough and physical PSP testing remain pending.']
 proof=dict(version=V,result='PASS: all four shared reference element sprites verified on status/abilities/Potential and deity list',iso=identity,screens=screens,elements=r['elements'],reference=r['reference'],runtime_widgets={q['context']:len(q['draws']) for q in runtime},mips=mips,checks=r['checks'],texture_replacement=False,github_release=False,limits=limits)
 print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],changes=['Build identity, asset ledger and glossary','README, CHANGELOG and progress','Selected actual UI captures and native image readback'],limits=limits),indent=2))
 if not a.write:return
 dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'elements.report.json',r)
 dump(ROOT/'work/translation/en/graphics/element_icons.en.json',dict(version=V,category='User-requested non-text shared sprites',reference=r['reference'],rows=r['elements']))
 dump(ROOT/'work/glossary/element_icons.json',dict(version=V,source='User-provided Oreshika reference screenshot',scope='Shared elemental affinity/stat symbols',terms=[dict(element=x['element'],color=c,shape=s,native_file=x['file']) for x,c,s in zip(r['elements'],['red','blue','green','yellow'],['flame','droplet','wind swirl','earth/rock hexagon'])]))
 p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version='0.2.27',file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],native_hd_image_assets=87,native_hd_unique_images=67,native_element_icons=4,element_icon_evidence='work/ui/element-icons-0.2.28/verification.json')
 q['title_branding'].update(version='v'+V,visual_evidence='work/ui/element-icons-0.2.28/title.png');q['checks']['reference_element_icons']=proof['result'];dump(p,q)
 p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q['version']=V;q['native_hd_image_assets']=87;q['native_hd_unique_images']=67;q['native_element_icons']=4;q['element_icon_evidence']='work/ui/element-icons-0.2.28/verification.json';dump(p,q)
 p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/element-icons-0.2.28/verification.json',scope=proof['result']+'; indexed text fit count unchanged')];dump(p,q)
 p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry="""## 0.2.28 (2026-10-18)

- Reused the four element icon designs from the user's Oreshika reference: red flame (Fire), blue droplet (Water), green swirl (Wind), and yellow earth/rock hexagon (Earth).
- Replaced the shared 17.ppt–20.ppt resources as four embedded native sprites. Extracted reference pixels have transparent outer corners and retain their square aspect within the original 16x14 logical bounds. Status, ability/Potential charts, deity lists and other consumers reuse these shared resources.
- Preserved all 0.2.27 text, gameplay scripts, layouts, existing native renderer hooks and unrelated archive members. Original resource loader sizes are unchanged. Updated the title footer to 0.2.28; texture replacement remains disabled.
- Passed 48 actual MIPS crop cases and four descriptor-proxy cases. Verified all four icons in the final ISO's status/abilities/Potential screen and deity list, including native palettes, pixels and UV coordinates. Original isolated-profile saves restored and user profile left unchanged.
- Source detail is limited by the supplied screenshot. Full-playthrough and physical PSP checks remain pending. Local test build only; no GitHub release.

"""
 if '## 0.2.28 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
 p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('Current local test build: **0.2.27**,','Current local test build: **0.2.28**,')
 line='- '+chr(96)+'work/output/english-native-0.2.28.iso'+chr(96)+': reused the four reference element icons in shared native sprites; all0.2.27 fixes retained. See [QA evidence](work/ui/element-icons-0.2.28/verification.json).\n'
 if line not in s:s=s.replace('- '+chr(96)+'work/output/english-native-0.2.27.iso'+chr(96),line+'- '+chr(96)+'work/output/english-native-0.2.27.iso'+chr(96),1)
 p.write_text(s,encoding='utf-8')
 (ROOT/'docs/element-icons.txt').write_text('Reference element icons — local build0.2.28\n\nFire/red/flame, Water/blue/droplet, Wind/green/swirl, Earth/yellow/rock.\nThe exact screenshot icon pixels are reused from incoming/element-icons-reference.png.\nCrop coordinates and source SHA256 are recorded in work/ui/element-icons-0.2.28/layout.json.\nThe four shared native resources17/18/19/20.ppt have unchanged16x14 logical geometry\nand1328-byte decompressed proxies. Each new64x64 texture has a64x56 visible region;\nthe square artwork is centered inside it without distortion. Existing native image\nbinding/UV hooks are reused; no new renderer code or gameplay/text changes.\n\nActual status/Potential/abilities and deity-list screenshots and native image readbacks\nare in work/ui/element-icons-0.2.28/. All earlier0.2.27 fixes remain. No texture pack\nor GitHub release. Full-playthrough and physical PSP testing remain pending.\n',encoding='utf-8')
if __name__=='__main__':main()

"""Record original Oreshika icon sources, local build identity and selected QA."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.31';UI=ROOT/('work/ui/native-icons-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((OUT/'icons.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso');symbols={'HP','MP','HLTH','Fire','Water','Wind','Earth'}
assert sha(OUT/'EBOOT.icons.elf')==r['elf_sha256'] and sha(OUT/'data.icons.ore')==r['archive_sha256'] and len(r['icons'])==10 and {x['stat'] for x in r['icons']}==symbols
source_tests=json.loads((UI/'source-tests.json').read_text());assert source_tests['result']=='PASS' and source_tests['independent_pixel_checks']==5824
assert json.loads((UI/'save-preservation.json').read_text())['user_source_unchanged']
mips=(UI/'mips-tests.txt').read_text(encoding='utf-8-sig').strip();assert '48 actual MIPS crop cases and 10 embedded descriptor proxies' in mips
runtime=[]
for context,required in [('status',symbols),('roster',{'HP','MP','HLTH'})]:
 q=json.loads((UI/('runtime-'+context+'.json')).read_text());assert q['result']=='PASS' and q['elf_sha256']==r['elf_sha256'] and required<={x['stat'] for x in q['draws']};runtime.append(q)
for context in ('battle','party'):
 p=UI/('runtime-'+context+'.json')
 if p.exists():
  q=json.loads(p.read_text());assert q['result']=='PASS' and q['elf_sha256']==r['elf_sha256'];runtime.append(q)
observed={x['file'] for q in runtime for x in q['draws']};screens=[]
for name in ('title','status','abilities','roster','sortie-entry','battle'):
 p=UI/(name+'.png')
 if name=='battle' and not p.exists():continue
 assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
limits=['Source pixels retain the Vita game\'s original BC3 compression. PSP assets are resized and palette-converted within their existing bounds.','Full playthrough and physical PSP testing remain pending.']
compact_missing=[label for name,label in [('11.ppt','HP'),('12.ppt','MP'),('13.ppt','HLTH')] if name not in observed]
if compact_missing:limits.append('Compact '+', '.join(compact_missing)+' have native payload/geometry checks; their draw descriptors were not captured in the selected live contexts.')
proof=dict(version=V,result='PASS: original Oreshika HP/MP/HLTH and four element designs replace screenshot copies',iso=identity,screens=screens,source=r['source'],independent_source_tests=source_tests,observed_files=sorted(observed),all_ten_native_payloads='Read back from the final ISO test instance',mips=mips,checks=r['checks'],texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=limits)
print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],original_native_sheets=list(r['source']['native_sheets']),observed_files=sorted(observed),limits=limits),indent=2))
if not a.write:raise SystemExit()
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'icons.report.json',r)
vitals=[x for x in r['icons'] if x['stat'] in {'HP','MP','HLTH'}];elements=[dict(element=x['stat'],**x) for x in r['icons'] if x['stat'] not in {'HP','MP','HLTH'}]
dump(ROOT/'work/translation/en/graphics/vital_icons.en.json',dict(version=V,category='Original Oreshika native HP/MP/HLTH artwork',reference=r['source'],rows=vitals));dump(ROOT/'work/translation/en/graphics/element_icons.en.json',dict(version=V,category='Original Oreshika native element artwork',reference=r['source'],rows=elements))
for filename,keys in [('vital_icons.json',{'HP','MP','HLTH'}),('element_icons.json',{'Fire','Water','Wind','Earth'})]:
 dump(ROOT/('work/glossary/'+filename),dict(version=V,source='Original native PCSA00155 textures from the user-supplied Oreshika folder',terms=[dict(symbol=x['symbol'],source_sheet=x['sheet'],source_crop=x['crop'],native_files=[z['file'] for z in r['icons'] if z['stat']==x['symbol']]) for x in r['source']['icons'] if x['symbol'] in keys]))
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],native_icon_source='Original PCSA00155 UI texture sheets',native_icon_evidence='work/ui/native-icons-0.2.31/verification.json',native_vital_icon_assets=6,native_element_icons=4);q['title_branding'].update(version='v'+V,visual_evidence='work/ui/native-icons-0.2.31/title.png');q['checks']['original_oreshika_icons']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,native_icon_source='Original PCSA00155 UI texture sheets',native_icon_evidence='work/ui/native-icons-0.2.31/verification.json');dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/native-icons-0.2.31/verification.json',scope=proof['result']+'; indexed text fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.31 (2026-10-18)

- Replaced all seven screenshot-derived icon designs with original assets extracted locally from the supplied Oreshika Tainted Bloodlines (USA) folder. HP/MP/HLTH come from udtx_status_us.ppt; Fire/Water/Wind/Earth come from uitx_icon_us.ppt. Exact native crops and source hashes are recorded under incoming/oreshika-native-icons/ and work/ui/native-icons-0.2.31/.
- Decoded the native BC3 texture sheets and retained their alpha/outlines. Added an independent block-decoder check across all 5,824 icon pixels; recovered crops match the source sheets exactly. Resized and palette-converted those originals into ten existing PSP variants: six vital icons and four shared element icons.
- Retained original image descriptors, logical dimensions, renderer code and all 0.2.30 profile/layout fixes. Only ten embedded image payloads/palettes and the title version footer changed; scripts and translations remain byte-identical.
- Passed 48 actual MIPS crop cases and ten descriptor-proxy cases. Final-ISO status/abilities and roster captures verify the original designs; native memory readback verifies all ten payloads and selected draw UVs. Additional selected context evidence is in the verification report. Original isolated-profile saves restored; user source save left unchanged.
- Local test build only; no GitHub release. Full-playthrough and physical PSP testing remain pending.

'''
if '## 0.2.31 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.30**,','Current local test build: **0.2.31**,');line='- `work/output/english-native-0.2.31.iso`: original native Oreshika HP/MP/HLTH and element icons, replacing the earlier screenshot copies. See [source and QA evidence](work/ui/native-icons-0.2.31/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.30.iso`',line+'- `work/output/english-native-0.2.30.iso`',1)
p.write_text(s,encoding='utf-8');(ROOT/'docs/original-oreshika-icons.txt').write_text('''Original Oreshika icon assets — local build 0.2.31

The supplied PCSA00155 game uses PFS encryption. Vita3K extracted a separate
local working copy using the included local license. Source folders and keys
were not uploaded. Tool version/hash are in extraction-tool.json.

The decrypted data.img contains EZBIND archives. Selected original US UI sheets:
udtx_status_us.ppt: archive 1638172672, entry 0; native 512x512 BC3 GXT.
uitx_icon_us.ppt: archive 1635518464, entry 2; native 512x1024 BC3 GXT.
HP/MP/HLTH: [0,16,24,40], [24,16,48,40], [48,16,72,40].
Fire/Water/Wind/Earth: x444..476, y0..32 / 32..64 / 64..96 / 96..128.
Recovered PNGs in incoming/oreshika-native-icons retain exact decoded pixels
and alpha. No screenshot masks or redraws are used. The native source is BC3
compressed; it is not a vector master. Decoder Morton order follows Vita3K:
https://github.com/Vita3K/Vita3K/blob/master/vita3k/renderer/src/texture/format.cpp

Each crop is placed at 56x56 physical pixels in the existing PSP 4x native
sprites, retaining original logical bounds: compact vitals24x16, standard
vitals32x16, elements16x14. Existing palette conversion is required by the PSP
format. Ten embedded pixel/palette payloads change; descriptors, renderer,
scripts and profile-trait code remain byte-identical to0.2.30.

Source coordinates/hashes, 5,824 independent BC3 pixel checks, selected actual
framebuffer captures, all-ten native payload readbacks and 48 actual MIPS crop
cases plus ten proxy cases are recorded in work/ui/native-icons-0.2.31/.
Original isolated-profile saves restored. Texture replacement disabled.
No release was created. Full-game and physical PSP testing remain pending.
''',encoding='utf-8')

"""Record translated shop/calendar banners and final ISO evidence. Dry run first."""
import argparse,calendar,json,struct
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
from build_menu_fixes import container,member
from repack_text import root_entries
from inspect_native_textures import decode
V='0.2.32';UI=ROOT/('work/ui/left-banners-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((OUT/'banners.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
assert sha(OUT/'EBOOT.banners.elf')==r['elf_sha256'] and sha(OUT/'data.banners.ore')==r['archive_sha256']
assert len(r['graphics'])==13 and r['resident_added_bytes']==388
source=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();data=(OUT/'data.banners.ore').read_bytes();oe,_=root_entries(source);be,_=root_entries(data);index=next(i for i,_,_,o in oe if o==0xb4a800);arc,en=container(data,next(x[3] for x in be if x[0]==index));del source,data
for g in r['graphics']:
 ppt=member(arc,en,g['member_entry']);assert len(ppt)==g['resource_bytes']==g['original_bytes']==13744
 assert struct.unpack_from('<H',ppt,8)[0]==4
 im,info=decode(ppt);assert im.tobytes()==Image.open(UI/(g['file']+'.png')).tobytes() and im.size==(96,264)
runtime=[]
for context,text in [('home','APRIL'),('herbal','HERBAL MEDICINE')]:
 q=json.loads((UI/('runtime-'+context+'.json')).read_text());assert q['result']=='PASS' and q['elf_sha256']==r['elf_sha256'] and q['archive_sha256']==r['archive_sha256'] and text in {d['text'] for d in q['draws']};runtime.append(q)
mips=(UI/'mips-tests.txt').read_text(encoding='utf-8-sig').strip();assert '112 actual MIPS crop cases and 10 embedded descriptor proxies' in mips
saves=json.loads((UI/'save-preservation.json').read_text());assert saves['result']=='PASS' and saves['user_source_unchanged'] and saves['original_project_hashes']==saves['restored_project_hashes']
screens=[]
for name in ('title','home','herbal-medicine','status'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False;screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
limits=['All twelve month images were preview-checked; April and the herbal-medicine banner were observed in the final ISO.','Four-bit palettes use sixteen colors and 2x horizontal/native vertical sampling to fit the original memory budgets.','Full playthrough and physical PSP testing remain pending.']
proof=dict(version=V,result='PASS: English herbal-medicine and calendar ribbons',iso=identity,screens=screens,runtime=runtime,mips=mips,checks=r['checks'],translated_banners=13,original_resource_bytes_each=13744,resident_added_bytes=388,texture_replacement=False,save_record_writes=False,github_release=False,limits=limits)
print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],banners=[x['translation_en'] for x in r['graphics']],resident_added_bytes=388,limits=limits),indent=2))
if not a.write:raise SystemExit
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);r['runtime_verification']=proof['result'];dump(OUT/'banners.report.json',r)
dump(ROOT/'work/translation/en/graphics/left_banners.en.json',dict(version=V,status='Final-ISO April and herbal banner verified; other months preview checked',rows=r['graphics']))
month_jp=['\u4e00','\u4e8c','\u4e09','\u56db','\u4e94','\u516d','\u4e03','\u516b','\u4e5d','\u5341','\u5341\u4e00','\u5341\u4e8c']
terms=[dict(source_jp='\u6f22\u65b9\u85ac\u5c4b',translation_en='HERBAL MEDICINE',context='Left medicine-shop banner',note='Traditional herbal medicine shop; shop function is clear from the menu context.')]
terms += [dict(source_jp=month_jp[n-1]+'\u6708',translation_en=calendar.month_name[n].upper(),month=n,context='Left home calendar banner') for n in range(1,13)]
dump(ROOT/'work/glossary/left_banners.json',dict(version=V,terms=terms))
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],native_graphic_labels=70,native_hd_image_assets=100,native_hd_unique_images=80,left_banner_evidence='work/ui/left-banners-0.2.32/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/left-banners-0.2.32/title.png');q['checks']['left_shop_and_calendar_banners']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,native_hd_image_assets=100,left_banner_evidence='work/ui/left-banners-0.2.32/verification.json');q['additional_draft_records_by_domain']['graphics']=70;dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/left-banners-0.2.32/verification.json',scope=proof['result']+'; indexed text fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.32 (2026-10-18)

- Translated the left medicine-shop ribbon as HERBAL MEDICINE and all twelve home calendar ribbons as JANUARY through DECEMBER, including the reported APRIL label. Retained their seasonal diamond patterns, original positions and logical dimensions.
- Rendered the English labels in Noto Sans. Each 96x264 four-bit texture retains the original 13,744-byte resource size; only 388 bytes of tagged image-renderer support are appended. This preserves startup and sound-thread memory while allowing twice the original horizontal sampling. Existing eight-bit HD assets and untagged images retain their original paths.
- Passed 112 actual MIPS crop/binding cases across four/eight-bit textures and ten existing icon descriptor proxies. Verified the final ISO's April and herbal-medicine ribbons by actual framebuffer captures, native palette/pixel matches and complete UV rectangles. All twelve calendar images were preview checked; status icons and the full creed were also checked for regressions.
- Retained 0.2.31's original Oreshika icons, full-profile fix and existing translations. Other archive resources, including the background shop sign, remain unchanged except the title version footer. Restored the isolated test saves and verified the user source save was unchanged.
- Local test build only; no GitHub release. Other calendar months still need live calendar progression checks; full-playthrough and physical PSP testing remain pending.

'''
if '## 0.2.32 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8')
p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.31**,','Current local test build: **0.2.32**,').replace('57 native graphic assets/label groups','70 native graphic assets/label groups');line='- `work/output/english-native-0.2.32.iso`: English herbal-medicine and all twelve calendar ribbons within the original memory budgets. See [QA evidence](work/ui/left-banners-0.2.32/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.31.iso`',line+'- `work/output/english-native-0.2.31.iso`',1)
p.write_text(s,encoding='utf-8')

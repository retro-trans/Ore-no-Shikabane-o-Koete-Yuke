"""Record full character traits and the local build identity. Dry run first."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.30';UI=ROOT/('work/ui/profile-traits-'+V);OUT=ROOT/('work/output/english-native-'+V)
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
r=json.loads((OUT/'traits.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
assert sha(OUT/'EBOOT.traits.elf')==r['elf_sha256'] and sha(OUT/'data.traits.ore')==r['archive_sha256']
mips=json.loads((UI/'mips-tests.json').read_text());assert mips['result']=='PASS' and mips['translated_rows']==731 and mips['elf_sha256']==r['elf_sha256']
preserve=json.loads((UI/'save-preservation.json').read_text());assert preserve['result']=='PASS' and preserve['user_source_unchanged']
runtime=[]
for n,t in [('hayate','Creed: An iron heart and iron will'),('kirara','Saying: Knock on wood.')]:
 q=json.loads((UI/('runtime-'+n+'.json')).read_text());assert q['result']=='PASS' and q['elf_sha256']==r['elf_sha256'] and q['full_trait'].replace('\n',' ')==t;runtime.append(q)
screens=[]
for name in ('hayate','kirara','returned-hayate','abilities','equipment-tab','longest-fixture'):
 p=UI/(name+'.png');assert Image.open(p).size==(480,272) and not json.loads(p.with_suffix('.json').read_text())['texture_replacement'];screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p),fixture=name=='longest-fixture'))
fixture=json.loads((UI/'longest-fixture-build.json').read_text());assert fixture['source_elf_sha256']==r['elf_sha256'] and not fixture['save_record_changes']
font=json.loads((UI/'font-traits.json').read_text());assert font['result']=='PASS' and font['required']==['Creed: An iron heart and iron will']
longfont=json.loads((UI/'font-longest-fixture.json').read_text());assert longfont['result']=='PASS' and longfont['required']==['Reputation: Knows more than','experience warrants']
identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
limits=['All 731 translated traits tested through native MIPS formatting; selected natural character traits and the longest text fixture checked visually.','Full playthrough and physical PSP testing remain pending.']
layout=dict(version=V,id='character_status.profile_trait',native_resolution=[480,272],screen='Character Status',field='Personal profile trait',source_file='intro.mlb',native_label_offset='0x1020',original_limit_bytes=20,new_buffer_bytes=1024,position=r['position'],available_area=[70,223,320,250],available_width=250,available_height=27,line_pitch=14,maximum_tested_lines=2,wrap_metric_budget=280,stats_frame_height=80,equipment_frame_height=108,visible_tabs=['Status','Abilities'],font_size_unchanged=16,second_line='Owned native cText child; ordinary label newline is not supported',save_format_changes=False,translations_changed=False)
proof=dict(version=V,result='PASS: complete profile traits, native two-line placement and repeated character switching',iso=identity,screens=screens,natural_traits=[q['full_trait'] for q in runtime],longest_fixture=fixture,native_font='Final full Creed and both longest-fixture lines use the embedded 4x atlas and matching glyph UVs',mips=mips,checks=r['checks'],texture_replacement=False,game_memory_writes=False,save_record_writes=False,github_release=False,limits=limits)
print(json.dumps(dict(write=a.write,iso=identity,result=proof['result'],layout=layout,limits=limits),indent=2))
if not a.write:raise SystemExit()
dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity);dump(UI/'layout.json',layout);r['runtime_verification']=proof['result'];dump(OUT/'traits.report.json',r)
p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],profile_trait_evidence='work/ui/profile-traits-0.2.30/verification.json');q['title_branding'].update(version='v'+V,visual_evidence='work/ui/profile-traits-0.2.30/title.png');q['checks']['full_profile_traits']=proof['result'];dump(p,q)
p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q.update(version=V,profile_trait_evidence='work/ui/profile-traits-0.2.30/verification.json');dump(p,q)
p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/profile-traits-0.2.30/verification.json',scope=proof['result']+'; indexed text fit count unchanged')];dump(p,q)
p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.30 (2026-10-18)

- Fixed the nine-character status-profile cutoff responsible for “Creed: An” and “Saying: K”. The native formatter now uses a bounded 1,024-byte display buffer instead of the 20-byte stack buffer; character records and save layout remain unchanged.
- Moved traits below the stats panel, retaining the native font size and removing eight empty pixels at the bottom of its frame. Measured word wrapping displays up to two lines using an owned native text child, since ordinary newlines are ignored by this label renderer. Character changes clear and rebuild both lines through the existing label lifecycle. Traits appear on Status/Abilities and hide on the taller equipment tab; its four item rows retain their space.
- Verified Hayate’s full “Creed: An iron heart and iron will” and Kirara’s “Saying: Knock on wood.” in the final ISO, including repeated switches and screen re-entry. A separate test-only executable displayed the longest trait; no character/save records were changed for that fixture.
- Passed actual MIPS formatting/wrapping checks for all 731 translated traits, dynamic name/city substitutions, five stress cases, buffer guards, original stack buffer preservation and three text-child/placement cases. Final ISO checksums, native hooks and original isolated saves verified. Existing translations, icons and unrelated archive members remain unchanged except the version footer.
- Local test build only; no GitHub release. Full-playthrough and physical PSP testing remain pending.

'''
if '## 0.2.30 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8').replace('Current local test build: **0.2.29**,','Current local test build: **0.2.30**,');line='- `work/output/english-native-0.2.30.iso`: complete character creeds/sayings, bounded formatting and two-line native placement. See [QA evidence](work/ui/profile-traits-0.2.30/verification.json).\n'
if line not in s:s=s.replace('- `work/output/english-native-0.2.29.iso`',line+'- `work/output/english-native-0.2.29.iso`',1)
p.write_text(s,encoding='utf-8');(ROOT/'docs/profile-traits.txt').write_text('''Character profile traits — local build 0.2.30

The intro.mlb translations were complete. Status formatting at 0x08948e0c
used a 20-byte UCS2 output buffer, leaving nine visible characters and a null.
Only this display path now formats into a dedicated 1,024-byte buffer.
The archive trait table, character trait IDs and saved records are unchanged.

Trait position is (70,229), with a second line at local offset (0,14).
English font metrics determine word breaks, with a 280-unit line budget.
The 80-pixel Status/Abilities frame leaves room for both trait lines and the
Back prompt. The taller 108-pixel equipment tab retains its four item rows;
traits hide on that tab and reappear on returning to Status or Abilities.
The native cLabel renderer ignores plain newlines. The trait setter therefore
sets the first line, appends an engine-allocated cText child for the second,
and restores the full formatted buffer. Native parent ownership handles
teardown and switching. Font size remains 16 (existing label setting).

All 731 translated traits pass actual MIPS formatting/wrapping tests; maximum
two lines with the tested eight-letter name and city substitutions. Five
stress cases check bounded termination and buffer guards. Additional tests
check caller registers, the untouched old stack slot, child ownership and
14-pixel placement. Selected final-ISO captures cover both reported characters,
repeated switching and re-entry. The longest-text image uses a separate QA
executable that redirects only the display formatter; save records are untouched.

Evidence: work/ui/profile-traits-0.2.30/. Original isolated-profile saves
restored; user profile unchanged. Texture replacement disabled. Local build
only, no GitHub release. Full-game and physical PSP checks remain pending.
''',encoding='utf-8')

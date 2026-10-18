"""Record selected equipment/deity checks and local build notes. Dry run unless --write."""
import argparse,hashlib,json
from PIL import Image
from catalog_text import ROOT

VERSION='0.2.20';UI=ROOT/'work/ui/equipment-deities-0.2.20'
SCREENS={
 'equipment-after.png':'English equipment ribbon, role/slot labels, Male and four separate equipped rows',
 'equipment-head-after.png':'Full equipment candidate, separated slot label/name, description and signed comparison controls retained',
 'equipment-female.png':'Female and second eight-letter character name use native font',
 'union-available.png':'Complete Available Classes text and highlight fit the enlarged Divine Union submenu',
 'deities-first.png':'Four two-line deity rows separate names, offering cost, element and gender; full right caption fits',
 'deities-missing.png':'English Missing banner in the original native portrait asset',
 'deities-last.png':'Native scrolling reaches later deity entries without layout collisions',
 'title.png':'Native v0.2.20 footer and full github.com/retro-trans URL'}
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    out=ROOT/'work/output/english-native-0.2.20';r=json.loads((out/'equipment.report.json').read_text());proof=json.loads((UI/'runtime-patches.json').read_text())
    assert len(proof['native_patches_verified'])==35 and proof['elf_sha256']==r['elf_sha256'] and proof['archive_sha256']==r['archive_sha256'] and proof['iso']=='work/source/qa-equipment-0.2.20d.iso'
    screens=[]
    for name,scope in SCREENS.items():
        p=UI/name;assert Image.open(p).size==(480,272) and json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False
        screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p),dimensions=[480,272],observed=scope,fit='pass'))
    for ctx in ('equipment-male','equipment-female','deity'):
        assert json.loads((UI/('font-'+ctx+'.json')).read_text())['result']=='PASS'
    unit=(ROOT/'work/source/test-equipment-0.2.20.txt').read_text();assert 'PASS:' in unit
    assert 'ALL 49 BATCHES PASS' in (ROOT/'work/source/check-translations-0.2.20.txt').read_text()
    final=ROOT/'work/output/english-native-0.2.20.iso';candidate=ROOT/'work/source/qa-equipment-0.2.20d.iso';identity=dict(version=VERSION,tested_iso=candidate.relative_to(ROOT).as_posix(),delivered_iso=final.relative_to(ROOT).as_posix(),bytes=final.stat().st_size,sha256=sha(final));assert identity['bytes']==candidate.stat().st_size==1079918592 and identity['sha256']==sha(candidate)
    verification=dict(version=VERSION,result='PASS: selected requested equipment/union/deity screens',component_sha256=dict(elf=r['elf_sha256'],archive=r['archive_sha256']),screens=screens,native_mips=unit.strip(),runtime_patches=35,static_name_measurements=r['static_names'],native_font='Required dynamic English labels verified against embedded atlas and UVs',texture_replacement=False,script_text_changes=0,github_release=False,limits=['Selected initial inventory/party contexts; dynamic heirloom/generated deity names and full-playthrough QA remain pending','The pre-existing low-offering confirmation warning may truncate its English text; it is outside the requested browsing/detail screens','Real PSP boot and performance remain untested'])
    print(json.dumps(dict(version=VERSION,write=a.write,screens=len(screens),new_literals=2,new_graphic_assets=len(r['graphics']),iso=identity,sample=screens[3]),indent=2))
    if not a.write:return
    dump(UI/'verification.json',verification);dump(UI/'image-identity.json',identity)
    r['runtime_verification']='PASS: work/ui/equipment-deities-0.2.20/verification.json';dump(out/'equipment.report.json',r)
    layout=json.loads((UI/'layout.json').read_text());layout['equipment_slots']['badge_sample_width']=24;layout['runtime_verification']='PASS: selected contexts; see verification.json';dump(UI/'layout.json',layout)
    graphics=dict(schema_version=1,version=VERSION,language='en',status='Draft; selected native runtime fit checked',rows=r['graphics'])
    for row in graphics['rows']:
        base,entry=row['archive_offset'],row['member_entry']
        rect=([0,0,24,16] if base==0x36000 and entry in (33,34,36,37) else [0,0,32,16]) if base==0x36000 and entry!=40 else ([0,0,48,192] if base in (0x36000,0xb4a800) else [48,11,80,119])
        row.update(label_rectangle=rect,fit_status='verified_selected_context_0.2.20',fit_evidence='work/ui/equipment-deities-0.2.20/verification.json')
    dump(ROOT/'work/translation/en/graphics/equipment_deities.en.json',graphics)
    dump(ROOT/'work/translation/en/equipment/literals.en.json',dict(version=VERSION,rows=r['literals'],status='Draft; native font and selected runtime fit checked',evidence='work/ui/equipment-deities-0.2.20/verification.json'))
    terms=[('\u5f53\u4e3b','Head','Portrait role flag'),('\u968a\u9577','Leader','Portrait role flag'),('\u51fa\u6483','Party','Portrait flag: selected for the expedition party'),('\u6b66\u5177\u88c5\u5099','EQUIPMENT','Screen ribbon'),('\u6b66\u5668','WPN','Equipped weapon slot'),('\u9386','ARM','Equipped body armor slot'),('\u515c','HEAD','Equipped headgear slot'),('\u88c5\u98fe','ACC','Equipped accessory slot'),('\u4ea4\u795e\u306e\u5100','DIVINE UNION','Screen ribbon'),('\u884c\u65b9\u4e0d\u660e','MISSING','Unavailable deity portrait'),('\u7537','Male','Character gender'),('\u5973','Female','Character gender')]
    dump(ROOT/'work/glossary/equipment_ui.json',dict(version=VERSION,scope='Context-specific compact UI labels; general glossary terms retain their existing prose/menu forms',terms=[dict(jp=jp,en=en,context=ctx) for jp,en,ctx in terms]))
    verified=json.loads((ROOT/'work/ui/verified_screens.json').read_text());verified['latest_evidence_version']=VERSION;evidence=dict(version=VERSION,evidence='work/ui/equipment-deities-0.2.20/verification.json',scope='Equipment graphics/slots, wider Divine Union submenu, two-line deity rows and complete details; core fit count unchanged')
    if evidence not in verified['additional_build_evidence']:verified['additional_build_evidence'].append(evidence)
    dump(ROOT/'work/ui/verified_screens.json',verified)
    status=json.loads((ROOT/'docs/local_build_status.json').read_text());status.update(latest_local_build=VERSION,archive_translation_version=VERSION,file=final.relative_to(ROOT).as_posix(),bytes=identity['bytes'],native_graphic_labels=34,additional_equipment_native_literals=2,equipment_deity_ui_evidence='work/ui/equipment-deities-0.2.20/verification.json')
    status['checks']['equipment_union_deities']='PASS: 35 runtime patches, MIPS geometry/coordinate checks, 463 equipment and 127 deity names measured, native-font UVs and selected actual screens'
    status['checks']['selected_actual_screen_fit']='64 indexed records retain accumulated selected-context evidence; equipment/union/deity layout additionally checked in 0.2.20'
    status['title_branding'].update(version='v0.2.20',visual_evidence='work/ui/equipment-deities-0.2.20/title.png');dump(ROOT/'docs/local_build_status.json',status)
    readme=ROOT/'README.md';s=readme.read_text(encoding='utf-8').replace('**0.2.19**, 2026-10-17; archive-text draft: **0.2.19**','**0.2.20**, 2026-10-17; archive-text draft: **0.2.20**').replace('Eighteen executable records, six additional shop literals, and twenty-three native graphic label groups are recorded separately.','Eighteen executable records, six shop literals, two equipment literals, and thirty-four native graphic assets/label groups are recorded separately.')
    line='- `work/output/english-native-0.2.20.iso`: translated equipment/role/slot labels, gender text and Missing portraits; four equipment rows, wider Divine Union submenu, two-line deity list and complete offering requirements. See [equipment/deity layout notes](docs/equipment-deities-layout.txt).\n'
    if line not in s:s=s.replace('- `work/output/english-native-0.2.19.iso`:',line+'- `work/output/english-native-0.2.19.iso`:')
    readme.write_text(s,encoding='utf-8')
    p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.20 — 2026-10-17

- Translated the native EQUIPMENT ribbon, Head/Leader/Party flags, WPN/HEAD/ARM/ACC slot labels, Male/Female text, DIVINE UNION ribbon, and both native Missing portrait copies. Original palettes and other artwork remain; texture replacement stays disabled.
- Changed equipped slots to four 248-pixel rows, with a 36-pixel label reserve. Candidate equipment uses a 240-pixel column with four visible rows and native scrolling. Repositioned the list, source caption and description to fit the taller slot frame. All 463 fixed equipment names fit the 212-pixel equipped-name budget.
- Widened the Divine Union submenu to 128 pixels of text space. Deity lists now show four two-line entries with separate cost, element and gender. Widened the details frame to 176 pixels, centered the portrait, and moved the element clear of the name. Offering Points Required fits in full; all 127 fixed deity names fit the measured detail-name budget.
- Verified 35 guarded runtime patches, appended Latin labels and the native geometry wrapper. Actual MIPS checks cover geometry, saved caller state and dirty-register coordinate setup. Selected runtime evidence includes both genders, equipment selection, the long submenu label, deity scrolling and the Missing portrait. All 49 translation batches pass; script payloads and unrelated archive members remain byte-identical to 0.2.19. Evidence: `work/ui/equipment-deities-0.2.20/`. Local test build only; no GitHub release. Dynamic generated names, the pre-existing low-offering warning, full-game and physical PSP checks remain pending.

'''
    if '## 0.2.20 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
    p.write_text(s,encoding='utf-8')
    (ROOT/'docs/equipment-deities-layout.txt').write_text('''Equipment and deity menus — local build 0.2.20

Source: delivered 0.2.19, pinned hashes in tools/build_equipment_deities.py.
Native 4x VWF and all script payloads are retained. The executable changes 35
guarded instructions and appends 40 bytes for two Latin labels/padding and a
16-byte native geometry wrapper. Eleven native graphics are translated, with
original palettes retained; the footer version changes. Other members match.

480x272 layout:
Equipment slots: four rows, one column, 248-pixel cells, name starts at x36.
The 212-pixel name budget exceeds the 202.286-pixel maximum among 463 fixed
equipment names. Available equipment has one 240-pixel column, four visible
rows and native scrolling. Source caption y100, candidates y126, description y218.
Slot frame is 268x90 at [208,8]; candidates are 260x90 at [216,126].
Divine Union submenu: 128-pixel text width, original centering/controls.
Deity list: four visible 32-pixel cells, width216. Name stays at [20,0];
cost is right-aligned at [90,16], element [106,18], gender centered [162,16].
The wrapper sets only row height before the original menu geometry routine.
Deity detail frame: [300,16,476,228]. Portrait [324,18,452,146].
Name [306,158], element [456,148], unions [306,179], required points [306,195],
required value right-aligned at [468,211]. Fixed deity names peak at 149.143
pixels, within a 160-pixel budget. The full requirement label is 147.429 pixels.

Build and checks:
tools/build_equipment_deities.py (dry run, then --write); tools/build_iso.py.
tools/test_equipment_deities.py; tools/verify_equipment_runtime.py;
tools/check_shop_font.py supports a version and output-directory override.
Runtime screenshots and identity proofs: work/ui/equipment-deities-0.2.20/.
The delivered image matches the tested candidate byte-for-byte. Original
project-profile saves are restored after QA; the tutorial-completed test save
is retained separately under ignored work/source/qa-save-equipment-0.2.20/.

Limits: selected initial party/stocks and fixed names; dynamic heirloom and
generated deity names need review. A pre-existing low-offering confirmation
warning can truncate its English message and is still pending. Full-playthrough
and real PSP boot/performance remain unverified. No GitHub release created.
''',encoding='utf-8')

if __name__=='__main__':main()

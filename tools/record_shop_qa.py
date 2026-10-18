"""Record selected native shop layout evidence and build notes. Dry run by default."""
import argparse,hashlib,json
from PIL import Image
from catalog_text import ROOT

VERSION='0.2.19';UI=ROOT/'work/ui/shop-layout-0.2.19'
SCREENS={
 'body-after.png':'Body armor: separated ownership/funds, stock/prices, names, equipped marker, DEF and signed change; two background kanji retained',
 'body-restricted.png':'Complete Female Exclusive restriction and Cannot Equip status; negative comparison',
 'body-detailed.png':'English Gear Stats heading and ATK/DEF/AGI native sprite labels',
 'head-armor.png':'Head armor list and two positive DEF comparisons',
 'sword-negative.png':'Weapons list, negative ATK comparison and Swordsman Exclusive restriction',
 'general-store.png':'General Store shares stock, prices, ownership and funds without comparison clutter',
 'inventory-detail.png':'Shared equipment description remains correctly separated in the wider inventory frame',
 'title.png':'Native v0.2.19 footer and complete github.com/retro-trans URL'}

def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    out=ROOT/'work/output/english-native-0.2.19';r=json.loads((out/'shop.report.json').read_text());proof=json.loads((UI/'runtime-patches.json').read_text())
    assert len(proof['native_patches_verified'])==71 and proof['elf_sha256']==r['elf_sha256'] and proof['archive_sha256']==r['archive_sha256']
    screens=[]
    for name,scope in SCREENS.items():
        p=UI/name;assert Image.open(p).size==(480,272);meta=json.loads(p.with_suffix('.json').read_text());assert meta['texture_replacement'] is False
        screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p),dimensions=[480,272],observed=scope,fit='pass'))
    for ctx in ('body','detailed','weapon'):
        f=json.loads((UI/('font-'+ctx+'.json')).read_text());assert f['result']=='PASS' and not f['texture_replacement']
    final=ROOT/'work/output/english-native-0.2.19.iso';candidate=ROOT/'work/source/qa-shop-0.2.19c.iso'
    assert final.exists();identity=dict(version=VERSION,tested_iso=candidate.relative_to(ROOT).as_posix(),delivered_iso=final.relative_to(ROOT).as_posix(),bytes=final.stat().st_size,sha256=sha(final))
    assert final.stat().st_size==candidate.stat().st_size==1079934976 and identity['sha256']==sha(candidate)
    unit=(ROOT/'work/source/test-shop-0.2.19.txt').read_text();assert '49 comparison-page cases' in unit and 'PASS' in unit
    checks=(ROOT/'work/source/check-translations-0.2.19.txt').read_text();assert 'ALL 49 BATCHES PASS' in checks
    verified=json.loads((ROOT/'work/ui/verified_screens.json').read_text());count=len(verified['visual_fit_verified_record_ids'])
    verification=dict(version=VERSION,result='PASS: selected native shop contexts',component_sha256=dict(elf=r['elf_sha256'],archive=r['archive_sha256']),screens=screens,native_mips=unit.strip(),runtime_patches=71,font_draws='Native atlas and UVs verified for funds, currency, ownership, DEF, ATK, signed change, popup heading and other English objects',script_text_changes=0,indexed_fit_count=count,background_helmet_and_armor_art='byte-identical',texture_replacement=False,limits=['Actual runtime party has two members with eight-letter names; 0..12 member paging covered by MIPS tests','Selected initial stocks; full-game/shop dynamic names and real PSP testing remain pending'],github_release=False)
    print(json.dumps(dict(version=VERSION,mode='write' if a.write else 'dry run',screens=len(screens),new_literals=len(r['literals']),new_graphic_labels=4,iso_identity=identity,sample=screens[1]),indent=2))
    if not a.write:return
    dump(UI/'image-identity.json',identity);dump(UI/'verification.json',verification)
    layout=json.loads((UI/'layout.json').read_text());layout['runtime_verification']='PASS: selected contexts; see verification.json';dump(UI/'layout.json',layout)
    r['runtime_verification']='PASS: work/ui/shop-layout-0.2.19/verification.json';dump(out/'shop.report.json',r)
    literal=ROOT/'work/translation/en/shop/literals.en.json';d=json.loads(literal.read_text());d['status']='Draft; selected native runtime font and layout checks pass';d['evidence']='work/ui/shop-layout-0.2.19/verification.json';dump(literal,d)
    graphics=dict(schema_version=1,version=VERSION,language='en',status='draft',rows=[])
    for file,base,entry,text,rect,screen in [('223.ppt',0xb4a800,16,'BUY / SELL',[0,0,48,112],'body-after.png'),('109.ppt',0x36000,12,'ATK',[0,0,32,16],'body-detailed.png'),('110.ppt',0x36000,14,'DEF',[0,0,32,16],'body-detailed.png'),('111.ppt',0x36000,15,'AGI',[0,0,32,16],'body-detailed.png')]:
        graphics['rows'].append(dict(file=file,archive_offset=base,member_entry=entry,translation_en=text,status='draft',label_rectangle=rect,fit_status='verified_selected_context_0.2.19',fit_evidence='work/ui/shop-layout-0.2.19/'+screen))
    dump(ROOT/'work/translation/en/graphics/shop_labels.en.json',graphics)
    glossary=dict(version=VERSION,scope='Native shop UI terms; UI source names only',terms=[dict(source_jp=jp,translation_en=en) for jp,en in [('\u6240\u6301\u91d1','Funds'),('\u4e21','ryo'),('\u653b','ATK'),('\u9632','DEF'),('\u654f','AGI'),('\u88c5\u5099\u6027\u80fd','Gear Stats'),('\u58f2\u8cb7','BUY / SELL')]])
    dump(ROOT/'work/glossary/shop_ui.json',glossary)
    verified['latest_evidence_version']=VERSION;evidence=dict(version=VERSION,evidence='work/ui/shop-layout-0.2.19/verification.json',scope='Native shop stock, funds, ownership, comparison, restrictions and Gear Stats popup; two background kanji preserved')
    if evidence not in verified['additional_build_evidence']:verified['additional_build_evidence'].append(evidence)
    dump(ROOT/'work/ui/verified_screens.json',verified)
    status=json.loads((ROOT/'docs/local_build_status.json').read_text());status.update(latest_local_build=VERSION,archive_translation_version=VERSION,file=final.relative_to(ROOT).as_posix(),bytes=final.stat().st_size,native_graphic_labels=23,additional_shop_native_literals=6,shop_ui_evidence='work/ui/shop-layout-0.2.19/verification.json')
    status['checks']['native_shop_layout']='PASS: 71 runtime patches, native-font UVs, selected armor/weapon/general-store/inventory screens, 49 MIPS comparison-page cases and expanded buffers'
    status['checks']['selected_actual_screen_fit']=f'{count} indexed records retain accumulated selected-context evidence; shop layout additionally verified in 0.2.19'
    status['title_branding'].update(version='v0.2.19',visual_evidence='work/ui/shop-layout-0.2.19/title.png');dump(ROOT/'docs/local_build_status.json',status)
    readme=ROOT/'README.md';text=readme.read_text(encoding='utf-8').replace('**0.2.18**, 2026-10-17; archive-text draft: **0.2.18**','**0.2.19**, 2026-10-17; archive-text draft: **0.2.19**').replace('Eighteen executable records and nineteen native graphic label groups are recorded separately.','Eighteen executable records, six additional shop literals, and twenty-three native graphic label groups are recorded separately.')
    line='- `work/output/english-native-0.2.19.iso`: translated and rearranged native shop screen, separate ownership/funds, wider stock/prices, four-member comparison paging, complete restrictions and English Gear Stats popup. The two large background kanji remain unchanged; see [shop layout notes](docs/shop-layout.txt).\n'
    if line not in text:text=text.replace('- `work/output/english-native-0.2.18.iso`:',line+'- `work/output/english-native-0.2.18.iso`:')
    readme.write_text(text,encoding='utf-8')
    changelog=ROOT/'CHANGELOG.md';text=changelog.read_text(encoding='utf-8');entry='''## 0.2.19 — 2026-10-17

- Translated native Funds/currency, ATK/DEF/AGI comparison labels, BUY / SELL ribbon and Gear Stats popup. The two large helmet/armor background kanji remain byte-identical. English text uses the embedded native 4× font, with texture replacement disabled.
- Separated ownership and funds at the top; widened stock cells to 398 pixels with right-aligned prices. Rebuilt the lower comparison area with four 100-pixel member cells, names above markers/stat changes, signed ASCII deltas, and native paging to all members. Retained the fifth allocation for destructor compatibility.
- Expanded four equipment-description buffers to 128 bytes each in a 736-byte stack frame. Separated stat/value and type/restriction fields, and added spaces without dropping restriction terms. The shared formatter also improves inventory details.
- Verified final components in game: 71 guarded runtime patches, appended strings/wrapper, native atlas/UVs, armor restrictions, positive/negative comparisons, weapons, General Store and inventory details. Actual MIPS tests cover coordinate assignments, register/stack preservation, buffer canaries and 49 paging cases for parties of 0–12. All 49 translation batches pass; script payloads and unrelated archive members remain byte-identical to 0.2.18. Evidence: `work/ui/shop-layout-0.2.19/`. Local test build only; no GitHub release. Full-game and physical PSP testing remain pending.

'''
    if '## 0.2.19 ' not in text:text=text.replace('# Changelog\n\n','# Changelog\n\n'+entry)
    changelog.write_text(text,encoding='utf-8')
    (ROOT/'docs/shop-layout.txt').write_text('''Native shop layout — local build 0.2.19

The two large helmet and armor background characters are preserved byte-for-byte.
The left BUY / SELL ribbon and three small popup icons are native PPT edits using
the original palettes. No texture replacement is used. Funds, ryo, comparison
labels and Gear Stats are six separately tracked native executable literals.

Native 480x272 layout (rectangles use left, top, right, bottom):
Stock: [56,42,474,168], one 398-pixel cell, six visible rows, original stock/paging.
Ownership: [56,8,208,34]. Funds: [290,10,470,34].
Comparison: [50,174,474,242], four 100-pixel cells at 104-pixel pitch.
Names occupy their own row. Equipped markers, stat labels and signed changes
occupy the next row. Native paging exposes every member; the fifth object stays
allocated for the existing destructor but is not attached or rendered.
Equipment details start at local [6,44], width 412. Stat/value region is 96;
armor type and restrictions start at x112. Four intermediate buffers are now
128 bytes each, at stack offsets 0xE0/0x160/0x1E0/0x260 in a 0x2E0 frame.
Saved registers and other locals retain their original offsets. All formatter
arguments/restriction words remain; the wrapper inserts separators as required.

Build: tools/build_shop_layout.py (dry run, then --write), then tools/build_iso.py.
Source inputs are pinned to delivered 0.2.18 hashes. Only the described guarded
executable bytes, appended 100-byte strings/wrapper, four native graphic assets
and footer version change. All script payloads and other archive members match.

Validation: tools/test_shop_layout.py; tools/verify_shop_runtime.py;
tools/check_shop_font.py; work/ui/shop-layout-0.2.19/verification.json.
The delivered ISO is byte-identical to the tested candidate. Runtime screenshots
use the original test party with two eight-letter names. Paging with up to 12
members is tested through actual native MIPS routines. Selected initial stocks
and screens are checked; full-game dynamic names and real PSP remain unverified.
Original project-profile save files are restored after QA. No release created.
''',encoding='utf-8')

if __name__=='__main__':main()

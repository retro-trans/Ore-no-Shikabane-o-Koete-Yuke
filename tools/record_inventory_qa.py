"""Record selected inventory/shop fit evidence. Dry run unless --write."""
import argparse,hashlib,json
from PIL import Image
from catalog_text import ROOT
from strip_jp import export

VERSION='0.2.18';UI=ROOT/'work/ui/menu-fit-0.2.18'
SCREENS={
 'title.png':'Native v0.2.18 footer; unchanged title/font behavior',
 'pack-actions.png':'Full action labels; capacity frame and digits clear of actions',
 'pack-firestorm.png':'Two columns; full Firestorm Talisman description inside widened frame',
 'pack-last-page.png':'Native scrolling reaches final inventory entries with no column collisions',
 'storehouse-categories.png':'First four categories in wider cells',
 'storehouse-curios.png':'Scrolled categories include complete Curios and Collectibles; heading stays on screen',
 'storehouse-prints.png':'Final Beauty Prints choice remains reachable',
 'shop-selector.png':'Three complete shop names with room inside the frame',
 'armor-submenu.png':'Armor submenu follows enlarged selector and clears its neighbor',
 'weapon-submenu.png':'Both weapon columns and right frame edge remain on screen'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    out=ROOT/'work/output/english-native-0.2.18';report=json.loads((out/'inventory.report.json').read_text())
    proof=json.loads((UI/'runtime-patches.json').read_text());layout=json.loads((UI/'layout.json').read_text())
    assert proof['elf_sha256']==report['elf_sha256'] and proof['archive_sha256']==report['archive_sha256']
    assert len(proof['native_patches_verified'])==40 and proof['wrapper_original_opcodes']=='pass'
    assert proof['iso']=='work/source/qa-inventory-0.2.18c.iso'
    assert layout['shops']['weapon_category_text_width']==84
    screens=[]
    for name,scope in SCREENS.items():
        p=UI/name;im=Image.open(p);assert im.size==(480,272)
        meta=json.loads(p.with_suffix('.json').read_text());assert meta['texture_replacement'] is False
        screens.append(dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),dimensions=[480,272],observed=scope,fit='pass'))
    rows={r['id']:r for p in (ROOT/'work/translation/en').glob('*.en.json') for r in json.loads(p.read_text(encoding='utf-8')).get('rows',[])}
    ids={f'ore:00028000:0003:03:{i:04d}' for i in (0,3,4,6)}
    ids|={f'ore:00028000:0003:01:{i:04d}' for i in (8,9,10,11,19,20,21)}
    ids|={f'ore:0000c000:0001:00:{i:04d}' for i in (1,12,13,14)}
    ids|={f'ore:00027000:0001:00:{i:04d}' for i in (16,17)}
    ids.add('ore:00028000:0002:00:0002')
    names={'Young Leaf Pills','Evergreen Elixir','Orb of Divine Favor','Firestorm Talisman','Catfish Talisman','Swift Wind Charm','Iron-Indigo Naginata','Asbestos Kimono','Fresh Green Hood','Spring Wind Bracelet'}
    found={r['translation_en']:r['id'] for r in rows.values() if r.get('archive_offset')==0x28000 and r.get('member_entry')==0 and r['translation_en'] in names}
    assert set(found)==names;ids.update(found.values());assert len(ids)==28 and ids<=rows.keys()
    verified=json.loads((ROOT/'work/ui/verified_screens.json').read_text())
    allids=sorted(set(verified['visual_fit_verified_record_ids'])|ids)
    final=ROOT/'work/output/english-native-0.2.18.iso'
    verification=dict(version=VERSION,result='PASS: selected shared inventory and shop layouts',
       component_sha256=dict(elf=report['elf_sha256'],archive=report['archive_sha256']),
       screens=screens,selected_record_ids=sorted(ids),accumulated_selected_record_count=len(allids),
       static_audit=dict(fixed_names=631,name_advance_budget=220,longest_advance=218.571,descriptions=232,description_budget=456,longest_description_advance=450.857,numeric_expansion='Conservative signed 32-bit values for all 41 numeric descriptions'),
       native_mips='PASS: both margin hooks preserve caller/stack/saved registers; original geometry returns 472x90; unhooked legacy geometry retained',
       navigation='PASS: last inventory page, all eight categories, armor and weapon submenus',
       limits=['Selected contexts; fixed-name measurements are not 631 actual-screen checks','Dynamic heirloom names and other menu families need separate review','Physical PSP and full-playthrough testing pending'],
       texture_replacement=False,font_changes=False,script_text_changes=0,github_release=False)
    print(json.dumps(dict(version=VERSION,write=a.write,screens=len(screens),selected_records=len(ids),accumulated_selected_records=len(allids),final_iso_exists=final.exists(),sample=screens[2]),indent=2))
    if not a.write:return
    assert final.exists() and final.stat().st_size==1079937024
    manifest=json.loads(final.with_suffix('.manifest.json').read_text());assert manifest['files'][0]['sha256']==report['elf_sha256'] and manifest['files'][1]['sha256']==report['archive_sha256']
    (UI/'verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
    layout['runtime_verification']='PASS: selected contexts; see verification.json'
    (UI/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
    report['runtime_verification']='PASS: selected contexts; work/ui/menu-fit-0.2.18/verification.json'
    (out/'inventory.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    verified['visual_fit_verified_record_ids']=allids;verified['latest_evidence_version']=VERSION
    evidence=dict(version=VERSION,evidence='work/ui/menu-fit-0.2.18/verification.json',scope='Shared inventory, category paging, descriptions and shop menu fit')
    if evidence not in verified['additional_build_evidence']:verified['additional_build_evidence'].append(evidence)
    (ROOT/'work/ui/verified_screens.json').write_text(json.dumps(verified,indent=2)+'\n',encoding='utf-8')
    for p in (ROOT/'work/translation/en').glob('*.json'):
        if p.name.endswith('.en.json'):continue
        d=json.loads(p.read_text(encoding='utf-8'));changed=False
        for r in d.get('rows',[]):
            if r.get('id') not in ids:continue
            r['fit_status']='verified_native_0.2.18_selected_context'
            note='Actual selected inventory/shop fit checked in work/ui/menu-fit-0.2.18/verification.json; this is visual evidence, not meaning approval.'
            if note not in r.setdefault('review_notes',[]):r['review_notes'].append(note)
            changed=True
        if changed:
            d['version']=VERSION;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            p.with_name(p.stem+'.en.json').write_text(json.dumps(export(p),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    status=json.loads((ROOT/'docs/local_build_status.json').read_text())
    status.update(latest_local_build=VERSION,archive_translation_version=VERSION,file='work/output/english-native-0.2.18.iso',bytes=final.stat().st_size,inventory_ui_evidence='work/ui/menu-fit-0.2.18/verification.json')
    status['checks']['selected_actual_screen_fit']=f'{len(allids)} indexed records have accumulated selected-context evidence; shared inventory/shop windows verified in 0.2.18'
    status['checks']['native_inventory_windows']='PASS: final component runtime patch checks, MIPS geometry, native item/category paging, full description and adjacent shop frames'
    for value in status.values():
        if isinstance(value,dict) and value.get('group')=='github.com/retro-trans':value.update(version='v0.2.18',visual_evidence='work/ui/menu-fit-0.2.18/title.png')
    (ROOT/'docs/local_build_status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()

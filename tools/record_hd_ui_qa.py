"""Record native HD UI evidence and update build notes. Dry run before --write."""
import argparse,json
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
V='0.2.26';UI=ROOT/('work/ui/hd-fonts-'+V);OUT=ROOT/('work/output/english-native-'+V)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    r=json.loads((OUT/'hd.report.json').read_text());iso=ROOT/('work/output/english-native-'+V+'.iso')
    assert sha(OUT/'EBOOT.hd.elf')==r['elf_sha256'] and sha(OUT/'data.hd.ore')==r['archive_sha256']
    assert len(r['graphics'])==83 and len(set(r['renderer']['embedded_descriptors']))==63
    assert '83 embedded descriptor proxies' in (UI/'mips-tests.txt').read_text()
    assert json.loads((UI/'save-preservation.json').read_text())['result']=='PASS'
    screens=[]
    for name in ('final-title','final-status','final-roster','final-equipment','final-spells'):
        p=UI/(name+'.png');assert Image.open(p).size==(480,272)
        assert json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False
        screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    runtime=[]
    for name in ('status','equipment','spells'):
        p=json.loads((UI/('final-runtime-'+name+'.json')).read_text());assert p['result']=='PASS'
        assert all(int(x['descriptor'],16) in r['renderer']['embedded_descriptors'] for x in p['images'])
        runtime.extend(p['images'])
    assert any(x['logical_size']==[142,252] for x in runtime)
    assert any(x['logical_size']==[44,260] for x in runtime)
    old=json.loads((ROOT/'work/source/qa-hd26-shared-tested/english-native-0.2.26/hd.report.json').read_text())
    lookup={(g['archive_offset'],g['member_entry']):g for g in r['graphics']}
    assert all(lookup[(g['archive_offset'],g['member_entry'])]['sha256']==g['sha256'] for g in old['graphics'])
    previous=[]
    for p in (ROOT/'work/translation/en/graphics').glob('*.en.json'):
        if p.name=='hd_ui.en.json':continue
        previous.extend((g['archive_offset'],g['member_entry']) for g in json.loads(p.read_text(encoding='utf-8')).get('rows',[]) if 'archive_offset' in g)
    new=[g for g in r['graphics'] if not g.get('category') and (g['archive_offset'],g['member_entry']) not in previous]
    assert len(new)==16
    identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
    limits=['Combat digit placement and battle-results screen still need live battle visual verification.','Full-playthrough and physical PSP tests remain pending.','Unrelated graphic text outside this screenshot-focused pass is not declared complete.']
    proof=dict(version=V,result='PASS: selected shared HD UI screens; battle visual QA pending',iso=identity,screens=screens,native_runtime_images=len(runtime),mips=(UI/'mips-tests.txt').read_text().strip(),checks=r['checks'],assets=83,unique_native_images=63,combat_digit_assets=50,additional_translated_label_groups=16,shared_intermediate_images_byte_identical=32,additional_component_evidence=['oni-after.png','runtime-oni.json','dungeon-walk.png'],additional_component_source_elf=old['elf_sha256'],texture_replacement=False,game_memory_writes=False,github_release=False,limits=limits)
    print(json.dumps(dict(write=a.write,iso=identity,assets=83,translated_label_groups_total=57,qa=proof['result'],limits=limits,changes=['QA and layout evidence','English graphic ledger','README and CHANGELOG','Local build status and translation progress']),indent=2))
    if not a.write:return
    dump(UI/'verification.json',proof);dump(UI/'image-identity.json',identity)
    dump(UI/'layout.json',dict(version=V,assets=r['graphics'],renderer=r['renderer'],geometry='Original logical size and selectors retained; source UV crops scaled to embedded HD pixels',badge_digit_raster_scale=4,tall_graphic_limit=[512,512],source_data_and_scripts='Preserved',capture_dimensions=[480,272]))
    dump(ROOT/'work/translation/en/graphics/hd_ui.en.json',dict(version=V,status='Draft; shared selected screens verified; combat visual check pending',rows=r['graphics']))
    r['runtime_verification']=proof['result'];dump(OUT/'hd.report.json',r)
    p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'],native_graphic_labels=57,native_hd_image_assets=83,native_hd_unique_images=63,native_hd_combat_digit_assets=50,native_hd_ui_evidence='work/ui/hd-fonts-0.2.26/verification.json')
    q['title_branding'].update(version='v'+V,visual_evidence='work/ui/hd-fonts-0.2.26/final-title.png');q['checks']['native_hd_ui']=proof['result'];dump(p,q)
    p=ROOT/'docs/translation_progress.json';q=json.loads(p.read_text());q['version']=V;q['additional_draft_records_by_domain']['graphics']=57;q['native_hd_image_assets']=83;q['native_hd_combat_digit_assets']=50;dump(p,q)
    p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text());q['latest_evidence_version']=V;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/hd-fonts-0.2.26/verification.json',scope=proof['result']+'; core indexed fit count unchanged')];dump(p,q)
    p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.26 (2026-10-18)

- Replaced 83 native image assets with Noto Sans artwork: 33 shared badges, headings and chart backgrounds, plus 50 white/green/purple combat digit images across both number packs. Badges and digits use 4x rasters; tall headings and the Potential chart respect the PSP 512-by-512 texture limit.
- Translated remaining selected graphic labels: STATUS, BATTLE RESULTS, ONI RECORDS, ITEM CATALOG, Defeated, Specialty, WINS, Growth, compact Spirit/Skill/Body labels and Study/Train/Command badges. Replaced the Japanese Potential watermarks with SPIRIT, SKILL and BODY. Existing unknown-enemy question marks remain intentional.
- Embedded 63 unique native images and added image binding/UV hooks. Archive resources retain exactly their original decompressed sizes, keeping within the shared loader budget. Original logical geometry, crop rectangles, selection borders, scripts and unrelated archive members are preserved. Texture replacement remains disabled.
- Passed 40 actual MIPS crop cases and 83 descriptor-proxy cases. Verified the final ISO title, status, roster, equipment and spell screens, including physical texture sizes and native UVs. Oni Records and dungeon traversal were also checked on a shared-image candidate whose 32 images are byte-identical in the final build.
- Combat digits and battle-results artwork are included; their live battle visual check remains pending. Full-playthrough and physical PSP checks remain pending. Evidence: work/ui/hd-fonts-0.2.26/. Original project-profile saves restored after QA. Local test build only; no GitHub release.

'''
    if '## 0.2.26 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
    p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('**0.2.25**, 2026-10-18; archive-text draft: **0.2.25**.','**0.2.26**, 2026-10-18; archive-text draft: **0.2.26**.').replace('forty-one native graphic assets/label groups','57 native graphic assets/label groups')
    line='- `work/output/english-native-0.2.26.iso`: 83 native HD badge, heading, chart and combat-digit assets; selected remaining graphic translations. Battle visual QA pending. See [QA evidence](work/ui/hd-fonts-0.2.26/verification.json).\n'
    if line not in s:s=s.replace('- `work/output/english-native-0.2.25.iso`',line+'- `work/output/english-native-0.2.25.iso`',1)
    p.write_text(s,encoding='utf-8')
    (ROOT/'docs/native-hd-ui.txt').write_text('Native HD UI — local build 0.2.26\n\n83 archive resources redirect to 63 unique embedded native images. Each proxy\nhas its original decompressed byte size and logical dimensions. This avoids\nexceeding the fixed shared resource loader budget. Image binding redirects\nonly tagged resources; source rectangles map from logical pixels to physical\nHD pixels on every update. Other sprites retain their original handling.\n\nBadges/digits use 4x rasters. Tall ribbons use192x512 storage and the Potential\nchart512x512, preserving original44x260/142x252 logical geometry. Native PSP\ntexture replacement is disabled. All scripts and unrelated archive members\nmatch0.2.25. The existing eight-character names and punctuation fix remain.\n\nSee work/ui/hd-fonts-0.2.26/verification.json for actual screens, native UV\nreadbacks and explicit QA limits. Combat digits/results still need a live\nbattle visual check. Saves were restored and verified. No GitHub release.\n',encoding='utf-8')
if __name__=='__main__':main()

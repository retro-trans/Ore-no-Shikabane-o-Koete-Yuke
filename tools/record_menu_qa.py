"""Record reviewed 0.2.9 guest-framebuffer evidence. Dry run first."""
import argparse
import hashlib
import json
from PIL import Image
from catalog_text import ROOT
from strip_jp import export


def prepare():
    ui = ROOT/'work/ui/menu-fixes-0.2.9'
    build = ROOT/'work/output/english-native-0.2.9'
    report = json.loads((build/'menu.report.json').read_text())
    for name,key in [('EBOOT.menu.elf','elf_sha256'),('data.menu.ore','archive_sha256')]:
        assert hashlib.sha256((build/name).read_bytes()).hexdigest() == report[key]
    files = ['deity-confirm.png','character-menu.png','character-best-equipment.png',
             'home-menu.png','home-facilities.png','home-save.png',
             'portrait-studio.png','portrait-studio-long-choice.png','final-title.png']
    shots = []
    for name in files:
        p = ui/name
        assert Image.open(p).size == (480,272)
        capture = json.loads(p.with_suffix('.json').read_text())
        assert capture['game'] == 'UCJS10117' and capture['texture_replacement'] is False
        shots.append(dict(file=str(p.relative_to(ROOT)).replace('\\','/'),
                          sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    groups = [
        dict(request=1,result='pass',wording='"Sasara no Oen"?\nIs that your choice?',
             explanation='The old 64-byte runtime buffer cut off choice. The 256-byte allocation and formatter preserve the complete question; the popup measures its text.',
             screenshot='deity-confirm.png'),
        dict(request=2,result='pass',box=[162,82,156,108],cell_width=112,
             explanation='All five labels fit. Best Equipment selected; full highlight remains inside the wider window.',
             screenshot='character-best-equipment.png'),
        dict(request=3,result='pass',box=[50,64,312,90],cell_width=96,
             explanation='Twelve entries occupy three distinct columns. The draw key keeps the window above both the umbrella and SAVE poses.',
             screenshots=['home-menu.png','home-facilities.png','home-save.png']),
        dict(request=4,result='pass',box=[122,165,268,54],cell_width=248,
             explanation='Family Photo and Portrait Studio native artwork translated. Both complete choices and their highlights fit below the banner heading.',
             screenshots=['portrait-studio.png','portrait-studio-long-choice.png'])]
    evidence = dict(version='0.2.9',review='Selected four requested screens visually reviewed; not full-game approval.',
                    capture_method='Actual guest display buffers; isolated PPSSPP profile, software backend.',
                    texture_replacement=False,iso='work/output/english-native-0.2.9.iso',
                    iso_bytes=(ROOT/'work/output/english-native-0.2.9.iso').stat().st_size,
                    elf_sha256=report['elf_sha256'],archive_sha256=report['archive_sha256'],
                    cases=groups,screenshots=shots,
                    checks=['ISO directory and replacement hashes','Unrelated archive payloads/members byte-identical',
                            'Actual MIPS stack/register preservation and contextual studio positioning',
                            'All 49 translation batches pass'],
                    limitations=['Selected runtime name and menu contexts only; broad gameplay and real PSP testing remain pending.'])
    changes = {}
    ids = ['ore:001e8000:0000:03:0013']
    ids += ['ore:0000c000:0009:00:%04d'%n for n in [0,1,2,3,13]]
    ids += ['ore:0000c000:0000:00:%04d'%n for n in range(12)]
    ids += ['ore:0000c000:0010:00:%04d'%n for n in [56,57]]
    for name in ['initial_batch.json','ui_batch_002.json','ui_batch_004.json','ui_batch_005.json']:
        p = ROOT/'work/translation/en'/name
        batch = json.loads(p.read_text(encoding='utf-8'))
        for row in batch['rows']:
            if row['id'] in ids:
                row['fit_status'] = 'verified_selected_context_0.2.9'
                row['fit_evidence'] = 'work/ui/menu-fixes-0.2.9/verification.json'
        changes[p] = batch
    qpath = ROOT/'work/ui/verified_screens.json'
    qa = json.loads(qpath.read_text())
    qa['visual_fit_verified_record_ids'] = list(dict.fromkeys(qa['visual_fit_verified_record_ids']+ids))
    qa['latest_evidence_version'] = '0.2.9'
    qa.setdefault('additional_build_evidence',[]).append(dict(version='0.2.9',
        evidence='work/ui/menu-fixes-0.2.9/verification.json',scope='Four requested deity/character/home/studio fixes'))
    changes[qpath] = qa
    statuspath = ROOT/'docs/local_build_status.json'
    status = json.loads(statuspath.read_text())
    status.update(latest_local_build='0.2.9',file='work/output/english-native-0.2.9.iso',
                  bytes=evidence['iso_bytes'],native_graphic_labels=8,
                  menu_ui_evidence='work/ui/menu-fixes-0.2.9/verification.json')
    status['title_branding']['version'] = 'v0.2.9'
    status['title_branding']['visual_evidence'] = 'work/ui/menu-fixes-0.2.9/final-title.png'
    status['checks'].update(menu_four_requested_fixes='PASS; final 0.2.9 guest-framebuffer captures',
        native_menu_hooks='PASS; MIPS stack/register return preservation and studio-only positioning',
        home_preview_overlap='PASS; umbrella and SAVE poses',
        selected_actual_screen_fit='%d indexed records have accumulated selected-context fit evidence; seven standalone UI records verified in 0.2.8'%len(qa['visual_fit_verified_record_ids']))
    changes[statuspath] = status
    gpath = ROOT/'work/translation/en/graphics/menu_labels.en.json'
    graphics = json.loads(gpath.read_text())
    for row in graphics['rows']:
        row['fit_status'] = 'verified_selected_context_0.2.9'
        row['fit_evidence'] = 'work/ui/menu-fixes-0.2.9/portrait-studio.png'
    changes[gpath] = graphics
    report['runtime_verification'] = 'PASS; work/ui/menu-fixes-0.2.9/verification.json'
    changes[build/'menu.report.json'] = report
    changes[ui/'verification.json'] = evidence
    return changes,ids


def main():
    ap = argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    changes,ids = prepare()
    print(json.dumps(dict(version='0.2.9',cases=4,reviewed_core_records=len(ids),
                          samples=['Is that your choice?','Best Equipment','Divine Union','FAMILY PHOTO','PORTRAIT STUDIO'],
                          files=[str(p.relative_to(ROOT)).replace('\\','/') for p in changes]),indent=2))
    if args.write:
        for p,obj in changes.items():p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for p in changes:
            if p.parent == ROOT/'work/translation/en' and not p.name.endswith('.en.json'):
                safe = p.with_name(p.stem+'.en.json')
                safe.write_text(json.dumps(export(p),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Evidence recorded.' if args.write else 'DRY RUN: metadata unchanged.')


if __name__ == '__main__':main()

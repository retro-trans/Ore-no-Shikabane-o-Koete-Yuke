"""Record inspected destination-menu captures. Dry run unless --write."""
import argparse
import hashlib
import json

from catalog_text import ROOT
from strip_jp import export

VERSION='0.2.11'


def prepare():
    ui=ROOT/'work/ui/destination-fixes-0.2.11'
    build=ROOT/'work/output/english-native-0.2.11'
    report=json.loads((build/'destination.report.json').read_text())
    for name,key in [('EBOOT.destination.elf','elf_sha256'),('data.destination.ore','archive_sha256')]:
        assert hashlib.sha256((build/name).read_bytes()).hexdigest()==report[key]
    shots=[]
    for name in ['title','destination-enter','destination-records','destination-treasures']:
        p=ui/(name+'.png');meta=json.loads(p.with_suffix('.json').read_text())
        assert meta['game']=='UCJS10117' and meta['dimensions']==[480,272] and not meta['texture_replacement']
        shots.append(dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    ids=[f'ore:00027000:0001:00:{i:04d}' for i in range(3)]
    verification=dict(version=VERSION,texture_replacement=False,font_raster_scale=4,
                      capture_method='Actual guest framebuffer; isolated PPSSPP, software backend; final ISO',
                      result='PASS in Mount Oe destination context',screenshots=shots,
                      translated_banner='MOUNT OE; native 279.ppt from 0.2.10',
                      menu=dict(labels=['Enter','Oni Records','Treasures'],cell_width=88,columns=3,
                                bounds=[79,18,322,36],all_three_highlights='verified',
                                original_centering_and_navigation='retained'),
                      visual_fit_record_ids=ids,elf_sha256=report['elf_sha256'],archive_sha256=report['archive_sha256'],
                      checks=report['checks'],limitations='Selected destination context only; full gameplay and real PSP testing remain pending.')
    changes={ui/'verification.json':verification}
    path=ROOT/'work/translation/en/ui_batch_011.json';batch=json.loads(path.read_text(encoding='utf8'))
    for row in batch['rows']:
        if row['id'] in ids:
            row['fit_status']='verified_selected_context_0.2.11';row['fit_evidence']='work/ui/destination-fixes-0.2.11/verification.json'
    changes[path]=batch
    qpath=ROOT/'work/ui/verified_screens.json';qa=json.loads(qpath.read_text())
    qa['visual_fit_verified_record_ids']=list(dict.fromkeys(qa['visual_fit_verified_record_ids']+ids))
    qa['latest_evidence_version']=VERSION
    qa['additional_build_evidence']=[x for x in qa.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/destination-fixes-0.2.11/verification.json',scope='Mount Oe banner and three dungeon destination menu labels')]
    changes[qpath]=qa
    spath=ROOT/'docs/local_build_status.json';status=json.loads(spath.read_text())
    status.update(latest_local_build=VERSION,file=f'work/output/english-native-{VERSION}.iso',
                  bytes=(ROOT/f'work/output/english-native-{VERSION}.iso').stat().st_size,
                  destination_ui_evidence='work/ui/destination-fixes-0.2.11/verification.json')
    status['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/destination-fixes-0.2.11/title.png')
    status['checks']['destination_menu']='PASS; English Mount Oe banner and all three menu highlights in actual final-build captures'
    status['checks']['selected_actual_screen_fit']=f"{len(qa['visual_fit_verified_record_ids'])} indexed records have accumulated selected-context fit evidence; seven standalone UI records verified in 0.2.8"
    changes[spath]=status
    # Update evidence for the already catalogued Mount Oe graphic, without
    # creating a duplicate translation record or increasing draft coverage.
    gpath=ROOT/'work/translation/en/graphics/map_labels.en.json';graphics=json.loads(gpath.read_text())
    for row in graphics['rows']:
        if row['translation_en']=='Mount Oe':
            row['fit_status']='verified_selected_context_0.2.11';row['fit_evidence']=['work/ui/destination-fixes-0.2.11/destination-enter.png']
    changes[gpath]=graphics
    report['runtime_verification']='PASS: Mount Oe English banner, complete labels and all three highlights; work/ui/destination-fixes-0.2.11/verification.json'
    changes[build/'destination.report.json']=report
    print(json.dumps(dict(version=VERSION,actual_captures=shots,fit_ids=ids,total_core_fit_records=len(qa['visual_fit_verified_record_ids']),new_translation_records=0,changes=[str(p.relative_to(ROOT)) for p in changes]),indent=2))
    return changes,path


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    changes,batch=prepare()
    if args.write:
        for path,obj in changes.items():path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        batch.with_name(batch.stem+'.en.json').write_text(json.dumps(export(batch),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('QA records written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()

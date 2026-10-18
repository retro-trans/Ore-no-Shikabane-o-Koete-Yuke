"""Record inspected 0.2.10 map captures and source-free catalog. Dry run by default."""
import argparse
import hashlib
import json

from catalog_text import ROOT

VERSION='0.2.10'


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    output=ROOT/'work/output/english-native-0.2.10'
    report=json.loads((output/'map.report.json').read_text())
    captures=['final-title','final-kyoto','final-soyokuin','final-overview']
    evidence=[]
    for name in captures:
        path=ROOT/f'work/ui/map-fixes-0.2.10/{name}.png'
        meta=json.loads(path.with_suffix('.json').read_text())
        assert meta['texture_replacement'] is False and meta['dimensions']==[480,272]
        evidence.append(dict(file=str(path.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),display_dimensions=[480,272]))
    ore=output/'data.map.ore';assert hashlib.sha256(ore.read_bytes()).hexdigest()==report['archive_sha256']
    rows=[]
    labels=list(dict.fromkeys(x['translation'] for x in report['assets']))
    for label in labels:
        assets=[x for x in report['assets'] if x['translation']==label]
        visible=label in ['Kyoto','Soyokuin','Kujuro','Torii Senmangu','KYO / N / E / S / W']
        rows.append(dict(id='map-'+('compass' if label.startswith('KYO /') else label.lower().replace(' ','-')),
                         translation_en=label,status='draft',assets=assets,
                         fit_status='verified_selected_context_0.2.10' if visible else 'native_asset_preview_checked; runtime_pending',
                         fit_evidence=[e['file'] for e in evidence[1:]] if visible else ['work/ui/map-fixes-0.2.10/native-contact-sheet.png'],
                         context='Overworld signs and selected destination. Map copies use the same glossary spelling across both sets and all seasons.'))
    catalog=dict(schema_version=1,version=VERSION,language='en',status='draft',rows=rows)
    verification=dict(version=VERSION,date='2026-10-17',texture_replacement=False,font_raster_scale=4,
                      emulator='Isolated project PPSSPP; software backend; final ISO',
                      runtime_result='PASS in selected April map context',
                      verified=['Title footer v0.2.10','Kyoto portrait banner','Soyokuin selected-destination banner',
                                'Soyokuin, Kujuro and Torii Senmangu small map signs','English Kyoto compass'],
                      native_asset_checks=dict(destination_banners=10,map_sign_copies=50,compass_copies=8,
                                                preview='work/ui/map-fixes-0.2.10/native-contact-sheet.png',
                                                coordinates='work/output/english-native-0.2.10/map.report.json'),
                      remaining='Other seasonal/late-game instances have static native-asset checks only; full playthrough and real PSP testing remain pending.',
                      screenshots=evidence,archive_sha256=report['archive_sha256'],
                      screen_rectangles=dict(kyoto_banner=[400,12,60,190],destination_banner=[410,30,65,210],
                                             map_signs='World-space sprites; screen coordinates vary with party movement.',compass='World-space sprite; coordinates vary with movement.'))
    status_path=ROOT/'docs/local_build_status.json';status=json.loads(status_path.read_text())
    status.update(latest_local_build=VERSION,file=f'work/output/english-native-{VERSION}.iso',
                  bytes=(ROOT/f'work/output/english-native-{VERSION}.iso').stat().st_size,native_graphic_labels=19,
                  map_ui_evidence='work/ui/map-fixes-0.2.10/verification.json')
    status['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/map-fixes-0.2.10/final-title.png')
    status['checks']['overworld_map_labels']='PASS; Kyoto/Soyokuin banners, three small signs and English compass in final April captures; other instances preview checked'
    qa_path=ROOT/'work/ui/verified_screens.json';qa=json.loads(qa_path.read_text())
    qa['latest_evidence_version']=VERSION
    qa['additional_build_evidence']=[x for x in qa.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/map-fixes-0.2.10/verification.json',scope='Native overworld labels; core script fit count unchanged')]
    report['runtime_verification']='PASS in selected April map context; see work/ui/map-fixes-0.2.10/verification.json'
    writes={ROOT/'work/translation/en/graphics/map_labels.en.json':catalog,
            ROOT/'work/ui/map-fixes-0.2.10/verification.json':verification,
            status_path:status,qa_path:qa,output/'map.report.json':report}
    print(json.dumps(dict(version=VERSION,graphic_label_groups=len(rows),actual_captures=evidence,
                         archive_sha256=report['archive_sha256'],iso_bytes=status['bytes'],
                         writes=[str(p.relative_to(ROOT)) for p in writes]),indent=2))
    if args.write:
        for path,obj in writes.items():path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
    print('QA records written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()

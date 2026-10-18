"""Record the completed 0.2.8 setup-screen checks. Dry run before --write."""
import argparse
import hashlib
import json

import numpy as np
from PIL import Image

from catalog_text import ROOT
from strip_jp import export

MAIN_IDS=['ore:001e8000:0000:'+s for s in
          ['02:0000','02:0001','02:0002','02:0003','02:0015','02:0016','04:0004','06:0002','06:0004']]
NAME_INDICES={0,1,2,3,5,6,12}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    ui=ROOT/'work/ui/setup-fixes-0.2.8'
    output=ROOT/'work/output/english-native-0.2.8'
    build=json.loads((output/'setup.report.json').read_text())
    percentages=json.loads((ui/'percent-native-font.json').read_text())
    assert percentages['status']=='PASS' and percentages['percentage_objects']==3 and percentages['padded_value_verified']
    assert hashlib.sha256((output/'data.setup.ore').read_bytes()).hexdigest()==build['output_archive_sha256']
    assert hashlib.sha256((output/'EBOOT.setup.elf').read_bytes()).hexdigest()==build['native_date']['output_sha256']
    screens=['gender-choice','family-prompt','family-entry','family-confirm','given-entry','given-confirm',
             'birthdate-year','birthdate-month','birthdate-day','birthdate-confirm','difficulty-light','difficulty-thorough']
    for name in screens:
        assert Image.open(ui/(name+'.png')).size==(480,272)
    dates=[]
    for name in ['birthdate-year','birthdate-month','birthdate-day']:
        a=np.asarray(Image.open(ui/(name+'.png'))).astype(int)
        ys,xs=np.where((a[:,:,1]>a[:,:,0]+25)&(a[:,:,1]>a[:,:,2]+25))
        dates.append(dict(id=name,highlight_rectangle=[int(xs.min()),int(ys.min()),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)]))
    cases=[dict(id=1,result='PASS',fix='Three-line family-name instruction fits; unselected gender label clears screen edge.',screens=screens[:3]),
           dict(id=2,result='PASS',fix='Input / Auto / OK and family/given-name labels are English.',screens=['family-entry','given-entry']),
           dict(id=3,result='PASS',fix='Name-confirmation prose is English; player-entered/generated names are retained.',screens=['family-confirm','given-confirm']),
           dict(id=4,result='PASS',fix='Gregorian YYYY/MM/DD; year/month/day highlights align and day increment works.',screens=['birthdate-year','birthdate-month','birthdate-day','birthdate-confirm']),
           dict(id=5,result='PASS',fix='All three percentages, including non-breaking-space padding, use the native 4x atlas.',screens=['difficulty-light','difficulty-thorough'],native_evidence='percent-native-font.json')]
    report=dict(version='0.2.8',status='PASS',capture='Actual guest PSP framebuffer, isolated PPSSPP software backend',
                dimensions=[480,272],texture_replacement=False,executable_sha256=build['native_date']['output_sha256'],
                archive_sha256=build['output_archive_sha256'],requested_fixes=cases,
                family_dialogue_rectangle=[91,6,297,69],family_text_area=[100,16,278,49],
                name_menu_rectangle=[61,102,48,68],name_field_rectangle=[161,123,158,26],
                date_rectangle=[150,123,180,26],date_highlights=dates,
                measurement_note='Window coordinates estimated from actual captures; green highlight bounds measured by pixel color. No character limit is inferred.',
                main_visual_fit_record_ids=MAIN_IDS,
                standalone_visual_fit_record_ids=[f'root:0027:00:{i:04d}' for i in sorted(NAME_INDICES)],
                limitation='Unvisited name-entry errors/child-name/OSK contexts, other gameplay layouts and real PSP hardware remain unverified.')
    print(json.dumps(report,indent=2))
    if not args.write:
        print('DRY RUN: no metadata or translations written.')
        return
    (ui/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for relative in ['work/translation/en/ui_batch_002.json','work/translation/en/name_entry/prompts.json']:
        path=ROOT/relative;batch=json.loads(path.read_text(encoding='utf-8'))
        for row in batch['rows']:
            if row['id'] in MAIN_IDS or (relative.endswith('prompts.json') and row['index'] in NAME_INDICES):
                row['fit_status']='verified_in_game_0.2.8'
        path.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        path.with_suffix('.en.json').write_text(json.dumps(export(path),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    path=ROOT/'work/ui/verified_screens.json';qa=json.loads(path.read_text())
    qa['visual_fit_verified_record_ids']=list(dict.fromkeys(qa['visual_fit_verified_record_ids']+MAIN_IDS))
    qa['latest_evidence_version']='0.2.8'
    extra=[r for r in qa.get('additional_build_evidence',[]) if r['version']!='0.2.8']
    extra.append(dict(version='0.2.8',feature='Five reported setup UI fixes',verification='work/ui/setup-fixes-0.2.8/verification.json'))
    qa['additional_build_evidence']=extra
    path.write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8')
    path=ROOT/'docs/local_build_status.json';status=json.loads(path.read_text())
    status.update(latest_local_build='0.2.8',archive_translation_version='0.2.8',file='work/output/english-native-0.2.8.iso',
                  bytes=(ROOT/'work/output/english-native-0.2.8.iso').stat().st_size,native_font_selector_version='0.2.8',
                  additional_standalone_name_entry_ui_records=14,retained_japanese_player_name_pool_records=1735,
                  archive_draft_records_including_empty_and_non_japanese=11594,
                  draft_coverage_scope='Indexed EZBIND text; 14 standalone UI prompts tracked separately, Japanese player-name pools retained.')
    status['title_branding']['version']='v0.2.8'
    status['indexed_ezbind_japanese_bearing_records']=status.pop('japanese_bearing_archive_records',11026)
    status['checks'].update(setup_five_requested_fixes='PASS; actual 0.2.8 framebuffer captures',
                            native_percentages='PASS; all three values including padded 94%, 12 glyph descriptors',
                            mips_date_and_font_padding='PASS; actual MIPS cursor ranges/year forwarding, ASCII/NBSP and Japanese fallback',
                            standalone_name_entry='14 source/token/line checks and all 1735 name-pool records preserved',
                            runtime_native_font='Verified in 0.2.8 on all three percentage objects; native atlas/UVs/ASCII advances',
                            selected_actual_screen_fit='10 indexed records have accumulated fit evidence; seven standalone UI records verified in 0.2.8')
    status['setup_ui_evidence']='work/ui/setup-fixes-0.2.8/verification.json'
    path.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    build['runtime_verification']='PASS: five requested fixes; see work/ui/setup-fixes-0.2.8/verification.json'
    (output/'setup.report.json').write_text(json.dumps(build,indent=2)+'\n',encoding='utf-8')
    print('Verification, fit metadata and local build status written.')


if __name__=='__main__':main()

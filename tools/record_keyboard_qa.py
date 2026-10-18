"""Record inspected native keyboard evidence. Dry run unless --write."""
import argparse
import hashlib
import json

from catalog_text import ROOT
from strip_jp import export
from build_english_keyboard import INSTRUCTION


def prepare():
    ui=ROOT/'work/ui/alphabet-0.2.12';build=ROOT/'work/output/english-native-0.2.12'
    report=json.loads((build/'keyboard.report.json').read_text())
    for name,key in [('EBOOT.keyboard.elf','elf_sha256'),('data.keyboard.ore','archive_sha256')]:
        assert hashlib.sha256((build/name).read_bytes()).hexdigest()==report[key]
    shots=[]
    for name in ['title','lowercase','uppercase','japanese-retained','mixed-case','family-entered','family-confirm','given-entered','child-entered','save-complete','reloaded-names']:
        p=ui/(name+'.png');meta=json.loads(p.with_suffix('.json').read_text())
        assert meta['game']=='UCJS10117' and meta['dimensions']==[480,272] and not meta['texture_replacement']
        shots.append(dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    request=json.loads((ui/'native-request.json').read_text())
    assert request['language']==2 and request['inputtype']=='0xd00f' and request['limit']==3
    loaded=json.loads((ui/'reloaded-memory.json').read_text())
    assert all(loaded['names'][name]['normalized']==name and any(loaded['names'][name]['guest_addresses'].values()) for name in ['AbZ','1Te','aaa'])
    evidence=dict(version='0.2.12',result='PASS in selected family/given-name contexts',texture_replacement=False,
                  capture_method='Actual guest framebuffer; isolated PPSSPP software backend; final ISO',
                  screenshots=shots,native_request=request,reloaded_names=loaded,checks=report['checks'],
                  tested=['English lowercase is the default','Select toggles uppercase','Japanese remains available with shoulder-button switching',
                          'OSK output AbZ preserves both cases','Fourth character is rejected at the original three-character limit',
                          'Family, given and child names accepted by game validation and native rendering',
                          'AbZ family, 1Te given and aaa child names survive actual game save and reload; original fullwidth storage preserves case'],
                  keyboard_font='PSP system OSK font; game display retains native 4x VWF',
                  save_profile='Project-isolated UCJS10117; previous QA save backed up under work/source/qa-backup-before-0.2.12/',
                  limitations='Physical PSP and unvisited name-entry error paths remain untested. Three-character limit retained.')
    changes={ui/'verification.json':evidence}
    p=ROOT/'work/translation/en/ui_batch_002.json';batch=json.loads(p.read_text(encoding='utf-8'))
    row=next(x for x in batch['rows'] if x['id']=='ore:001e8000:0000:02:0001')
    row['translation_en']=INSTRUCTION;row['fit_status']='verified_selected_context_0.2.12'
    row['fit_evidence']='work/ui/alphabet-0.2.12/family-entered.png'
    note='0.2.12: user-requested English name input; adapt the kanji-only reminder to spelling. Three lines retained.'
    if note not in row.setdefault('review_notes',[]):row['review_notes'].append(note)
    batch['version']='0.2.12';changes[p]=batch
    qpath=ROOT/'work/ui/verified_screens.json';qa=json.loads(qpath.read_text())
    qa['latest_evidence_version']='0.2.12'
    qa['additional_build_evidence']=[x for x in qa.get('additional_build_evidence',[]) if x['version']!='0.2.12']+[dict(version='0.2.12',evidence='work/ui/alphabet-0.2.12/verification.json',scope='Native Latin name input, case/language switching, validation and save reload')]
    changes[qpath]=qa
    spath=ROOT/'docs/local_build_status.json';status=json.loads(spath.read_text())
    status.update(latest_local_build='0.2.12',archive_translation_version='0.2.12',file='work/output/english-native-0.2.12.iso',
                  bytes=(ROOT/'work/output/english-native-0.2.12.iso').stat().st_size,
                  english_name_entry_evidence='work/ui/alphabet-0.2.12/verification.json')
    status['title_branding'].update(version='v0.2.12',visual_evidence='work/ui/alphabet-0.2.12/title.png')
    status['checks']['native_english_name_entry']='PASS; lowercase/uppercase/Japanese switching, three-character bound, validation and actual save/reload'
    status['checks']['mips_osk_initializer']='PASS; Latin flags, English language, other field bytes, stack and saved registers'
    changes[spath]=status
    report['runtime_verification']='PASS: work/ui/alphabet-0.2.12/verification.json'
    changes[build/'keyboard.report.json']=report
    print(json.dumps(dict(version='0.2.12',captures=len(shots),instruction=INSTRUCTION,keyboard=request,changes=[str(p.relative_to(ROOT)) for p in changes]),indent=2))
    return changes,p


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    changes,batch=prepare()
    if args.write:
        for path,obj in changes.items():path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        batch.with_name(batch.stem+'.en.json').write_text(json.dumps(export(batch),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('QA records written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':main()

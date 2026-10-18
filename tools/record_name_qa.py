"""Record inspected eight-character-name evidence; dry run unless --write."""
import argparse
import hashlib
import json
from catalog_text import ROOT, parse_mlt
from check_translation import tokens_equal
from strip_jp import export
from build_long_names import VERSION, PROMPTS

def prepare():
    ui=ROOT/('work/ui/names-'+VERSION);build=ROOT/('work/output/english-native-'+VERSION)
    report=json.loads((build/'names.report.json').read_text(encoding='utf-8'))
    for name,key in [('EBOOT.names.elf','elf_sha256'),('data.names.ore','archive_sha256')]:
        assert hashlib.sha256((build/name).read_bytes()).hexdigest()==report[key]
    screenshots=[]
    for name in ['title','reloaded-roster','save-complete','keyboard-eight','short-name-hd','family-confirm','reopened-eight']:
        p=ui/(name+'.png');meta=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
        assert meta['game']=='UCJS10117' and meta['dimensions']==[480,272] and not meta['texture_replacement']
        screenshots.append(dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    loaded=json.loads((ui/'reloaded-memory.json').read_text(encoding='utf-8'))
    assert all(loaded['names'][n]['guest_addresses'] for n in ['WWWWWWWW','aaaaAAAA','bbbbBBBB'])
    request=json.loads((ui/'native-request.json').read_text(encoding='utf-8'))
    output=json.loads((ui/'osk-output.json').read_text(encoding='utf-8'))
    assert request['limit']==8 and request['capacity']==128 and request['language']==2 and request['inputtype']=='0xd00f'
    assert output['length']==8 and output['normalized']=='poppPPPP' and output['ninth_character_attempted']
    evidence=dict(version=VERSION,result='PASS in selected name-entry, confirmation, roster and save/reload contexts',
                  texture_replacement=False,font_raster_scale=4,screenshots=screenshots,reloaded_names=loaded,
                  native_request=request,actual_osk_output=output,
                  maximum_english_characters=8,maximum_japanese_characters=3,
                  storage='Original eight-byte records; compact printable Latin for 4..8 letters, legacy UCS-2 for shorter/Japanese names',
                  display='Packed names decode to original fullwidth game text; glyph creation normalizes Latin to the native 4x atlas',
                  card_layout=dict(original_height=104,height=116,name_y=87,original_age_y=87,age_y=99),
                  prior_setup_evidence='work/ui/names-0.2.14/summary.png and child-eight-confirm.png; same storage encoding',
                  save_compatibility='Existing legacy names retain their original bytes. Long-name saves require 0.2.15 or newer; earlier test candidates are unsupported.',
                  checks=report['checks'],
                  mips='127 codec cases, adjacent-record canaries, complete comparisons, bounded/counted copies, both literal and substitution formatters, original byte conversion, invalid-input recovery, stack and callee-save registers',
                  limitations='Physical PSP and full-playthrough name contexts remain unverified. The PSP system keyboard retains its system font.')
    changes={ui/'verification.json':evidence}
    p=ROOT/'work/translation/en/name_entry/prompts.json';batch=json.loads(p.read_text(encoding='utf-8'))
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()[0x3b9800:0x3b9800+17856]
    original_rows={(s,i):t for s,i,_,t in parse_mlt(original)}
    for row in batch['rows']:
        row['context']='Native name entry: up to eight printable English characters or three Japanese characters. Auto retains the original Japanese pools; legacy save records remain eight bytes.'
        key=(row['section'],row['index'])
        if key in PROMPTS:
            row['translation_en']=PROMPTS[key]
            row['fit_status']='verified_selected_context_'+VERSION if key==(0,9) else 'pending_runtime_error_dialog'
            note='User requested eight English characters; Japanese capacity remains three. Native compact storage and decoder required.'
            if note not in row.setdefault('review_notes',[]):row['review_notes'].append(note)
        if row['index'] in (5,10):
            row['fit_status']='verified_selected_context_'+VERSION
            row['fit_evidence']='work/ui/names-'+VERSION+'/verification.json'
        jp=original_rows[key]
        assert jp==row['source_jp'] and hashlib.sha256(jp.encode()).hexdigest()==row['source_sha256']
        assert tokens_equal(jp,row['translation_en']) and jp.count('\n')==row['translation_en'].count('\n')
    batch['version']=VERSION;changes[p]=batch
    qpath=ROOT/'work/ui/verified_screens.json';qa=json.loads(qpath.read_text(encoding='utf-8'))
    qa['latest_evidence_version']=VERSION
    qa['additional_build_evidence']=[x for x in qa.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/names-'+VERSION+'/verification.json',scope='Eight English characters, native fullwidth Latin HD font, two-row portrait labels, actual save/reload')]
    changes[qpath]=qa
    spath=ROOT/'docs/local_build_status.json';status=json.loads(spath.read_text(encoding='utf-8'))
    status.update(latest_local_build=VERSION,archive_translation_version=VERSION,file='work/output/english-native-'+VERSION+'.iso',
                  bytes=(ROOT/('work/output/english-native-'+VERSION+'.iso')).stat().st_size,
                  english_name_entry_evidence='work/ui/names-'+VERSION+'/verification.json')
    status['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/names-'+VERSION+'/title.png')
    status['checks']['native_english_name_entry']='PASS; eight-character family/given/child names, mixed case, original eight-byte records, actual save/reload'
    status['checks']['native_name_font']='PASS; fullwidth Latin normalized before glyph measurement into existing 4x atlas; Japanese fallback retained'
    status['checks']['mips_long_names']=evidence['mips']
    status['checks']['portrait_card_names']='PASS in selected loaded roster; age moved to a separate row inside taller frames'
    changes[spath]=status
    report['runtime_verification']='PASS in selected contexts: work/ui/names-'+VERSION+'/verification.json'
    changes[build/'names.report.json']=report
    print(json.dumps(dict(version=VERSION,prompts={str(k):v for k,v in PROMPTS.items()},captures=len(screenshots),changes=[str(p.relative_to(ROOT)) for p in changes]),indent=2))
    return changes,p

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    changes,batch=prepare()
    if args.write:
        for path,obj in changes.items():path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        batch.with_name(batch.stem+'.en.json').write_text(json.dumps(export(batch),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('QA records written.' if args.write else 'DRY RUN: no files written.')

if __name__=='__main__':main()

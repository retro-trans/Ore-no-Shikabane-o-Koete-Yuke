"""Record checked Latin Auto/title/controller evidence. Dry run unless --write."""
import argparse,hashlib,json,re
from catalog_text import ROOT,parse_mlt
from repack_text import root_entries
from strip_jp import export
V='0.2.16'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    dest=ROOT/('work/output/english-native-'+V);ui=ROOT/('work/ui/latin-auto-'+V)
    report=json.loads((dest/'latin.report.json').read_text(encoding='utf-8'));manifest=json.loads((ROOT/('work/output/english-native-'+V+'.manifest.json')).read_text(encoding='utf-8'))
    assert sha(dest/'EBOOT.latin.elf')==report['elf_sha256'] and sha(dest/'data.latin.ore')==report['archive_sha256']
    assert manifest['files'][0]['sha256']==report['elf_sha256'] and manifest['files'][1]['sha256']==report['archive_sha256']
    data=(dest/'data.latin.ore').read_bytes();entries,_=root_entries(data);n=next(i for i,e in enumerate(entries) if e[0]==27);a=entries[n];rows=list(parse_mlt(data[a[3]:entries[n+1][3]-(a[2]&2047)]))
    gloss=json.loads((ROOT/'work/glossary/latin_auto_names.json').read_text(encoding='utf-8'))
    names=[(s,''.join(chr(ord(c)-0xfee0) for c in t)) for s,i,o,t in rows if s>0];assert len(names)==180 and all(t.isascii() and t.isalpha() and 1<=len(t)<=8 for s,t in names)
    assert names==[(r['section'],r['latin']) for r in gloss['rows']]
    screenshots=[]
    for name in ['title-opening','title-menu','family-auto-final','family-eight-confirm','family-auto-cycled','family-auto-confirm','given-auto','keyboard-auto-name','keyboard-start-finished','reloaded-save','reloaded-roster']:
        p=ui/(name+'.png');meta=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'));assert meta['dimensions']==[480,272] and not meta['texture_replacement']
        screenshots.append(dict(file=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p),dimensions=[480,272]))
    control=ROOT/'work/source/controller-backup-0.2.16';assert (control/'user.ini').exists() and (control/'project.ini').exists()
    for p in [ROOT/'work/source/emulator/profile.ini',__import__('pathlib').Path.home()/'Documents/PPSSPP/PSP/SYSTEM/ppsspp.ini']:
        text=p.read_text(encoding='utf-8-sig')
        for key,value in [('AllowXInput','True'),('AllowDInput','False'),('AllowHIDInput','False')]:assert re.search(r'(?m)^'+key+' = '+value,text)
    save=ROOT/'work/source/emulator/memstick/PSP/SAVEDATA/UCJS10117/SAVEDATA.BIN';assert sha(save)=='e97eaf0a38116b78d58a4f0d114d68912b6335def8a91a638145876c0b9056b0'
    evidence=dict(version=V,scope='Selected actual title, Auto-name, keyboard and existing-save contexts',texture_replacement=False,font_raster_scale=4,
                  screenshots=screenshots,footer=report['footer'],title_help_box=dict(x=12,width=300),footer_global_draw_key='0x8003',
                  latin_auto=dict(surnames=22,female=85,male=73,provisional_kanji_readings=62,maximum_letters=8,original_source_candidates=1735,curated_subset=True),
                  runtime_names=['Keage','Kitasaga','Oharano','Hachijo','Aran'],native_mips='PASS: all 180 Auto names encode/decode/compare against native fullwidth candidates, eight-byte-record canaries, stack and saved registers; footer registration and matching teardown',
                  controller=dict(observed_xinput_start='0x10',observed_legacy_joystick='0x80 (button 8)',default_conflict='DirectInput button 8 maps to R; OSK handles R before Start',input_backends=dict(XInput=True,DirectInput=False,HID=False),backup='work/source/controller-backup-0.2.16',physical_after_fix_verified=False,native_start_finishes_keyboard=True,hardware_log_sha256=sha(ROOT/'work/source/controller-input.jsonl')),
                  existing_save=dict(loaded=True,eight_character_names=['WWWWWWWW','aaaaAAAA','bbbbBBBB'],sha256=sha(save),overwritten=False),
                  capture_note='Title, save and earlier selected captures use the identical executable, native title asset and visible labels. The final Auto table retains internal fullwidth Latin for duplicate comparisons; the final Auto capture and all 180 codec/comparison cases are checked separately.',
                  limitations=['Physical controller confirmation after configuration change','Real PSP boot/performance','Full playthrough and broad UI QA','Independent review of provisional readings'])
    changes={ui/'verification.json':evidence}
    report['runtime_verification']='PASS in selected contexts; work/ui/latin-auto-'+V+'/verification.json';report['native_auto_storage']='Fullwidth Latin as in original saved/decoded name conventions; native VWF normalizes glyphs';changes[dest/'latin.report.json']=report
    p=ROOT/'docs/local_build_status.json';status=json.loads(p.read_text(encoding='utf-8'));status.update(latest_local_build=V,archive_translation_version=V,file='work/output/english-native-'+V+'.iso',bytes=manifest['bytes'],retained_japanese_player_name_pool_records=0,original_source_player_name_pool_records=1735,latin_auto_name_pool_records=180,provisional_auto_name_readings=62,latin_auto_evidence='work/ui/latin-auto-'+V+'/verification.json',draft_coverage_scope='Indexed EZBIND draft; standalone name-entry UI and curated Latin Auto choices are tracked separately.')
    status['title_branding'].update(version='v'+V,group='github.com/retro-trans',footer_screen_rectangle=[342,222,475,254],extra_uncompressed_bytes=55808,title_only_instruction_changes=3,visual_evidence='work/ui/latin-auto-'+V+'/title-menu.png')
    status['checks'].update(title_footer='PASS: full enlarged version/URL on opening and menu; help box clear; native global draw key 0x8003',title_footer_teardown='PASS: removed on leaving title before existing-save load',standalone_name_entry='14 unchanged UI prompts; 180 curated Latin Auto candidates, all at most eight letters',latin_auto_mips='PASS: all 180 shipped candidates through actual native encoder/copy/comparison, record canaries and saved registers',controller_start='Input conflict removed in both local INIs; physical retest pending. Native PSP Start finishes keyboard.')
    changes[p]=status
    p=ROOT/'work/ui/verified_screens.json';qa=json.loads(p.read_text(encoding='utf-8'));qa['latest_evidence_version']=V;qa['additional_build_evidence']=[x for x in qa.get('additional_build_evidence',[]) if x['version']!=V]+[dict(version=V,evidence='work/ui/latin-auto-'+V+'/verification.json',scope='Enlarged full footer, Latin Auto names, original long-name save loading, native Start and emulator input correction')];changes[p]=qa
    p=ROOT/'work/translation/en/name_entry/prompts.json';batch=json.loads(p.read_text(encoding='utf-8'));batch['version']=V
    for row in batch['rows']:row['context']='Native name entry: eight English or three Japanese characters. Auto uses curated Latin pools; original save records remain eight bytes.'
    english=export(p);english['version']=V
    for row,source in zip(english['rows'],batch['rows']):row['context']=source['context']
    changes[p]=batch;changes[p.with_name(p.stem+'.en.json')]=english
    print(json.dumps(dict(version=V,iso_bytes=manifest['bytes'],screenshots=len(screenshots),auto_names=len(names),controller_physical_retest='pending',changes=[str(p.relative_to(ROOT)) for p in changes]),indent=2))
    return changes
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();changes=prepare()
    if a.write:
        for p,obj in changes.items():p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Evidence recorded.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

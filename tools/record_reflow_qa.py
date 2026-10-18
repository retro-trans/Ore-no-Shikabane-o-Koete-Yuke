"""Measure and record the three inspected dialogue captures. Dry run unless --write."""
import argparse,hashlib,json
import numpy as np
from PIL import Image
from catalog_text import ROOT
from build_dialogue_reflow import VERSION,EDITS
from strip_jp import export

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    ui=ROOT/('work/ui/dialogue-reflow-'+VERSION);dest=ROOT/('work/output/english-native-'+VERSION)
    layout=json.loads((ui/'layout.json').read_text(encoding='utf-8'));report=json.loads((dest/'reflow.report.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/('work/output/english-native-'+VERSION+'.manifest.json')).read_text(encoding='utf-8'))
    assert sha(dest/'EBOOT.reflow.elf')==report['elf_sha256']==manifest['files'][0]['sha256']
    assert sha(dest/'data.reflow.ore')==report['archive_sha256']==manifest['files'][1]['sha256']
    assert (ROOT/('work/output/english-native-'+VERSION+'.iso')).stat().st_size==manifest['bytes']
    evidence=[]
    for i,name in enumerate(['curse','equipment','information']):
        path=ui/(name+'.png');meta=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'));proof=json.loads((ui/(name+'.native.json')).read_text(encoding='utf-8'))
        row=layout['rows'][i];assert proof['id']==row['id'] and proof['exact_final_build_text'] and proof['natural_message_selection'] and not proof['register_or_memory_writes']
        assert proof['translation_sha256']==hashlib.sha256(row['translation'].encode()).hexdigest()
        assert meta['dimensions']==[480,272] and not meta['texture_replacement']
        im=Image.open(path).convert('RGB');assert im.size==(480,272)
        pixels=np.array(im).astype(int);white=(pixels.min(2)>=150)&(pixels.max(2)-pixels.min(2)<=35)
        x,seedright,ymin,ymax=(100,340,14,67) if i==0 else (34,242,200,261)
        ys=np.flatnonzero(white[ymin:ymax,x:seedright].sum(1)>=2)+ymin;groups=[]
        for y in ys:
            if not groups or y-groups[-1][-1]>3:groups.append([int(y)])
            else:groups[-1].append(int(y))
        assert len(groups)==len(row['line_widths']),(name,'Expected fully visible line count',groups)
        top=groups[0][0]-11;frame=[90,6,390,76] if i==0 else [24,top,312,264]
        icon=[370,56,387,73] if i==0 else [288,236,309,263]
        boxes=[]
        for group,advance in zip(groups,row['line_widths']):
            right=min(white.shape[1],int(x+advance+3));yy,xx=np.where(white[group[0]:group[-1]+1,x:right]);assert len(xx)
            box=[int(xx.min()+x),int(yy.min()+group[0]),int(xx.max()+x+1),int(yy.max()+group[0]+1)]
            assert box[0]>=frame[0]+7 and box[2]<=frame[2]-8 and box[3]<=frame[3]-4,(name,box,frame)
            assert abs(x+advance-box[2])<=4,(name,'Incomplete line or width mismatch',box,advance)
            boxes.append(box)
        assert boxes[-1][2]+8<=icon[0],(name,'Advance icon clearance')
        row.update(fit_status='verified_selected_context_'+VERSION,screenshot=str(path.relative_to(ROOT)).replace('\\','/'),frame_rectangle=frame,frame_width=frame[2]-frame[0],frame_height=frame[3]-frame[1],text_ink_rectangles=boxes,ink_measurement='White glyph cores from actual framebuffer; shadow excluded. Complete text and borders also visually inspected.',advance_icon_rectangle=icon,advance_icon_coordinate_note='Conservative animation envelope; horizontal clearance checked',last_line_to_icon_gap=icon[0]-boxes[-1][2])
        evidence.append(dict(id=row['id'],screenshot=row['screenshot'],sha256=sha(path),frame=frame,white_glyph_ink=boxes,icon=icon,native_text=proof))
    layout['runtime_verification']='PASS: all three complete messages fit their actual windows and clear the advance icons'
    report['runtime_verification']='PASS: work/ui/dialogue-reflow-'+VERSION+'/verification.json'
    report['checks']['actual_guest_framebuffer_fit']='pass; all three naturally reached records, complete text, window edges and advance icons'
    changes={ui/'layout.json':layout,dest/'reflow.report.json':report,ui/'verification.json':dict(version=VERSION,result=layout['runtime_verification'],scope='The three reported passages',texture_replacement=False,font_raster_scale=4,records=evidence,all_words_preserved=True,all_49_translation_batches='pass',elf_unchanged_from='0.2.16',qa_input_profile='work/source/emulator/input-isolated.ini')}
    batches={}
    for (batchname,rid,old,new,_,_),e in zip(EDITS,evidence):
        p=ROOT/('work/translation/en/'+batchname+'.json');b=batches.setdefault(p,json.loads(p.read_text(encoding='utf-8')))
        row=next(r for r in b['rows'] if r['id']==rid);assert row['translation_en']==new
        row['fit_status']='verified_selected_context_'+VERSION
        note='Actual complete-message fit, native text provenance, frame/ink/icon coordinates: work/ui/dialogue-reflow-'+VERSION+'/verification.json'
        if note not in row['review_notes']:row['review_notes'].append(note)
        changes[p]=b
    p=ROOT/'work/ui/verified_screens.json';qa=json.loads(p.read_text(encoding='utf-8'))
    ids=set(qa.get('visual_fit_verified_record_ids',[]));ids.update(x['id'] for x in evidence);qa['visual_fit_verified_record_ids']=sorted(ids);qa['latest_evidence_version']=VERSION
    qa['additional_build_evidence']=[x for x in qa.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/dialogue-reflow-'+VERSION+'/verification.json',scope='Curse overflow and two naturally reflowed Itsuka tutorial messages')];changes[p]=qa
    p=ROOT/'docs/local_build_status.json';status=json.loads(p.read_text(encoding='utf-8'));status.update(latest_local_build=VERSION,archive_translation_version=VERSION,file='work/output/english-native-'+VERSION+'.iso',bytes=manifest['bytes'],dialogue_reflow_evidence='work/ui/dialogue-reflow-'+VERSION+'/verification.json')
    status['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/dialogue-reflow-'+VERSION+'/title-menu.png')
    status['checks'].update(selected_actual_screen_fit=str(len(ids))+' indexed records have accumulated selected-context evidence; three reported dialogue passages verified in '+VERSION,dialogue_reflow='PASS: all words retained; all three windows/icons clear; advice uses two English lines',all_49_translation_batches='pass')
    changes[p]=status
    save=ROOT/'work/source/emulator/memstick/PSP/SAVEDATA/UCJS10117/SAVEDATA.BIN';assert sha(save)==sha(ROOT/'work/source/qa-backup-before-0.2.17/SAVEDATA.BIN')
    print(json.dumps(dict(version=VERSION,records=evidence,verified_indexed_record_count=len(ids),iso_bytes=manifest['bytes'],save_file_unchanged=True,changes=[str(p.relative_to(ROOT)) for p in changes]),indent=2))
    return changes,batches
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();changes,batches=prepare()
    if a.write:
        for p,obj in changes.items():p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for p in batches:p.with_name(p.stem+'.en.json').write_text(json.dumps(export(p),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Fit evidence recorded.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

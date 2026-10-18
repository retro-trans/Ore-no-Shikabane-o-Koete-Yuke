"""Reflow the three reported English dialogue records. Dry run unless --write."""
import argparse,hashlib,json
from catalog_text import ROOT,parse_mlt
from check_translation import tokens_equal
from build_menu_fixes import container,member,pack
from build_latin_auto import footer
from repack_text import root_entries,rebuild_ez,rebuild_mlt,rebuild_root
from strip_jp import export

VERSION='0.2.17'
EDITS=[('ui_batch_002','ore:001e8000:0000:03:0002',
        'The first is the Curse of Short Life.\nYou will grow many times faster than ordinary people\nand die within a few years.',
        'The first is the Curse of Short Life.\nYou will grow many times faster than\nordinary people and die within a few years.',278,256),
       ('initial_batch','ore:0000c000:0015:04:0006',
        "...But first, equip your swords and armor,\nget all your items ready,\nand make sure you haven't forgotten anything!",
        "...But first, equip your swords and armor,\nget all your items ready, and make sure\nyou haven't forgotten anything!",268,254),
       ('initial_batch','ore:0000c000:0015:04:0007',
        'And please look over\nall the information, too.\nA quick skim will do!',
        'And please look over all the information, too.\nA quick skim will do!',268,254)]

def digest(b):return hashlib.sha256(b).hexdigest()
def build():
    source=ROOT/'work/output/english-native-0.2.16'
    elf=(source/'EBOOT.latin.elf').read_bytes();data=(source/'data.latin.ore').read_bytes()
    assert digest(elf)=='498dcae55831b40a4f3126d35c3b54ca926b3a3e65183bbefeef5c06beb46a3c'
    assert digest(data)=='23d0e03fa8a28f1909f6033f2eab735d1f91d969020aa89e21a3c4fe61a025ec'
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_=root_entries(original);be,bend=root_entries(data);rootmap={o:next(x[3] for x in be if x[0]==i) for i,_,_,o in oe}
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    batches={};updates={};fit=[];exceptions=[]
    for batchname,rid,old,new,limit,lastlimit in EDITS:
        assert old.replace('\n',' ')==new.replace('\n',' '),'Reflow must preserve every word'
        p=ROOT/('work/translation/en/'+batchname+'.json')
        batch=batches.setdefault(p,json.loads(p.read_text(encoding='utf-8')))
        row=next(r for r in batch['rows'] if r['id']==rid);assert row['translation_en'] in (old,new)
        assert tokens_equal(row['source_jp'],new) and digest(row['source_jp'].encode())==row['source_sha256']
        widths=[sum(metrics[str(ord(c))]['advance'] for c in line)*12/14 for line in new.split('\n')]
        assert all(w<=limit for w in widths[:-1]) and widths[-1]<=lastlimit and len(widths)<=3
        oldwidths=[sum(metrics[str(ord(c))]['advance'] for c in line)*12/14 for line in old.split('\n')]
        fit.append(dict(id=rid,translation=new,old_line_widths=[round(w,3) for w in oldwidths],line_widths=[round(w,3) for w in widths],font_logical_size=12,atlas_metrics_size=14,nonfinal_advance_budget=limit,final_advance_budget=lastlimit,last_line_icon_reserve=14,context='Setup curse introduction' if batchname.startswith('ui') else 'Itsuka sortie tutorial',context_review='Original row and both neighboring records examined; meaning and all words unchanged'))
        if row['source_jp'].count('\n')!=new.count('\n'):
            exceptions.append(dict(id=rid,source_sha256=row['source_sha256'],translation_sha256=digest(new.encode()),source_lines=row['source_jp'].count('\n')+1,target_lines=new.count('\n')+1,reason='User-requested English dialogue reflow'))
        row['translation_en']=new;row['fit_status']='pending_runtime_'+VERSION
        note='User requested natural English line breaks; all words and engine controls retained. Measured with the native VWF; last line reserves space for the advance icon.'
        if note not in row.setdefault('review_notes',[]):row['review_notes'].append(note)
        batch['version']=VERSION
        base=rootmap[row['archive_offset']];entry=row['member_entry'];updates.setdefault(base,{}).setdefault(entry,{})[(row['section'],row['index'])]=(old,new)
    changed={};member_changes={}
    for base,members in updates.items():
        arc,entries=container(data,base);patches={}
        for entry,rows in members.items():
            oldmlt=member(arc,entries,entry);lookup={(s,i):t for s,i,_,t in parse_mlt(oldmlt)}
            assert all(lookup[k]==a for k,(a,b) in rows.items())
            newmlt=rebuild_mlt(oldmlt,{k:b for k,(a,b) in rows.items()})
            actual={(s,i):t for s,i,_,t in parse_mlt(newmlt)}
            assert all(actual[k]==(rows[k][1] if k in rows else t) for k,t in lookup.items())
            patches[entry]=pack(newmlt)
        member_changes[base]=set(patches);changed[base]=rebuild_ez(arc,patches)
    tb=rootmap[0x1e8000];ta,te=container(changed[tb],0);ot,ote=container(original,0x1e8000)
    ppt,preview,footer_report=footer(member(ot,ote,25),VERSION)
    changed[tb]=rebuild_ez(ta,{25:pack(ppt)});member_changes[tb].add(25)
    output=rebuild_root(data,changed);ae,aend=root_entries(output)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa=(be[n+1][3] if n+1<len(be) else bend)-(a[2]&2047);sb=(ae[n+1][3] if n+1<len(ae) else aend)-(b[2]&2047)
        aa=data[a[3]:sa];bb=output[b[3]:sb]
        if a[3] not in changed:assert aa==bb
        else:
            _,ar=container(aa,0);_,br=container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in member_changes[a[3]]:assert aa[p:p+z]==bb[pp:pp+zz]
    report=dict(version=VERSION,source_version='0.2.16',texture_replacement=False,font_raster_scale=4,elf_unchanged=True,elf_sha256=digest(elf),archive_sha256=digest(output),archive_bytes=len(output),changed_dialogue_records=3,checks=dict(all_words='unchanged',engine_tokens='unchanged',row_ids_and_section_counts='unchanged',other_text_rows='unchanged',unrelated_members_and_root_payloads='byte-identical',compression_and_mlt_roundtrips='pass'),footer=footer_report,runtime_verification='pending')
    layout=dict(version=VERSION,requested_scope='Three screenshot-reported passages; English line positions may differ from Japanese',font_raster_scale=4,texture_replacement=False,rows=fit,line_break_exceptions=exceptions,runtime_verification='pending')
    return elf,output,preview,report,layout,batches

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    elf,data,preview,report,layout,batches=build()
    print(json.dumps(dict(report=report,layout=layout),indent=2))
    if a.write:
        dest=ROOT/('work/output/english-native-'+VERSION);dest.mkdir(parents=True,exist_ok=True);assert not (dest/'data.reflow.ore').exists()
        (dest/'EBOOT.reflow.elf').write_bytes(elf);(dest/'data.reflow.ore').write_bytes(data);(dest/'reflow.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/dialogue-reflow-'+VERSION);ui.mkdir(parents=True,exist_ok=True);preview.save(ui/'native-footer.png');(ui/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
        for p,batch in batches.items():
            batchtext=json.dumps(batch,ensure_ascii=False,indent=2)+'\n';p.write_text(batchtext,encoding='utf-8')
            p.with_name(p.stem+'.en.json').write_text(json.dumps(export(p),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for stem in ('initial_draft_input','ui_batch_002_input'):
            p=ROOT/('work/translation/en/'+stem+'.json');text=p.read_text(encoding='utf-8')
            for _,_,old,new,_,_ in EDITS:text=text.replace(json.dumps(old)[1:-1],json.dumps(new)[1:-1])
            json.loads(text);p.write_text(text,encoding='utf-8')
    print('Build and translation records written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

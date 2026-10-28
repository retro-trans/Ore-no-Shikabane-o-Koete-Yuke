"""Record verified local broker fixes and build status. Dry run before --write."""
import argparse,json,hashlib
from PIL import Image
from catalog_text import ROOT
from build_market_ui import V
from strip_jp import export


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def dump(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    ui=ROOT/('work/ui/market-ui-'+V);out=ROOT/('work/output/english-native-'+V)
    report=read(out/'market.report.json');runtime=read(ui/'runtime.json');static=read(ui/'static-tests.json')
    ribbon=read(ui/'runtime-ribbon.json');saves=read(ui/'save-preservation.json')
    assert runtime['result']==static['result']==ribbon['result']==saves['result']=='PASS'
    assert saves['original_project_hashes']==saves['restored_project_hashes'] and saves['user_source_unchanged']
    assert not saves['user_source_written'] and not runtime['purchase_confirmed']
    assert report['elf_sha256']==runtime['elf_sha256']==ribbon['elf_sha256']==static['executable_sha256']==sha(out/'EBOOT.market.elf')
    assert report['archive_sha256']==runtime['archive_sha256']==ribbon['archive_sha256']==sha(out/'data.market.ore')
    previews=[read(ui/name) for name in ['preview-market-entry.json','preview-graph-entry.json']]
    assert all(p['result']=='OVERRIDE APPLIED' and not p['delivered_image_modified'] and not p['game_memory_writes'] for p in previews)
    screenshots=[]
    for name in ['title','market','quantity-one','quantity-two','confirmation','retry','graph']:
        p=ui/(name+'.png');assert Image.open(p).size==(480,272)
        assert not read(p.with_suffix('.json'))['texture_replacement']
        screenshots.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    iso=ROOT/('work/output/english-native-'+V+'.iso')
    identity=dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
    result='PASS: commodity ribbon, Money/ryo, aligned Now/High/Low, quantity/confirmation/retry and graph labels checked in native UI'
    proof=dict(version=V,date='2026-10-27',result=result,iso=identity,runtime=runtime,
        static_tests=static,ribbon=ribbon,screenshots=screenshots,checks=report['checks'],
        fixture=dict(purpose='Public-works level getter previewed as 1 to expose locked broker',
            reports=['preview-market-entry.json','preview-graph-entry.json'],register_override=True,
            gameplay_unlock_verified=False,save_state_loaded=False,delivered_image_modified=False,
            money_price_investment_data_changed=False),save_preservation=saves,
        cold_boot=True,texture_replacement=False,purchase_confirmed=False,github_release=False,
        limits=['Visual checks use Rice, quantities 1/2, unchanged native prices 100/200 and fee total 220.',
            'Other commodities, extreme values and physical PSP retesting remain pending.',
            'The physical PSP screenshots were reported as public 0.2.48. Final 0.2.49 checked in isolated PPSSPP.',
            'The old native caption literal already contained Funds; 0.2.49 explicitly relocates its caption to Money.',
            'Untranslated decorative background shop sign is retained.'])
    print(json.dumps(dict(write=args.write,result=result,iso=identity,saves_restored=True),indent=2))
    if not args.write:return
    dump(ui/'verification.json',proof);dump(ui/'image-identity.json',identity)
    dump(ui/'layout.json',dict(version=V,graphics=report['graphics'],literals=report['literals'],
        patches=report['patches'],unit_wrapper=report['unit_wrapper'],fit=report['fit']))
    report['runtime_verification']=result;dump(out/'market.report.json',report)
    path=ROOT/'work/translation/en/executable/market_prompts.json';batch=read(path)
    for row in batch['rows']:row['fit_status']='verified_selected_context_'+V
    dump(path,batch);path.with_suffix('.en.json').write_text(json.dumps(export(path),ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    for rel in ['docs/local_build_status.json','docs/translation_progress.json']:
        path=ROOT/rel;obj=read(path);obj['market_ui_evidence']=(ui/'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],
                sha256=identity['sha256'],native_graphic_labels=72,additional_market_native_literals=6,
                release='Local test build 0.2.49; latest public release remains 0.2.48.')
            obj['checks']['commodity_broker_ui']=result
            obj['title_branding'].update(version='v'+V,visual_evidence=(ui/'title.png').relative_to(ROOT).as_posix())
        else:
            obj.update(version=V,date='2026-10-27')
            obj['additional_draft_records_by_domain'].update(native_market=6,graphics=72)
        dump(path,obj)
    path=ROOT/'work/ui/verified_screens.json';obj=read(path);obj['latest_layout_candidate_version']=V
    obj['additional_build_evidence']=[r for r in obj.get('additional_build_evidence',[]) if r['version']!=V]+[
        dict(version=V,evidence=(ui/'verification.json').relative_to(ROOT).as_posix(),scope=result)]
    dump(path,obj)
    path=ROOT/'docs/LOCAL_DEVELOPMENT.md';text=path.read_text(encoding='utf-8')
    text=text.replace('**0.2.48**, 2026-10-18; archive-text draft: **0.2.48**.','**0.2.49**, 2026-10-27; archive-text draft: **0.2.49**.')
    text=text.replace('one investment currency literal, and 71 native graphic assets/label groups',
        'one investment currency literal, six market literals, and 72 native graphic assets/label groups')
    line='- `work/output/english-native-0.2.49.iso`: translated native commodity-broker prompts/ribbon, Money/ryo, aligned price headings and graph units. See [QA evidence and fixture limits](../work/ui/market-ui-0.2.49/verification.json).\n'
    if line not in text:text=text.replace('- `work/output/english-native-0.2.48.iso`',line+'- `work/output/english-native-0.2.48.iso`',1)
    path.write_text(text,encoding='utf-8')


if __name__=='__main__':main()

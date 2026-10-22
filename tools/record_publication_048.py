"""Record verified 0.2.48 publication. Run without --write first."""
import argparse,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V='0.2.48'
REPO='retro-trans/Ore-no-Shikabane-o-Koete-Yuke'


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def dump(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],text=True,encoding='utf-8'))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id',required=True,type=int)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    folder=ROOT/('work/source/publication-'+V)
    upload=read(folder/'upload-verification.json')
    catalog=read(folder/'catalog-verification.json')
    package=read(ROOT/('work/source/packaging-'+V+'.json'))
    manifest=read(ROOT/('docs/releases/'+V+'/BUILD-MANIFEST.json'))
    assert upload['result']==catalog['result']=='PASS'
    assert not upload['draft'] and upload['author']=='binhlt0402'
    assert catalog['source_recognized'] and catalog['previous_release_recognized'] and len(catalog['plans'])==6
    assert package['roundtrip_verified'] and not package['game_images_uploaded']
    assert package['source_commit']==upload['source_commit']==manifest['source_commit']
    assert len(upload['assets'])==len(manifest['patches'])+3==5
    run=gh('repos/retro-trans/retro-trans-tools/actions/runs/'+str(args.run_id))
    assert run['conclusion']=='success' and run['name']=='Refresh patch catalog'
    release=gh('repos/'+REPO+'/releases/latest')
    assert release['tag_name']=='v'+V and not release['draft'] and not release['prerelease']
    assert release['author']['login']=='binhlt0402' and release['id']==upload['release_id']
    proof=dict(version=V,date='2026-10-22',repository='https://github.com/'+REPO,
        release_url=release['html_url'],release_id=release['id'],author='binhlt0402',
        published_at=release['published_at'],result='PASS',source_commit=manifest['source_commit'],
        packager=dict(repository=package['builder_repository'],commit=package['builder_commit'],
            source_window_bytes=package['source_window_bytes'],roundtrip_verified=True),
        assets=upload['assets'],uploaded_asset_verification=upload['verification'],
        catalog=dict(workflow_url=run['html_url'],workflow_conclusion=run['conclusion'],
            commit=catalog['catalog_commit'],source_recognized=True,previous_release_recognized=True,
            plans=catalog['plans'],gui_launched=False),
        complete_game_images_uploaded=False,source_dialogue_committed=False)
    print(json.dumps(dict(write=args.write,url=proof['release_url'],assets=5,
        catalog=run['conclusion'],published_at=proof['published_at']),indent=2))
    if not args.write:return
    dump(ROOT/('docs/releases/'+V+'/PUBLICATION.json'),proof)
    p=ROOT/'docs/local_build_status.json';value=read(p)
    value.update(public_repository=proof['repository'],latest_public_release=dict(version=V,
        url=proof['release_url'],evidence='docs/releases/'+V+'/PUBLICATION.json'),retro_trans_catalog_verified=True)
    dump(p,value)
    p=ROOT/'docs/translation_progress.json';value=read(p)
    value['public_release']=dict(version=V,url=proof['release_url'],evidence='docs/releases/'+V+'/PUBLICATION.json')
    dump(p,value)
    p=ROOT/'CHANGELOG.md';value=p.read_text(encoding='utf-8')
    line='- Published on 2026-10-22 with compact full and 0.2.38 upgrade patches. Both decode to the exact tested ISO; all five uploaded asset sizes and SHA-256 digests verified. Retro Trans catalog refresh and all six original/0.2.38 selection routes verified. See `docs/releases/0.2.48/PUBLICATION.json`.\n'
    if line not in value:value=value.replace('## 0.2.48 (2026-10-18)\n\n','## 0.2.48 (2026-10-18)\n\n'+line)
    value=value.replace('Local build only; no GitHub release. Other draws,','Build verification completed locally before publication. Other draws,',1)
    p.write_text(value,encoding='utf-8')


if __name__=='__main__':main()

"""Verify full and previous-release routes in the live Retro Trans catalog."""
import argparse,json,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO='retro-trans/Ore-no-Shikabane-o-Koete-Yuke'
V='0.2.48'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true')
    ap.add_argument('--version',choices=['0.2.48','0.2.52'],default=V)
    args=ap.parse_args()
    version=args.version
    previous_version='0.2.38' if version=='0.2.48' else '0.2.48'
    if not args.execute:
        print('DRY RUN: read live catalog, recognize original/'+previous_version+' ISOs, verify Latest/specific/next routes. No game image writes.')
        return
    commit=subprocess.check_output(['gh','api','repos/retro-trans/retro-trans-tools/commits/main','--jq','.sha'],text=True,encoding='utf-8').strip()
    url='https://raw.githubusercontent.com/retro-trans/retro-trans-tools/'+commit+'/retro_trans/resources/catalog.json'
    with urllib.request.urlopen(url,timeout=30) as response:data=json.load(response)
    row=next(r for r in data['releases'] if r['repo']==REPO and r['tag']=='v'+version)
    manifest=json.loads((ROOT/('work/output/release-'+version+'/BUILD-MANIFEST.json')).read_text())
    assert row['manifest']==manifest
    sys.path.insert(0,str(ROOT/'work/source/retro-trans-tools'))
    from retro_trans.catalog import Catalog,recognize
    catalog=Catalog(data);plans=[]
    for source_version,path in [('original',ROOT/'Ore no Shikabane o Koete Yuke (Japan).iso'),
                         (previous_version,ROOT/('work/output/english-native-'+previous_version+'.iso'))]:
        node=next(n for n in recognize(path,catalog) if n.id[0]==manifest['game_id'] and n.version==source_version)
        for target in ['Latest',version,'Next version only']:
            plan=catalog.plan(node,target)
            expected='0.2.38' if source_version=='original' and target=='Next version only' else version
            assert plan.target.version==expected and len(plan.edges)==1
            edge=plan.edges[0]
            if expected==version:
                patch=next(p for p in manifest['patches'] if p['source_version']==source_version)
                assert edge.asset.sha256==patch['patch_sha256'] and plan.target.hashes['sha256']==patch['target_sha256']
            else:
                previous=json.loads((ROOT/'docs/releases/0.2.38/BUILD-MANIFEST.json').read_text())['patches'][0]
                assert edge.asset.sha256==previous['patch_sha256']
            plans.append(dict(source=source_version,selection=target,target=expected,patches=1,patch_url=edge.asset.url))
    proof=dict(version=version,result='PASS',repository=REPO,catalog_commit=commit,catalog_url=url,
        source_recognized=True,previous_release_recognized=True,plans=plans,game_image_writes=False,gui_launched=False)
    print(json.dumps(proof,indent=2))
    if args.write:
        out=ROOT/('work/source/publication-'+version);out.mkdir(exist_ok=True)
        (out/'catalog-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()

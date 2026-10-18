"""Check the live Retro Trans catalog, source recognition and automatic route."""
import argparse,json,subprocess,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO='retro-trans/Ore-no-Shikabane-o-Koete-Yuke';VERSION='0.2.38'
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
 if not a.execute:print('DRY RUN: read public catalog, recognize the original ISO, and check Latest/0.2.38 routes; no image writes.');return
 commit=subprocess.check_output(['gh','api','repos/retro-trans/retro-trans-tools/commits/main','--jq','.sha'],text=True,encoding='utf-8').strip();assert len(commit)==40
 url='https://raw.githubusercontent.com/retro-trans/retro-trans-tools/'+commit+'/retro_trans/resources/catalog.json'
 with urllib.request.urlopen(url,timeout=30) as response:data=json.load(response)
 row=next(x for x in data['releases'] if x['repo']==REPO and x['tag']=='v'+VERSION);manifest=json.loads((ROOT/('work/output/release-'+VERSION+'/BUILD-MANIFEST.json')).read_text());assert row['manifest']==manifest
 sys.path.insert(0,str(ROOT/'work/source/retro-trans-tools'))
 from retro_trans.catalog import Catalog,recognize
 catalog=Catalog(data);original=ROOT/'Ore no Shikabane o Koete Yuke (Japan).iso';nodes=recognize(original,catalog);node=next(n for n in nodes if n.id[0]==manifest['game_id']);assert node.version=='original'
 plans=[]
 for target in ('Latest',VERSION,'Next version only'):
  plan=catalog.plan(node,target);assert plan.target.version==VERSION and len(plan.edges)==1 and plan.target.hashes['sha256']==manifest['patches'][0]['target_sha256'];edge=plan.edges[0];assert edge.asset.sha256==manifest['patches'][0]['patch_sha256'];plans.append(dict(selection=target,source=node.version,target=plan.target.version,patches=len(plan.edges),patch_url=edge.asset.url))
 proof=dict(version=VERSION,result='PASS',repository=REPO,catalog_commit=commit,catalog_url=url,source_recognized=True,edition=node.edition,language=node.language,plans=plans,game_image_writes=False,gui_launched=False)
 print(json.dumps(proof,indent=2))
 if a.write:
  dest=ROOT/('work/source/publication-'+VERSION);dest.mkdir(exist_ok=True);(dest/'catalog-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

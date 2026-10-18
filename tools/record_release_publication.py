"""Record the published release and verified automatic catalog entry. Dry run first."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];V='0.2.38';REPO='retro-trans/Ore-no-Shikabane-o-Koete-Yuke';RUN=39100719059
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--run-id',type=int,default=RUN);a=ap.parse_args();folder=ROOT/('work/source/publication-'+V);upload=json.loads((folder/'upload-verification.json').read_text());catalog=json.loads((folder/'catalog-verification.json').read_text());assert upload['result']==catalog['result']=='PASS' and not upload['draft'] and catalog['source_recognized']
 run=json.loads(subprocess.check_output(['gh','api','repos/retro-trans/retro-trans-tools/actions/runs/'+str(a.run_id)],text=True,encoding='utf-8'));assert run['conclusion']=='success'
 release=json.loads(subprocess.check_output(['gh','api','repos/'+REPO+'/releases/latest'],text=True,encoding='utf-8'));assert release['tag_name']=='v'+V and not release['draft'] and release['author']['login']=='binhlt0402'
 proof=dict(version=V,date='2026-10-18',repository='https://github.com/'+REPO,release_url=release['html_url'],release_id=release['id'],author='binhlt0402',published_at=release['published_at'],result='PASS',source_commit=upload['source_commit'],packager=dict(repository='https://github.com/retro-trans/retro-trans-tools',commit='d0269d3bbb167b14ac53fbd86a59ea10783a95dc',roundtrip_verified=True),assets=upload['assets'],uploaded_asset_verification=upload['verification'],catalog=dict(workflow_url=run['html_url'],workflow_conclusion=run['conclusion'],commit=catalog['catalog_commit'],source_recognized=True,plans=catalog['plans'],gui_launched=False),complete_game_images_uploaded=False,source_dialogue_committed=False,reference='https://github.com/retro-trans/Macross-Triangle-Frontier')
 if (ROOT/('docs/releases/'+V+'/REPACKAGING.json')).exists():proof['repackaging']='docs/releases/'+V+'/REPACKAGING.json'
 print(json.dumps(dict(write=a.write,release=proof['release_url'],published=proof['published_at'],assets=len(proof['assets']),catalog=proof['catalog']['workflow_conclusion'],source_recognized=True),indent=2))
 if not a.write:return
 dump(ROOT/('docs/releases/'+V+'/PUBLICATION.json'),proof)
 p=ROOT/'docs/local_build_status.json';d=json.loads(p.read_text());d.update(public_repository=proof['repository'],latest_public_release=dict(version=V,url=proof['release_url'],evidence='docs/releases/'+V+'/PUBLICATION.json'),retro_trans_catalog_verified=True);dump(p,d)
 p=ROOT/'docs/translation_progress.json';d=json.loads(p.read_text());d['public_release']=dict(version=V,url=proof['release_url'],evidence='docs/releases/'+V+'/PUBLICATION.json');dump(p,d)
 p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8').replace('Prepared the first public repository/release using Macross Triangle Frontier\'s repository and release conventions:','Published the first public repository/release using Macross Triangle Frontier\'s repository and release conventions:');line='- Verified all four uploaded asset sizes/SHA-256 hashes against the local round-trip-verified bundle. Retro Trans catalog refresh succeeded, and its source recognition plus Latest/specific/next-version routes resolve the original ISO to 0.2.38. See `docs/releases/0.2.38/PUBLICATION.json`.\n'
 if line not in s:s=s.replace('## 0.2.38 (2026-10-18)\n\n','## 0.2.38 (2026-10-18)\n\n'+line)
 p.write_text(s,encoding='utf-8')
if __name__=='__main__':main()

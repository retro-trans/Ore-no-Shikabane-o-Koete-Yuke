"""Compare GitHub's uploaded asset hashes/sizes with the verified local bundle."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];REPO='retro-trans/Ore-no-Shikabane-o-Koete-Yuke';VERSION='0.2.38'
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],cwd=ROOT,text=True,encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args()
 if not a.execute:print('DRY RUN: read release metadata and compare all four uploaded hashes/sizes with the local verified bundle.');return
 release=next(x for x in gh('repos/'+REPO+'/releases') if x['tag_name']=='v'+VERSION);assert release['author']['login']=='binhlt0402' and not release['prerelease']
 folder=ROOT/('work/output/release-'+VERSION);local={p.name:p for p in folder.iterdir() if p.is_file()};remote={x['name']:x for x in release['assets']};assert set(local)==set(remote) and len(local)==4
 verified=[]
 for name,p in local.items():
  asset=remote[name];digest=sha(p);assert asset['state']=='uploaded' and asset['size']==p.stat().st_size and asset['digest']=='sha256:'+digest,name
  verified.append(dict(name=name,bytes=p.stat().st_size,sha256=digest))
 manifest=json.loads(local['BUILD-MANIFEST.json'].read_text());commit=manifest['source_commit'];assert gh('repos/'+REPO+'/commits/'+commit)['sha']==commit
 proof=dict(version=VERSION,repository=REPO,release_id=release['id'],url=release['html_url'],tag=release['tag_name'],draft=release['draft'],author=release['author']['login'],result='PASS',source_commit=commit,assets=verified,verification='All GitHub-reported uploaded SHA-256 digests and sizes equal the locally round-trip-verified bundle')
 print(json.dumps(proof,indent=2))
 if a.write:
  dest=ROOT/('work/source/publication-'+VERSION);dest.mkdir(exist_ok=True);(dest/'upload-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

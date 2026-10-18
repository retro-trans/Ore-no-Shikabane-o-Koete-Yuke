"""Package the tested build with Retro Trans Tools. Dry run before --write."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();v='0.2.38'
 source=ROOT/'Ore no Shikabane o Koete Yuke (Japan).iso';target=ROOT/('work/output/english-native-'+v+'.iso');backend=ROOT/'work/source/retro-trans-tools';config=ROOT/('work/source/release-'+v+'.json');out=ROOT/('work/output/release-'+v)
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert len(commit)==40
 assert sha(target)=='c7a51ee07bf8f42d47d65c670c80e270eae9fe7743551b1ffe732e3efe6569f8'
 settings=dict(game_id='ore-no-shikabane-o-koete-yuke',game_name='Ore no Shikabane o Koete Yuke',platform='PSP',version=v,source_commit=commit,patches=[dict(patch='OreNoShikabane-English-'+v+'.xdelta',edition='UCJS10117',language='en',source_version='original',source_format='iso',target_format='iso',source=str(source),target=str(target))])
 print(json.dumps(dict(write=a.write,source=dict(bytes=source.stat().st_size,sha256=sha(source)),target=dict(bytes=target.stat().st_size,sha256=sha(target)),source_commit=commit,backend_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=backend,text=True).strip(),assets=[settings['patches'][0]['patch'],'BUILD-MANIFEST.json','VALIDATION.json','SHA256SUMS.txt'],output=str(out),private_configuration=str(config)),indent=2),flush=True)
 if not a.write:return
 assert not out.exists();config.write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
 subprocess.run([sys.executable,'-m','retro_trans.release','build',str(config),'--out',str(out)],cwd=backend,check=True)
 subprocess.run([sys.executable,'-m','retro_trans.release','validate',str(out)],cwd=backend,check=True)
 print('Verified release bundle:',out)
if __name__=='__main__':main()

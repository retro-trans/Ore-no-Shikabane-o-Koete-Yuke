"""Stage/restore normal saves only in the project QA profile. Dry run first."""
import argparse,hashlib,json,shutil
from catalog_text import ROOT
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');ap.add_argument('--restore',action='store_true');ap.add_argument('--version',default='0.2.35');ap.add_argument('--context',default='status-layout');a=ap.parse_args()
assert __import__('re').fullmatch(r'0\.\d+\.\d+',a.version) and __import__('re').fullmatch(r'[a-z-]+',a.context)
target=ROOT/'work/source/emulator/memstick/PSP/SAVEDATA/UCJS10117';source=__import__('pathlib').Path('C:/Users/Binh/Documents/PPSSPP/PSP/SAVEDATA/UCJS10117');backup=ROOT/('work/source/qa-backup-before-'+a.version);ui=ROOT/('work/ui/'+a.context+'-'+a.version);files=['SAVEDATA.BIN','PARAM.SFO','ICON0.PNG','PIC1.PNG'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert str(target.resolve()).startswith(str(ROOT.resolve())+'\\')
if a.restore:
 r=json.loads((backup/'preservation.json').read_text());assert all(sha(backup/f)==r['before'][f] for f in files);print(json.dumps(dict(write=a.write,action='Restore original isolated saves',hashes=r['before']),indent=2))
 if a.write:
  for f in files:shutil.copyfile(backup/f,target/f)
  actual={f:sha(target/f) for f in files};assert actual==r['before'];proof=dict(version=a.version,result='PASS',original_project_hashes=r['before'],restored_project_hashes=actual,user_source_written=False,user_source_unchanged=all(sha(source/f)==r['source'][f] for f in files),save_states_loaded=False);(ui/'save-preservation.json').write_text(json.dumps(proof,indent=2)+'\n')
else:
 assert not backup.exists();r=dict(before={f:sha(target/f) for f in files},source={f:sha(source/f) for f in files});assert r['before']['SAVEDATA.BIN']=='e97eaf0a38116b78d58a4f0d114d68912b6335def8a91a638145876c0b9056b0';print(json.dumps(dict(write=a.write,action='Back up isolated saves and stage normal user save copy; user profile read only',hashes=r),indent=2))
 if a.write:
  backup.mkdir()
  for f in files:shutil.copyfile(target/f,backup/f);shutil.copyfile(source/f,target/f)
  (backup/'preservation.json').write_text(json.dumps(r,indent=2)+'\n')

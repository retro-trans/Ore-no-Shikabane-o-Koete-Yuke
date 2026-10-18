"""Extract the supplied Vita game into an isolated local profile. Dry run first."""
import argparse,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'Oreshika Tainted Bloodlines (USA)/app/PCSA00155'
runtime=ROOT/'work/source/vita3k-tools'
profile=ROOT/'work/source/vita3k-icons-profile'
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
config=runtime/'config-icons.yml'
command=[str(runtime/'Vita3K.exe'),'--console','--frontend','sdl','--config-location',str(config),'--load-config','--keep-config',str(source)]
print(json.dumps(dict(write=args.write,source=str(source),destination=str(profile),method='Offline PFS extraction using the included local license; separate Vita3K profile',license_material='Not printed or transmitted',source_changes=False),indent=2),flush=True)
if not args.write:raise SystemExit()
assert not (profile/'ux0/app/PCSA00155').exists()
profile.mkdir(parents=True,exist_ok=True)
config.write_text('pref-path: '+json.dumps(profile.as_posix())+'\nfrontend: sdl\n',encoding='utf-8')
log=ROOT/'work/source/vita3k-icon-extraction.log'
with log.open('wb') as out:
 p=subprocess.Popen(command,cwd=str(runtime),stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 print(json.dumps(dict(pid=p.pid,private_log=str(log))),flush=True)
 try:
  deadline=time.monotonic()+1200
  while p.poll() is None:
   if time.monotonic()>deadline:raise TimeoutError('Extraction exceeded twenty minutes')
   s=log.read_text(encoding='utf-8',errors='replace')
   installed=profile/'ux0/app/PCSA00155'
   icon=installed/'system/icon.png'
   completed=(installed/'data.img').exists() and not (installed/'sce_pfs').exists() and icon.exists() and icon.open('rb').read(8)==b'\x89PNG\r\n\x1a\n'
   if completed or 'Content installed, will auto-boot:' in s:
    p.terminate();break
   time.sleep(.5)
  p.wait(timeout=10)
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=10)
files=list(profile.rglob('data.img'))
print(json.dumps(dict(exit=p.returncode,archives=[dict(path=str(f),bytes=f.stat().st_size,header=f.open('rb').read(16).hex()) for f in files]),indent=2))

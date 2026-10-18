"""Back up and select the recorded controller's XInput path. Dry run unless --write."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    paths=[Path.home()/'Documents/PPSSPP/PSP/SYSTEM/ppsspp.ini',root/'work/source/emulator/profile.ini']
    plans=[]
    for p in paths:
        data=p.read_bytes();text=data.decode('utf-8-sig')
        import re
        for key,value in [('AllowHIDInput','False'),('AllowDInput','False'),('AllowXInput','True')]:
            pattern=r'(?m)^'+key+r' = (True|False)'
            if re.search(pattern,text):text=re.sub(pattern,key+' = '+value,text)
            else:
                if '[Control]' not in text:text+='\r\n[Control]\r\n'
                text=text.replace('[Control]','[Control]\r\n'+key+' = '+value,1)
        new=text.encode('utf-8')
        backup=root/'work/source/controller-backup-0.2.16'/('user.ini' if p==paths[0] else 'project.ini')
        plans.append((p,data,new,backup))
    print(json.dumps([dict(path=str(p),backup=str(b),old_sha256=hashlib.sha256(d).hexdigest(),changed=d!=n,settings=dict(AllowHIDInput=False,AllowDInput=False,AllowXInput=True)) for p,d,n,b in plans],indent=2))
    if a.write:
        for p,d,n,b in plans:
            if d==n:continue
            b.parent.mkdir(parents=True,exist_ok=True)
            assert not b.exists(),'Preserve original backup'
            b.write_bytes(d);p.write_bytes(n)
    print('Settings written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

"""Refresh the undelivered 0.2.16 candidate with checked components. Dry run unless --write."""
import argparse,hashlib,json,struct
from catalog_text import ROOT
from extract_iso import inventory

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    iso=ROOT/'work/output/english-native-0.2.16.iso';mp=iso.with_suffix('.manifest.json');manifest=json.loads(mp.read_text(encoding='utf-8'));assert manifest['version']=='0.2.16'
    assert json.loads((ROOT/'work/output/english-native-0.2.16/latin.report.json').read_text(encoding='utf-8'))['runtime_verification']=='pending','Verified builds must be preserved; refresh is for pending candidates only'
    changes=[]
    with iso.open('rb') as f:
        entries={x['path']:x for x in inventory(f)}
        for p in manifest['files']:
            e=entries[p['path']];assert e['size']==p['new_size'] and e['iso_offset']==p['new_iso_offset'];f.seek(e['iso_offset']);assert hashlib.sha256(f.read(e['size'])).hexdigest()==p['sha256']
            data=(ROOT/p['replacement']).read_bytes();sha=hashlib.sha256(data).hexdigest()
            if sha!=p['sha256']:changes.append((p,data,sha))
    print(json.dumps([dict(path=p['path'],old_sha256=p['sha256'],new_sha256=sha,old_bytes=p['new_size'],new_bytes=len(data)) for p,data,sha in changes],indent=2))
    if a.write:
        assert changes
        backup=ROOT/('work/source/latin-candidate-manifests/'+changes[0][0]['sha256']+'.json');assert not backup.exists();backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(mp.read_bytes())
        with iso.open('r+b') as f:
            for p,data,sha in changes:
                off=p['new_iso_offset'];limit=(p['new_size']+2047)&~2047
                if len(data)>limit:f.seek(0,2);off=(f.tell()+2047)&~2047
                f.seek(off);f.write(data);f.write(bytes((-len(data))%2048));f.seek(p['directory_record_offset']+2);f.write(struct.pack('<I',off//2048)+struct.pack('>I',off//2048));f.seek(p['directory_record_offset']+10);f.write(struct.pack('<I',len(data))+struct.pack('>I',len(data)))
                p.update(new_size=len(data),new_iso_offset=off,sha256=sha)
            f.seek(0,2);size=f.tell();assert size%2048==0;f.seek(16*2048+80);f.write(struct.pack('<I',size//2048)+struct.pack('>I',size//2048))
        manifest['bytes']=size;mp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        with iso.open('rb') as f:
            entries={x['path']:x for x in inventory(f)}
            for p in manifest['files']:
                e=entries[p['path']];assert e['size']==p['new_size'] and e['iso_offset']==p['new_iso_offset'];f.seek(e['iso_offset']);assert hashlib.sha256(f.read(e['size'])).hexdigest()==p['sha256']
    print('Candidate refreshed and verified.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

"""Package local PSP test routes with Retro Trans Tools; no GitHub operations.

Dry run unless --write. Verifies both complete patched images after encoding.
"""
import argparse,json,os,subprocess,sys
from package_release import ROOT,sha

V='0.2.50'


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true')
    ap.add_argument('--version',choices=['0.2.50','0.2.51','0.2.52'],default=V)
    ap.add_argument('--source-version',choices=['all','original','0.2.48','0.2.50','0.2.51'],default='all')
    a=ap.parse_args();version=a.version
    suffix='' if a.source_version=='all' else '-from-'+a.source_version
    backend=ROOT/'work/source/retro-trans-tools';out=ROOT/('work/output/hardware-test-'+version+suffix)
    target=ROOT/('work/output/english-native-'+version+'.iso');target_hash=sha(target)
    sources=[(ROOT/'Ore no Shikabane o Koete Yuke (Japan).iso','original','full'),
        (ROOT/'work/output/english-native-0.2.48.iso','0.2.48','0.2.48-to-'+version)]
    assert sha(sources[1][0])=='43569c29fb58ece6ade5f02f4ac39ea8df86041ba6bce7fc461f7293e1dcc907'
    original_hash=json.loads((ROOT/'docs/releases/0.2.48/BUILD-MANIFEST.json').read_text())['patches'][0]['source_sha256']
    assert sha(sources[0][0])==original_hash
    if version in ('0.2.51','0.2.52'):
        previous=ROOT/'work/output/english-native-0.2.50.iso'
        assert sha(previous)=='896cb22228cf4a2d649e78ed52823db3419fabd26716b66feb0953520d8fd74b'
        sources.append((previous,'0.2.50','0.2.50-to-'+version))
    if version=='0.2.52':
        previous=ROOT/'work/output/english-native-0.2.51.iso'
        assert sha(previous)=='3e58ffb361fc5fda6ef7a943b2a84800df1ba57712a41d65e11a42d87eccea84'
        sources.append((previous,'0.2.51','0.2.51-to-'+version))
    if a.source_version!='all':
        sources=[s for s in sources if s[1]==a.source_version]
        assert sources, 'Requested source version is not an available route'
    settings=dict(game_id='ore-no-shikabane-o-koete-yuke',game_name='Ore no Shikabane o Koete Yuke',
        platform='PSP',version=version,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        patches=[dict(patch='OreNoShikabane-English-'+(version+'-full' if route=='full' else route)+'-PSP-test.xdelta',
            edition='UCJS10117',language='en',source_version=source_version,source_format='iso',target_format='iso',
            source=str(source),target=str(target)) for source,source_version,route in sources])
    print(json.dumps(dict(write=a.write,output=str(out),target_sha256=target_hash,
        target_bytes=target.stat().st_size,routes=[p['patch'] for p in settings['patches']],github_release=False),indent=2),flush=True)
    if not a.write:return
    assert not out.exists()
    config=ROOT/('work/source/hardware-test-'+version+suffix+'.json');assert not config.exists()
    config.write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
    sys.path.insert(0,str(backend));from retro_trans import release
    def encode(engine,source,modified,destination,cancel=None,progress=None):
        env=os.environ.copy();env.pop('XDELTA',None)
        print('Encoding:',destination.name,flush=True)
        subprocess.run([str(engine),'-e','-D','-A','-B',str(1<<30),'-s',str(source),str(modified),str(destination)],
            check=True,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    release.encode=encode
    manifest=release.build_release(config,out);release.validate_directory(out)
    assert all(p['target_sha256']==target_hash for p in manifest['patches'])
    print('PASS: %d local test route(s) reproduce the complete target image.'%len(manifest['patches']),flush=True)


if __name__=='__main__':main()

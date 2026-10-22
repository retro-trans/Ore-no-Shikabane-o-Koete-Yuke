"""Package the verified 0.2.48 full/upgrade routes. Dry run before --write."""
import argparse,json,os,subprocess,sys,tempfile,time
from pathlib import Path
from package_release import sha

ROOT=Path(__file__).resolve().parents[1]
V='0.2.48'
WINDOW=1<<30
TARGET='43569c29fb58ece6ade5f02f4ac39ea8df86041ba6bce7fc461f7293e1dcc907'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    source=ROOT/'Ore no Shikabane o Koete Yuke (Japan).iso'
    previous=ROOT/'work/output/english-native-0.2.38.iso'
    target=ROOT/('work/output/english-native-'+V+'.iso')
    backend=ROOT/'work/source/retro-trans-tools'
    config=ROOT/('work/source/release-'+V+'.json')
    out=ROOT/('work/output/release-'+V)
    assert out.parent.resolve()==(ROOT/'work/output').resolve()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    backend_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=backend,text=True).strip()
    assert len(commit)==len(backend_commit)==40
    old=json.loads((ROOT/'docs/releases/0.2.38/BUILD-MANIFEST.json').read_text())['patches'][0]
    assert sha(source)==old['source_sha256'] and sha(previous)==old['target_sha256']
    assert sha(target)==TARGET
    patches=[]
    for src,version,name in [(source,'original','OreNoShikabane-English-'+V+'-full.xdelta'),
                            (previous,'0.2.38','OreNoShikabane-English-0.2.38-to-'+V+'.xdelta')]:
        patches.append(dict(patch=name,edition='UCJS10117',language='en',source_version=version,
            source_format='iso',target_format='iso',source=str(src),target=str(target)))
    settings=dict(game_id='ore-no-shikabane-o-koete-yuke',game_name='Ore no Shikabane o Koete Yuke',
        platform='PSP',version=V,source_commit=commit,patches=patches)
    print(json.dumps(dict(write=args.write,version=V,source_commit=commit,backend_commit=backend_commit,
        target_sha256=TARGET,target_bytes=target.stat().st_size,source_window_bytes=WINDOW,
        routes=[dict(source=p['source_version'],patch=p['patch']) for p in patches],output=str(out)),indent=2),flush=True)
    if not args.write:return
    assert not out.exists()
    config.write_text(json.dumps(settings,indent=2)+'\n',encoding='utf-8')
    sys.path.insert(0,str(backend))
    from retro_trans import release
    from retro_trans.core import PatchError,check_cancel,report
    encodings=[]
    def compact_encode(engine,source,modified,destination,cancel=None,progress=None):
        # Keep the official builder/decoder/validator; only enlarge the encoder
        # source window, so relocated unchanged bytes do not bloat the delta.
        check_cancel(cancel)
        env=os.environ.copy();env.pop('XDELTA',None)
        command=[str(engine),'-e','-D','-A','-B',str(WINDOW),'-s',str(source),str(modified),str(destination)]
        print('Encoding compact patch:',destination.name,flush=True)
        with tempfile.TemporaryFile() as errors:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=errors,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                while process.poll() is None:
                    check_cancel(cancel);report(progress,'Creating compact xdelta patch',None);time.sleep(.1)
                if process.returncode:
                    errors.seek(0)
                    raise PatchError('Compact encode failed: '+errors.read(4096).decode('utf-8',errors='replace'))
            finally:
                if process.poll() is None:process.kill()
                process.wait()
        encodings.append(dict(patch=destination.name,bytes=destination.stat().st_size,
            sha256=sha(destination),engine_sha256=sha(Path(engine))))
        print('Patch bytes:',destination.stat().st_size,'; verifying complete target',flush=True)
    release.encode=compact_encode
    manifest=release.build_release(config,out)
    release.validate_directory(out)
    assert all(p['target_sha256']==TARGET for p in manifest['patches'])
    evidence=dict(version=V,source_commit=commit,builder_repository='https://github.com/retro-trans/retro-trans-tools',
        builder_commit=backend_commit,source_window_bytes=WINDOW,application_header=False,
        encoder_override='Official xdelta engine with -B 1073741824; standard Retro Trans builder, decoder and validator otherwise unchanged',
        encodings=encodings,roundtrip_verified=True,game_images_uploaded=False)
    (ROOT/('work/source/packaging-'+V+'.json')).write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('PASS: both routes round-trip to the exact tested image.',flush=True)


if __name__=='__main__':main()

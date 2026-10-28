"""Record the local PSP candidate and create its test ZIP. Dry run before --write."""
import argparse,json,hashlib,zipfile
from pathlib import Path
from package_release import ROOT,sha

V='0.2.50'
README='''Ore no Shikabane o Koete Yuke - English 0.2.50 PSP TEST

Experimental local test. Physical PSP startup is NOT yet confirmed.
Latest public release remains 0.2.48. This package has not been published.

1. Extract this ZIP. Use ONE matching patch with Retro Trans Tools:
   - Public 0.2.48 ISO: 0.2.48-to-0.2.50-PSP-test.xdelta
   - Original Japanese UCJS10117 ISO: 0.2.50-full-PSP-test.xdelta
   The tool verifies the source and patched ISO hashes. Do not apply both.
2. Copy the resulting 0.2.50 ISO to the PSP as a separate file.
3. Fully quit the game. Back up PSP/GAME/UCJS10117/PBOOT.PBP, then temporarily
   rename that one file to PBOOT.PBP.disabled. Leave savedata untouched.
4. Start the 0.2.50 ISO fresh. Check that the title says v0.2.50 and the home
   menu has three clearly separated columns with complete help text.
5. Report whether it starts, and send a home-menu photo if it does.
   If it fails, restore the exact PBOOT.PBP filename. Report the error number
   or whether it freezes, stays black or shuts down. Also report System
   Settings > System Information > System Software.

Keep the old ISO and update backup. No firmware changes are needed for this
test. An enabled PBOOT.PBP can override the patched executable, so testing
with it enabled does not establish whether this startup candidate works.

Change: the exact 0.2.49 executable is now compressed inside the source game's
PSP loader format. Runtime code/assets/addresses are unchanged. The archive
changes only its title version. Includes the commodity-screen fixes from
0.2.49. This does not port the official update's gameplay bug fixes.

Checked: independent decryption, header/body authentication, exact payload,
malformed-file rejection, emulator cold boot and loaded home layout, and
complete round-trip decoding of both test patches. These emulator checks
do not replace the physical PSP test.

Expected patched ISO:
Bytes: 1077526528
SHA-256: 896cb22228cf4a2d649e78ed52823db3419fabd26716b66feb0953520d8fd74b
'''


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    ui=ROOT/('work/ui/hardware-startup-'+V);out=ROOT/('work/output/english-native-'+V)
    hardware_report=ui/'hardware-report.json'
    if hardware_report.exists() and json.loads(hardware_report.read_text()).get('candidate_tested'):
        raise ValueError('A physical hardware result is already recorded; preserve it instead of resealing emulator-only evidence.')
    bundle=ROOT/('work/output/hardware-test-'+V)
    runtime=json.loads((ui/'runtime.json').read_text());static=json.loads((ui/'static-tests.json').read_text())
    assert runtime['result']==static['result']=='PASS' and static['independent_decryption']
    assert not runtime['hardware_verified'] and not static['hardware_verified']
    manifest=json.loads((bundle/'BUILD-MANIFEST.json').read_text())
    image=ROOT/('work/output/english-native-'+V+'.iso');identity=dict(file=str(image.relative_to(ROOT)),bytes=image.stat().st_size,sha256=sha(image))
    assert identity['sha256']=='896cb22228cf4a2d649e78ed52823db3419fabd26716b66feb0953520d8fd74b'
    assert all(p['target_sha256']==identity['sha256'] for p in manifest['patches'])
    qa=ROOT/'work/source/hardware-qa-0.2.50';before=json.loads((qa/'save-source-before.json').read_text())
    user=Path('C:/Users/Binh/Documents/PPSSPP/PSP/SAVEDATA/UCJS10117')
    assert all(sha(user/name)==value for name,value in before.items())
    preservation=dict(result='PASS',user_source_written=False,user_source_unchanged=True,
        source_hashes_before=before,source_hashes_after={n:sha(user/n) for n in before},
        isolated_save_copy=True,save_states_loaded=False)
    executable=json.loads((out/'hardware.report.json').read_text())
    executable['sfo_sha256']=sha(out/'PARAM.SFO')
    assert executable['sfo_sha256']=='92418e39e2c99ca68e48ff92c9668d459786eefc08a98959082d810dd5e40c80'
    executable['runtime_status']='PASS: emulator cold boot/title/home; physical PSP pending'
    proof=dict(version=V,result='PASS: local packaging and selected emulator checks; hardware pending',
        iso=identity,executable=executable,
        static=static,runtime=runtime,patches=manifest['patches'],save_preservation=preservation,
        psp1000_emulator_title_checked=True,hardware_verified=False,github_release=False,
        notes='System software and exact hardware failure symptom remain pending; no physical fix claimed.')
    zip_path=ROOT/('work/output/OreNoShikabane-English-'+V+'-PSP-test.zip')
    print(json.dumps(dict(write=args.write,iso=identity,zip=str(zip_path),hardware_verified=False,github_release=False),indent=2))
    if not args.write:return
    assert not zip_path.exists() and not (bundle/'README.txt').exists()
    (bundle/'README.txt').write_text(README,encoding='utf-8')
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(bundle.iterdir()):
            if p.is_file():z.write(p,p.name)
    proof['test_zip']=dict(file=str(zip_path.relative_to(ROOT)),bytes=zip_path.stat().st_size,sha256=sha(zip_path))
    (out/'hardware.report.json').write_text(json.dumps(executable,indent=2)+'\n',encoding='utf-8')
    (ui/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    (ui/'save-preservation.json').write_text(json.dumps(preservation,indent=2)+'\n',encoding='utf-8')
    path=ROOT/'docs/local_build_status.json';status=json.loads(path.read_text())
    status.update(latest_local_build=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'])
    status['checks']['hardware_startup_packaging']='PASS: exact payload, independent decryptor, authenticated header/body, emulator title/home and full patch round trips; real PSP pending'
    status['hardware_startup_candidate']=dict(version=V,based_on='0.2.49',hardware_verified=False,
        executable_format='Compressed type-2 ~PSP; same game tag and metadata',payload_identical=True,
        evidence='work/ui/hardware-startup-0.2.50/verification.json')
    status['release']='Local hardware test candidate 0.2.50; latest public release remains 0.2.48.'
    path.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    path=ROOT/'work/ui/verified_screens.json';index=json.loads(path.read_text())
    index['additional_build_evidence'].append(dict(version=V,
        evidence='work/ui/hardware-startup-0.2.50/verification.json',
        scope='PASS: selected emulator title/home checks for compressed executable; physical PSP pending'))
    index['latest_hardware_candidate_version']=V
    path.write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print('Local hardware test ZIP and evidence written. No GitHub operations.')


if __name__=='__main__':main()

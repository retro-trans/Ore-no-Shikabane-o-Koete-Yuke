"""Seal local 0.2.52 evidence and its 0.2.51 upgrade ZIP; dry run first."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from package_release import ROOT, sha
from extract_iso import inventory

V = '0.2.52'
TARGET = '5e821290c20f25f0642c4834f602e9fc7d46925d820f3ccfd83b78cc7f86590b'
README = '''Ore no Shikabane o Koete Yuke - English 0.2.52 PSP TEST

Local test candidate. Physical PSP startup is NOT confirmed.
0.2.51 still failed with PBOOT disabled. The user also reports that the clean
Japanese ISO fails with PBOOT disabled, so the shutdown is not unique to the
translation and the hardware boot-path problem remains unresolved.

This candidate removes a separately reproduced ELF loading conflict: the
PSP-style in-place loader model clears the old translation segment before
reading it. The new contiguous ELF preserves the entire intended runtime
image. Game code, addresses, assets and reserved memory stay unchanged.
The executable remains compressed; only the title version changes in data.ore.
The startup flag remains as in 0.2.51. Official update fixes are not ported.

1. Extract this ZIP. Use Retro Trans Tools to apply the included patch to
   your exact English 0.2.51 ISO. It is NOT a patch for the original ISO.
2. Copy the resulting english-native-0.2.52.iso to the PSP as a separate file.
3. Back up PSP/GAME/UCJS10117/PBOOT.PBP, then temporarily disable that file.
4. Fully power off/restart the PSP and launch the new ISO. Check for v0.2.52
   on the title screen and three clearly separated home-menu columns.
5. If it still fails, restore the exact PBOOT.PBP filename for normal play.

Do not change firmware or savedata for this test. Keeping PBOOT enabled loads
its original executable and does not test the translated native layout.

Checked locally: original/update loader-model controls, old failure/new pass,
identical intended memory image, ELF sections/import metadata, authenticated
packing, isolated emulator cold boot/title/normal save/home/font, source save
hash preservation and exact Retro Trans patch round trip. A firmware-source
model and an emulator are not physical hardware tests. No GitHub release.

Expected patched ISO:
Bytes: 1077544960
SHA-256: 5e821290c20f25f0642c4834f602e9fc7d46925d820f3ccfd83b78cc7f86590b
'''


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true'); args = ap.parse_args()
    ui = ROOT/('work/ui/psp-contiguous-'+V)
    assert not (ui/'hardware-report.json').exists(), 'Preserve recorded hardware outcome'
    out = ROOT/('work/output/english-native-'+V)
    bundle = ROOT/('work/output/hardware-test-'+V+'-from-0.2.51')
    image = ROOT/('work/output/english-native-'+V+'.iso')
    assert image.stat().st_size == 1077544960 and sha(image) == TARGET
    report = json.loads((out/'contiguous.report.json').read_text())
    runtime = json.loads((ui/'runtime.json').read_text())
    static = json.loads((ui/'static-tests.json').read_text())
    assert static['result'] == 'PASS' and runtime['normal_save_loaded'] and runtime['font_atlas_exact']
    assert report['loader_model']['after']['matches_intended_memory']
    with image.open('rb') as f:
        rows = {r['path']:r for r in inventory(f)}
        for name, component in [('PSP_GAME/SYSDIR/EBOOT.BIN','EBOOT.hardware.bin'),
                                ('PSP_GAME/USRDIR/data.ore','data.hardware.ore'),
                                ('PSP_GAME/PARAM.SFO','PARAM.SFO')]:
            row = rows[name]; f.seek(row['iso_offset'])
            assert hashlib.sha256(f.read(row['size'])).hexdigest() == sha(out/component)
    manifest = json.loads((bundle/'BUILD-MANIFEST.json').read_text())
    validation = json.loads((bundle/'VALIDATION.json').read_text())
    assert len(manifest['patches']) == 1
    assert all(p['target_sha256']==TARGET for p in manifest['patches'])
    assert all(p['roundtrip_verified'] and p['target_sha256']==TARGET for p in validation['patches'])
    for line in (bundle/'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1); assert sha(bundle/name) == digest
    before = json.loads((ROOT/'work/source/hardware-qa-0.2.52/save-source-before.json').read_text())
    source = Path('C:/Users/Binh/Documents/PPSSPP/PSP/SAVEDATA/UCJS10117')
    assert all(sha(source/name)==digest for name,digest in before.items())
    preservation = dict(result='PASS', source_written=False, source_unchanged=True,
        source_hashes=before, isolated_save_copy=True, save_states_loaded=False)
    zip_path = ROOT/('work/output/OreNoShikabane-English-'+V+'-from-0.2.51-PSP-test.zip')
    proof = dict(version=V, result='PASS: local loader model, selected emulator checks and patch round trip; physical PSP pending',
        iso=dict(file=image.relative_to(ROOT).as_posix(), bytes=image.stat().st_size, sha256=TARGET),
        changes=report, runtime=runtime, static=static, patches=manifest['patches'],
        save_preservation=preservation, physical_psp_tested=False, hardware_verified=False,
        original_iso_control='User correction: clean Japanese ISO also fails with PBOOT disabled',
        limitations='Source-based loader model is not a firmware replay; physical shutdown cause unconfirmed',
        github_release=False)
    print(json.dumps(dict(write=args.write, iso=proof['iso'], zip=str(zip_path)), indent=2))
    if not args.write:
        return
    assert not zip_path.exists() and not (bundle/'README.txt').exists()
    (bundle/'README.txt').write_text(README, encoding='utf-8')
    with (bundle/'SHA256SUMS.txt').open('a', encoding='utf-8') as f:
        f.write(sha(bundle/'README.txt')+'  README.txt\n')
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(bundle.iterdir()):
            if p.is_file():
                z.write(p, p.name)
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            digest, name = line.split('  ', 1)
            assert hashlib.sha256(z.read(name)).hexdigest() == digest
    proof['test_zip'] = dict(file=zip_path.relative_to(ROOT).as_posix(), bytes=zip_path.stat().st_size, sha256=sha(zip_path))
    write_json(ui/'verification.json', proof)
    write_json(ui/'save-preservation.json', preservation)
    path = ROOT/'docs/local_build_status.json'; status = json.loads(path.read_text())
    status.update(latest_local_build=V, file=proof['iso']['file'], bytes=proof['iso']['bytes'], sha256=TARGET)
    status['checks']['psp_contiguous_load'] = 'PASS: in-place model, identical intended runtime image, selected emulator checks and upgrade round trip; hardware pending'
    status['hardware_startup_candidate'] = dict(version=V, based_on='0.2.51', hardware_tested=False,
        hardware_verified=False, physical_test_status='Pending; prior 0.2.51 and clean Japanese ISO fail with PBOOT disabled',
        reported_system_software='6.61 ARK-5', prior_failed_versions=['0.2.48','0.2.50','0.2.51'],
        original_iso_control=proof['original_iso_control'], evidence='work/ui/psp-contiguous-0.2.52/verification.json')
    status['release'] = 'Local contiguous-loader test candidate 0.2.52; hardware pending. Latest public release remains 0.2.48.'
    write_json(path, status)
    path = ROOT/'work/ui/verified_screens.json'; index = json.loads(path.read_text())
    assert not any(row['version']==V for row in index['additional_build_evidence'])
    index['additional_build_evidence'].append(dict(version=V, evidence='work/ui/psp-contiguous-0.2.52/verification.json',
        scope='PASS: loader model, identical intended runtime image, selected emulator title/home; physical PSP pending'))
    index['latest_hardware_candidate_version'] = V; write_json(path, index)
    print(json.dumps(proof['test_zip'], indent=2))


if __name__ == '__main__':
    main()

"""Seal local 0.2.51 checks and test ZIPs; dry run before --write."""
import argparse,json,struct,zipfile
from pathlib import Path
from package_release import ROOT,sha
from extract_iso import inventory

V='0.2.51'
TARGET='3e58ffb361fc5fda6ef7a943b2a84800df1ba57712a41d65e11a42d87eccea84'
README='''Ore no Shikabane o Koete Yuke - English 0.2.51 PSP TEST

Local diagnostic candidate. Physical PSP startup is NOT confirmed.
It tests one startup setting identified by comparing your working PBOOT.PBP.
Executable/code/memory layout are identical to 0.2.50. Only the extra disc
EBOOT-decryption request is disabled; the title version advances to 0.2.51.

1. Extract the ZIP. Apply ONE patch matching your input ISO using Retro Trans
   Tools. This small package upgrades the exact 0.2.50 test ISO to 0.2.51.
   The full package also has original/0.2.48 routes; do not apply multiple patches.
2. Copy the resulting ISO separately as english-native-0.2.51.iso on the PSP.
3. Back up PSP/GAME/UCJS10117/PBOOT.PBP. Temporarily rename only that file
   to PBOOT.PBP.disabled. Do not change saves or firmware.
4. Fully restart the PSP (not sleep), then launch the newly named 0.2.51 ISO.
   This matters because the launcher may retain older startup metadata.
5. Check that the title says v0.2.51 and the home-menu columns are separated.
   Report whether it starts. If it shuts down, restore PBOOT.PBP and report it.

An enabled installed update bypasses the patched executable, so testing with
PBOOT.PBP enabled cannot establish whether this candidate fixes startup.
Previous 0.2.48/0.2.50 hardware failures remain unresolved; emulator success
does not prove this hypothesis. No GitHub release was published.

Expected output ISO:
Bytes: 1077526528
SHA-256: 3e58ffb361fc5fda6ef7a943b2a84800df1ba57712a41d65e11a42d87eccea84
'''


def flag(sfo):
    _,_,ko,vo,n=struct.unpack_from('<5I',sfo)
    for i in range(n):
        k,fmt,length,cap,off=struct.unpack_from('<HHIII',sfo,20+16*i)
        pos=ko+k;name=sfo[pos:sfo.index(b'\0',pos)]
        if name==b'HRKGMP_VER':
            assert fmt==0x404 and length==4
            return struct.unpack_from('<I',sfo,vo+off)[0]
    return None


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    ui=ROOT/('work/ui/psp-boot-flag-'+V);out=ROOT/('work/output/english-native-'+V)
    hardware_report=ui/'hardware-report.json'
    if hardware_report.exists():
        assert not json.loads(hardware_report.read_text())['candidate_tested'], 'Hardware result already recorded; do not reseal as pending'
    runtime=json.loads((ui/'runtime.json').read_text());assert runtime['cold_boot'] and runtime['font_atlas_exact']
    report=json.loads((out/'boot-flag.report.json').read_text())
    assert report['executable_identical'] and not report['code_or_ram_changes']
    image=ROOT/('work/output/english-native-'+V+'.iso');assert sha(image)==TARGET
    with image.open('rb') as f:
        rows={r['path']:r for r in inventory(f)}
        def read(name):
            row=rows[name];f.seek(row['iso_offset']);return f.read(row['size'])
        sfo=read('PSP_GAME/PARAM.SFO');exe=read('PSP_GAME/SYSDIR/EBOOT.BIN')
        module=read('PSP_GAME/SYSDIR/OPNSSMP.BIN')
    previous=(ROOT/'work/output/english-native-0.2.50/PARAM.SFO').read_bytes()
    changed=[i for i,(x,y) in enumerate(zip(previous,sfo)) if x!=y]
    assert changed==[408] and flag(previous)==19 and flag(sfo)==0
    assert flag((ROOT/'work/source/pboot-analysis/PARAM.SFO').read_bytes()) is None
    assert exe==(ROOT/'work/output/english-native-0.2.50/EBOOT.hardware.bin').read_bytes()
    with (ROOT/'Ore no Shikabane o Koete Yuke (Japan).iso').open('rb') as f:
        original=next(r for r in inventory(f) if r['path']=='PSP_GAME/SYSDIR/OPNSSMP.BIN')
        f.seek(original['iso_offset']);assert module==f.read(original['size'])
    assert sha(ROOT/'incoming/PBOOT.PBP')=='b023e5942af7392abeac03407106b4f6e38915d58c7805a6f528b409ad77eaf7'
    qa=ROOT/'work/source/hardware-qa-0.2.51';before=json.loads((qa/'save-source-before.json').read_text())
    source=Path('C:/Users/Binh/Documents/PPSSPP/PSP/SAVEDATA/UCJS10117')
    assert all(sha(source/n)==v for n,v in before.items())
    bundles=[ROOT/('work/output/hardware-test-'+V),ROOT/('work/output/hardware-test-'+V+'-from-0.2.50')]
    manifests=[json.loads((b/'BUILD-MANIFEST.json').read_text()) for b in bundles]
    assert all(p['target_sha256']==TARGET for m in manifests for p in m['patches'])
    save=dict(result='PASS',user_source_written=False,user_source_unchanged=True,source_hashes=before,
        isolated_profile=True,save_states_loaded=False)
    proof=dict(version=V,result='PASS: metadata, selected emulator checks and patch round trips; hardware pending',
        iso=dict(file=image.relative_to(ROOT).as_posix(),bytes=image.stat().st_size,sha256=TARGET),
        changes=report,runtime=runtime,physical_psp_tested=False,hardware_verified=False,
        sfo=dict(previous_flag=19,new_flag=0,update_flag=None,changed_byte_offsets=changed),
        save_preservation=save,original_pboot_unchanged=True,github_release=False,
        patches=manifests[0]['patches'],basis='Specific decryption-request difference; cause remains unconfirmed')
    print(json.dumps(dict(write=a.write,target_sha256=TARGET,metadata_changes=changed,hardware_verified=False,
        planned_zips=['all routes','small 0.2.50 upgrade']),indent=2))
    if not a.write:return
    zips=[]
    for bundle,suffix in zip(bundles,['','-from-0.2.50']):
        zp=ROOT/('work/output/OreNoShikabane-English-'+V+suffix+'-PSP-test.zip')
        assert not zp.exists() and not (bundle/'README.txt').exists()
        (bundle/'README.txt').write_text(README,encoding='utf-8')
        with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(bundle.iterdir()):
                if p.is_file():z.write(p,p.name)
        with zipfile.ZipFile(zp) as z:
            assert z.testzip() is None
            for line in z.read('SHA256SUMS.txt').decode().splitlines():
                digest,name=line.split('  ',1)
                import hashlib
                assert hashlib.sha256(z.read(name)).hexdigest()==digest
        zips.append(dict(file=zp.relative_to(ROOT).as_posix(),bytes=zp.stat().st_size,sha256=sha(zp)))
    proof['test_zips']=zips
    (ui/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    (ui/'save-preservation.json').write_text(json.dumps(save,indent=2)+'\n',encoding='utf-8')
    update=json.loads((ROOT/'work/source/pboot-analysis/report.json').read_text())
    (ui/'update-inspection.json').write_text(json.dumps(update,indent=2)+'\n',encoding='utf-8')
    p=ROOT/'docs/local_build_status.json';status=json.loads(p.read_text())
    status.update(latest_local_build=V,file=proof['iso']['file'],bytes=proof['iso']['bytes'],sha256=TARGET)
    status['checks']['psp_boot_decryption_flag']='PASS: one-byte SFO change, exact executable, final ISO, selected emulator checks and three patch routes; hardware pending'
    status['hardware_startup_candidate']=dict(version=V,based_on='0.2.50',hardware_tested=False,
        hardware_verified=False,physical_test_status='Pending: clear HRKGMP_VER request; original PBOOT inspected',
        reported_system_software='6.61 ARK-5',prior_failed_versions=['0.2.48','0.2.50'],
        evidence='work/ui/psp-boot-flag-0.2.51/verification.json')
    status['release']='Local startup-flag candidate 0.2.51; prior 0.2.50 failed hardware. Latest public release remains 0.2.48.'
    p.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    p=ROOT/'work/ui/verified_screens.json';index=json.loads(p.read_text())
    index['additional_build_evidence'].append(dict(version=V,evidence='work/ui/psp-boot-flag-0.2.51/verification.json',
        scope='PASS: startup-flag metadata and selected emulator title/home; physical PSP pending'))
    index['latest_hardware_candidate_version']=V;p.write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(zips,indent=2))


if __name__=='__main__':main()

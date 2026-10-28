"""Check executable packaging, independent decryption and corrupted inputs."""
import argparse,gzip,importlib.util,json,struct
from pack_hardware_eboot import ROOT,pack,unpack,sha


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference-decryptor',help='Optional independent local PPSSPP type-2 decryptor')
    args=ap.parse_args()
    original=(ROOT/'work/source/iso/PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes()
    elf=(ROOT/'work/output/english-native-0.2.49/EBOOT.market.elf').read_bytes()
    packed,report=pack(elf,original)
    assert pack(elf,original)[0]==packed
    assert unpack(packed)==elf
    assert packed[:6]==original[:6] and packed[8:0x27]==original[8:0x27]
    assert packed[0x78:0x80]==original[0x78:0x80]
    assert struct.unpack_from('<H',packed,6)[0]==3
    assert struct.unpack_from('<I',packed,0x30)[0]==struct.unpack_from('<I',elf,24)[0]
    assert struct.unpack_from('<I',packed,0x54)[0]==struct.unpack_from('<I',original,0x54)[0]
    offsets=[0,4,6,0x27,0x28,0x2C,0x30,0x34,0x38,0x3C,0x44,0x48,
        0x54,0x58,0x78,0x7C,0x80,0x90,0xB0,0xB4,0xC0,0xD0,0xD4,
        0x12C,0x140,0x150,0x160,len(packed)//2,len(packed)-1]
    for offset in offsets:
        bad=bytearray(packed);bad[offset]^=1
        try:unpack(bad)
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Corruption accepted at '+hex(offset))
    for size in [0,0x14F,0x150,len(packed)-1]:
        try:unpack(packed[:size])
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Truncation accepted')
    independent=False
    if args.reference_decryptor:
        spec=importlib.util.spec_from_file_location('independent_prx',args.reference_decryptor)
        reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
        assert gzip.decompress(reference.decrypt(packed))==elf
        assert reference.decrypt(original)==(ROOT/'work/source/EBOOT.decrypted.elf').read_bytes()
        independent=True
    print(json.dumps(dict(result='PASS',input_elf_sha256=sha(elf),packed_sha256=sha(packed),
        deterministic=True,payload_exact=True,header_and_body_cmac=True,
        metadata_retained=True,corruption_cases=len(offsets),truncation_cases=4,
        independent_decryption=independent,hardware_verified=False),indent=2))


if __name__=='__main__':main()

"""Package the verified static ELF as a compressed, authenticated PSP executable.

Uses the source game's type-2 tag and loader metadata, with sizes and segments
derived again from the patched ELF. Does not sign for official firmware.
Format references and limitations: docs/psp-hardware-startup.txt.
Dry run by default; never overwrites output.
"""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.cmac import CMAC

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = 'c4ac713790de64798793917d1729d4ffdea1e1c6fec13c9dd2eda31833472d03'
TAG = 0xD91613F0
SEED = bytes.fromhex('ebff40d8b41ae166913b8f64b6fcb712')
SLOT = bytes.fromhex('115a5d20d53a8dd39cc5af410f0f186f')
MASTER = bytes.fromhex('98c940975c1d10e87fe60ea3fd03a8ba')
sha = lambda b: hashlib.sha256(b).hexdigest()


def cbc(key, data, encrypt=True):
    ctx = Cipher(algorithms.AES(key), modes.CBC(bytes(16)))
    op = ctx.encryptor() if encrypt else ctx.decryptor()
    return op.update(bytes(data)) + op.finalize()


def mac(key, data):
    ctx = CMAC(algorithms.AES(key)); ctx.update(bytes(data)); return ctx.finalize()


def xor(a, b):
    assert len(a) == len(b)
    return bytes(x ^ y for x, y in zip(a, b))


def stream():
    return cbc(SLOT, b''.join(bytes([i]) + SEED[1:] for i in range(9)), False)


def elf_segments(elf):
    assert elf[:7] == b'\x7fELF\x01\x01\x01'
    assert struct.unpack_from('<HH', elf, 16) == (2, 8), 'Only this static MIPS ELF is supported'
    offset = struct.unpack_from('<I', elf, 28)[0]
    size, count = struct.unpack_from('<HH', elf, 42)
    assert size == 32 and 1 <= count <= 4
    segs = [struct.unpack_from('<8I', elf, offset + i * size) for i in range(count)]
    assert all(s[0] == 1 and s[4] <= s[5] and s[1]+s[4] <= len(elf) for s in segs)
    assert all(s[2] >= 0x08800000 and s[2]+s[5] <= 0x0A000000 for s in segs)
    assert all(segs[i][2]+segs[i][5] <= segs[i+1][2] for i in range(count-1))
    assert all(s[7] > 0 and s[7] <= 65535 and (s[1]-s[2]) % s[7] == 0 for s in segs)
    return segs


def pack(elf, original):
    assert sha(original) == SOURCE_SHA and original[:4] == b'~PSP'
    assert struct.unpack_from('<I', original, 0xD0)[0] == TAG
    segs = elf_segments(elf)
    payload = gzip.compress(bytes(elf), compresslevel=9, mtime=0)
    padded = payload + bytes((-len(payload)) % 16)
    metadata = bytearray(original[:0x80])
    struct.pack_into('<H', metadata, 6, 3)  # compressed + static ELF
    metadata[0x27] = len(segs)
    struct.pack_into('<4I', metadata, 0x28, len(elf), 0x150+len(padded),
                     struct.unpack_from('<I', elf, 24)[0], segs[0][3])
    struct.pack_into('<I', metadata, 0x38, sum(s[5]-s[4] for s in segs))
    metadata[0x3C:0x64] = bytes(40)
    # The source's static-ELF header describes the full reserved memory span.
    # Preserve that convention, including the original BSS in segment zero.
    for i, s in enumerate(segs):
        struct.pack_into('<H', metadata, 0x3C+i*2, s[7])
        struct.pack_into('<I', metadata, 0x44+i*4, s[2])
        struct.pack_into('<I', metadata, 0x54+i*4, s[5])
    def derive(label):
        return hashlib.sha256(b'oreshika-hardware-eboot/v1\0'+label+bytes(elf)).digest()[:16]
    aes, auth, ident = derive(b'aes'), derive(b'cmac'), derive(b'id')
    body = cbc(aes, padded)
    kirk = bytearray(0x90)
    struct.pack_into('<I', kirk, 0x60, 1)
    struct.pack_into('<II', kirk, 0x70, len(payload), 0x80)
    kirk[:32] = cbc(MASTER, aes+auth)
    kirk[0x20:0x30] = mac(auth, kirk[0x60:0x90])
    kirk[0x30:0x40] = mac(auth, kirk[0x60:0x90]+metadata+body)
    x = stream()
    masked = xor(cbc(SLOT, xor(kirk[:0x40], x[0x50:0x90])), x[0x10:0x50])
    fields = struct.pack('<I', TAG)+x[:16]+bytes(0x58)+ident+masked+kirk[0x70:0x80]+metadata
    digest = hashlib.sha1(fields).digest()
    scrambled = cbc(SLOT, ident+digest+masked[:0x3C])
    scattered = scrambled[0x24:]+masked[0x3C:]
    header = bytearray(0x150)
    header[:0x80] = metadata
    header[0x80:0xB0] = scattered[:0x30]
    header[0xB0:0xC0] = kirk[0x70:0x80]
    header[0xC0:0xD0] = scattered[0x30:]
    struct.pack_into('<I', header, 0xD0, TAG)
    header[0x12C:0x140] = scrambled[0x10:0x24]
    header[0x140:0x150] = scrambled[:0x10]
    result = bytes(header)+body
    assert unpack(result) == bytes(elf)
    report = dict(format='type-2 ~PSP; gzip-compressed static ELF', tag=hex(TAG),
        source_header_sha256=sha(original[:0x150]), input_elf_sha256=sha(elf),
        packed_sha256=sha(result), elf_bytes=len(elf), packed_bytes=len(result),
        compressed_bytes=len(payload), comp_attribute=3, decrypt_mode=metadata[0x7C],
        module_attributes=struct.unpack_from('<H',metadata,4)[0],
        segments=[dict(address=hex(s[2]), file_bytes=s[4], memory_bytes=s[5]) for s in segs],
        payload_identical=True, runtime_addresses_unchanged=True, hardware_verified=False)
    return result, report


def unpack(data):
    """Check both KIRK CMACs, header SHA-1, gzip CRC and exact size bounds."""
    assert len(data) >= 0x150 and data[:4] == b'~PSP'
    assert struct.unpack_from('<I', data, 0xD0)[0] == TAG
    assert not any(data[0xD4:0x12C])
    x = stream()
    scrambled = cbc(SLOT, data[0x140:0x150]+data[0x12C:0x140]+data[0x80:0xB0]+data[0xC0:0xCC], False)
    masked = scrambled[0x24:]+data[0xCC:0xD0]
    fields = data[0xD0:0xD4]+x[:16]+bytes(0x58)+scrambled[:16]+masked+data[0xB0:0xC0]+data[:0x80]
    assert hashlib.sha1(fields).digest() == scrambled[0x10:0x24]
    keys_and_macs = xor(cbc(SLOT, xor(masked, x[0x10:0x50]), False), x[0x50:0x90])
    keys = cbc(MASTER, keys_and_macs[:32], False)
    aes, auth = keys[:16], keys[16:]
    kirk_tail = bytearray(0x30)
    struct.pack_into('<I', kirk_tail, 0, 1)
    kirk_tail[0x10:0x20] = data[0xB0:0xC0]
    assert mac(auth, kirk_tail) == keys_and_macs[0x20:0x30]
    assert mac(auth, kirk_tail+data[:0x80]+data[0x150:]) == keys_and_macs[0x30:0x40]
    size, offset = struct.unpack_from('<II', data, 0xB0)
    assert offset == 0x80 and len(data) == 0x150+((size+15)&~15)
    assert struct.unpack_from('<I', data, 0x2C)[0] == len(data)
    payload = cbc(aes, data[0x150:], False)[:size]
    elf = gzip.decompress(payload)
    assert len(elf) == struct.unpack_from('<I', data, 0x28)[0]
    elf_segments(elf)
    return elf


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--elf',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--write',action='store_true'); args=ap.parse_args()
    result, report=pack(args.elf.read_bytes(),(ROOT/'work/source/iso/PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes())
    print(json.dumps(report,indent=2))
    if args.write:
        assert not args.output.exists()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_bytes(result)
        args.output.with_suffix('.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__': main()

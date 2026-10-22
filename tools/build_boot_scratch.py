"""Reserve the startup archive's complete shared framebuffer scratch area. Dry run first."""
import argparse
import hashlib
import json
import struct

from catalog_text import ROOT
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import align, rebuild_ez, rebuild_root, root_entries

V = '0.2.40'
BASE = 0x08803000
SCRATCH_BYTES = 0x88000
sha = lambda data: hashlib.sha256(data).hexdigest()


def build():
    prior = ROOT / 'work/output/english-native-0.2.39'
    source = (prior / 'EBOOT.prompt.elf').read_bytes()
    data = (prior / 'data.prompt.ore').read_bytes()
    assert sha(source) == 'bd9ad72cb56a81a0d2e90404f606d9ffb802ee722e228a5b39813beec137d3f2'
    assert sha(data) == '03ab0ea898aa008c314214f0eadf93655a0332c82b741837d252071019b590da'
    old_report = json.loads((ROOT / 'work/output/english-native-0.2.23/disclaimer.report.json').read_text())
    archive = old_report['embedded_archive']
    blob = source[int(archive['new_file_offset'], 16):int(archive['new_file_offset'], 16) + archive['bytes']]
    assert sha(blob) == archive['sha256'] and blob[:8] == b'EZBIND\0\0'
    assert len(blob) < SCRATCH_BYTES
    elf = bytearray(source)
    po = struct.unpack_from('<I', elf, 28)[0]
    ph = list(struct.unpack_from('<8I', elf, po + 32))
    assert ph[1] + ph[4] == len(elf)
    # The original writable workspace has 0x88000 bytes, including zero
    # padding after its archive. The English archive is smaller than the old
    # archive, so return to that full workspace with no extra PSP RAM cost.
    file_offset = 0x275230
    address = BASE + file_offset
    original_archive, _ = container(source, file_offset)
    assert len(blob) <= len(original_archive) < SCRATCH_BYTES
    assert file_offset + SCRATCH_BYTES <= struct.unpack_from('<I', source, po + 16)[0] + 0x1000
    assert not any(source[file_offset + len(original_archive):file_offset + SCRATCH_BYTES])
    elf[file_offset:file_offset + len(original_archive)] = blob + bytes(len(original_archive) - len(blob))
    patches = []
    for hi, lo in [(0x0881ad40, 0x0881ad48), (0x0881ad4c, 0x0881ad54)]:
        for pc, old, new in [(hi, 0x3c0209b8, 0x3c020000 | ((address + 0x8000) >> 16)),
                             (lo, 0x2442e320, 0x24420000 | (address & 65535))]:
            assert struct.unpack_from('<I', elf, pc - BASE)[0] == old
            struct.pack_into('<I', elf, pc - BASE, new)
            patches.append(dict(address=hex(pc), before=hex(old), after=hex(new)))
    allowed = set(range(file_offset, file_offset + len(original_archive)))
    for patch in patches:
        p = int(patch['address'], 16) - BASE
        allowed.update(range(p, p + 4))
    assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(source, elf)))
    assert address + SCRATCH_BYTES == 0x08b00230 < ph[2]
    assert len(elf) == len(source)

    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original)
    be, bend = root_entries(data)
    ti = next(i for i, _, _, o in oe if o == 0x1e8000)
    tb = next(o for i, _, _, o in be if i == ti)
    ta, te = container(data, tb)
    ot, ote = container(original, 0x1e8000)
    title, preview, fr = footer(member(ot, ote, 25), V)
    ore = rebuild_root(data, {tb: rebuild_ez(ta, {25: pack(title)})}, mutable=True)
    ae, aend = root_entries(ore)
    for n, (a, b) in enumerate(zip(be, ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend) - (a[2] & 2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend) - (b[2] & 2047)
        aa, bb = data[a[3]:sa], ore[b[3]:sb]
        if a[3] != tb:
            assert aa == bb
        else:
            _, ar = container(aa, 0)
            _, br = container(bb, 0)
            for j, ((_, z, p, _), (_, zz, pp, _)) in enumerate(zip(ar, br)):
                if j != 25:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V, source_version='0.2.39', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore), patches=patches,
        scratch=dict(address=hex(address), end=hex(address + SCRATCH_BYTES), bytes=SCRATCH_BYTES,
            file_offset=hex(file_offset), startup_archive_bytes=len(blob), startup_archive_sha256=sha(blob),
            original_shared_address=archive['new_address'], allocation='Original full writable workspace restored', framebuffer_stride=512,
            framebuffer_width=480, framebuffer_height=272, pixel_bytes=4),
        extra_ram_bytes=len(elf) - len(source),
        checks=dict(existing_patch_code_and_assets='byte-identical', startup_logos_and_english_warning='byte-identical',
            original_scratch_size='0x88000 preserved', source_and_target_buffer_lifetime='native shared lifetime preserved',
            script_wording_controls_and_saves='unchanged', archive='title version only'),
        texture_replacement=False, footer=fr, runtime_verification='pending')
    return elf, ore, preview, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    elf, ore, preview, report = build()
    print(json.dumps({k: v for k, v in report.items() if k != 'footer'}, indent=2))
    if args.write:
        folder = ROOT / ('work/output/english-native-' + V)
        folder.mkdir(exist_ok=True)
        assert not (folder / 'EBOOT.scratch.elf').exists()
        (folder / 'EBOOT.scratch.elf').write_bytes(elf)
        (folder / 'data.scratch.ore').write_bytes(ore)
        (folder / 'scratch.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        ui = ROOT / ('work/ui/boot-scratch-' + V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')

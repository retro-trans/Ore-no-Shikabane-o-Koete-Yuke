"""Build 0.2.52 with a contiguous static ELF; dry run unless --write.

The earlier two-segment image places segment one's source inside segment zero's
BSS clear range when the PSP loads the ELF in place. Embed that zero area in the
file and use one PT_LOAD. Loaded instructions, data and addresses stay identical.
The source-based loader model is not a physical-PSP or firmware-emulation test.
"""
import argparse
import json
import struct

from pack_hardware_eboot import ROOT, sha, pack as pack_executable, unpack, elf_segments
from build_latin_auto import footer
from build_menu_fixes import container, member, pack
from repack_text import root_entries, rebuild_ez, rebuild_root

V = '0.2.52'
PRIOR_ELF = 'e889461d7e2a7ab11ce9b32b3d12fed36c18219b49f0d6c63f1080330edc7dec'


def ideal_image(elf):
    segments = elf_segments(elf)
    base = segments[0][2]
    image = bytearray(max(s[2] + s[5] for s in segments) - base)
    for s in segments:
        start = s[2] - base
        image[start:start + s[4]] = elf[s[1]:s[1] + s[4]]
    return base, bytes(image)


def inplace_load(elf):
    """Model static ELF buffer at the first VA, forward memmove + per-segment BSS.

    See uOFW modulemgr.c _LoadModule and loadelf.c sceKernelLoadExecutableObject.
    Capture program headers first, as the loader saves segment descriptors before
    moving bytes. Python slice assignment models memmove, including self-overlap.
    """
    segments = elf_segments(elf)
    base, expected = ideal_image(elf)
    memory = bytearray(max(len(elf), len(expected)))
    memory[:len(elf)] = elf
    cleared_sources = []
    for i, s in enumerate(segments):
        dst = s[2] - base
        memory[dst:dst+s[4]] = memory[s[1]:s[1]+s[4]]
        lo, hi = dst+s[4], dst+s[5]
        for j, later in enumerate(segments[i+1:], i+1):
            overlap = max(0, min(hi, later[1]+later[4]) - max(lo, later[1]))
            if overlap:
                cleared_sources.append(dict(clearing_segment=i, unread_segment=j, bytes=overlap))
        memory[lo:hi] = bytes(hi-lo)
    actual = bytes(memory[:len(expected)])
    return dict(matches_intended_memory=actual == expected,
        actual_sha256=sha(actual), intended_sha256=sha(expected),
        unread_source_overlaps=cleared_sources,
        segment_results=[dict(index=i, matches=actual[s[2]-base:s[2]-base+s[4]] == elf[s[1]:s[1]+s[4]])
                         for i, s in enumerate(segments)]), actual


def contiguous_elf(source):
    assert sha(source) == PRIOR_ELF
    segments = elf_segments(source)
    assert len(segments) == 2 and segments[0][1] == 0x1000
    base, memory = ideal_image(source)
    phoff = struct.unpack_from('<I', source, 28)[0]
    shoff = struct.unpack_from('<I', source, 32)[0]
    shsize, shcount, strindex = struct.unpack_from('<HHH', source, 46)
    assert shsize == 40 and shcount == 24 and strindex == 23
    sections = [list(struct.unpack_from('<10I', source, shoff+i*40)) for i in range(shcount)]
    string_section = sections[strindex]
    names = source[string_section[4]:string_section[4]+string_section[5]]
    assert names[-1:] == b'\0'
    out = bytearray(source[:0x1000]) + memory
    # The ELF header is outside the loaded memory image.
    struct.pack_into('<H', out, 44, 1)
    out[phoff+32:phoff+64] = bytes(32)
    ph = list(segments[0]); ph[4] = ph[5] = len(memory)
    struct.pack_into('<8I', out, phoff, *ph)
    # Keep all original section names/addresses for debuggers and CFW inspection.
    # BSS is now explicit zero-filled file data. Move only non-loaded metadata.
    for section in sections:
        if section[2] & 2:
            if section[1] == 8:
                section[1] = 1
            section[4] = 0x1000 + section[3] - base
        else:
            assert section is sections[0] or section is string_section
    sections.append([len(names), 1, 7, segments[1][2],
                     0x1000+segments[1][2]-base, segments[1][4], 0, 0, 16, 0])
    names += b'.translation\0'
    out.extend(bytes((-len(out)) % 16))
    string_section[4], string_section[5] = len(out), len(names)
    out.extend(names)
    out.extend(bytes((-len(out)) % 16))
    struct.pack_into('<I', out, 32, len(out))
    struct.pack_into('<H', out, 48, len(sections))
    for section in sections:
        out.extend(struct.pack('<10I', *section))
    result = bytes(out)
    assert ideal_image(result) == (base, memory)
    assert struct.unpack_from('<I', source, 24) == struct.unpack_from('<I', result, 24)
    before, _ = inplace_load(source)
    after, actual = inplace_load(result)
    assert not before['matches_intended_memory'] and before['unread_source_overlaps']
    assert after['matches_intended_memory'] and not after['unread_source_overlaps']
    assert actual == memory
    return result, dict(before=before, after=after, runtime_base=hex(base),
        runtime_end=hex(base+len(memory)), runtime_bytes=len(memory),
        intended_memory_identical=True, source_elf_sha256=sha(source), elf_sha256=sha(result),
        old_elf_bytes=len(source), elf_bytes=len(result), segments_before=2, segments_after=1,
        scope='Source-based in-place loader model; not hardware verification')


def build():
    prior = ROOT/'work/output/english-native-0.2.51'
    source = unpack((prior/'EBOOT.hardware.bin').read_bytes())
    elf, model = contiguous_elf(source)
    executable, packing = pack_executable(elf, (ROOT/'work/source/iso/PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes())
    assert unpack(executable) == elf
    sfo = (prior/'PARAM.SFO').read_bytes()
    assert sha(sfo) == 'db6c717236c3ff5a96e1440d0290cbfc6cd1e522b2ea8f4b1dd19d3a3dacf52d'
    data = (prior/'data.hardware.ore').read_bytes()
    assert sha(data) == 'b5bcb5b3d9f0ff42bd7716aba84779600ed161264f47fc4cec2a6c6edeb4de75'
    original = (ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original); be, bend = root_entries(data)
    title_id = next(r[0] for r in oe if r[3] == 0x1E8000)
    tb = next(r[3] for r in be if r[0] == title_id)
    arc, _ = container(data, tb); oa, oe2 = container(original, 0x1E8000)
    title, preview, fr = footer(member(oa, oe2, 25), V)
    ore = rebuild_root(data, {tb:rebuild_ez(arc, {25:pack(title)})}, mutable=True)
    ae, aend = root_entries(ore)
    assert len(be) == len(ae)
    for i, (a, b) in enumerate(zip(be, ae)):
        ea = (be[i+1][3] if i+1<len(be) else bend) - (a[2]&2047)
        eb = (ae[i+1][3] if i+1<len(ae) else aend) - (b[2]&2047)
        aa, bb = data[a[3]:ea], ore[b[3]:eb]
        if a[3] != tb:
            assert aa == bb
        else:
            _, ar = container(aa, 0); _, br = container(bb, 0)
            assert len(ar) == len(br)
            for j, ((_, z, p, _), (_, zz, pp, _)) in enumerate(zip(ar, br)):
                if j != 25:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V, based_on='0.2.51', loader_model=model, packing=packing,
        executable_sha256=sha(executable), archive_sha256=sha(ore), archive_bytes=len(ore),
        sfo_sha256=sha(sfo), sfo_unchanged=True, runtime_code_data_addresses_unchanged=True,
        archive_changes='Title version only; all other members exact', footer=fr,
        hardware_verified=False, github_release=False)
    return elf, executable, ore, sfo, preview, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true'); args = ap.parse_args()
    elf, executable, ore, sfo, preview, report = build()
    print(json.dumps({k:v for k,v in report.items() if k!='footer'}, indent=2))
    if args.write:
        out = ROOT/('work/output/english-native-'+V)
        assert not out.exists(); out.mkdir()
        (out/'EBOOT.contiguous.elf').write_bytes(elf)
        (out/'EBOOT.hardware.bin').write_bytes(executable)
        (out/'data.hardware.ore').write_bytes(ore)
        (out/'PARAM.SFO').write_bytes(sfo)
        (out/'contiguous.report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        ui = ROOT/('work/ui/psp-contiguous-'+V); ui.mkdir(exist_ok=True)
        preview.save(ui/'native-footer.png')
    print('Written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

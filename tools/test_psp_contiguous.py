"""Regression controls for the PSP in-place loading failure; no files written."""
import json
import struct
from io import BytesIO
from elftools.elf.elffile import ELFFile
from build_psp_contiguous import ROOT, contiguous_elf, ideal_image, inplace_load
from pack_hardware_eboot import unpack, sha


def main():
    source = (ROOT/'work/output/english-native-0.2.49/EBOOT.market.elf').read_bytes()
    target, report = contiguous_elf(source)
    for path in ['work/source/EBOOT.decrypted.elf', 'work/source/pboot-analysis/EBOOT.update.elf']:
        control = (ROOT/path).read_bytes()
        assert inplace_load(control)[0]['matches_intended_memory'], path
    # Independent ELF parser: all PT_LOAD contents, entry, allocated sections,
    # import/export descriptors and zero-filled memory agree with the old image.
    old = ELFFile(BytesIO(source)); new = ELFFile(BytesIO(target))
    assert new.num_segments() == 1 and new.header.e_entry == old.header.e_entry
    base, expected = ideal_image(source)
    segment = next(new.iter_segments())
    assert segment.header.p_vaddr == base and segment.data() == expected
    assert segment.header.p_filesz == segment.header.p_memsz == len(expected)
    checked = 0
    for section in old.iter_sections():
        if section.header.sh_flags & 2:
            after = new.get_section_by_name(section.name)
            assert after.header.sh_addr == section.header.sh_addr
            assert after.header.sh_size == section.header.sh_size
            assert after.data() == section.data()
            checked += 1
    metadata = old.get_section_by_name('.rodata.sceModuleInfo')
    assert metadata.header.sh_offset == segment.header.p_paddr
    assert new.get_section_by_name('.translation').data() == list(old.iter_segments())[1].data()
    packed = (ROOT/'work/output/english-native-0.2.52/EBOOT.hardware.bin').read_bytes()
    assert unpack(packed) == target
    assert struct.unpack_from('<I', packed, 0x38)[0] == 0
    print(json.dumps(dict(result='PASS', controls=['original ISO ELF', 'supplied update ELF'],
        old_candidate_reproduces_source_erasure=not report['before']['matches_intended_memory'],
        new_candidate_preserves_entire_image=report['after']['matches_intended_memory'],
        allocated_sections_checked=checked, module_info_and_entry_unchanged=True,
        authenticated_round_trip=True, elf_sha256=sha(target), hardware_verified=False), indent=2))


if __name__ == '__main__':
    main()

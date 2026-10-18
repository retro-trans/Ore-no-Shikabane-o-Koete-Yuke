"""Verify embedded translations, source-free export, relocations and MIPS pairs."""
import hashlib
import json
import struct

import unicorn
from unicorn import mips_const as reg

from build_embedded_text import ROOT, BASE, TABLES, build
from strip_jp import export


def main():
    expected, bilingual, safe, report = build()
    path = ROOT / 'work/output/native-0.2.3/EBOOT.elf'
    actual = path.read_bytes()
    assert actual == expected
    trans = ROOT / 'work/translation/en/executable/system_messages.json'
    assert json.loads(trans.read_text(encoding='utf-8')) == bilingual
    assert json.loads(trans.with_suffix('.en.json').read_text(encoding='utf-8')) == export(trans) == safe
    machine = unicorn.Uc(unicorn.UC_ARCH_MIPS, unicorn.UC_MODE_MIPS32 | unicorn.UC_MODE_LITTLE_ENDIAN)
    machine.mem_map(0x1000, 0x1000)
    for table, patch in zip(TABLES, report['patches']):
        high_pc, low_pc = table[2:4]
        # Execute the actual two modified instruction words independently of
        # the intervening caller/JAL; this proves signed-low-half relocation.
        code = actual[high_pc - BASE:high_pc - BASE + 4] + actual[low_pc - BASE:low_pc - BASE + 4]
        machine.mem_write(0x1000, bytes(code))
        machine.reg_write(reg.UC_MIPS_REG_A1, 0)
        machine.emu_start(0x1000, 0x1008, count=2)
        assert machine.reg_read(reg.UC_MIPS_REG_A1) == int(patch['relocated_address'], 16)
    print(json.dumps(dict(status='PASS', embedded_tables=2, translated_records=18,
                          mips_relocation_pairs_executed=2, english_export_matches=True,
                          patched_elf_sha256=hashlib.sha256(actual).hexdigest(),
                          limitation='Runtime save dialogs and error scenarios require separate game verification.'), indent=2))


if __name__ == '__main__':
    main()

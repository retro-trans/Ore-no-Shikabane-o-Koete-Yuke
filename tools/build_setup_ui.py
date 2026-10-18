"""Build the standalone name prompts and native Gregorian date-cursor fix.

Reads the branded 0.2.8 candidates; never modifies earlier builds. Dry run first.
"""
import argparse
import hashlib
import json
import struct

import keystone

from catalog_text import ROOT, parse_mlt
from check_translation import tokens_equal
from repack_text import align, rebuild_mlt, rebuild_root, root_entries, u32
from strip_jp import export
from build_vwf import CODE, IMAGE, UVS, assemble_selector

VERSION='0.2.8'
BASE=0x08803000
ORIGINAL_ROOT=0x3B9800
BOUNDS=0x0882B764


def padded_selector():
    # The formatter pads %3d using U+00A0. It is spacing, not a Japanese
    # glyph: use the atlas's transparent space while preserving its advance.
    assembly=f'''
    .set noreorder
    lui $t0, 0x09af
    lw $v0, 0x54e4($t0)
    lw $t1, 0xd4($a0)
    beqz $t1, fallback
    move $t2, $t1
scan:
    lhu $t3, 4($t2)
    beqz $t3, remap
    addiu $t4, $zero, 160
    beq $t3, $t4, next
    addiu $t3, $t3, -32
    sltiu $t4, $t3, 95
    beqz $t4, fallback
    nop
next:
    b scan
    addiu $t2, $t2, 28
remap:
    move $t2, $t1
glyph:
    lhu $t3, 4($t2)
    beqz $t3, ready
    addiu $t4, $zero, 160
    bne $t3, $t4, mapped
    nop
    addiu $t3, $zero, 32
mapped:
    addiu $t3, $t3, -32
    sll $t3, $t3, 3
    li $t4, {UVS}
    addu $t4, $t4, $t3
    lw $t5, 0($t4)
    lw $t6, 4($t4)
    sw $t5, 0x10($t2)
    sw $t6, 0x14($t2)
    b glyph
    addiu $t2, $t2, 28
ready:
    li $v0, {IMAGE}
    addiu $t0, $zero, 1
    sb $t0, 0xc0($a0)
fallback:
    jr $ra
    nop
    '''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    return bytes(ks.asm(assembly,addr=CODE)[0])


def native_date(source):
    assert hashlib.sha256(source).hexdigest() == 'cfb4cc0f220e1dbfb9957f5eab6005c3a32aa534fc85cf8dab0ac923c0c52304'
    native=bytearray(source)
    phoff=u32(native,28)
    header=list(struct.unpack_from('<8I',native,phoff+32))
    assert header[0]==1 and header[1]+header[4]==len(native)
    code_offset=header[1]+CODE-header[2]
    old_selector=assemble_selector()
    assert native[code_offset:code_offset+len(old_selector)]==old_selector
    selector=padded_selector()
    assert len(selector)<=0x100
    native[code_offset:code_offset+len(selector)]=selector
    native.extend(bytes(align(len(native),16)-len(native)))
    address=header[2]+len(native)-header[1]
    assembly=f'''
    .set noreorder
    addiu $t0, $zero, 1
    bne $a2, $t0, tail
    nop
    addiu $a2, $zero, 3
tail:
    j {BOUNDS}
    nop
    '''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    wrapper=bytes(ks.asm(assembly,addr=address)[0])
    assert len(wrapper)==24
    native.extend(wrapper)
    patches=[(0x08970704,0x24100002,0x24100000),
             (0x08970714,0x24100002,0x24100000),
             (0x089708BC,0x02603821,0x96470000),
             (0x08970728,0x0C000000|(BOUNDS//4),0x0C000000|(address//4))]
    for pc,old,new in patches:
        assert u32(source,pc-BASE)==old,(hex(pc),hex(u32(source,pc-BASE)),hex(old))
        struct.pack_into('<I',native,pc-BASE,new)
    header[4]=header[5]=len(native)-header[1]
    struct.pack_into('<8I',native,phoff+32,*header)
    report=dict(input_sha256=hashlib.sha256(source).hexdigest(),output_sha256=hashlib.sha256(native).hexdigest(),
                bytes=len(native),extra_ram_bytes=len(native)-len(source),wrapper_address=hex(address),
                wrapper_bytes=len(wrapper),patches=[dict(address=hex(pc),before=hex(o),after=hex(n)) for pc,o,n in patches],
                date_format='YYYY/MM/DD',cursor_character_ranges=[[0,3],[5,6],[8,9]],
                font_selector=dict(address=hex(CODE),bytes=len(selector),alias='U+00A0 -> transparent native space UVs; original code, advance and destination quad preserved',
                                   atlas_and_width_table_unchanged=True,mixed_japanese_fallback_preserved=True),
                retained='Original Gregorian storage, input bounds, month/day validation and save format; native font atlas and metrics unchanged.')
    return bytes(native),report


def build():
    dest=ROOT/('work/output/english-native-'+VERSION)
    data=(dest/'data.branded.ore').read_bytes()
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    index=next(i for i,_,_,off in root_entries(original)[0] if off==ORIGINAL_ROOT)
    assert index==27
    entries,end=root_entries(data)
    n=next(n for n,r in enumerate(entries) if r[0]==index)
    _,_,packed,base=entries[n]
    stop=entries[n+1][3] if n+1<len(entries) else end
    old=data[base:stop-(packed&2047)]
    assert old==original[ORIGINAL_ROOT:ORIGINAL_ROOT+17856]
    working=ROOT/'work/translation/en/name_entry/prompts.json'
    safe=ROOT/'work/translation/en/name_entry/prompts.en.json'
    assert export(working)==json.loads(safe.read_text(encoding='utf-8'))
    batch=json.loads(working.read_text(encoding='utf-8'))
    records=list(parse_mlt(old));lookup={(s,i):t for s,i,_,t in records}
    changes={}
    for r in batch['rows']:
        key=(r['section'],r['index']);jp=lookup[key];en=r['translation_en']
        assert key[0]==0 and jp==r['source_jp']
        assert hashlib.sha256(jp.encode()).hexdigest()==r['source_sha256']
        assert tokens_equal(jp,en) and jp.count('\n')==en.count('\n')
        changes[key]=en
    assert len(changes)==14
    new=rebuild_mlt(old,changes)
    after={(s,i):t for s,i,_,t in parse_mlt(new)}
    assert all(after[s,i]==t for s,i,_,t in records if s>0)
    output=rebuild_root(data,{base:new})
    elf,elf_report=native_date((dest/'EBOOT.elf').read_bytes())
    report=dict(version=VERSION,additional_ui_prompts=14,player_name_pool_records_retained=1735,
                raw_root_index=27,original_offset=hex(ORIGINAL_ROOT),original_mlt_bytes=len(old),new_mlt_bytes=len(new),
                input_archive_sha256=hashlib.sha256(data).hexdigest(),output_archive_sha256=hashlib.sha256(output).hexdigest(),
                output_archive_bytes=len(output),native_date=elf_report,texture_replacement=False,
                checks='14 source identities, controls, row/line counts; all 1735 name-pool entries unchanged; MLT round trip; guarded MIPS patches.',
                runtime_verification='pending')
    return output,elf,report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    output,elf,report=build()
    print(json.dumps(report,indent=2))
    if args.write:
        dest=ROOT/('work/output/english-native-'+VERSION)
        for p in [dest/'data.setup.ore',dest/'EBOOT.setup.elf']:
            if p.exists():raise FileExistsError(p)
        (dest/'data.setup.ore').write_bytes(output)
        (dest/'EBOOT.setup.elf').write_bytes(elf)
        (dest/'setup.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Setup fixes written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()

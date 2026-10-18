"""Render fullwidth Latin names with the existing native 4x VWF atlas."""
import hashlib
import struct

import keystone

BASE=0x08803000
HOOK=0x089BA6EC
FONT_SERVICE=0x0896B10C


def patch(source):
    elf=bytearray(source)
    assert struct.unpack_from('<3I',elf,HOOK-BASE)==(0x3252FFFF,0x0C000000|(FONT_SERVICE>>2),0x3250FFFF)
    phoff=struct.unpack_from('<I',elf,28)[0]
    ph=list(struct.unpack_from('<8I',elf,phoff+32))
    assert ph[0]==1 and ph[1]+ph[4]==len(elf)
    elf.extend(bytes((-len(elf))%16))
    cave=ph[2]+len(elf)-ph[1]
    assembly=f'''.set noreorder
        andi $s2, $s2, 0xffff
        ori $t0, $zero, 0xff01
        subu $t1, $s2, $t0
        sltiu $t1, $t1, 94
        beqz $t1, space
        ori $t0, $zero, 0xfee0
        b tail
        subu $s2, $s2, $t0
    space:
        ori $t0, $zero, 0x3000
        bne $s2, $t0, tail
        nop
        addiu $s2, $zero, 32
    tail:
        j {FONT_SERVICE}
        nop
    '''
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    code=bytes(ks.asm(assembly,addr=cave)[0]);elf.extend(code)
    # The original delay-slot assignment to s0 executes after the font
    # service returns. The service has no character argument and preserves
    # s0, so width/spacing calls still receive the canonical character.
    struct.pack_into('<2I',elf,HOOK-BASE,0x0C000000|(cave>>2),0)
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph)
    allowed=set(range(HOOK-BASE,HOOK-BASE+8))|set(range(phoff+32+16,phoff+32+24))
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    return bytes(elf),dict(hook=hex(HOOK),wrapper=hex(cave),wrapper_bytes=len(code),
                           extra_ram_bytes=len(elf)-len(source),
                           normalization='U+FF01..U+FF5E to ASCII; U+3000 to space, before glyph measurement',
                           stored_names='unchanged',font_atlas='existing native 4x atlas unchanged',
                           sha256=hashlib.sha256(elf).hexdigest())

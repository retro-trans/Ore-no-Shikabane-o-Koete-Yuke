"""Eight printable ASCII characters in the original eight-byte name record.

Legacy UCS-2 names remain unchanged. Long names use a reserved surrogate
header, a three-bit length and 56 payload bits (eight seven-bit characters).
Wide-string operations decode these records before measuring/copying text.
"""
import struct
import keystone

BASE=0x08803000


def encode_reference(text):
    if not 4<=len(text)<=8 or any(not 32<=ord(c)<=126 for c in text) or not text.strip():
        raise ValueError('Long names require 4..8 printable ASCII characters')
    bits=sum(ord(c)<<(7*i) for i,c in enumerate(text))
    return struct.pack('<H',0xD800|((len(text)-1)<<8)|(bits&255))+(bits>>8).to_bytes(6,'little')


def decode_reference(raw):
    head=struct.unpack_from('<H',raw)[0]
    if head&0xF800!=0xD800 or (head>>8&7)<3:return None
    bits=(head&255)|(int.from_bytes(raw[2:8],'little')<<8)
    return ''.join(chr(bits>>(7*i)&127) for i in range((head>>8&7)+1))


def patch(source):
    elf=bytearray(source);phoff=struct.unpack_from('<I',elf,28)[0]
    ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    addresses={};patches=[]
    def emit(name,asm):
        elf.extend(bytes((-len(elf))%16));addr=ph[2]+len(elf)-ph[1]
        code=bytes(ks.asm('.set noreorder\n'+asm,addr=addr)[0]);elf.extend(code)
        addresses[name]=addr;return addr
    def words(pc,new,note):
        old=struct.unpack_from('<'+'I'*len(new),elf,pc-BASE)
        struct.pack_into('<'+'I'*len(new),elf,pc-BASE,*new)
        patches.append(dict(address=hex(pc),before=[hex(w) for w in old],after=[hex(w) for w in new],purpose=note))
    def jump(pc,target,note):words(pc,[0x08000000|(target>>2),0],note)
    def call(pc,target,note):words(pc,[0x0C000000|(target>>2)],note)

    # State = source pointer, remaining packed chars, packed field pointer,
    # index (bit 31 remembers a preceding literal prefix). A leading encoded
    # name is a bounded stand-alone string, even with no trailing UCS-2 NUL.
    nxt=emit('next_char','''
        lw $t0, 4($a0)
        bnez $t0, packed
        nop
        lw $t1, 0($a0)
        beqz $t1, end
        nop
        lhu $v0, 0($t1)
        andi $t2, $v0, 0xf800
        ori $t3, $zero, 0xd800
        bne $t2, $t3, ordinary
        nop
        srl $t2, $v0, 8
        andi $t2, $t2, 7
        sltiu $t3, $t2, 3
        bnez $t3, ordinary
        nop
        addiu $t0, $t2, 1
        sw $t0, 4($a0)
        sw $t1, 8($a0)
        lw $t3, 12($a0)
        srl $t3, $t3, 31
        sll $t3, $t3, 31
        sw $t3, 12($a0)
        addiu $t1, $t1, 8
        bnez $t3, has_prefix
        nop
        move $t1, $zero
    has_prefix:
        sw $t1, 0($a0)
    packed:
        lw $t1, 8($a0)
        lw $t2, 12($a0)
        sll $t3, $t2, 1
        srl $t3, $t3, 1
        sll $t4, $t3, 3
        subu $t4, $t4, $t3
        srl $t5, $t4, 3
        andi $t4, $t4, 7
        move $t6, $t5
        beqz $t5, low_byte
        nop
        addiu $t6, $t6, 1
    low_byte:
        addu $t6, $t6, $t1
        lbu $v0, 0($t6)
        sltiu $t6, $t5, 6
        beqz $t6, combine
        nop
        addiu $t5, $t5, 2
        addu $t5, $t5, $t1
        lbu $t6, 0($t5)
        sll $t6, $t6, 8
        or $v0, $v0, $t6
    combine:
        srlv $v0, $v0, $t4
        andi $v0, $v0, 127
        addiu $t5, $zero, 32
        bne $v0, $t5, wide_latin
        ori $t6, $zero, 0xfee0
        b wide_ready
        ori $v0, $zero, 0x3000
    wide_latin:
        addu $v0, $v0, $t6
    wide_ready:
        addiu $t2, $t2, 1
        sw $t2, 12($a0)
        addiu $t0, $t0, -1
        jr $ra
        sw $t0, 4($a0)
    ordinary:
        addiu $t1, $t1, 2
        sw $t1, 0($a0)
        lui $t2, 0x8000
        jr $ra
        sw $t2, 12($a0)
    end:
        jr $ra
        move $v0, $zero
    ''')
    # Wrapper frame: two 16-byte iterator states and normal callee-save slots.
    pro='''addiu $sp, $sp, -96
        sw $ra, 92($sp)
        sw $s0, 88($sp)
        sw $s1, 84($sp)
        sw $s2, 80($sp)
        sw $s3, 76($sp)
        sw $s4, 72($sp)
        sw $s5, 68($sp)
        sw $a0, 64($sp)
        sw $a1, 60($sp)
        sw $a2, 56($sp)
        sw $a3, 52($sp)
    '''
    epi='''lw $ra, 92($sp)
        lw $s0, 88($sp)
        lw $s1, 84($sp)
        lw $s2, 80($sp)
        lw $s3, 76($sp)
        lw $s4, 72($sp)
        lw $s5, 68($sp)
        jr $ra
        addiu $sp, $sp, 96
    '''
    def init(reg,offset=0):return f'''sw ${reg}, {offset}($sp)
        sw $zero, {offset+4}($sp)
        sw $zero, {offset+8}($sp)
        sw $zero, {offset+12}($sp)
    '''
    length=emit('length',pro+init('a0')+f'''
        move $s0, $zero
    loop:
        jal {nxt}
        move $a0, $sp
        beqz $v0, done
        nop
        b loop
        addiu $s0, $s0, 1
    done:
        move $v0, $s0
        lw $a0, 64($sp)
    '''+epi)
    jump(0x089AA690,length,'Bounded logical length for packed names and ordinary UCS-2')

    def copy_wrapper(name,bounded=False,counted=False):
        setup=pro+'''move $s0, $a0
            move $s1, $a0
        '''+init('a2' if bounded else 'a1')
        if bounded:
            # The existing name setters explicitly copy eight-byte records.
            # Preserve those bytes, rather than expanding into adjacent data.
            setup+=('''addiu $t0, $zero, 8
                bne $a1, $t0, text_copy
                nop
                lhu $t0, 0($a2)
                andi $t1, $t0, 0xf800
                ori $t2, $zero, 0xd800
                bne $t1, $t2, text_copy
                nop
                srl $t0, $t0, 8
                andi $t0, $t0, 7
                sltiu $t1, $t0, 3
                bnez $t1, text_copy
                nop
                lhu $t0, 0($a2)
                lhu $t1, 2($a2)
                lhu $t2, 4($a2)
                lhu $t3, 6($a2)
                sh $t0, 0($s0)
                sh $t1, 2($s0)
                sh $t2, 4($s0)
                b done
                sh $t3, 6($s0)
            text_copy:
            ''' if not counted else '')+'''sra $s2, $a1, 1
                addiu $s2, $s2, -1
            '''
            if counted:setup+='''slt $t0, $a3, $s2
                movn $s2, $a3, $t0
            '''
        else:setup+='li $s2, 0x7fffffff\n'
        code=setup+f'''
        blez $s2, finish
        nop
    loop:
        jal {nxt}
        move $a0, $sp
        beqz $v0, finish
        nop
        sh $v0, 0($s1)
        addiu $s2, $s2, -1
        bgtz $s2, loop
        addiu $s1, $s1, 2
    finish:
        sh $zero, 0($s1)
    done:
        move $v0, $s0
        move $a0, $s0
        lw $a2, 56($sp)
    '''+epi
        return emit(name,code)
    copy=copy_wrapper('bounded_copy',True)
    ncopy=copy_wrapper('counted_copy',True,True)
    jump(0x089AA6B8,copy,'Decode long names into bounded text buffers; eight-byte record copies remain packed')
    jump(0x089AA700,ncopy,'Decode long names for counted UCS-2 copies')
    # This routine converts UCS-2 to the game's byte encoding, rather than
    # copying UCS-2. Only intercept packed ASCII names; ordinary strings must
    # retain the original converter and its one-/two-byte output contract.
    convert=emit('legacy_bytes',pro+'''move $s0, $a0
        move $s1, $a0
        lhu $t0, 0($a1)
        andi $t1, $t0, 0xf800
        ori $t2, $zero, 0xd800
        bne $t1, $t2, ordinary_conversion
        nop
        srl $t0, $t0, 8
        andi $t0, $t0, 7
        sltiu $t1, $t0, 3
        bnez $t1, ordinary_conversion
        nop
        beqz $s0, converted
        nop
    '''+init('a1')+f'''
    loop:
        jal {nxt}
        move $a0, $sp
        beqz $v0, finish
        nop
        jal 0x089ab288
        move $a0, $v0
        sltiu $t0, $v0, 256
        bnez $t0, one_byte
        srl $t1, $v0, 8
        sb $t1, 0($s1)
        addiu $s1, $s1, 1
    one_byte:
        sb $v0, 0($s1)
        b loop
        addiu $s1, $s1, 1
    finish:
        sb $zero, 0($s1)
    converted:
        move $v0, $zero
    '''+epi+'''
    ordinary_conversion:
        lw $a0, 64($sp)
        lw $a1, 60($sp)
        lw $ra, 92($sp)
        lw $s0, 88($sp)
        lw $s1, 84($sp)
        lw $s2, 80($sp)
        lw $s3, 76($sp)
        lw $s4, 72($sp)
        lw $s5, 68($sp)
        addiu $sp, $sp, 96
        addiu $sp, $sp, -16
        sw $s1, 4($sp)
        j 0x089ab218
        nop
    ''')
    jump(0x089AB210,convert,'Decode packed names into original fullwidth legacy bytes; preserve the original converter for ordinary strings')

    # Names are also passed as literal format strings. Such records have no
    # UCS-2 terminator; stop at the encoded length instead of reading the
    # next save field. Ordinary formats retain their exact original entry.
    literal=emit('literal_format',pro+'''move $s0, $a0
        move $s1, $a0
        sra $s2, $a1, 1
        addiu $s2, $s2, -1
        move $s3, $zero
    '''+init('a2')+f'''
        blez $s2, finish
        nop
    loop:
        jal {nxt}
        move $a0, $sp
        beqz $v0, finish
        nop
        sh $v0, 0($s1)
        addiu $s3, $s3, 1
        addiu $s1, $s1, 2
        addiu $s2, $s2, -1
        bgtz $s2, loop
        nop
    finish:
        sh $zero, 0($s1)
        move $v0, $s3
    '''+epi)
    for name,pc,replay in [
        ('game_format_entry',0x08969A30,'srl $a1, $a1, 1\nsll $a1, $a1, 1\naddu $a1, $a0, $a1'),
        ('wide_format_entry',0x089AA7AC,'addiu $sp, $sp, -48\nsw $a3, 28($sp)')]:
        entry=emit(name,f'''
            lhu $v0, 0($a2)
            andi $v1, $v0, 0xf800
            xori $v1, $v1, 0xd800
            bnez $v1, ordinary
            srl $v0, $v0, 8
            andi $v0, $v0, 7
            sltiu $v1, $v0, 3
            bnez $v1, ordinary
            nop
            j {literal}
            nop
        ordinary:
            {replay}
            j {pc+8}
            nop
        ''')
        jump(pc,entry,'Bound packed literal names before format parsing; preserve ordinary formats and all varargs')

    compare=emit('compare',pro+init('a0')+init('a1',16)+f'''
    loop:
        jal {nxt}
        move $a0, $sp
        move $s0, $v0
        jal {nxt}
        addiu $a0, $sp, 16
        subu $v0, $s0, $v0
        bnez $v0, done
        nop
        bnez $s0, loop
        nop
    done:
    '''+epi)
    jump(0x089AB0A8,compare,'Compare complete logical names, including their last characters')
    cat=emit('concatenate',pro+'''move $s0, $a0
        move $s1, $a0
    scan:
        lhu $t0, 0($s1)
        bnez $t0, scan
        addiu $s1, $s1, 2
        addiu $s1, $s1, -2
    '''+init('a1')+f'''
    loop:
        jal {nxt}
        move $a0, $sp
        beqz $v0, done
        nop
        sh $v0, 0($s1)
        b loop
        addiu $s1, $s1, 2
    done:
        sh $zero, 0($s1)
        move $v0, $s0
        move $a0, $s0
    '''+epi)
    jump(0x089AA75C,cat,'Append decoded names to allocated UCS-2 strings')

    # The printf string handler reads characters itself, so give it an
    # iterator in its own enlarged stack frame. No global scratch buffers.
    fmt_init=emit('printf_init',f'''
        addiu $sp, $sp, -16
        sw $ra, 12($sp)
        sw $s1, 32($sp)
        sw $zero, 36($sp)
        sw $zero, 40($sp)
        sw $zero, 44($sp)
        jal {length}
        nop
        lw $ra, 12($sp)
        jr $ra
        addiu $sp, $sp, 16
    ''')
    save_regs=['a0','a1','a2','a3','v1']+['t'+str(i) for i in range(10)]+['ra']
    fmt_get='addiu $sp, $sp, -80\n'+''.join(f'sw ${reg}, {i*4}($sp)\n' for i,reg in enumerate(save_regs))
    fmt_get+=f'jal {nxt}\naddiu $a0, $sp, 96\n'
    fmt_get+=''.join(f'lw ${reg}, {i*4}($sp)\n' for i,reg in enumerate(save_regs))+'jr $ra\naddiu $sp, $sp, 80\n'
    fmt_get_addr=emit('printf_char',fmt_get)
    words(0x089AACF8,[0x27BDFFD0],'Add a local iterator to the printf string-handler frame')
    words(0x089AAE30,[0x27BD0030],'Restore the enlarged printf string-handler frame')
    call(0x089AAD34,fmt_init,'Measure and initialize the decoded printf string')
    call(0x089AADBC,fmt_get_addr,'Read a complete logical character in the printf string loop')
    words(0x0896A0A0,[0x27BDFFD0],'Add a local iterator to the game control-code string handler')
    words(0x0896A1CC,[0x27BD0030],'Restore the enlarged game string-handler frame')
    call(0x0896A0D0,fmt_init,'Initialize the decoded game-format string iterator')
    call(0x0896A158,fmt_get_addr,'Read decoded names in game script substitutions')

    # Input conversion: short/Japanese names retain the original conversion;
    # long printable Latin strings become one bounded eight-byte record.
    encode=emit('encode',pro+'''move $s0, $a0
        move $s1, $a1
        lhu $t0, 0($s1)
        andi $t1, $t0, 0xf800
        ori $t2, $zero, 0xd800
        bne $t1, $t2, count
        nop
        srl $t1, $t0, 8
        andi $t1, $t1, 7
        sltiu $t2, $t1, 3
        beqz $t2, copy_existing
        nop
    count:
        move $s2, $zero
        move $t0, $s1
    count_loop:
        lhu $t1, 0($t0)
        beqz $t1, counted
        nop
        addiu $s2, $s2, 1
        sltiu $t2, $s2, 9
        beqz $t2, invalid
        addiu $t0, $t0, 2
        b count_loop
        nop
    counted:
        sltiu $t0, $s2, 4
        bnez $t0, legacy
        nop
        sw $zero, 32($sp)
        sw $zero, 36($sp)
        addiu $t0, $s2, -1
        sll $t0, $t0, 8
        ori $t0, $t0, 0xd800
        sh $t0, 32($sp)
        move $s3, $zero
        move $s4, $zero
    encode_loop:
        sll $t0, $s4, 1
        addu $t0, $t0, $s1
        lhu $t1, 0($t0)
        ori $t2, $zero, 0xff01
        subu $t3, $t1, $t2
        sltiu $t3, $t3, 94
        beqz $t3, wide_space
        ori $t2, $zero, 0xfee0
        b normalized
        subu $t1, $t1, $t2
    wide_space:
        ori $t2, $zero, 0x3000
        bne $t1, $t2, normalized
        nop
        addiu $t1, $zero, 32
    normalized:
        addiu $t2, $t1, -32
        sltiu $t2, $t2, 95
        beqz $t2, invalid
        addiu $t2, $zero, 32
        beq $t1, $t2, position
        nop
        addiu $s3, $zero, 1
    position:
        sll $t2, $s4, 3
        subu $t2, $t2, $s4
        srl $t3, $t2, 3
        andi $t2, $t2, 7
        sllv $t1, $t1, $t2
        move $t4, $t3
        beqz $t3, byte_offset
        nop
        addiu $t4, $t4, 1
    byte_offset:
        addiu $t5, $sp, 32
        addu $t4, $t4, $t5
        lbu $t6, 0($t4)
        or $t6, $t6, $t1
        sb $t6, 0($t4)
        sltiu $t4, $t3, 6
        beqz $t4, next
        nop
        addiu $t3, $t3, 2
        addu $t3, $t3, $t5
        lbu $t4, 0($t3)
        srl $t1, $t1, 8
        or $t4, $t4, $t1
        sb $t4, 0($t3)
    next:
        addiu $s4, $s4, 1
        slt $t0, $s4, $s2
        bnez $t0, encode_loop
        nop
        beqz $s3, invalid
        nop
        lw $t0, 32($sp)
        lw $t1, 36($sp)
        sw $t0, 0x4e50($s0)
        b update
        sw $t1, 0x4e54($s0)
    copy_existing:
        lhu $t0, 0($s1)
        lhu $t1, 2($s1)
        lhu $t2, 4($s1)
        lhu $t3, 6($s1)
        sh $t0, 0x4e50($s0)
        sh $t1, 0x4e52($s0)
        sh $t2, 0x4e54($s0)
        sh $t3, 0x4e56($s0)
    update:
        jal 0x08976ce8
        move $a0, $s0
        b complete
        nop
    invalid:
        move $a0, $s0
        jal 0x08977000
        addiu $a1, $zero, 4
        move $a0, $v0
        addiu $a1, $zero, 1
        jal 0x0882491c
        move $a2, $zero
    complete:
    '''+epi+'''
    legacy:
        lw $a0, 64($sp)
        lw $a1, 60($sp)
        lw $ra, 92($sp)
        lw $s0, 88($sp)
        lw $s1, 84($sp)
        lw $s2, 80($sp)
        lw $s3, 76($sp)
        lw $s4, 72($sp)
        lw $s5, 68($sp)
        addiu $sp, $sp, 96
        addiu $sp, $sp, -32
        sw $ra, 16($sp)
        j 0x08976d40
        nop
    ''')
    jump(0x08976D38,encode,'Preserve short names; encode 4..8 printable English characters without changing record size')
    words(0x089768A8,[0x24050008],'Request up to eight OSK characters for player names')
    words(0x08976CA4,[0x240500F8],'Widen the name-entry value window to 248 pixels')
    words(0x08976CC8,[0x24050074],'Center the wider name-entry value window at x=116')
    for pc in (0x088FCDC0,0x088FD110):
        assert struct.unpack_from('<I',elf,pc-BASE)[0]==0x24060057
        words(pc,[0x24060063],'Place portrait-card age below the name on its own row')
    for pc in (0x088FCDF8,0x088FD148):
        assert struct.unpack_from('<I',elf,pc-BASE)[0]==0x24060068
        words(pc,[0x24060074],'Extend portrait-card frame to contain the separate age row')
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph)
    return bytes(elf),dict(encoding='Reserved UCS-2 surrogate header + length + 56 ASCII payload bits; original eight-byte record size',
                           maximum_english_characters=8,maximum_japanese_characters=3,
                           decoded_game_text='Fullwidth Latin as in original short names; prevents name punctuation becoming formatting/control syntax',
                           existing_saves='Legacy names unchanged; long-name saves require this patch or newer',
                           extra_ram_bytes=len(elf)-len(source),functions={k:hex(v) for k,v in addresses.items()},patches=patches)

"""Native high-resolution PPT sprites with original logical geometry and UV crops."""
import hashlib,struct
import keystone,numpy as np
from PIL import Image
from inspect_native_textures import decode
BASE=0x08803000;TAG=0x00444834;PROXY_TAG=0x00585048
BIND=0x089B95EC;RECT=0x089B9620

def encode(original,image,pixel_format=5):
    _,old=decode(original);ow,oh=old['logical_width'],old['logical_height']
    w,h=image.size;assert w<=512 and h<=512 and w%16==0 and h%8==0
    pw=round(ow*w/old['width']);ph=round(oh*h/old['height'])
    assert pixel_format in (4,5)
    colors=16 if pixel_format==4 else 240
    q=image.convert('RGBA').quantize(colors=colors,method=Image.Quantize.FASTOCTREE)
    indices=np.asarray(q,dtype=np.uint8);assert indices.max()<colors
    if pixel_format==4:
        assert w%32==0
        indices=indices[:,::2] | (indices[:,1::2]<<4)
    stride=indices.shape[1]
    pixels=indices.reshape(h//8,8,stride//16,16).transpose(0,2,1,3).tobytes()
    pal=bytearray(q.getpalette('RGBA'));pal.extend(bytes(1024-len(pal)))
    for index,value in [(251,pw),(252,ph),(253,ow),(254,oh),(255,TAG)]:struct.pack_into('<I',pal,index*4,value)
    head=bytearray(original[:32]);tw=1<<(w-1).bit_length();th=1<<(h-1).bit_length()
    struct.pack_into('<8H',head,4,tw,th,pixel_format,1,w,h,pw,ph);struct.pack_into('<I',head,24,32+len(pixels))
    ppc=struct.pack('<4sHHII',b'ppc\0',3,32,0,0)
    out=bytes(head)+pixels+ppc+bytes(pal)
    actual,info=decode(out);assert actual.size==image.size and info['logical_width']==pw and info['logical_height']==ph
    return out,actual,dict(logical_size=[ow,oh],physical_storage_size=[w,h],physical_visible_size=[pw,ph],
                           scale=[pw/ow,ph/oh],native_texture=[tw,th],bytes=len(out),sha256=hashlib.sha256(out).hexdigest())

def proxy(original,address):
    # Keep each archive resource within its original loader budget. The real
    # HD descriptor/pixels live once in the executable's native asset segment.
    im,_=decode(original);out,_,_=encode(original,im)
    out=bytearray(out);po=struct.unpack_from('<I',out,24)[0]
    struct.pack_into('<I',out,po+16+251*4,address)
    struct.pack_into('<I',out,po+16+255*4,PROXY_TAG)
    return bytes(out)

def patch(source,assets=()):
    elf=bytearray(source);p=struct.unpack_from('<I',elf,28)[0];ph=list(struct.unpack_from('<8I',elf,p+32));assert ph[1]+ph[4]==len(elf)
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    changes=[];embedded=[];asset_cache={}
    def reserve(b):
        elf.extend(bytes((-len(elf))%16));addr=ph[2]+len(elf)-ph[1];elf.extend(b);return addr
    for ppt in assets:
        key=hashlib.sha256(ppt).digest()
        if key in asset_cache:
            embedded.append(asset_cache[key]);continue
        po=struct.unpack_from('<I',ppt,24)[0]
        desc=reserve(bytes(48));palette=reserve(ppt[po:po+1040]);pixels=reserve(ppt[32:po])
        off=desc- ph[2]+ph[1];head=bytearray(32)
        head[4:20]=ppt[4:20]
        tw,th=struct.unpack_from('<2H',head,4)
        head[28:30]=bytes([tw.bit_length()-1,th.bit_length()-1])
        elf[off:off+32]=head
        struct.pack_into('<III',elf,off+32,pixels,palette,pixels)
        struct.pack_into('<I',elf,palette-ph[2]+ph[1]+8,palette+16)
        embedded.append(desc)
        asset_cache[key]=desc
    def emit(code):
        elf.extend(bytes((-len(elf))%16));addr=ph[2]+len(elf)-ph[1];b=bytes(ks.asm('.set noreorder\n'+code,addr=addr)[0]);elf.extend(b);return addr,len(b)
    # Palette slots251..255 are unused transparent metadata. Ordinary sprites
    # retain their complete original path. All logical geometry stays native.
    def guard(ptr,allow_proxy=False):
        redirect=f'''
        li $t3, {PROXY_TAG}
        bne $t2, $t3, check_hd
        nop
        lw $a1, 1004($t1)
        lw $t1, 0x24($a1)
        lw $t1, 8($t1)
        lw $t2, 1020($t1)
    check_hd:
        ''' if allow_proxy else ''
        return f'''
        beqz {ptr}, original
        nop
        lhu $t2, 8({ptr})
        andi $t2, $t2, 0xfffe
        li $t3, 4
        bne $t2, $t3, original
        nop
        lw $t1, 0x24({ptr})
        beqz $t1, original
        nop
        lhu $t2, 4($t1)
        li $t3, 3
        bne $t2, $t3, original
        nop
        lhu $t2, 6($t1)
        li $t3, 32
        bne $t2, $t3, original
        nop
        lw $t1, 8($t1)
        beqz $t1, original
        nop
        lw $t2, 1020($t1)
        {redirect}
        li $t3, {TAG}
        bne $t2, $t3, original
        nop
    '''
    bind,nb=emit(guard('$a1',True)+f'''
        lhu $t2, 1012($t1)
        lhu $t3, 1016($t1)
        sh $t2, 0x10($a1)
        sh $t3, 0x12($a1)
    original:
        move $v1, $a1
        j {BIND+8}
        addiu $sp, $sp, -16
    ''')
    # UV inputs are source-pixel coordinates. Recompute from those inputs on
    # every call, avoiding cumulative scaling when a widget changes its crop.
    uv='''lw $t4, 1004($t1)
        lw $t5, 1008($t1)
        lw $t2, 1012($t1)
        lw $t3, 1016($t1)
    '''
    for reg,physical,logical in [('$a1','$t4','$t2'),('$a3','$t4','$t2'),('$a2','$t5','$t3'),('$t0','$t5','$t3')]:
        uv+=f'''multu {reg}, {physical}
        mflo $t6
        divu $zero, $t6, {logical}
        mflo {reg}
        '''
    rect,nr=emit('lw $t7, 0xbc($a0)\n'+guard('$t7')+uv+f'''
    original:
        li $v0, 1
        sb $v0, 0xcc($a0)
        j {RECT+8}
        nop
    ''')
    allowed=set(range(p+48,p+56))
    for addr,old,new,n in [(BIND,(0x00a01821,0x27bdfff0),bind,nb),(RECT,(0x24020001,0xa08200cc),rect,nr)]:
        off=addr-BASE;assert struct.unpack_from('<2I',elf,off)==old
        struct.pack_into('<2I',elf,off,0x08000000|(new>>2),0);allowed.update(range(off,off+8))
        changes.append(dict(address=hex(addr),wrapper=hex(new),wrapper_bytes=n,before=list(old)))
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,p+32,*ph)
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    return elf,dict(hooks=changes,tag=hex(TAG),proxy_tag=hex(PROXY_TAG),embedded_descriptors=embedded,geometry='Original logical dimensions; UV crops mapped to HD pixels',
                    texture_replacement=False,untagged_images='Unchanged',metadata_palette_entries=[251,252,253,254,255])

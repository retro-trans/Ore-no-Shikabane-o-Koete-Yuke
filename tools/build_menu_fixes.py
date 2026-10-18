"""Native menu layout and Portrait Studio artwork fixes for local build 0.2.9.

Dry run by default. Earlier build files are immutable inputs.
"""
import argparse
import hashlib
import json
import struct
import zlib

import numpy as np
import keystone
from PIL import Image, ImageDraw, ImageFont

from catalog_text import ROOT, unpack_member
from repack_text import align, rebuild_ez, rebuild_root, root_entries, u32
from inspect_native_textures import decode
from build_title_branding import footer

VERSION = '0.2.9'
BASE = 0x08803000
PATCHES = [
    (0x089756E0, 0x24040040, 0x24040100, 'Deity confirmation allocation: 64 to 256 bytes'),
    (0x08975718, 0x24050040, 0x24050100, 'Matching formatter capacity: 64 to 256 bytes'),
    (0x08901134, 0x24050040, 0x24050070, 'Character action cell: 64 to 112 pixels'),
    (0x0891F538, 0x24050030, 0x24050060, 'Home grid cell: 48 to 96 pixels'),
]


def pack(blob):
    z = zlib.compressobj(9, zlib.DEFLATED, -15)
    result = b'\x1f\x8b\x09\0' + struct.pack('<I', len(blob)) + z.compress(blob) + z.flush()
    assert unpack_member(result)[0] == blob
    return result


def container(data, base):
    count, alignment = struct.unpack_from('<II', data, base + 8)
    entries = [struct.unpack_from('<4I', data, base + 16 + i*16) for i in range(count)]
    end = align(max(p+s for _,s,p,_ in entries), alignment)
    return data[base:base+end], entries


def member(data, entries, entry):
    _, size, pos, _ = entries[entry]
    return unpack_member(data[pos:pos+size])[0]


def encode_native(blob, image, rectangle):
    """Quantize only the edited rectangle; retain all other source indices."""
    original, info = decode(blob)
    assert info['format'] == 5 and info['swizzled']
    width, height = original.size
    po = u32(blob, 24)
    assert struct.unpack_from('<H', blob, po+4)[0] == 3
    palette = np.frombuffer(blob[po+16:po+1040], dtype=np.uint8).reshape(256,4).astype(np.int32)
    pixels = bytearray(blob[32:po])
    x0,y0,x1,y1 = rectangle
    rgba = np.asarray(image)[y0:y1,x0:x1].reshape(-1,4).astype(np.int32)
    # Batch rows keep the nearest-palette calculation small.
    indices = np.concatenate([((chunk[:,None,:]-palette[None,:,:])**2).sum(2).argmin(1)
                              for chunk in np.array_split(rgba, max(1,len(rgba)//1024))]).astype(np.uint8)
    indices = indices.reshape(y1-y0,x1-x0)
    for y in range(y0,y1):
        for x in range(x0,x1):
            address = ((y//8)*(width//16)+x//16)*128+(y%8)*16+x%16
            pixels[address] = int(indices[y-y0,x-x0])
    result = blob[:32]+bytes(pixels)+blob[po:]
    actual, _ = decode(result)
    outside = np.ones((height,width), dtype=bool);outside[y0:y1,x0:x1] = False
    assert np.array_equal(np.asarray(actual)[outside], np.asarray(original)[outside])
    assert result[po:] == blob[po:]
    return result, actual


def banner(blob):
    original, _ = decode(blob)
    assert original.size == (480,160)
    edited = original.copy()
    scale = 4
    layer = Image.new('RGBA',(480*scale,160*scale))
    d = ImageDraw.Draw(layer)
    # A clean title plaque covers the complete original lettering. The
    # camera, projection beam and outer floral frame retain native pixels.
    d.rounded_rectangle((69*scale,10*scale,214*scale,147*scale),radius=9*scale,
                        fill=(95,21,48,255),outline=(185,153,89,255),width=scale)
    d.rounded_rectangle((72*scale,13*scale,211*scale,144*scale),radius=7*scale,
                        outline=(135,61,76,255),width=scale)
    font = ImageFont.truetype(str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf'), 25*scale)
    for label,y in [('FAMILY',61),('PHOTO',94)]:
        d.text((140*scale,y*scale),label,font=font,anchor='mm',fill='white',
               stroke_width=2*scale,stroke_fill=(20,8,15,255))
    edited.alpha_composite(layer.resize(edited.size,Image.Resampling.LANCZOS))
    return encode_native(blob,edited,(68,9,216,149))


def studio_heading(blob):
    original,_ = decode(blob)
    assert original.size == (48,264)
    edited = original.copy()
    # Reuse the native diamond pattern underneath the Japanese heading.
    edited.paste(original.crop((0,132,48,264)),(0,0))
    scale = 4
    layer = Image.new('RGBA',(264*scale,48*scale))
    d = ImageDraw.Draw(layer)
    font = ImageFont.truetype(str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf'),20*scale)
    d.text((132*scale,24*scale),'PORTRAIT STUDIO',font=font,anchor='mm',fill='white',
           stroke_width=scale,stroke_fill=(15,15,24,255))
    layer = layer.resize((264,48),Image.Resampling.LANCZOS).transpose(Image.Transpose.ROTATE_270)
    edited.alpha_composite(layer)
    return encode_native(blob,edited,(0,0,48,264))


def build():
    prior = ROOT/'work/output/english-native-0.2.8'
    source = (prior/'EBOOT.setup.elf').read_bytes()
    assert hashlib.sha256(source).hexdigest() == 'ca0b182e29396c03a1542d1731f2b2073eddc210541b724cef61592b5eb86753'
    elf = bytearray(source)
    for pc,old,new,note in PATCHES:
        assert u32(elf,pc-BASE) == old, (hex(pc),hex(u32(elf,pc-BASE)))
        struct.pack_into('<I',elf,pc-BASE,new)
    # Portrait Studio's dedicated parameter table, used by its two choices.
    assert struct.unpack_from('<11h',elf,0x08A37F80-BASE) == (2,1,4,2,128,16,10,10,10,10,0)
    struct.pack_into('<h',elf,0x08A37F88-BASE,248)
    # Set the home window's draw-list key before it is registered. Itsuka's
    # preview is key 0x8002; 0x8003 keeps the widened grid readable above it.
    # Service/confirmation windows at 0xBEFF and higher still appear on top.
    phoff = u32(elf,28)
    ph = list(struct.unpack_from('<8I',elf,phoff+32))
    assert ph[1]+ph[4] == len(elf)
    elf.extend(bytes(align(len(elf),16)-len(elf)))
    cave = ph[2]+len(elf)-ph[1]
    asm = '''.set noreorder
        ori $t0, $zero, 0x8003
        sw $t0, 0x30($s0)
        lw $ra, 0x10($sp)
        lw $s3, 0xc($sp)
        lw $s2, 8($sp)
        lw $s1, 4($sp)
        lw $s0, 0($sp)
        jr $ra
        addiu $sp, $sp, 0x20
    '''
    ks = keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    code = bytes(ks.asm(asm,addr=cave)[0])
    elf.extend(code)
    tail = [(0x0891F56C,0x8FBF0010,0x08000000|(cave//4),'Home constructor tail: draw key before registration'),
            (0x0891F570,0x8FB3000C,0,'Tail jump delay slot; original restore moved into wrapper')]
    for pc,old,new,note in tail:
        assert u32(elf,pc-BASE) == old
        struct.pack_into('<I',elf,pc-BASE,new)
    elf.extend(bytes(align(len(elf),16)-len(elf)))
    studio_cave = ph[2]+len(elf)-ph[1]
    studio_asm = '''.set noreorder
        li $t0, 0x08a37f80
        bne $s0, $t0, tail
        nop
        addiu $a2, $zero, 56
    tail:
        j 0x0882387c
        nop
    '''
    studio_code = bytes(ks.asm(studio_asm,addr=studio_cave)[0])
    elf.extend(studio_code)
    studio_hook = (0x08967564,0x0c000000|(0x0882387c//4),0x0c000000|(studio_cave//4),
                   'Portrait Studio choices 56 pixels lower, clear of the English banner')
    pc,old,new,_ = studio_hook
    assert u32(elf,pc-BASE) == old
    struct.pack_into('<I',elf,pc-BASE,new)
    ph[4] = ph[5] = len(elf)-ph[1]
    struct.pack_into('<8I',elf,phoff+32,*ph)

    data = (prior/'data.setup.ore').read_bytes()
    assert hashlib.sha256(data).hexdigest() == '0283f249293227f512eb88367658ae0e885f990a3119b5a1b7391b1d0157c7e2'
    original = (ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_ = root_entries(original);ne,_ = root_entries(data)
    current = {i:off for i,_,_,off in ne}
    def relocated(oldbase):
        return current[next(i for i,_,_,off in oe if off == oldbase)]
    previews = {};updates = {}
    artbase = relocated(0xB4A800)
    art,entries = container(data,artbase)
    assets = {}
    for entry,fn,name in [(12,banner,'family-photo'),(53,studio_heading,'portrait-studio')]:
        blob = member(art,entries,entry)
        result,preview = fn(blob)
        assets[entry] = pack(result);previews[name] = preview
    updates[artbase] = rebuild_ez(art,assets)

    titlebase = relocated(0x1E8000)
    title,entries = container(data,titlebase)
    origtitle,origentries = container(original,0x1E8000)
    new,preview,detail = footer(member(origtitle,origentries,25),VERSION)
    updates[titlebase] = rebuild_ez(title,{25:pack(new)})
    previews['title-footer'] = preview
    result = rebuild_root(data,updates)
    # Repacking changes offsets, never unrelated payloads or members.
    out_entries,out_end = root_entries(result)
    in_entries,in_end = root_entries(data)
    for n,(before,after) in enumerate(zip(in_entries,out_entries)):
        before_stop = in_entries[n+1][3] if n+1<len(in_entries) else in_end
        after_stop = out_entries[n+1][3] if n+1<len(out_entries) else out_end
        old = data[before[3]:before_stop-(before[2]&2047)]
        new = result[after[3]:after_stop-(after[2]&2047)]
        if before[3] not in updates:
            assert old == new
        else:
            _,old_rows = container(old,0)
            _,new_rows = container(new,0)
            changed = {12,53} if before[3] == artbase else {25}
            for j,((_,s,p,_),(_,ns,np_,_)) in enumerate(zip(old_rows,new_rows)):
                if j not in changed:assert old[p:p+s] == new[np_:np_+ns]
    allowed = {a-BASE+j for a,_,_,_ in PATCHES+tail+[studio_hook] for j in range(4)} | {0x08A37F88-BASE,0x08A37F89-BASE}
    allowed |= set(range(phoff+32+16,phoff+32+24))
    assert all(a == b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    report = dict(version=VERSION,texture_replacement=False,
                  source_version='0.2.8',new_script_translations=0,
                  patches=[dict(address=hex(a),before=hex(b),after=hex(c),purpose=d) for a,b,c,d in PATCHES+tail+[studio_hook]],
                  home_draw_order=dict(wrapper=hex(cave),bytes=len(code),sort_key='0x8003'),
                  studio_position=dict(wrapper=hex(studio_cave),bytes=len(studio_code),vertical_offset=56,
                                       other_menus_unchanged=True),extra_ram_bytes=len(elf)-len(source),
                  studio_cell=dict(address='0x08a37f88',before=128,after=248),
                  graphics=[dict(asset='219.ppt',entry=12,translation='Family Photo'),
                            dict(asset='260.ppt',entry=53,translation='Portrait Studio')],
                  elf_sha256=hashlib.sha256(elf).hexdigest(),archive_sha256=hashlib.sha256(result).hexdigest(),
                  elf_bytes=len(elf),archive_bytes=len(result),runtime_verification='pending')
    report['checks'] = dict(all_unrelated_root_payloads='byte-identical',
                            all_unrelated_archive_members='byte-identical',
                            executable_diff='seven guarded instructions, one guarded width field and a bounded segment extension only',
                            prior_font_date_name_prompts='preserved',native_palettes='preserved')
    return bytes(elf),result,previews,report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    ap.add_argument('--previews',action='store_true',help='Write asset previews only; no game outputs')
    args = ap.parse_args()
    elf,ore,previews,report = build()
    print(json.dumps(report,indent=2))
    if args.previews or args.write:
        dest = ROOT/'work/ui/menu-fixes-0.2.9'
        dest.mkdir(parents=True,exist_ok=True)
        for name,im in previews.items():im.save(dest/('native-'+name+'.png'))
    if args.write:
        dest = ROOT/'work/output/english-native-0.2.9'
        dest.mkdir(parents=True,exist_ok=True)
        assert not (dest/'EBOOT.menu.elf').exists() and not (dest/'data.menu.ore').exists()
        (dest/'EBOOT.menu.elf').write_bytes(elf)
        (dest/'data.menu.ore').write_bytes(ore)
        (dest/'menu.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Build written.' if args.write else 'DRY RUN: game files unchanged.')


if __name__ == '__main__':main()

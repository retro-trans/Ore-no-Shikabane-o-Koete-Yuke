"""Add the local build number and group to the native title foreground.

Dry run by default. Keeps the previous translated archive and original ISO intact.
"""
import argparse
import hashlib
import json
import struct
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from catalog_text import ROOT, unpack_member
from inspect_native_textures import decode
from repack_text import align, rebuild_ez, rebuild_root, root_entries, u32

TITLE_BASE = 0x1E8000
FOOTER_ENTRY = 25
GROUP = 'retro-trans'


def footer(blob, version):
    original, info = decode(blob)
    assert (info['width'], info['height'], info['format'], info['swizzled']) == (352, 16, 5, True)
    # The existing centered sprite stays at (240,265). Its expanded 480x64
    # image begins at (0,233); original copyright pixels remain at (64,257).
    origin = (0, 233)
    # Keep the footer clear of the title caption (right edge 388) and the
    # copyright line (top 260). Render at four times size before reduction.
    scale = 4
    rect = (442, 234, 480, 259)
    layer = Image.new('RGBA', ((rect[2]-rect[0])*scale, (rect[3]-rect[1])*scale))
    draw = ImageDraw.Draw(layer)
    rows = []
    for text, top, size in [('v'+version, 236, 30), (GROUP, 248, 26)]:
        font = ImageFont.truetype(str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf'), size)
        bounds = draw.textbbox((0, 0), text, font=font, anchor='rt', stroke_width=scale)
        assert (bounds[2]-bounds[0])/scale <= rect[2]-rect[0]
        draw.text(((478-rect[0])*scale, (top-rect[1])*scale), text,
                  font=font, anchor='rt', fill=(235,235,235,255),
                  stroke_width=scale, stroke_fill=(18,18,18,255))
        rows.append(dict(text=text, right=478, top=top, font_size=size/scale,
                         outline=1, alignment='right'))
    layer = layer.resize((rect[2]-rect[0], rect[3]-rect[1]), Image.Resampling.LANCZOS)
    edited = Image.new('RGBA',(480,64))
    edited.alpha_composite(layer, (rect[0],rect[1]-origin[1]))
    palette_offset = u32(blob,24)
    palette_data = blob[palette_offset:]
    assert struct.unpack_from('<H',palette_data,4)[0] == 3
    palette = np.frombuffer(palette_data[16:1040],dtype=np.uint8).reshape(256,4)
    desired = np.asarray(edited).reshape(-1,4).astype(np.int32)
    distance = ((desired[:,None,:]-palette.astype(np.int32)[None,:,:])**2).sum(axis=2)
    linear = distance.argmin(axis=1).astype(np.uint8).reshape(64,480)
    stored = blob[32:palette_offset]
    original_indices = np.frombuffer(bytes(stored[((y//8)*22+x//16)*128+(y%8)*16+x%16]
                                          for y in range(16) for x in range(352)),dtype=np.uint8).reshape(16,352)
    linear[24:40,64:416] = original_indices
    linear = linear.tobytes()
    stride = 480
    pixels = bytearray(len(linear))
    for y in range(64):
        for x in range(0, stride, 16):
            dest = ((y//8)*(stride//16)+x//16)*128+(y%8)*16
            pixels[dest:dest+16] = linear[y*stride+x:y*stride+x+16]
    header = bytearray(blob[:32])
    struct.pack_into('<8H', header, 4, 512,64,5,1,480,64,480,64)
    struct.pack_into('<I', header, 24, 32+len(pixels))
    result = bytes(header)+bytes(pixels)+palette_data
    actual, actual_info = decode(result)
    assert np.array_equal(np.asarray(actual)[24:40,64:416],np.asarray(original))
    assert result[32+len(pixels):] == palette_data
    return result, actual, dict(rows=rows, editable_rectangle=list(rect), atlas_screen_origin=list(origin),
                               original_format=info, output_format=actual_info,
                               extra_uncompressed_bytes=len(result)-len(blob),
                               original_copyright_pixels_and_palette_exact=True)


def executable():
    path = ROOT/'work/output/native-0.2.3/EBOOT.elf'
    source = path.read_bytes()
    assert hashlib.sha256(source).hexdigest() == '830332ff4e7af40ad59dc125997eb4e895a0ed8dec895ddcb440fd998da3f97b'
    result = bytearray(source)
    # Title menu originally hides the copyright sprite. Keep the expanded
    # footer visible; normal title teardown still removes and frees it.
    patches = [(0x089797B0,0x0C000000|(0x089BB624//4),0x0C000000|(0x089BB66C//4))]
    for address, old, new in patches:
        offset = address-0x08803000
        assert u32(source,offset) == old
        struct.pack_into('<I',result,offset,new)
    expected_changed = {a-0x08803000+j for a,_,_ in patches for j in range(4)}
    assert all(a==b or i in expected_changed for i,(a,b) in enumerate(zip(source,result)))
    return bytes(result),dict(source_elf_sha256=hashlib.sha256(source).hexdigest(),
                              output_elf_sha256=hashlib.sha256(result).hexdigest(),
                              patches=[dict(address=hex(a),original=hex(o),replacement=hex(n)) for a,o,n in patches])


def build(source, version):
    original = (ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    data = source.read_bytes()
    index = next(i for i,_,_,off in root_entries(original)[0] if off == TITLE_BASE)
    base = next(off for i,_,_,off in root_entries(data)[0] if i == index)
    count, alignment = struct.unpack_from('<II',data,base+8)
    entries = [struct.unpack_from('<4I',data,base+16+i*16) for i in range(count)]
    name_offset, size, pos, _ = entries[FOOTER_ENTRY]
    assert data[base+name_offset:base+name_offset+18] == b'copyright_sce.ppt\0'
    old, compression = unpack_member(data[base+pos:base+pos+size])
    assert compression == 'custom_deflate'
    new, preview, detail = footer(old, version)
    z = zlib.compressobj(9,zlib.DEFLATED,-15)
    packed = b'\x1f\x8b\x09\0'+struct.pack('<I',len(new))+z.compress(new)+z.flush()
    assert unpack_member(packed)[0] == new
    end = align(max(p+s for _,s,p,_ in entries),alignment)
    container = rebuild_ez(data[base:base+end],{FOOTER_ENTRY:packed})
    for i, (_,s,p,_) in enumerate(entries):
        if i == FOOTER_ENTRY:
            continue
        _, ns, np_, _ = struct.unpack_from('<4I',container,16+i*16)
        assert container[np_:np_+ns] == data[base+p:base+p+s]
    output = rebuild_root(data,{base:container})
    # Every other top-level payload must also stay byte-identical.
    old_entries, old_end = root_entries(data)
    new_entries, new_end = root_entries(output)
    for n, (old_entry, new_entry) in enumerate(zip(old_entries,new_entries)):
        if old_entry[0] == index:
            continue
        old_stop = old_entries[n+1][3] if n+1<len(old_entries) else old_end
        new_stop = new_entries[n+1][3] if n+1<len(new_entries) else new_end
        assert data[old_entry[3]:old_stop] == output[new_entry[3]:new_stop]
    report = dict(version=version, source=str(source.relative_to(ROOT)),
                  source_sha256=hashlib.sha256(data).hexdigest(),
                  output_sha256=hashlib.sha256(output).hexdigest(), bytes=len(output),
                  native_asset='copyright_sce.ppt', member_entry=FOOTER_ENTRY,
                  texture_replacement=False, all_other_archive_members_unchanged=True,
                  runtime_fit='pending', **detail)
    return output, preview, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version',default='0.2.7')
    ap.add_argument('--source',default='work/output/english-native-0.2.5/data.graphics.ore')
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    output, preview, report = build(ROOT/args.source,args.version)
    elf, elf_report = executable()
    report['executable'] = elf_report
    print(json.dumps(report,indent=2))
    if args.write:
        dest = ROOT/('work/output/english-native-'+args.version)
        dest.mkdir(parents=True,exist_ok=True)
        path = dest/'data.branded.ore'
        if path.exists():
            raise FileExistsError(path)
        path.write_bytes(output)
        (dest/'EBOOT.elf').write_bytes(elf)
        (dest/'branding.report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        ui = ROOT/('work/ui/title-branding-'+args.version)
        ui.mkdir(parents=True,exist_ok=True)
        preview.save(ui/'native-footer.png')
        (ui/'layout.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Native title branding written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

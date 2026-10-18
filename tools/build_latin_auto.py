"""Larger native title footer and curated Latin Auto pools. Dry run unless --write."""
import argparse
import hashlib
import json
import re
import struct
import keystone
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from catalog_text import ROOT, parse_mlt
from build_menu_fixes import container, member, pack
from inspect_native_textures import decode
from repack_text import align, rebuild_ez, rebuild_root, root_entries, u32

VERSION='0.2.16'
FAMILIES={1:'Sanjo',2:'Rokkaku',5:'Shijo',7:'Bukkoji',10:'Nijo',11:'Oike',12:'Nawate',13:'Mibugawa',15:'Nishioji',17:'Rokujo',24:'Karasuma',28:'Hachijo',31:'Gojo',38:'Shichijo',40:'Shiokoji',45:'Umekoji',48:'Kujo',56:'Mukomachi',57:'Rokujizo',58:'Keage',59:'Rokuhara',61:'Oharano',62:'Kitasaga'}
MALE={11:'Amon',12:'Aran',13:'Aren',14:'Atago',15:'Akutaro',16:'Asahi',17:'Ayato',19:'Yasukiyo',20:'Yasutake',21:'Izo',22:'Iemon',23:'Ibuki',24:'Tameyoshi',25:'Tamegoro',26:'Tamenobu',27:'Kaoru',28:'Ichigo',29:'Kazuki',30:'Ikki',32:'Kazuma',33:'Kazuto',34:'Ichizu',35:'Kazuma',37:'Ippei',38:'Ippo',39:'Kazuya',40:'Kazuya',41:'Kazuhiro',42:'Kazuharu',43:'Ichiro',44:'Ichirota',45:'Ichimaru',46:'Uemon',47:'Ukyo',48:'Ukon',50:'Kagemaru',51:'Kagetora',54:'Sakae',55:'Eikichi',56:'Nagataka',57:'Hidetaka',58:'Hidehiko',59:'Hideo',60:'Mamoru',61:'Homura',63:'Homura',67:'Otomaru',68:'Otojiro',69:'Otoya',70:'Yoshitsugu',71:'Yoshito',72:'Natsuchika',73:'Natsuki',74:'Ienaga',75:'Ietsugu',77:'Hanamaru',79:'Hanamichi',80:'Kazan',81:'Kanan',83:'Kibao',85:'Masaomi',86:'Masahiko',87:'Kai',88:'Kai',89:'Kaio',90:'Kaito',91:'Kaito',92:'Ebizo',93:'Ema',96:'Gai',97:'Kakihiko',99:'Kadomaru'}
# Explicit kana in the original pools supplies unambiguous readings.
KANA='あいうえおかきくけこがぎぐげござじずぜぞさしすせそたちつてとだぢづでどなにぬねのはひふへほばびぶべぼぱぴぷぺぽまみむめもやゆよらりるれろわをん'
ROMA='a i u e o ka ki ku ke ko ga gi gu ge go za ji zu ze zo sa shi su se so ta chi tsu te to da ji zu de do na ni nu ne no ha hi fu he ho ba bi bu be bo pa pi pu pe po ma mi mu me mo ya yu yo ra ri ru re ro wa o n'.split()
TABLE=dict(zip(KANA,ROMA))
def romanize(text):
    text=''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ヶ' else c for c in text)
    syll=[]
    for c in text:
        if c in 'ゃゅょ':
            base=syll.pop();syll.append((base[:-1] if base not in ('shi','chi','ji') else base[:-1])+'y'*(base not in ('shi','chi','ji'))+{'ゃ':'a','ゅ':'u','ょ':'o'}[c])
        else:syll.append(TABLE[c])
    value=''.join(syll)
    value=re.sub('n(?=[bmp])','m',value)
    value=value.replace('ou','o').replace('uu','u')
    return value.capitalize()

def names_mlt(original):
    rows=list(parse_mlt(original));sections=[[t for s,i,o,t in rows if s==0]];gloss=[]
    for section in (1,2,3):
        chosen=[]
        for s,i,o,t in rows:
            if s!=section:continue
            latin=FAMILIES.get(i) if s==1 else romanize(t) if re.fullmatch('[ぁ-んァ-ヶ]+',t) else MALE.get(i) if s==3 else None
            if latin and len(latin)<=8 and latin not in chosen:
                assert latin.isascii() and latin.isalpha();chosen.append(latin)
                gloss.append(dict(section=s,source_index=i,source_name=t,latin=latin,reading_basis='Kyoto place name' if s==1 else 'Explicit source kana' if re.fullmatch('[ぁ-んァ-ヶ]+',t) else 'Project-selected conventional kanji reading; provisional'))
        assert chosen
        # Stored short names and decoded compact names use fullwidth Latin.
        # Match that convention so the original duplicate-name filter sees
        # the same text as the candidate table. Rendering normalizes to VWF.
        sections.append([''.join(chr(ord(c)+0xfee0) for c in t) for t in chosen])
    out=bytearray(original[:4]+bytes(len(sections)*4));locations=[]
    for s,values in enumerate(sections):
        out.extend(b'\xff'*(align(len(out),4)-len(out)));struct.pack_into('<I',out,4+s*4,len(out))
        oldsec=u32(original,4+s*4);flags=u32(original,oldsec)>>16;assert flags==0
        out.extend(struct.pack('<I',len(values)));table=len(out);out.extend(bytes(4*len(values)))
        locations.extend((table+i*4,t) for i,t in enumerate(values))
    for ptr,t in locations:
        struct.pack_into('<I',out,ptr,len(out));out.extend(t.encode('utf-16-le')+b'\0\0')
    out.extend(b'\xff'*(align(len(out),4)-len(out)))
    assert [(s,i,t) for s,i,_,t in parse_mlt(out)]==[(s,i,t) for s,values in enumerate(sections) for i,t in enumerate(values)]
    return bytes(out),gloss,[len(x) for x in sections]

def footer(blob, version=VERSION):
    original,info=decode(blob);assert original.size==(352,16)
    origin=(0,201);rect=(330,222,480,256);scale=4
    layer=Image.new('RGBA',(480*scale,128*scale));draw=ImageDraw.Draw(layer);rows=[]
    for text,top,size in [('v'+version,223,14),('github.com/retro-trans',241,12)]:
        font=ImageFont.truetype(str(ROOT/'incoming/noto-sans/NotoSans-Regular.ttf'),size*scale)
        bounds=draw.textbbox((474*scale,(top-origin[1])*scale),text,font=font,anchor='rt',stroke_width=scale)
        assert bounds[0]>=330*scale and bounds[3]<(257-origin[1])*scale
        draw.text((474*scale,(top-origin[1])*scale),text,font=font,anchor='rt',fill=(235,235,235,255),stroke_width=scale,stroke_fill=(18,18,18,255))
        rows.append(dict(text=text,right=474,top=top,font_size=size,bounds=[bounds[0]/scale,bounds[1]/scale+201,bounds[2]/scale,bounds[3]/scale+201]))
    image=layer.resize((480,128),Image.Resampling.LANCZOS)
    po=u32(blob,24);pal=blob[po:];palette=np.frombuffer(pal[16:1040],dtype=np.uint8).reshape(256,4).astype(np.int32)
    rgba=np.asarray(image).reshape(-1,4).astype(np.int32)
    indices=np.concatenate([((c[:,None,:]-palette[None,:,:])**2).sum(2).argmin(1) for c in np.array_split(rgba,64)]).astype(np.uint8).reshape(128,480)
    stored=blob[32:po];old=np.array([stored[((y//8)*22+x//16)*128+(y%8)*16+x%16] for y in range(16) for x in range(352)],dtype=np.uint8).reshape(16,352)
    indices[56:72,64:416]=old;pixels=bytearray(480*128)
    for y in range(128):
        for x in range(0,480,16):pixels[((y//8)*30+x//16)*128+(y%8)*16:((y//8)*30+x//16)*128+(y%8)*16+16]=indices[y,x:x+16].tobytes()
    header=bytearray(blob[:32]);struct.pack_into('<8H',header,4,512,128,5,1,480,128,480,128);struct.pack_into('<I',header,24,32+len(pixels))
    result=bytes(header)+pixels+pal;actual,_=decode(result)
    assert np.array_equal(np.asarray(actual)[56:72,64:416],np.asarray(original))
    return result,actual,dict(rows=rows,atlas_screen_origin=origin,copyright_exact=True)

def build():
    source=ROOT/'work/output/english-native-0.2.15';elf=(source/'EBOOT.names.elf').read_bytes();data=(source/'data.names.ore').read_bytes()
    assert hashlib.sha256(elf).hexdigest()=='affb82ab8833ba559cd076511753a027c8abe3130a49145314e09440458602ad'
    assert hashlib.sha256(data).hexdigest()=='be62ef8ec37629db336ac8b40f3762099ed140729c8687fd2fd83594ea12f3f5'
    elf=bytearray(elf)
    phoff=u32(elf,28);ph=list(struct.unpack_from('<8I',elf,phoff+32));assert ph[1]+ph[4]==len(elf)
    elf.extend(bytes(align(len(elf),16)-len(elf)));cave=ph[2]+len(elf)-ph[1]
    ks=keystone.Ks(keystone.KS_ARCH_MIPS,keystone.KS_MODE_MIPS32|keystone.KS_MODE_LITTLE_ENDIAN)
    helpers=[]
    for method in (0x104,0x108):
        addr=ph[2]+len(elf)-ph[1];helpers.append(addr)
        asm='''.set noreorder
            addiu $sp, $sp, -16
            sw $ra, 12($sp)
            sw $s0, 8($sp)
            move $s0, $a1
            jal 0x08804d24
            nop
            lw $t9, 0($v0)
            move $a0, $v0
            move $a1, $s0
            ori $a2, $zero, 0x8003
            lw $t9, %d($t9)
            jalr $t9
            nop
            lw $ra, 12($sp)
            lw $s0, 8($sp)
            jr $ra
            addiu $sp, $sp, 16
        '''%method
        elf.extend(bytes(ks.asm(asm,addr=addr)[0]))
    ph[4]=ph[5]=len(elf)-ph[1];struct.pack_into('<8I',elf,phoff+32,*ph)
    patches=[(0x08978F40,0x0C000000|(0x089B8050//4),0x0C000000|(helpers[0]//4),'Register title footer independently above Itsuka at draw key 0x8003'),
             (0x08978FFC,0x0C000000|(0x089B82D0//4),0x0C000000|(helpers[1]//4),'Unregister footer before freeing title resources'),
             (0x0897B3A8,0x2405005A,0x2405000C,'Title-menu help window x=12; width remains 300')]
    for pc,old,new,note in patches:
        assert u32(elf,pc-0x08803000)==old
        struct.pack_into('<I',elf,pc-0x08803000,new)
    elf=bytes(elf)
    original=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes();oe,_=root_entries(original);be,end=root_entries(data)
    ti=next(i for i,_,_,o in oe if o==0x1e8000);tb=next(o for i,_,_,o in be if i==ti)
    n=next(n for n,e in enumerate(be) if e[0]==27);nb=be[n][3];stop=be[n+1][3]-(be[n][2]&2047)
    name,gloss,counts=names_mlt(data[nb:stop]);title,te=container(data,tb);ot,ote=container(original,0x1e8000)
    new,preview,fr=footer(member(ot,ote,25));result=rebuild_root(data,{nb:name,tb:rebuild_ez(title,{25:pack(new)})})
    ae,aend=root_entries(result)
    for j,(a,b) in enumerate(zip(be,ae)):
        if a[3] in (nb,tb):continue
        sa=(be[j+1][3] if j+1<len(be) else end)-(a[2]&2047);sb=(ae[j+1][3] if j+1<len(ae) else aend)-(b[2]&2047)
        assert data[a[3]:sa]==result[b[3]:sb]
    report=dict(version=VERSION,source_version='0.2.15',elf_sha256=hashlib.sha256(elf).hexdigest(),archive_sha256=hashlib.sha256(result).hexdigest(),archive_bytes=len(result),name_pool_counts=counts,footer=fr,title_patches=[dict(pc=hex(pc),old=hex(old),new=hex(new),purpose=note) for pc,old,new,note in patches],texture_replacement=False,unrelated_payloads_unchanged=True,runtime_verification='pending')
    return elf,result,preview,report,gloss
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    elf,data,preview,report,gloss=build();print(json.dumps(report,indent=2))
    print('Auto samples:',[x['latin'] for x in gloss[:8]])
    if a.write:
        dest=ROOT/('work/output/english-native-'+VERSION);dest.mkdir(parents=True,exist_ok=True);assert not (dest/'data.latin.ore').exists()
        (dest/'EBOOT.latin.elf').write_bytes(elf);(dest/'data.latin.ore').write_bytes(data);(dest/'latin.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui=ROOT/('work/ui/latin-auto-'+VERSION);ui.mkdir(parents=True,exist_ok=True);preview.save(ui/'native-footer.png')
        (ROOT/'work/glossary/latin_auto_names.json').write_text(json.dumps(dict(version=VERSION,policy='Curated source names with explicit kana, Kyoto place readings, or marked project-selected conventional kanji readings; ASCII Hepburn, maximum eight letters, no truncation. Original excluded names remain in the source archive.',sources=['https://www.ezairyu.mofa.go.jp/passport/hebon.html','https://www.city.kyoto.lg.jp/bunshi/cmsfiles/contents/0000206/206129/english-ura.pdf','https://www2.city.kyoto.lg.jp/kotsu/webguide/en/tika/pop_station_map.html'],rows=gloss),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Build written.' if a.write else 'DRY RUN: no files written.')
if __name__=='__main__':main()

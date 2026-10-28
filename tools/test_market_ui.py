"""Check relocated market pointers and run the scoped unit hook as MIPS code."""
import argparse,json,re,struct
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN
from unicorn.mips_const import *
from catalog_text import ROOT
from build_market_ui import BASE,V,sha
from strip_jp import export


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');args=ap.parse_args()
    out=ROOT/('work/output/english-native-'+V)
    elf=(out/'EBOOT.market.elf').read_bytes();r=json.loads((out/'market.report.json').read_text())
    assert sha(elf)==r['elf_sha256']
    po=struct.unpack_from('<I',elf,28)[0];ph=struct.unpack_from('<8I',elf,po+32)
    offset=lambda address:ph[1]+address-ph[2]
    for literal in r['literals']:
        p=offset(int(literal['address'],16));raw=elf[p:elf.index(b'\0',p)]
        assert raw.decode('ascii')==literal['translation_en']
        original=int(literal['original_address'],16)-BASE
        old=elf[original:elf.index(b'\0',original)].decode('euc_jp')
        assert re.findall(r'%[sd]',old)==literal['format_arguments']
    pairs=[(0x0893eb08,0x0893eb10,0),(0x0893eb84,0x0893eb10,0),
           (0x0893ec34,0x0893ec38,1),(0x0893d4e8,0x0893d4f0,2),(0x0893d538,0x0893d540,3),
           (0x089401d8,0x089401e8,4)]
    for high,low,n in pairs:
        h=struct.unpack_from('<I',elf,high-BASE)[0]&65535
        l=struct.unpack_from('<h',elf,low-BASE)[0]
        assert (h<<16)+l==int(r['literals'][n]['address'],16)
    assert struct.unpack_from('<I',elf,0x08b2b770-BASE)[0]==int(r['literals'][5]['address'],16)
    # These native literals are outside the indexed archive corpus used by
    # check_translation.py. Validate their source identity and public export here.
    path=ROOT/'work/translation/en/executable/market_prompts.json'
    batch=json.loads(path.read_text(encoding='utf-8'))
    assert len(batch['rows'])==len(r['literals'])==6
    for row,literal in zip(batch['rows'],r['literals']):
        old=int(literal['original_address'],16)-BASE
        jp=elf[old:elf.index(b'\0',old)].decode('euc_jp')
        assert row['id']==literal['id'] and row['source_jp']==jp
        assert row['source_sha256']==sha(jp.encode())
        assert row['translation_en']==literal['translation_en']
        assert re.findall(r'%[sd]',jp)==re.findall(r'%[sd]',row['translation_en'])
    public=json.loads(path.with_suffix('.en.json').read_text(encoding='utf-8'))
    assert public==export(path) and all('source_jp' not in row for row in public['rows'])
    w=r['unit_wrapper'];address=int(w['address'],16);contracts=int(w['literal'],16);setter=int(w['setter'],16)
    cases=[]
    for caller in [0x0893eb60,0x08932c1c,0x08951ba4,0x0895245c,0]:
        uc=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
        uc.mem_map(0x08800000,0x02000000)
        uc.mem_write(address,elf[offset(address):offset(address)+w['bytes']])
        sp=0x09fff000;stack=bytearray([0x6b]*256);struct.pack_into('<I',stack,28,caller)
        uc.mem_write(sp,bytes(stack))
        initial={UC_MIPS_REG_SP:sp,UC_MIPS_REG_RA:0x0894e730,
            UC_MIPS_REG_A0:0x09000000,UC_MIPS_REG_A1:0x09000100,
            UC_MIPS_REG_A2:0x12345678,UC_MIPS_REG_A3:0x23456789}
        for n,reg in enumerate([UC_MIPS_REG_S0,UC_MIPS_REG_S1,UC_MIPS_REG_S2,UC_MIPS_REG_S3,
                UC_MIPS_REG_S4,UC_MIPS_REG_S5,UC_MIPS_REG_S6,UC_MIPS_REG_S7,UC_MIPS_REG_FP]):initial[reg]=0x15000000+n
        for reg,value in initial.items():uc.reg_write(reg,value)
        uc.emu_start(address,setter,count=40)
        assert uc.reg_read(UC_MIPS_REG_PC)==setter
        assert uc.reg_read(UC_MIPS_REG_A1)==(contracts if caller==0x0893eb60 else initial[UC_MIPS_REG_A1])
        for reg,value in initial.items():
            if reg!=UC_MIPS_REG_A1:assert uc.reg_read(reg)==value,(caller,reg)
        assert bytes(uc.mem_read(sp,256))==bytes(stack)
        cases.append(dict(caller=hex(caller),unit='contracts' if caller==0x0893eb60 else 'original',
            stack_and_callee_saved_registers='unchanged',tail_target=hex(setter)))
    proof=dict(version=V,result='PASS',relocated_pointer_pairs=len(pairs),format_argument_order='unchanged',
        native_translation_records=6,translation_source_hashes='PASS',english_only_export='PASS',
        original_narrow_literals='unchanged',mips_unit_cases=cases,guest_gameplay='not executed by this test',
        executable_sha256=r['elf_sha256'])
    print(json.dumps(dict(write=args.write,**proof),indent=2))
    if args.write:(ROOT/('work/ui/market-ui-'+V+'/static-tests.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()

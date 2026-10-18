"""Cross-check every recovered icon pixel against an independent BC3 block decoder."""
import functools,json,struct
from PIL import Image
from catalog_text import ROOT,unpack_member
from extract_oreshika_icon_sheets import extract,SOURCE,SPECS
glyphs,sheets,provenance=extract();native={}
with SOURCE.open('rb') as f:
 for file,row in provenance['native_sheets'].items():
  f.seek(row['member_offset']);gxt,_=unpack_member(f.read(row['size']));off,size,pal,flags,kind,fmt,w,h,mips,pad=struct.unpack_from('<6I4H',gxt,32);assert kind==0 and fmt==0x87000000
  native[file]=(gxt[off:off+size],w//4,h//4)
def morton(x,y,w,h):
 bits=min(w,h).bit_length()-1;result=((x>>bits)|(y>>bits))<<(2*bits)
 for i in range(bits):result|=((x>>i)&1)<<(2*i+1);result|=((y>>i)&1)<<(2*i)
 return result
def rgb565(c):return (((c>>11)&31)*255//31,((c>>5)&63)*255//63,(c&31)*255//31)
@functools.lru_cache(None)
def block(file,x,y):
 data,w,h=native[file];p=morton(x,y,w,h)*16;b=data[p:p+16];a0,a1=b[:2];alphas=[a0,a1]
 if a0>a1:alphas.extend(((7-i)*a0+i*a1)//7 for i in range(1,7))
 else:alphas.extend(((5-i)*a0+i*a1)//5 for i in range(1,5));alphas.extend([0,255])
 abits=int.from_bytes(b[2:8],'little');c0,c1,bits=struct.unpack_from('<HHI',b,8);c0,c1=rgb565(c0),rgb565(c1);colors=[c0,c1,tuple((2*a+b)//3 for a,b in zip(c0,c1)),tuple((a+2*b)//3 for a,b in zip(c0,c1))]
 return [colors[(bits>>(2*i))&3]+(alphas[(abits>>(3*i))&7],) for i in range(16)]
checked=0;maxdelta=0
for stat,file,box in SPECS:
 im=glyphs[stat];saved=Image.open(ROOT/('incoming/oreshika-native-icons/'+stat.lower()+'.png')).convert('RGBA');assert saved.tobytes()==im.tobytes()
 for y in range(box[1],box[3]):
  for x in range(box[0],box[2]):
   expected=block(file,x//4,y//4)[(y%4)*4+x%4];actual=im.getpixel((x-box[0],y-box[1]));delta=max(abs(a-b) for a,b in zip(actual,expected));maxdelta=max(maxdelta,delta);assert delta<=3,(stat,x,y,actual,expected);checked+=1
 colors=[p for p in im.getdata() if p[3]>200];assert len(colors)>40
proof=dict(version='0.2.31',result='PASS',source='Two original native Vita BC3 texture sheets',independent_pixel_checks=checked,maximum_channel_difference=maxdelta,rounding_tolerance=3,crops='All seven incoming PNGs equal the native decoded crop exactly',source_resampling=False,original_alpha='Retained',decoder_reference='https://github.com/Vita3K/Vita3K/blob/master/vita3k/renderer/src/texture/format.cpp')
(ROOT/'work/ui/native-icons-0.2.31/source-tests.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,indent=2))

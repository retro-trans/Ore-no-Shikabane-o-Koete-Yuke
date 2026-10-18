"""Decode single-texture Vita GXT BC1/BC2/BC3 UI sheets without resampling.

Morton layout follows Vita3K renderer/src/texture/format.cpp.
"""
import io,struct
import numpy as np
from PIL import Image

def compact(x):
 x=x&0x55555555;x=(x^(x>>1))&0x33333333;x=(x^(x>>2))&0x0f0f0f0f
 x=(x^(x>>4))&0x00ff00ff;return (x^(x>>8))&0xffff

def decode(blob):
 assert blob[:4]==b'GXT\0' and struct.unpack_from('<I',blob,8)[0]==1
 off,size,pal,flags,kind,fmt,w,h,mips,pad=struct.unpack_from('<6I4H',blob,32)
 codecs={0x85:(b'DXT1',8),0x86:(b'DXT3',16),0x87:(b'DXT5',16)}
 fourcc,block=codecs[fmt>>24];bw,bh=(w+3)//4,(h+3)//4;pixels=blob[off:off+bw*bh*block];assert len(pixels)==bw*bh*block
 if kind==0:
  minimum=min(bw,bh);assert minimum&(minimum-1)==0;k=minimum.bit_length()-1;i=np.arange(bw*bh,dtype=np.uint32)
  x=compact(i>>1)&(minimum-1);y=compact(i)&(minimum-1);upper=(i>>(2*k))<<k
  if bw>=bh:x|=upper
  else:y|=upper
  blocks=np.frombuffer(pixels,dtype=np.uint8).reshape((-1,block));linear=np.empty_like(blocks);linear[y*bw+x]=blocks;pixels=linear.tobytes()
 else:assert kind==0x60000000,hex(kind)
 header=bytearray(128);header[:4]=b'DDS ';struct.pack_into('<7I',header,4,124,0x81007,h,w,len(pixels),0,1);struct.pack_into('<2I',header,76,32,4);header[84:88]=fourcc;struct.pack_into('<I',header,108,0x1000)
 im=Image.open(io.BytesIO(header+pixels)).convert('RGBA')
 return im,dict(width=w,height=h,kind=hex(kind),format=hex(fmt),compression=fourcc.decode(),mipmaps=mips,source_pixel_bytes=len(pixels),resampled=False)

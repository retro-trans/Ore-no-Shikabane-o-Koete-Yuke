"""Capture the translated startup disclaimer from the isolated emulator. Dry run by default."""
import argparse,base64,hashlib,json,time
import numpy as np
from PIL import Image
from catalog_text import ROOT
from ppsspp_debug import Session
from capture_psp_frame import capture
UI=ROOT/'work/ui/startup-disclaimer-0.2.23';OUT=ROOT/'work/output/english-native-0.2.23'
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 print('Read native startup display frames and match the English image; no input or memory edits.',flush=True)
 if not a.execute:return
 template=np.asarray(Image.open(UI/'native-warning.png').convert('RGB')).max(axis=2);mask=template>127
 best=-1;best_image=None;best_meta=None;deadline=time.monotonic()+45;attempts=0
 while time.monotonic()<deadline:
  try:im,meta=capture()
  except (AssertionError,ConnectionError,OSError,TimeoutError,TypeError):time.sleep(.1);continue
  attempts+=1;rgb=np.asarray(im.convert('RGB')).max(axis=2);peak=int(rgb.max());actual=rgb>max(16,peak/2);union=np.count_nonzero(mask|actual);score=np.count_nonzero(mask&actual)/max(1,union)
  if score>best:best=score;best_image=im;best_meta=meta
  if score>.92 and peak>=240:break
  if attempts%20==0:print(json.dumps(dict(frames=attempts,best_match=round(best,4))),flush=True)
  time.sleep(.1)
 assert best_image is not None
 best_image.save(UI/'disclaimer-after.png');(UI/'disclaimer-after.json').write_text(json.dumps(best_meta,indent=2)+'\n',encoding='utf-8')
 assert best>.75,('English disclaimer was not matched',best)
 r=json.loads((OUT/'disclaimer.report.json').read_text());verified=[]
 with Session() as s:
  assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
  for p in r['patches']:
   word=s.call('memory.disasm',address=int(p['address'],16),count=1,displaySymbols=False)['lines'][0]['encoding'];assert word.to_bytes(4,'little').hex()==p['after'];verified.append(p['address'])
  embed=r['embedded_archive'];b=base64.b64decode(s.call('memory.read',address=int(embed['new_address'],16),size=embed['bytes'])['base64']);assert hashlib.sha256(b).hexdigest()==embed['sha256']
  assert not s.call('cpu.breakpoint.list')['breakpoints']
 proof=dict(version='0.2.23',tested_iso='work/source/qa-disclaimer-0.2.23.iso',result='PASS',mask_intersection_over_union=best,frames_examined=attempts,actual_display='Native PSP framebuffer',native_pointer_instructions=verified,embedded_archive_sha256=hashlib.sha256(b).hexdigest(),elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],game_memory_writes=False,button_input=False,texture_replacement=False)
 (UI/'runtime-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()

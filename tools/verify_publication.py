"""Read the staged Git blobs and reject private/game/source-script content."""
import ast,collections,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
names=subprocess.check_output(['git','diff','--cached','--name-only','-z','--diff-filter=ACMR'],cwd=ROOT).decode().split('\0');names=[x for x in names if x];assert names,'No staged files to audit'
forbidden={'.iso','.cso','.bin','.elf','.ore','.pmf','.prx','.at3','.mlb','.ppt','.vpk','.zip','.png','.exe','.dll'}
proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE);total=0;exports=0
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  assert 'source_jp' not in x or name.startswith('work/glossary/'),('Bilingual source record staged',name)
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
try:
 for name in names:
  p=Path(name);assert p.suffix.lower() not in forbidden,name
  assert name=='work/output/.gitkeep' or not name.startswith(('work/source/','work/output/','Oreshika Tainted Bloodlines (USA)/')),name
  assert not name.startswith('incoming/') or name.startswith('incoming/noto-sans/'),name
  assert not name.startswith('work/translation/') or name.endswith('.en.json'),name
  proc.stdin.write((':'+name+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().decode().split();assert len(head)==3 and head[1]=='blob',name;n=int(head[2]);data=proc.stdout.read(n);assert proc.stdout.read(1)==b'\n';total+=n
  assert n<50*1024*1024,(name,'Unexpected large source blob')
  if p.suffix=='.ttf':assert name=='incoming/noto-sans/NotoSans-Regular.ttf';continue
  text=data.decode('utf-8-sig');assert not re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)',text),('Potential credential in',name)
  if p.suffix=='.json':vals=list(strings(json.loads(text)))
  elif p.suffix=='.py':vals=[n.value for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
  else:vals=text.splitlines()
  if name.endswith('.en.json'):exports+=1
  for value in vals:
   count=len(re.findall(r'[\u3040-\u30ff\u3400-\u9fff]',value))
   if count<=16:continue
   assert name.startswith('work/glossary/') or (name=='tools/build_latin_auto.py' and re.fullmatch(r'[\u3040-\u309f]+',value)),('Review possible Japanese script text',name)
finally:
 proc.stdin.close();proc.wait()
print(json.dumps(dict(result='PASS',files=len(names),english_exports=exports,bytes=total,extensions=dict(collections.Counter(Path(x).suffix for x in names)),checks=['No game binaries, raw screenshots, private working folders or source dialogue','English-only translation exports; Japanese names/UI terms and kana alphabet retained','No credential patterns found']),indent=2))

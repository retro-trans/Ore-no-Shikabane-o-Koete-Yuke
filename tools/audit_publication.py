"""Read-only inventory of Japanese text and sizes before public staging."""
import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=[]
for folder in ('tools','docs','work/glossary','work/ui','work/translation/en'):
 for p in (ROOT/folder).rglob('*'):
  if p.suffix not in ('.py','.json','.md','.txt'):continue
  try:s=p.read_text(encoding='utf-8-sig')
  except UnicodeError:continue
  if folder=='work/translation/en' and not p.name.endswith('.en.json'):continue
  if p.suffix=='.json':
   def strings(x,path=''):
    if isinstance(x,str):yield path,x
    elif isinstance(x,dict):
     for k,v in x.items():yield from strings(v,path+'/'+str(k))
    elif isinstance(x,list):
     for i,v in enumerate(x):yield from strings(v,path+'/'+str(i))
   values=list(strings(json.loads(s)))
  elif p.suffix=='.py':values=[(str(n.lineno),n.value) for n in ast.walk(ast.parse(s)) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
  else:values=[(str(n+1),line) for n,line in enumerate(s.splitlines())]
  lines=[(path,len(re.findall(r'[\u3040-\u30ff\u3400-\u9fff]',line))) for path,line in values if re.search(r'[\u3040-\u30ff\u3400-\u9fff]',line)]
  if lines and (folder!='work/ui' or max(count for _,count in lines)>16):out.append(dict(file=p.relative_to(ROOT).as_posix(),lines=len(lines),max_jp_chars=max(count for _,count in lines),long_values=[path for path,count in lines if count>16][:12]))
print(json.dumps(out,indent=2))

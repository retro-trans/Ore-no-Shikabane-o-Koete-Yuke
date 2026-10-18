"""Regenerate source-free English exports before publication. Dry run first."""
import argparse,json
from catalog_text import ROOT
from strip_jp import export
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();rows=[]
for p in sorted((ROOT/'work/translation/en').rglob('*.json')):
 if p.name.endswith('.en.json'):continue
 d=json.loads(p.read_text(encoding='utf-8'))
 if not isinstance(d,dict) or not all(k in d for k in ('schema_version','version','language','status','rows')):continue
 if not any('source_jp' in r for r in d['rows']):continue
 clean=export(p);dest=p.with_suffix('.en.json');old=json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else None
 assert all('source_jp' not in row and 'has_japanese' not in row for row in clean['rows'])
 rows.append(dict(file=dest.relative_to(ROOT).as_posix(),rows=len(clean['rows']),changed=old!=clean))
 if a.write:dest.write_text(json.dumps(clean,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(write=a.write,files=len(rows),rows=sum(x['rows'] for x in rows),changed=[x for x in rows if x['changed']]),indent=2))

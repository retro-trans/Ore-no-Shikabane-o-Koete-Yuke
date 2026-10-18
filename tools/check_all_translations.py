"""Read-only structural validation of every bilingual batch and safe export."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    failed=[]
    count=0
    for p in sorted((ROOT/'work/translation/en').glob('*.en.json')):
        bilingual=p.with_name(p.name.replace('.en.json','.json'))
        result=subprocess.run([sys.executable,str(ROOT/'tools/check_translation.py'),'--batch',str(bilingual)],
                              capture_output=True,text=True,encoding='utf-8')
        try:
            info,_=json.JSONDecoder().raw_decode(result.stdout)
        except json.JSONDecodeError:
            failed.append(p.name)
            print(p.name, result.stdout, result.stderr)
            continue
        count+=1
        print(f'{p.name}: {info["rows"]} rows; {len(info["errors"])} errors')
        if result.returncode or info['errors']:
            failed.append(p.name)
            print(json.dumps(info['errors'],indent=2))
    print(json.dumps(dict(batches_checked=count,failed=failed),indent=2))
    if failed:
        raise SystemExit(1)


if __name__=='__main__':
    main()

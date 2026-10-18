"""Extract local PMF inputs and sample movie frames for a baked-lettering audit.

Dry run unless --write. Source movie bytes and preview frames stay ignored.
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from extract_iso import inventory

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--interval', type=int, default=10)
    args = ap.parse_args()
    iso = next(ROOT.glob('*.iso'))
    with iso.open('rb') as stream:
        rows = [r for r in inventory(stream) if r['path'].endswith('.pmf')]
    print(json.dumps(dict(movies=[dict(file=r['path'],bytes=r['size']) for r in rows],
                          seconds_between_samples=args.interval,
                          limitation='Sampled frames are an audit aid, not proof that every frame has been checked.'),indent=2))
    if not args.write:
        print('DRY RUN: no files written.')
        return
    dest = ROOT / 'work/source/movie-audit'
    dest.mkdir(parents=True,exist_ok=True)
    summaries=[]
    with iso.open('rb') as stream:
        for row in rows:
            name = Path(row['path']).stem
            source=dest/(name+'.pmf')
            if not source.exists():
                stream.seek(row['iso_offset'])
                source.write_bytes(stream.read(row['size']))
            frames=dest/name
            frames.mkdir(exist_ok=True)
            result=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),
                                   '-vf',f'fps=1/{args.interval},scale=240:136','-an',str(frames/'frame-%03d.png')],
                                  capture_output=True,text=True)
            if result.returncode:
                raise RuntimeError(name+': '+result.stderr[-1200:])
            images=sorted(frames.glob('frame-*.png'))
            sheet=Image.new('RGB',(960,((len(images)+3)//4)*157),(30,30,30))
            draw=ImageDraw.Draw(sheet)
            for i,path in enumerate(images):
                with Image.open(path) as image:
                    sheet.paste(image,(i%4*240,i//4*157+20))
                draw.text((i%4*240+3,i//4*157+3),f'{name} ~{(i+.5)*args.interval:g}s',fill='white')
            sheet.save(dest/(name+'-sheet.png'))
            summaries.append(dict(file=row['path'],sampled_frames=len(images),sheet=name+'-sheet.png'))
            print(name, 'sampled frames:',len(images),flush=True)
    (dest/'inventory.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()

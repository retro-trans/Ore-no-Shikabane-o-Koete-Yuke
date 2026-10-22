"""Space the Downpour effects; native auto-sizing widens its banner. Dry run first."""
import argparse
import hashlib
import json

from catalog_text import ROOT, parse_mlt
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import root_entries, rebuild_ez, rebuild_root, rebuild_mlt
from check_translation import tokens_equal
from strip_jp import export

V = '0.2.46'
RID = 'ore:00027000:0000:11:0001'
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.45'
    elf = (src / 'EBOOT.help.elf').read_bytes()
    data = (src / 'data.help.ore').read_bytes()
    assert sha(elf) == '2310261f36d77ec9a87da5cc9d8229a1b17a32fde0ff961b561d675d1a76fedc'
    assert sha(data) == '2523b20c6053278c8c806b4369b9a152ae5c208b489b0ba7c4db41c2960e90d9'
    path = ROOT / 'work/translation/en/ui_batch_011.json'
    batch = json.loads(path.read_text(encoding='utf-8'))
    row = next(r for r in batch['rows'] if r['id'] == RID)
    before = '[<e青]Downpour[>]\nFire power [<c青]DOWN↓[>]/Poor visibility'
    after = before.replace('[>]/Poor', '[>] / Poor')
    assert row['translation_en'] in (before, after)
    assert tokens_equal(row['source_jp'], after)
    assert sha(row['source_jp'].encode()) == row['source_sha256']
    row['translation_en'] = after
    row['fit_status'] = 'pending_runtime_' + V
    note = 'Weather effects: spaces around slash; native auto-size and centered alignment retained.'
    if note not in row.setdefault('review_notes', []):
        row['review_notes'].append(note)
    batch['version'] = V
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original)
    be, bend = root_entries(data)
    rootmap = {o: next(x[3] for x in be if x[0] == i) for i, _, _, o in oe}
    base = rootmap[0x27000]
    arc, entries = container(data, base)
    oldmlt = member(arc, entries, 0)
    oldrows = {(s,i):t for s,i,_,t in parse_mlt(oldmlt)}
    assert oldrows[(11,1)] == before
    newmlt = rebuild_mlt(oldmlt, {(11,1):after})
    newrows = {(s,i):t for s,i,_,t in parse_mlt(newmlt)}
    assert newrows == {k: after if k == (11,1) else v for k,v in oldrows.items()}
    changes = {base: rebuild_ez(arc, {0:pack(newmlt)})}
    changed_members = {base:{0}}
    tb = rootmap[0x1e8000]
    ta, te = container(data, tb)
    ot, ote = container(original, 0x1e8000)
    title, preview, fr = footer(member(ot, ote, 25), V)
    changes[tb] = rebuild_ez(ta, {25:pack(title)})
    changed_members[tb] = {25}
    ore = rebuild_root(data, changes, mutable=True)
    ae, aend = root_entries(ore)
    for n, (a,b) in enumerate(zip(be,ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend) - (a[2]&2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend) - (b[2]&2047)
        aa, bb = data[a[3]:sa], ore[b[3]:sb]
        if a[3] not in changes:
            assert aa == bb
        else:
            _, ar = container(aa,0)
            _, br = container(bb,0)
            for j, ((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in changed_members[a[3]]:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V, source_version='0.2.45', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore),
        text=dict(id=RID, before=before, after=after),
        native_layout=dict(weather_constructor='0x08891078..0x08891124',
            text_assignment='0x088910e4', center_alignment='0x088910f0',
            auto_size='0x088910fc calls 0x088244b0 with a1=0',
            width_rule='Longest rendered line plus 16 pixels; centered by native layout',
            effect='Two added spaces also widen the frame automatically'),
        checks=dict(executable='Byte-identical to 0.2.45; no added code/RAM',
            text='Only two separator spaces; every word, newline and markup token retained',
            archive='Only weather text and title version; other text rows and member/root payloads unchanged',
            prior_fixes='Preserved'), footer=fr, runtime_verification='pending', github_release=False)
    return elf, ore, preview, report, path, batch


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    elf, ore, preview, report, path, batch = build()
    print(json.dumps({k:v for k,v in report.items() if k != 'footer'}, indent=2))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'data.weather.ore').exists()
        (out / 'EBOOT.weather.elf').write_bytes(elf)
        (out / 'data.weather.ore').write_bytes(ore)
        (out / 'weather.report.json').write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8')
        ui = ROOT / ('work/ui/weather-spacing-' + V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
        path.write_text(json.dumps(batch, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        path.with_suffix('.en.json').write_text(json.dumps(export(path), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')

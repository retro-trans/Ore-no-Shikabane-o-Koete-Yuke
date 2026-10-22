"""Reflow overflowing prologue passages without changing words. Dry run first."""
import argparse
import hashlib
import json

from catalog_text import ROOT, parse_mlt
from check_translation import tokens_equal
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import root_entries, rebuild_ez, rebuild_mlt, rebuild_root
from strip_jp import export

V = '0.2.41'
EDITS = {
    'ore:00683000:0000:00:0004': (
        'But now,\na man and a woman had taken up the challenge\nand were at last about to work a miracle.',
        'But now, a man and a woman\nhad taken up the challenge and were\nat last about to work a miracle.'),
    'ore:06f77000:0000:00:0000': (
        'Hah... hah...\nBastards put up more of a fight than I expected...',
        'Hah... hah...\nBastards put up more of a fight\nthan I expected...'),
    'ore:06f77000:0000:00:0003': (
        "No. My breasts\nare getting full of milk.\nOur baby's probably crying with hunger by now.",
        "No. My breasts are getting full of milk.\nOur baby's probably crying with\nhunger by now."),
}
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.40'
    elf = (src / 'EBOOT.scratch.elf').read_bytes()
    data = (src / 'data.scratch.ore').read_bytes()
    assert sha(elf) == 'eefe8ff11a6ceb4e8a34d71095370e285c4dbee6d6c9fb41c7ceea032a61b1e7'
    assert sha(data) == '5d8314d68b6b7aea6e37fb7a9a9e0e40c62d8c2dc03a67f6747b217ca6a9c7dc'
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe, _ = root_entries(original)
    be, bend = root_entries(data)
    rootmap = {o: next(x[3] for x in be if x[0] == i) for i, _, _, o in oe}
    glyphs = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    def widths(text):
        return [round(sum(glyphs[str(ord(c))]['advance'] for c in line) * 12 / 14, 3)
                for line in text.split('\n')]
    batches, updates, audit, exceptions = {}, {}, [], []
    for name in ['initial_batch', 'events_batch_001']:
        p = ROOT / ('work/translation/en/' + name + '.json')
        batch = json.loads(p.read_text(encoding='utf-8'))
        for row in batch['rows']:
            if row['file'] not in ['prologue.mlb', 'ev_op_00.mlb', 'ev_op_01.mlb', 'ev_op_02.mlb']:
                continue
            rid, old = row['id'], row['translation_en']
            before, new = EDITS.get(rid, (old, old))
            assert old in (before, new)
            assert before.split() == new.split(), 'Every word and punctuation must survive'
            assert tokens_equal(row['source_jp'], new)
            assert sha(row['source_jp'].encode()) == row['source_sha256']
            ws = widths(new)
            # Native 288px portrait panel: 10px text inset, right border and
            # shadow clearance, with 14px extra space for the advance icon.
            assert len(ws) <= 3 and all(w <= 268 for w in ws[:-1]) and ws[-1] <= 254, (rid, ws)
            audit.append(dict(id=rid, file=row['file'], translation=new,
                before_widths=widths(before), line_widths=ws, changed=rid in EDITS,
                font_size=12, nonfinal_budget=268, final_budget=254,
                fit_status='measured; runtime pending' if rid in EDITS else 'measured; unchanged'))
            if rid not in EDITS:
                continue
            if row['source_jp'].count('\n') != new.count('\n'):
                exceptions.append(dict(id=rid, source_sha256=row['source_sha256'],
                    translation_sha256=sha(new.encode()), source_lines=row['source_jp'].count('\n') + 1,
                    target_lines=new.count('\n') + 1, reason='User-requested English dialogue reflow'))
            row['translation_en'] = new
            row['fit_status'] = 'pending_runtime_' + V
            note = 'Prologue reflow: full wording preserved; at most three native 12px lines, 268px advance budget and 254px final-line budget including icon clearance.'
            if note not in row.setdefault('review_notes', []):
                row['review_notes'].append(note)
            batch['version'] = V
            batches[p] = batch
            base = rootmap[row['archive_offset']]
            updates.setdefault(base, {}).setdefault(row['member_entry'], {})[(row['section'], row['index'])] = (before, new)
    assert len(audit) == 36 and sum(x['changed'] for x in audit) == len(EDITS)
    changed, changed_members = {}, {}
    for base, members in updates.items():
        arc, entries = container(data, base)
        patches = {}
        for entry, rows in members.items():
            oldmlt = member(arc, entries, entry)
            lookup = {(s, i): t for s, i, _, t in parse_mlt(oldmlt)}
            assert all(lookup[k] == a for k, (a, b) in rows.items())
            newmlt = rebuild_mlt(oldmlt, {k: b for k, (a, b) in rows.items()})
            actual = {(s, i): t for s, i, _, t in parse_mlt(newmlt)}
            assert actual == {k: rows[k][1] if k in rows else t for k, t in lookup.items()}
            patches[entry] = pack(newmlt)
        changed_members[base] = set(patches)
        changed[base] = rebuild_ez(arc, patches)
    tb = rootmap[0x1e8000]
    ta, te = container(data, tb)
    ot, ote = container(original, 0x1e8000)
    title, preview, fr = footer(member(ot, ote, 25), V)
    changed[tb] = rebuild_ez(ta, {25: pack(title)})
    changed_members[tb] = {25}
    ore = rebuild_root(data, changed, mutable=True)
    ae, aend = root_entries(ore)
    for n, (a, b) in enumerate(zip(be, ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend) - (a[2] & 2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend) - (b[2] & 2047)
        aa, bb = data[a[3]:sa], ore[b[3]:sb]
        if a[3] not in changed:
            assert aa == bb
        else:
            _, ar = container(aa, 0)
            _, br = container(bb, 0)
            for j, ((_, z, p, _), (_, zz, pp, _)) in enumerate(zip(ar, br)):
                if j not in changed_members[a[3]]:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V, source_version='0.2.40', elf_sha256=sha(elf), archive_sha256=sha(ore),
        elf_bytes=len(elf), archive_bytes=len(ore), audited_passages=len(audit), changed_passages=len(EDITS),
        checks=dict(words_and_punctuation='unchanged', controls='unchanged', row_identity_and_counts='unchanged',
            other_text_rows='unchanged', unrelated_root_and_member_payloads='byte-identical',
            mlt_and_compression_roundtrip='pass', executable='byte-identical to 0.2.40; scratch and prompt fixes preserved'),
        footer=fr, runtime_verification='pending', github_release=False)
    layout = dict(version=V, scope='All six opening narration records and all thirty opening event dialogue records',
        rows=audit, line_break_exceptions=exceptions, texture_replacement=False, runtime_verification='pending')
    return elf, ore, preview, report, layout, batches


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    elf, ore, preview, report, layout, batches = build()
    print(json.dumps(dict(report={k: v for k, v in report.items() if k != 'footer'},
        changed=[r for r in layout['rows'] if r['changed']]), indent=2))
    if args.write:
        out = ROOT / ('work/output/english-native-' + V)
        out.mkdir(exist_ok=True)
        assert not (out / 'data.prologue.ore').exists()
        (out / 'EBOOT.prologue.elf').write_bytes(elf)
        (out / 'data.prologue.ore').write_bytes(ore)
        (out / 'prologue.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        ui = ROOT / ('work/ui/dialogue-reflow-' + V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
        (ui / 'layout.json').write_text(json.dumps(layout, indent=2) + '\n', encoding='utf-8')
        for p, batch in batches.items():
            p.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            p.with_suffix('.en.json').write_text(json.dumps(export(p), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')

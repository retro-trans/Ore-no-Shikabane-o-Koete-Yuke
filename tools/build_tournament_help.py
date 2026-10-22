"""Repair reported public-build Help/tournament text. Dry run before --write."""
import argparse
import hashlib
import json
import re
import struct

from catalog_text import ROOT, parse_mlt
from build_menu_fixes import container, member, pack
from build_latin_auto import footer
from repack_text import align, root_entries, rebuild_ez, rebuild_root, rebuild_mlt
from check_translation import tokens_equal
from strip_jp import export

V = '0.2.48'
BASE = 0x08803000
HELP_ID = 'ore:0000c000:0019:01:0214'
HELP = ('Um... Well... What I mean is...\n'
        'If you could prepare yourself and think,\n'
        '"Perhaps it\'s almost time.\n'
        'I\'ll make \u25cb\u25cb the next head,"\n'
        'it would make things a little easier for me too...\n'
        'I\'m sorry for being so selfish.')
SHORT = {1:"Seimei's Circle",3:'Urabe-Watanabe',4:'Kintaro HQ',5:'Suzakumon Guard',
    6:'Capital Defense',7:'Patriot Dancers',8:'Seishin Vols.',9:'Ritsumeikan Trio',
    11:'Hieizan Monks',12:'Fushimi Dojo',13:'Modoribashi Gd.',14:'Keihan Mercs',
    17:'Blossom Assault',18:'Asahi Chargers',19:'33 Bays Society',20:'Stone-Fire Soc.',
    21:'Shimogamo Band',22:'White Lily Aid',23:'First Star Squad',24:'Mukomachi Rebel',
    25:'Doshisha Boxing',27:'Ikeda Main House',28:'Uzumasa Swords',30:'Honganin Select',
    31:'Kyogoku Assn.',32:'Chayamachi Assn.',33:'Maruyama Gang'}
sha = lambda b: hashlib.sha256(b).hexdigest()


def build():
    src = ROOT / 'work/output/english-native-0.2.47'
    source = (src / 'EBOOT.union.elf').read_bytes()
    data = (src / 'data.union.ore').read_bytes()
    assert sha(source) == '98ac28a585ada0ed4d46cadeb4b5fd64159ae844301fad9785d15125c9e03bd1'
    assert sha(data) == '471e2e951ef20a68972908f4da5b4223c2f1b58f6b4ae66238d8f8b8681ebfc5'
    elf = bytearray(source)
    po = struct.unpack_from('<I',elf,28)[0]
    ph = list(struct.unpack_from('<8I',elf,po+32))
    assert ph[1]+ph[4] == len(elf)
    elf.extend(bytes(align(len(elf),4)-len(elf)))
    emperor = ph[2]+len(elf)-ph[1]
    elf.extend(b'Emperor\0')
    patches = []
    allowed = set(range(po+48,po+56))
    for pc,old,new in [(0x08914a84,0x3c0408a4,0x3c040000|((emperor+0x8000)>>16)),
                       (0x08914a8c,0x2484e20c,0x24840000|(emperor&65535))]:
        off = pc-BASE
        assert struct.unpack_from('<I',elf,off)[0] == old
        struct.pack_into('<I',elf,off,new)
        allowed.update(range(off,off+4))
        patches.append(dict(address=hex(pc),before=hex(old),after=hex(new)))
    ph[4] = ph[5] = len(elf)-ph[1]
    struct.pack_into('<8I',elf,po+32,*ph)
    assert all(a == b or i in allowed for i,(a,b) in enumerate(zip(source,elf)))
    metrics = json.loads((ROOT / 'work/ui/vwf_metrics.json').read_text())['glyphs']
    def measure(text,size=12):
        return round(sum(22*14/size if c == '\u25cb' else metrics[str(ord(c))]['advance']
            for c in re.sub(r'\[.*?\]','',text))*size/14,3)
    original = (ROOT / 'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    oe,_ = root_entries(original)
    be,bend = root_entries(data)
    rootmap = {o:next(r[3] for r in be if r[0] == i) for i,_,_,o in oe}
    batches,updates,edits,aliases,team_fit = {},{},{},[],[]
    for name in ['ui_batch_008','ui_batch_014']:
        path = ROOT / ('work/translation/en/'+name+'.json')
        batch = json.loads(path.read_text(encoding='utf-8'))
        for row in batch['rows']:
            before = row['translation_en']
            after = before
            if row['id'] == HELP_ID:
                after = HELP
                assert before.split() == after.split()
                assert len(after.split('\n')) == 6
                assert all(measure(line) <= 330 for line in after.split('\n'))
            elif row['file'] == 'eMltGozen.mlb' and row['section'] == 0 and row['index'] == 43:
                after = before.replace('\n\u30fb','\n- ')
                assert after.count('\n- ') == 2
            elif row['file'] == 'eMltGozen.mlb' and row['section'] == 5 and row['index'] > 0:
                after = SHORT.get(row['index'],before)
                assert measure(after) <= 112,(after,measure(after))
                team_fit.append(dict(id=row['id'],text=after,advance=measure(after),budget=112))
                if after != before:
                    aliases.append(dict(id=row['id'],full_name=before,display_name=after))
            if after == before:
                continue
            assert tokens_equal(row['source_jp'],after),row['id']
            assert sha(row['source_jp'].encode()) == row['source_sha256']
            row['translation_en'] = after
            row['fit_status'] = 'pending_runtime_' + V
            note = 'Public screenshot fix: native font-safe bullets, full-word Help reflow, and concise tournament team names; controls retained.'
            if note not in row.setdefault('review_notes',[]):
                row['review_notes'].append(note)
            edits[row['id']] = dict(before=before,after=after)
            key = (row['section'],row['index'])
            updates.setdefault(rootmap[row['archive_offset']],{}).setdefault(row['member_entry'],{})[key] = (before,after)
        batch['version'] = V
        batches[path] = batch
    assert len(team_fit) == 33 and len(aliases) == len(SHORT)
    assert len(edits) == len(SHORT)+2
    changes,changed_members = {},{}
    for base,members in updates.items():
        arc,entries = container(data,base)
        packed = {}
        for entry,rows in members.items():
            oldmlt = member(arc,entries,entry)
            lookup = {(s,i):t for s,i,_,t in parse_mlt(oldmlt)}
            assert all(lookup[k] == before for k,(before,after) in rows.items())
            newmlt = rebuild_mlt(oldmlt,{k:after for k,(before,after) in rows.items()})
            actual = {(s,i):t for s,i,_,t in parse_mlt(newmlt)}
            assert actual == {k:rows[k][1] if k in rows else t for k,t in lookup.items()}
            packed[entry] = pack(newmlt)
        changes[base] = rebuild_ez(arc,packed)
        changed_members[base] = set(packed)
    tb = rootmap[0x1e8000]
    ta,te = container(data,tb)
    ot,ote = container(original,0x1e8000)
    title,preview,fr = footer(member(ot,ote,25),V)
    changes[tb] = rebuild_ez(ta,{25:pack(title)})
    changed_members[tb] = {25}
    ore = rebuild_root(data,changes,mutable=True)
    ae,aend = root_entries(ore)
    for n,(a,b) in enumerate(zip(be,ae)):
        sa = (be[n+1][3] if n+1 < len(be) else bend)-(a[2]&2047)
        sb = (ae[n+1][3] if n+1 < len(ae) else aend)-(b[2]&2047)
        aa,bb = data[a[3]:sa],ore[b[3]:sb]
        if a[3] not in changes:
            assert aa == bb
        else:
            _,ar = container(aa,0)
            _,br = container(bb,0)
            for j,((_,z,p,_),(_,zz,pp,_)) in enumerate(zip(ar,br)):
                if j not in changed_members[a[3]]:
                    assert aa[p:p+z] == bb[pp:pp+zz]
    report = dict(version=V,source_version='0.2.47',elf_sha256=sha(elf),archive_sha256=sha(ore),
        elf_bytes=len(elf),archive_bytes=len(ore),literal=dict(translation='Emperor',address=hex(emperor),bytes=8,
            original_literal='0x08a3e20c',patches=patches),edits=edits,team_aliases=aliases,team_fit=team_fit,
        help_line_advances=[measure(line) for line in HELP.split('\n')],
        checks=dict(help='Every word and punctuation retained; six lines within the existing 330px area',
            font='Rules use ASCII list markers; existing 0.2.39 Circle/Triangle font support retained',
            teams='All 33 fixed teams measured within 112px at 12px; six already-fitting names unchanged',
            controls='Unchanged',archive='Changed rows and title only; other rows and member/root payloads checked unchanged',
            executable='Two literal pointer arguments and segment byte counts; 8-byte English literal, no added code',
            prior_fixes='Preserved'),footer=fr,runtime_verification='pending',github_release=False)
    return elf,ore,preview,report,batches


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    elf,ore,preview,report,batches = build()
    print(json.dumps({k:v for k,v in report.items() if k not in ['footer','edits','team_aliases','team_fit']},indent=2))
    print('Changed text records:',len(report['edits']),'shortened team names:',len(report['team_aliases']))
    if args.write:
        out = ROOT / ('work/output/english-native-'+V)
        out.mkdir(exist_ok=True)
        assert not (out / 'EBOOT.tournament.elf').exists()
        (out / 'EBOOT.tournament.elf').write_bytes(elf)
        (out / 'data.tournament.ore').write_bytes(ore)
        (out / 'tournament.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        ui = ROOT / ('work/ui/tournament-help-'+V)
        ui.mkdir(exist_ok=True)
        preview.save(ui / 'native-footer.png')
        for path,batch in batches.items():
            path.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            path.with_suffix('.en.json').write_text(json.dumps(export(path),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        glossary = ROOT / 'work/glossary/tournament-team-display.en.json'
        glossary.write_text(json.dumps(dict(version=V,language='en',reason='Readable tournament bracket labels',
            aliases=report['team_aliases']),indent=2)+'\n',encoding='utf-8')
    print('Written.' if args.write else 'DRY RUN: no files written.')

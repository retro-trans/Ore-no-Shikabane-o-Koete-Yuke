"""Audit standalone root MLT resources overlooked by the EZBIND catalog."""
import argparse
import collections
import json

from catalog_text import ROOT, parse_mlt, unpack_member
from repack_text import root_entries


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    data=(ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()
    entries,end=root_entries(data)
    standalone=[]
    for n,(i,_,packed,base) in enumerate(entries):
        stop=entries[n+1][3] if n+1<len(entries) else end
        payload=data[base:stop-(packed&2047)]
        if payload.startswith(b'EZBIND'):continue
        decoded,compression=unpack_member(payload)
        if decoded[:3]!=b'MLT':continue
        rows=list(parse_mlt(decoded))
        standalone.append(dict(root_index=i,original_offset=hex(base),bytes=len(decoded),
                               compression=compression,records=len(rows),
                               records_by_section=dict(collections.Counter(r[0] for r in rows))))
    report=dict(version='0.2.8',root_payloads_checked=len(entries),standalone_mlt=standalone,
                scope_correction='The earlier 100% draft figure covered catalogued EZBIND text. Standalone root 27 adds 14 UI prompts, translated in 0.2.8, and 1735 original Japanese player-name choices retained as name-generation data.',
                other_payloads='This signature audit does not establish that every non-MLT binary or image is text-free.')
    print(json.dumps(report,indent=2))
    if args.write:
        (ROOT/'docs/standalone_root_text_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()

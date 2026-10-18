"""Prepare the five reported setup UI fixes. Inspect the dry run before --write."""
import argparse
import hashlib
import json

from catalog_text import ROOT, parse_mlt
from check_translation import tokens_equal

VERSION = '0.2.8'
LABELS = ['Input', 'Auto', 'Auto', 'OK',
          'This contains unsupported characters.',
          'Family name[w2]:[w2]%s', 'Given name[w2]:[w2]%s',
          "Boy's name[w2]:[w2]%s", "Girl's name[w2]:[w2]%s",
          'Up to 3 characters', '"%s", correct?', '%s, correct?',
          '"%s", correct?',
          'The %@ clan already has someone\nwith that name.\nPlease choose another name.']


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    changes = []
    batches = []
    for name in ['initial_batch','ui_batch_002']:
        path = ROOT/('work/translation/en/'+name+'.json')
        data = json.loads(path.read_text(encoding='utf-8'))
        for row in data['rows']:
            old = row['translation_en']
            new = old.replace('％','%%')
            if row['id'] == 'ore:001e8000:0000:02:0001':
                new = "Next, please enter your family name.\nYou'll only enter it once.\nPlease take care to use the correct kanji."
            if row['id'] == 'ore:001e8000:0000:04:0004':
                new = new.replace('Battle Experience','Battle EXP')
            if row['id'] == 'ore:001e8000:0000:02:0015':
                new = 'Japanese Lad'
            if row['id'] == 'ore:001e8000:0000:02:0016':
                new = 'Japanese Maiden'
            if row['file']=='title.mlb' and row['section']==6 and row['index']<4:
                new = '%1:02d/%2:02d/%3:02d'
            if old != new:
                assert tokens_equal(row['source_jp'],new)
                assert new.count('\n') == row['source_jp'].count('\n')
                row['translation_en'] = new
                row['fit_status'] = 'pending_0.2.8_runtime_check'
                row.setdefault('review_notes',[]).append('0.2.8 setup UI correction: measured overflow, Gregorian display, or ASCII percent escaping. Numeric arguments and original controls remain intact.')
                changes.append(dict(id=row['id'],before=old,after=new))
        data['version'] = VERSION
        batches.append((path,data))
    original = (ROOT/'work/source/iso/PSP_GAME/USRDIR/data.ore').read_bytes()[0x3B9800:0x3B9800+17856]
    records = list(parse_mlt(original))
    prompts = [r for r in records if r[0]==0]
    assert len(prompts)==len(LABELS)==14
    rows = []
    for (section,index,offset,jp), en in zip(prompts,LABELS):
        assert tokens_equal(jp,en) and jp.count('\n')==en.count('\n')
        rows.append(dict(id=f'root:0027:{section:02d}:{index:04d}',file='root_27_name_entry.mlb',
                         archive_offset=0x3B9800,member_entry=None,section=section,index=index,
                         text_offset=offset,source_jp=jp,source_sha256=hashlib.sha256(jp.encode()).hexdigest(),
                         category='name_entry_ui',translation_en=en,status='draft',kind='ui',
                         context='Standalone root payload 27, name-entry controls and confirmation. Auto retains the original Japanese player-name pools; three-character input limit is unchanged.',
                         fit_status='pending_0.2.8_runtime_check',meaning_review='self_reviewed',review_notes=[]))
    batch = dict(schema_version=1,version=VERSION,language='en',status='draft',rows=rows)
    print(json.dumps(dict(version=VERSION,archive_edits=changes,new_name_entry_prompts=LABELS,
                          retained_player_name_records=len(records)-14,mode='write' if args.write else 'dry run'),indent=2))
    if args.write:
        for path,data in batches:
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        dest=ROOT/'work/translation/en/name_entry'
        dest.mkdir(parents=True,exist_ok=True)
        (dest/'prompts.json').write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()

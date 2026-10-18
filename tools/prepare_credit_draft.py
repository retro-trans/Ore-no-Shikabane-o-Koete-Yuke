"""Prepare researched credit names and notices; dry run by default."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    'https://www.mobygames.com/game/163091/over-my-remain/credits/psp/?autoplatform=true',
    'https://w.atwiki.jp/oreshikar/pages/48.html',
    'https://www.mobygames.com/game/63167/tales-of-the-heroes-twin-brave/credits/psp/',
]
# Source coordinates are explicit. Unverified readings are deliberately absent;
# a common possible reading alone does not establish a real person's name.
NAMES = {
141:'Konami Yoshida',142:'Minami Takayama',143:'Yusaku Yara',144:'Mami Koyama',145:'Kenyu Horiuchi',
146:'Kanako Tojo',147:'Akane Ueda',148:'Akiko Koike',149:'Kenichiro Matsuda',150:'Haruo Sato',
151:'Eiji Takeuchi',152:'Kengo Takanashi',153:'Tomoaki Maeno',154:'Harumi Asai',
155:'Shoji Masuda',156:'Tetsuya Sasaki',157:'Makoto Sajima',158:'Lioko Kihara',159:'Katsuya Kira',
160:'Naoki Suda',161:'Takeshi Maeda',162:'Susumu Cho',164:'Ryuichi Sugashira',165:'Hiroshi Hasegawa',
166:'Koji Yamamoto',167:'Kazuhiro Okada',168:'Keisuke Nishihara',169:'Masatoshi Fukazawa',
170:'Masahide Kobayashi',171:'Masayuki Nagata',172:'Sasaki 2nd.',175:'Masaki Morita',
176:'Hisashi Sakaue',177:'Kenji Nagata',178:'Kazuaki Okada',179:'Ryoji Otsuka',180:'Hideki Watanabe',
181:'Tatsuya Nagata',182:'Yuki Azuma',183:'Yusuke Uemura',185:'Urara Takagi',186:'Takeharu Shima',
187:'Toyoji Tahira',188:'Tomoya Ohhara',189:'Shinpei Suzuki',190:'Shiori Maehara',
192:'Kazutaka Katoku',193:'Toru Kume',194:'Junichi Ueda',195:'Miku Sonoda',196:'Kei Harano',
197:'Azusa Iwahana',198:'Megumi Ueno',199:'Akiko Koyama',200:'Homare',201:'Takuya Yasuda',
202:'Kota Nakashima',203:'Masaaki Kokubu',209:'Kyosuke Onoue',210:'Kenichi Koga',211:'Koji Hisatomi',
212:'Yumiko Ezaki',213:'Yoshito Kuwa',214:'Takatoshi Anbe',215:'Tomohiro Nishikawa',
216:'Hiroyuki Saito',217:'Tatsuro Arai',218:'Yusei Kawada',220:'Seiki Tanaka',221:'Ryuji Kumano',
222:'Akira Ishida',223:'Rendo Kurosaki',224:'Yun Kouga',225:'Ajiko Kojima',226:'Tomomi Kobayashi',
227:'Misaki Saito',228:'Miku Sonoda',229:'toi8',230:'Hiro Touge',231:'Shiho Enta',232:'Ching Nakamura',
233:'Kaoru Fukaya',234:'huke',235:'Ju Ayakura',236:'Hiroyuki Maeda',237:'Haruyuki Morisawa',
238:'Mitsuo Kusakabe',239:'Shigeru Yamazaki',240:'Miyuki Shimabukuro',241:'Akihiro Kanayama',
242:'Yutaka Kawasuji',243:'Kenzo Koizumi',244:'Takashi Asakura',245:'Keiichi Ichikawa',
246:'Masayuki Takagi',247:'Yoshihiro Taniguchi',248:'Yuko Kiyoshima',249:'Saori Tomita',
253:'Shindo Production',254:'E&G Films',255:'M.I',256:'Sunshine Corporation',257:'Maasa',
258:'HEE WON CORPORATION',259:'Keiko Ogimori',260:'Kazuko Sato',261:'Natsuko Takio',
262:'Kazumi Hasegawa',263:'Aki Watanabe',264:'Kazumi Yamazaki',265:'Yukiko Hida',266:'Koji Abe',
267:'Trans Arts',268:'Kazushi Torigoe',269:'Yasuyuki Kuroki',270:'Falcon',271:'Tovic',
272:'Toei Kakou',273:'Noriyoshi Matsuura',274:'Mitsuyoshi Maruyama',275:'Katsumi Ito',
276:'GEN',277:'GEN',278:'Noriko Nishimiya',280:'Masayoshi Ozaki',281:'Studio SIGN',
282:'Kazuhiko Toyama',284:'Kiyoshi Okabe',285:'Ryogen Kihara',286:'Gokigen Band',
287:'Hiroki Miyano',288:'Yukihiro Takao',289:'Masatoshi Kainuma',290:'Kazuki Yao (Special Appearance)',
291:'Makoto Ishii',292:'Everyone in the Celebrated Party Orchestra',
299:'Midori Shimazawa',300:'Akihiro Yamada',301:'Swara Pro',302:'Sunset Studio',303:'Three S Studio',
304:'Midori Shimazawa',305:'Sayaka Iba',306:'Yuichiro Kubo',307:'Ryunosuke Miyazaki',308:'Shin Maekawa',
309:'Everyone who contributed ideas for Divine Union and Last Words',
310:"'Haruka: Tenku no Yamataikoku' / 'Haruka: Enten no Yamataikoku'",
311:'Author: Shoji Masuda',312:'Illustrator: Makoto Sajima',313:'Publisher: Enterbrain, Inc.',
314:'© Shoji Masuda Printed in Japan 2007, 2008',
315:'Tokuo Onuma',316:'Kunimasa Kitazawa',317:'Manabu Muto',318:'Toshimitsu Sueyoshi',
319:'Kazuyuki Tsuji',320:'Yuki Kofuji',323:'Megumi Onozuka',326:'Ryota Motoki',327:'Nobuaki Ueno',
330:'Ayaka Konishi',331:'Shinya Nakamura',332:'Naoko Isono',334:'Sachie Matsuda',
335:'Satoshi Takemae',336:'Shota Tobari',337:'Shigeru Kawai',338:'Yukie Katayama',339:'Shinpei Yamaguchi',
340:'Ryo Sogabe',341:'Noriko Fujisaki',342:'Masashi Nakamura',343:'Hironori Komiya',344:'Atsuyuki Sakimae',
345:'Yasuko Nii',346:'Tetsutaro Nishimoto',347:'Kenji Suganuma (SMC)',348:'Kanako Kusunoki (SMC)',
349:'Kenichiro Yasuhara (Toyotamaya)',350:'Shigeo Suzuki (ROUND DESIGN)',
352:'Satoshi Satake',353:'Go Ando',354:'Megumi Hayasaka',355:'Akiko Matsubara',356:'Koji Kitakawa',
357:'Kazuhiro Noya',358:'Taku Nishijima',359:'Akiko Teramoto',360:'Kayo Ishikawa',
361:'Yoshinori Matsumoto',362:'Ichiro Nemoto',363:'Mayuko Aoki',364:'Satoshi Tamaki',365:'Yasuzo Katayose',
366:'Satoshi Shirakawa',367:'Koichi Kodama',368:'Rumiko Shoji',369:'Hisao Wada',370:'Koji Tada',
371:'Yumi Chihara',372:'Reiko Ishida',375:'Hiroyuki Kotani',377:'Yuka Kojima',378:'Ai Kaneko',
379:'Yuka Orihara',380:'Takeshi Kajii',381:'Kohei Adachi',382:'Tatsuro Nakamura',
383:'Yasuhide Kobayashi',384:'Wataru Kato',385:'Junichi Yoshizawa',386:'Daisaku Ikejiri',
387:'Takahiro Kaneko',388:'Masami Yamamoto',389:'Allan Becker',390:'Shuhei Yoshida',391:'Hiroshi Kawano',
392:'DynaComware Corp.',393:'ASCII Media Works, Inc.',394:'Enterbrain, Inc.',395:'MARS Corporation',
396:'Alfa System Co., Ltd.',397:'Sony Computer Entertainment Inc.',398:'???',399:'(MARS Corporation)',
400:'(Alfa System Co., Ltd.)',401:'(Visual Workshop)',402:'(Studio Gouache)',403:'(Studio Shadow)',
404:'(P.P.M)',405:'(Sony Computer Entertainment Inc.)',406:'(Riverside Music)',407:'(Soytzer Music)',
408:'(S-Prism)',409:'(SMC)',410:"DynaFont is DynaComware Taiwan Inc.'s",411:'registered trademark.',
412:'(Enterbrain, Inc.)',413:'(ASCII Media Works, Inc.)',
}

# Later research: published readings matched against the same sound-production
# roles, rather than unrelated people sharing the same kanji.
RESEARCH = {
    163: ('Kentaro Tsunada', 'https://gamefaqs.gamespot.com/vita/685564-oreshika-tainted-bloodlines/credit',
          'Scenario-support name in the English sequel credits; kana corroborated by https://www.daiwair.co.jp/td_download.cgi?c=3632&i=2110045 . Identity matched by series and scenario role, not the contract name alone.'),
    173: ('Jun Hotta', 'https://gamefaqs.gamespot.com/vita/685564-oreshika-tainted-bloodlines/credit',
          'Effect-programming credit in the English sequel matches the Japanese PSP effect-programming name. Identity inferred from the same series, employer and role; unrelated people with similar names were excluded.'),
    184: ('Jun Sakamoto', 'https://gamefaqs.gamespot.com/vita/685564-oreshika-tainted-bloodlines/credit',
          'English sequel character-modeling credit matched to the developer and CEDEC Japanese biography: https://www.alfasystem.net/a_m/diary.cgi?page=5 . Identity inferred from the same series, employer and modeling role.'),
    283: ('Konosuke Kihara', 'https://pianoland.co.jp/schedule/schedule-23543',
          'Official biography supplies kana and the 2011 PSP arrangement credit; disc uses a different surname kanji.'),
    293: ('Akihiko Shimizu', 'https://www.mobygames.com/game/29202/rurouni-kenshin-ishin-gekitohen/credits/playstation/',
          'Paired reading and kanji in the same Soytzer Music production role; also matched against the original soundtrack credits.'),
    294: ('Takehiro Kawabe', 'https://digitalpr.jp/pdf.php?r=11502',
          'Publisher press release pairs the Japanese and English composer name; soundtrack role corroborates identity.'),
    295: ('Tomoyuki Hoshi', 'https://raido.moe/staff/ps2/ps2_sky_odyssey.html',
          'Bilingual original game credits match the sound-system programmer name and role.'),
    296: ('Youichi Ueda', 'https://downloads.khinsider.com/game-soundtracks/album/ore-no-shikabane-wo-koete-yuke-original-soundtrack-1999',
          'Original soundtrack credit transcription explicitly pairs the sound-tool programmer kanji and romanization.'),
    297: ('Masamichi Seki', 'https://dsdinc.jp/about',
          'Own company biography pairs kanji and romanization and establishes SCE sound-design employment.'),
    298: ('Takafumi Fujisawa', 'https://www.mobygames.com/person/57287/takafumi-fujisawa/',
          'Published kanji/romanization pairing matched against original soundtrack sound-producer credit.'),
}
NAMES.update({i: data[0] for i, data in RESEARCH.items()})

# User explicitly authorized researched project romaji when a personal reading
# cannot be verified. These remain provisional; no source is claimed to prove
# the individual's pronunciation. Alternatives stay in the glossary for review.
PROVISIONAL = {
    174: ('Taichi Tsusaka', 'Tsuzaka is another possible surname reading.'),
    191: ('Hiroshi Matsuzaki', 'Conventional given-name reading; personal reading unverified.'),
    204: ('Kento Ikeda', 'Taketo is another possible given-name reading.'),
    205: ('Shogo Hirata', 'Conventional given-name reading; personal reading unverified.'),
    206: ('Yosuke Iwakawa', 'Conventional reading; personal reading unverified.'),
    207: ('Shuji Tanaka', 'Conventional reading; personal reading unverified.'),
    208: ('Sho Nagaoka', 'Kakeru is another possible given-name reading.'),
    219: ('Ikuo Tama', 'Rare surname; Tama chosen provisionally, not established from the unrelated people found in searches.'),
    250: ('Junko Nakata', 'Nakada is another possible surname reading. The unrelated voice actor was excluded.'),
    251: ('Kayoko Wakayama', 'Conventional reading; the same-name politician does not establish the animator identity.'),
    252: ('Toshie Kawasuji', 'Conventional reading; personal reading unverified.'),
    279: ('Takayuki Otani', 'Conventional reading; personal reading unverified.'),
    321: ('Yohei Ikushima', 'Conventional surname and given-name readings; personal readings unverified.'),
    322: ('Shunichi Wada', 'Disc given name uses hayabusa kanji; Shunichi chosen. Junichi and the secondary listing kanji discrepancy remain unverified.'),
    324: ('Hiroaki Kodama', 'Conventional reading; personal reading unverified.'),
    325: ('Michifumi Nakajima', 'Conventional reading; personal given-name reading unverified.'),
    328: ('Hiroshi Yasumiba', 'Surname dictionaries list Yasumiba, Kyuba, Yasuba, Ikoiba and Yasumba; Yasumiba chosen provisionally.'),
    329: ('Yasushi Kanamaru', 'Conventional given-name reading; Yutaka and Tai are also possible.'),
    333: ('Teppei Shimono', 'Uses the disc surname. The secondary listing identifying Teppei Kabata was rejected as a different surname.'),
    351: ('Takao Nakagawa (ROUND DESIGN)', 'Conventional given-name reading; unrelated company executive was excluded.'),
    373: ('Akihito Kuchikata', 'Surname dictionaries list Kuchikata and Kutsukata; personal surname and given-name readings remain provisional.'),
    374: ('Kenichi Kudo', 'Conventional reading; personal reading unverified.'),
    376: ('Mitsuo Amano', 'Conventional reading; personal reading unverified.'),
}
NAMES.update({i: data[0] for i, data in PROVISIONAL.items()})
PROVISIONAL_SOURCES = {
    328: 'https://name-power.net/fn/%E4%BC%91%E5%A0%B4.html',
    373: 'https://myoji.namedic.jp/sei/detail/%E6%9C%BD%E6%96%B9',
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    c = json.loads((ROOT / 'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    rows = {r['index']: r for r in c if r['file']=='ending.mlb' and r['section']==1}
    missing = [i for i in range(141,414) if i not in NAMES]
    batches = []
    for i in sorted(NAMES):
        if batches and batches[-1]['end'] == i:
            batches[-1]['translations'].append(NAMES[i])
            batches[-1]['end'] += 1
        else:
            batches.append(dict(file='ending.mlb', section=1, start=i, end=i+1, kind='credit_name',
                                context='Original staff-roll name or notice. Published readings are recorded in the credits glossary; '
                                'provisional project readings are explicitly marked in row notes. No gender or biography inferred.',
                                translations=[NAMES[i]], review_notes=['Credit-name research: '+SOURCES[0]]))
    notes = {
        141:'Disc kanji differ from the published voice actor credit; Konami Yoshida follows documented identity.',
        147:'Historical Akane Ueda credit retained; later Akane Ouchi name not substituted.',
        153:'Disc given-name kanji differ from the published actor credit; Tomoaki Maeno follows documented identity.',
        162:'Published Susumu Chou romanization normalized to project ASCII Hepburn without macrons.',
        195:'Miku Sonoda is the documented reading/pen name, not Mirai inferred from kanji.',
        232:'Ching Nakamura is the established artist pen-name reading; not the dictionary reading of the given-name kanji.',
        233:'Kaoru Fukaya follows the modern pronunciation of historical kana kahoru.',
        333:'Not drafted: public credit listing has an apparent identity mismatch; do not substitute an unrelated name.',
        349:'Toyotamaya company name is distinct from Toyoyamaya in a secondary listing; local kanji preserved in the glossary.',
        410:'Trademark notice continues in 411; both original records retained.',
    }
    notes.update({i: data[2] + ' Source: ' + data[1] for i, data in RESEARCH.items()})
    notes.update({i: 'Provisional project romanization, explicitly authorized by the user after research on 2026-10-17. '
                    + data[1] for i, data in PROVISIONAL.items()})
    for b in batches:
        b['row_notes']={str(i):[notes[i]] for i in range(b['start'],b['end']) if i in notes}
    seed=dict(version='0.2.5',batches=batches,untranslated_rows=[dict(file='ending.mlb',section=1,index=i,
          reason='Credited name reading not yet verified; retained in original build until research resolves it.') for i in missing])
    glossary=dict(schema_version=1,version='0.2.5',sources=SOURCES,
                  policy='Staff and artist names only. Gender and personality unknown; no inferred biography. '
                         'Reading discrepancies are documented. User-authorized conventional readings are explicitly provisional, not presented as verified.',
                  entries=[dict(source_id=rows[i]['id'],jp=rows[i]['source_jp'],en=NAMES[i],
                                gender=None,personality=None,role=None,
                                notes=notes.get(i),reading_status='provisional_user_authorized' if i in PROVISIONAL else 'researched',
                                sources=([PROVISIONAL_SOURCES[i],SOURCES[0]] if i in PROVISIONAL_SOURCES else
                                         [RESEARCH[i][1]] if i in RESEARCH else SOURCES[:1])) for i in sorted(NAMES)],
                  unresolved=[dict(source_id=rows[i]['id'],jp=rows[i]['source_jp'],reading=None) for i in missing])
    print(json.dumps(dict(translated=len(NAMES),unresolved_indices=missing,
                          sample=[{k:r[k] for k in ('jp','en','notes')} for r in glossary['entries'][:3]]),ensure_ascii=True,indent=2))
    if args.write:
        for path,obj in [('work/translation/en/credits_batch_001_input.json',seed),('work/glossary/credits.json',glossary)]:
            (ROOT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Credit seed and glossary written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()

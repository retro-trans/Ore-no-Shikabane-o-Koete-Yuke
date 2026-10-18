"""Prepare reviewed portrait captions. Dry run by default; source prose stays local."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Display title, subject name, and caption. Pronunciation fields use the same
# localized subject name; their runtime ordering still needs visual checking.
GROUPS = [
    ('Rice Beauty', 'Hakurakuten Dayu', 'I came to Japan\nfor only one\nreason.\nGreat ukiyo-e,\nMr. Utamaro,\nplease!!!!'),
    ('Tropical-Paradise Beauty', 'Kuronushi Dayu', "I risked my life\non the Black Current\nfor 23 days to Japan.\nMr. Utamaro,\nI've dreamed of you.\nI want to meet soon."),
    ('Startled Beauty', 'Niwatori Dayu', "When I was little,\nI saw Grandma\nwring a chicken's neck.\nEver since then,\nI've lost my voice...\nJust kidding. A lie."),
    ('Heh Heh... Beauty', 'Suzuka Dayu', "When I find\nan ants' nest,\nI pour water in.\nAs they scramble,\nsquish, squish.\nI can't get enough..."),
    ('Bald Beauty', 'Jomyo Dayu', "I've done plenty\nof terrible things...\nThey told me to shave\nmy head. I said,\n'I'm bald already!'\nand got away with it."),
    ('Childlike Beauty', 'Nishikitenjin Dayu', None),
    ('Innocent Beauty', 'Ayagasa Dayu', "I like climbing\nthe pine on the corner\nin Pontocho.\nBeyond Kitayama,\nmy home village...\nStill can't see it."),
    ('Fidgety Beauty', 'Kikusui Dayu', "My specialty takes\nreal commitment!\nI sing songs\nby burping.\nConnoisseurs and the\nhard of hearing love it!"),
    ('Profile Beauty', 'Hakuga Dayu', "I hate the tear mole\non my right cheek.\nIt grows with each cry.\nBefore I knew it,\nI'd taken to turning\nmy face to the right."),
    ('The True Kyoto Beauty!', 'Minami Kannon Dayu', "Kita Kannon Dayu\nis my imitation.\nAlways cross-legged,\npicking her nose\nand eating it...\nSo the rumors say."),
    ('Refreshing Beauty', 'Tsuki Dayu', "Full moons\nmake me hungry.\nI eat everything\nuntil my face is rounder\nthan the full moon.\nStill like me?"),
    ('Ooh La La Beauty', 'Shijokasa Dayu', "My hobby is\nmaking dolls.\nBundle up some straw\nin a human shape,\ndrive in a big nail,\nand there you are!"),
    ('Bighearted Beauty', 'Tokusa Dayu', "My earnings feed\nmy husband and\neight brats. It's hard,\nbut with love,\nyou somehow\nmake it work."),
    ('Bashful Beauty', 'Koi Dayu', "I found a cat\nunder Gojo Bridge.\nIt goes 'Woof!'\nso I named it\n'Chuta,'\nlike a mouse."),
    ('Lucky Pussy Beauty', 'Iwato Dayu', "A samurai I only\npassed on the road\non my way to Kyoto.\nThat was my first love...\nAh, my dear\n%@%$."),
    ('Icy Beauty', 'Aburatenjin Dayu', "Sorry!\nMy tooth aches,\nand I haven't had\na bowel movement\nin two weeks. So,\na smile next time!"),
    ('Explosive Beauty!!', 'Hachiman Dayu', "At a party, I was\nlaunching chopsticks\nwith my breasts.\nOne stuck right in\na guest's forehead.\nHad me worried a bit."),
    ('Tempting Beauty', 'Hoge Dayu', "A dog bit\nmy bottom yesterday.\nFirst time\na dog's ever\nbitten me there.\nAnd for free, too."),
    ('Melancholy Beauty', 'Ashikari Dayu', None),
    ('Over-the-Shoulder Beauty', 'Funa Dayu', "Turned this way,\nat this angle,\nmy shoulders look\nnarrow and feminine.\nMy Adam's apple\nis less obvious too."),
    ('Tipsy Beauty', 'Kankoku Dayu', "Even hungover\nand ready to puke,\nI force down a drink!\nThat's where\ndrinking gets fun.\nJust like life."),
    ('Made-Up Beauty', 'Urade Dayu', "In my line of work,\nit's half a day\nin front of the mirror.\nLately, I've forgotten\nmy face without makeup...\nNo inconvenience, though."),
    ('The Original Kyoto Beauty!', 'Kita Kannon Dayu', "I hear some vixen\nseduced the artist\nto get her portrait\npainted in garish\nyellow and pink\nkimonos. Just hers."),
    ('Ahhh... Beauty', 'Hashibenkei Dayu', "I like rainy days.\nFewer customers,\nfor one thing...\nIf I can spend all day\ncounting raindrops,\nI'm happy."),
    ('Traveling Hat', 'Traveling Hat', '(Ching Nakamura)\nCongratulations\non the release\nof the remake of\nOre no Shikabane\no Koete Yuke.'),
    ('Odds or Evens', 'Odds or Evens', "(Rendo Kurosaki)\nOdds or evens...\nEven if we can't\nread others' hearts,\nthinking of them\nis what matters."),
    ('Flowers of Sagano', 'Flowers of Sagano', "(Hiroyuki Maeda)\nHeh! You caught me.\nI thought that\nin disguise,\nI could hold you\nin my arms..."),
    ('Oni Samurai', 'Oni Samurai', '(Kei Harano)\nFill lotus-root holes\nwith mustard miso,\nand chikuwa tempura\nwith potato salad.\nThat is the way!'),
    ('Kyogoku Belle', 'Kyogoku Belle', '(Homare)\nEnjoy this reborn\nOreshika\nto the fullest!\nHeh heh heh heh...'),
    ('White-Bridal Princess', 'White-Bridal Princess', '(Akira Ishida)\nAre you\nmy destiny...?\nNo, you are not...\nWhere is\nmy destiny...?'),
    ('Concealed-Blade Shamisen', 'Concealed-Blade Shamisen', "(Haruyuki Morisawa)\nIn this world,\nart alone won't\nput food on the table.\nAre you ready\nfor what's coming?"),
    ('Shirotsume / Kurotsume', 'Shirotsume / Kurotsume', "(Kaoru Fukaya)\nA brother and sister\nwho wield white clover.\nWhat kind of weapon\nis that? Well...\nlet's just say: unbeatable."),
    ('Glass Wind Chimes', 'Glass Wind Chimes', '(Hiro Touge)\nYou can never\nhave too many\nwind chimes, right?\nThis year?\nThis is my twentieth.\nWhat of it?'),
    ('Peony and Plum', 'Peony and Plum', '(Miku Sonoda)\nMy first project\nfrom the start\nafter joining the firm.\nMaking the pixel art\nwas such fun...'),
    ('Kunoichi', 'Kunoichi', "(huke)\nWhite hair?\nDon't worry about it!\nDaily struggles\nwith a strange ninja sword.\nNin, nin!"),
    ('Undercover Maiko', 'Undercover Maiko', "(Hiroyuki Maeda)\nYou've got some nerve,\nusing me\nas a bribe...\nCare for dreams\nfrom a poisoned fang?"),
    ('Electricity', 'Electricity', '(Rendo Kurosaki)\nAh, my legs are numb.\nI cannot move...\nWould someone\nplease massage them?\n...Hurry.'),
    ('One-Eyed Dragon', 'One-Eyed Dragon', '(Miku Sonoda)\nCome to think of it,\nOreshika was\nmy last job\nworking in pixel art.\nHow nostalgic...'),
    ('Fox Girl', 'Fox Girl', '(Shiho Enta)\nCongratulations\non the remake!\nI had a\nwonderful time\ndrawing this.'),
    ('Seven Lantern Plants', 'Seven Lantern Plants', '(Kei Harano)\nI drew the\neight great serpents.\nSmiled all the way!\nHave a look\nin the heat of battle!'),
    ('Young Warrior', 'Young Warrior', '(Homare)\nCongratulations!\nAn Oreshika remake!\nI hope\nyou have\na wonderful time.'),
    ('Bespectacled Lord Genji', 'Bespectacled Lord Genji', "(Yun Kouga)\nI'm manga artist\nYun Kouga. So happy\nabout this remake.\nI'll play it\nlots again!"),
    ('Oiran', 'Oiran', '(Tomomi Kobayashi)\nTo all the players,\nplease keep\nenjoying Oreshika\nfor years to come.'),
    ('Butterfly Beauty', 'Butterfly Beauty', "(Ajiko Kojima)\nLovely, like\na butterfly?\nActually, this is just\nbecause I haven't\nwashed my hair."),
    ('Outlaw', 'Outlaw', "(Misaki Saito)\nCongrats on the remake!\nWhen I play Oreshika,\nI'm so overcautious\nthat my family\ngets fed up with me..."),
    ("Shuten's Daughter", "Shuten's Daughter", "(Ju Ayakura)\nCongratulations on\nthe Oreshika remake!\nSurely I can wish for\na broken horn's worth\nof happiness, at least?"),
    ('Female Utamaro', 'Female Utamaro', "(toi8)\nI make my living\nas an artist\nof sorts.\nBut I'm no good\nwith those 'wa' seals."),
    ('47', '47', "On my way to Kyoto,\nI met a samurai woman\nwho looked just like me!\nI asked her name:\n%$! My real name\nis %$ too..."),
    ('98', '98', '98'),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    assert len(GROUPS) == 49
    batches = []
    for start, (title, name, caption) in zip(range(76, 272, 4), GROUPS):
        translations = [title, name, name] + ([caption] if caption is not None else [])
        batches.append(dict(file='eMltFacil.mlb', section=0, start=start,
                            end=start + len(translations), kind='portrait_caption',
                            context='Print-shop portrait title, subject, localized reading and caption. '
                            'Captions are separate character or artist comments, not a connected scene. '
                            'Pronunciation fields match the English subject name; sorting/display unverified.',
                            review_notes=['All original line-break counts retained; portrait panel fit unverified.'],
                            translations=translations))
    result = dict(version='0.2.2', batches=batches, untranslated_rows=[
        dict(file='eMltFacil.mlb', section=0, index=99,
             reason='Sexualized child-coded portrait caption; left untranslated.'),
        dict(file='eMltFacil.mlb', section=0, index=151,
             reason='Sexualized attraction to explicitly twelve/thirteen-year-old boys; left untranslated.')])
    for batch in batches:
        if batch['start'] == 132:
            batch['review_notes'].append('Crude adult lucky-vulva title pun retained, not normalized into a generic good-fortune title.')
        if batch['start'] in (188, 236):
            batch['review_notes'].append('Artist credited by documented pen name Homare; legal given-name reading not guessed.')
        if batch['start'] in (208, 224):
            batch['review_notes'].append('Artist credited by documented pen name Miku Sonoda rather than guessing the kanji-name reading.')
        if batch['start'] == 260:
            batch['review_notes'].append('Wa seal allusion left marked as unclear; no invented commercial activity or forgery explanation.')
        if batch['start'] == 264:
            batch['review_notes'].append('Numeric title/subject slots retained exactly; only the visible caption localized.')
    print(json.dumps(dict(rows=sum(len(b['translations']) for b in batches),
                          unresolved=result['untranslated_rows'], sample=batches[0]), ensure_ascii=True, indent=2))
    if args.write:
        (ROOT / 'work/translation/en/portraits_batch_001_input.json').write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Seed written.' if args.write else 'DRY RUN: no files written.')


if __name__ == '__main__':
    main()

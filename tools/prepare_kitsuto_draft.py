"""Prepare the reviewed Kitsuto event dialogue; dry run by default."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = {
'common_00':[
"Hi there.\nNice... to... meet... you!!\nMy name's Kitsuto.",
"The gods told me\nto help your clan.\nSo here I am.",
"Heh... In other words,\nI'm just an errand boy... I suppose?\nHa ha ha... Nice to meet you.",
"Well, I'll do my best to gather\nall sorts of information\nand make myself a little useful!!",
"Right, that's that.\nSee you again soon!!"],
'common_01':[
"Hi!!\nIt's Kitsuto's Beginner Battle Class:\n'Victory Points and Offering Points Made Easy.'",
"Besides loot and money, defeating oni\nearns Victory Points. They're split evenly\namong your companions as individual experience.",
"Once someone has enough points,\ntheir fighting strength naturally increases.",
"In other words, even a complete klutz\ncan become reasonably impressive\nwith enough experience.",
"And the same number of Victory Points\nis added at the same time to Offering Points,\nwhich you give the gods for Divine Union.",
"Offering Points represent a god's greatness!!\nThe higher the requirement,\nthe greater the potential of the child they grant.",
"Well, put another way,\nthe other world's not so generous\nthat they'll help you for free."],
'common_02':[
"Hi!!\nExploring here this month?\nYou've got a good eye!!",
"By the way, today I'll give you\na quick explanation of how time passes.",
"You may know this already,\nbut wherever you go, whatever you do,\na month passes all the same.",
"Be especially careful\nwhen a month passes during an expedition.",
"Think hard. Did you have Divine Union\nor the Mount Oe Selection Tournament\nplanned for next month?",
"And watch your companions' Health too.\nFatigue can catch up with you all at once\nwhen the month changes.",
"Ha ha ha...\n'I forgot' won't get you out of it."],
'common_03':[
"Hi!!\nAll those battles must be\nstarting to wear you out by now.",
"...So today's topic is\n'the relationship between Health and HP.'",
"Walking through caves on expeditions\nand fighting enemies tire your body,\nso Health drops little by little.",
"When you're young, a little rest sorts you out.\nBut once you're old, recovery takes\ntwice or three times as long.",
"Forcing a tired body into battle\nwon't do you any good.\nYou can't fight at your usual strength.",
"Retreating and resting are sound tactics too.\nHonestly, neither of us\nwants to get old, do we..."],
'common_04':[
"Hi!!\nWelcome to lesson two\nof Kitsuto's Beginner Battle Class.",
"What do you do when things\nstart looking bad in battle?",
"Running away quickly is fine,\nbut you can also find the enemy commander\nand focus your attacks to take that one down.",
"That wins the battle for you!!\nThough you'll earn fewer Victory Points.",
"And just so we're clear,\nif your captain goes down, it's all over,\nno matter how healthy everyone else is!!",
"Naturally, the enemy isn't stupid.\nWhen pressed, they'll try that too.\nBe very careful."],
'common_05':[
"You know that defeating oni\ngets you loot and money, right?\nHelping yourselves to plenty of it?",
"No need to hold back!!\nAfter all, that treasure was\nstolen from humans in the first place.",
"Now, sometimes there are scrolls\nmixed in with the spoils, right?\nI'll tell you how to use them.",
"...It's simple, really!!\nJust take them home.\nAnd one of each kind is enough.",
"That's all you need to do. Anyone with enough\nMP will read the scrolls, even sneaking a look,\nand learn the spells without being told.",
"That's how you protect yourself.\nSlack off and you'll die for nothing."],
'common_06':[
"Hi! Nice work slaying oni!!\nNow, try to remember\nwhat I'm about to tell you.",
"There's one here too,\nbut deep inside any cave or labyrinth,\nyou'll always find an oni boss.",
"Here's the important part!!\nClean out your ears\nand listen carefully.",
"Those fellows\ncome back no matter how often you kill them.\nThey aren't of this world, after all.",
"Well, you can keep earning Victory Points,\nso once you're strong enough,\nthey're good repeat customers."],
'common_07':[
"Hey, long time no see!!",
"How's the oni-slaying?\nWell, take your time!!\nLife is long...",
"Oh, sorry.\nI didn't mean it that way...\nSee you later."],
'common_08':[
"Hel-lo-there!!\nListen... a little late, I know,\nbut I thought I'd offer an excuse.",
"You probably don't expect anything\nfrom an errand boy like me...\nbut just for the record.",
"As you can see, I don't have\na physical body right now...\nSo I can't fight alongside you...",
"Some man I am, being so useless.\nI'm really sorry!!",
"But, you know... someday, surely...\nSomeday I'll get my body back,\nand there'll be a day I can fight with you...",
"I hope that day comes...\nAhh... Maybe it's impossible after all...\nWell, see you..."],
'common_09':[
"Hi!! I thought I'd\ncheer you up a little today,\nso here I am.",
"If you're still regretting\nletting me out of that oni,\nyou're blaming the wrong people.",
"Those heavenly bastards\nknew perfectly well\nI was sealed inside that oni.",
"At your next Divine Union,\ntake a good look at the gods.\nThere should be more unfamiliar faces.",
"They're the ones I dragged down with me\nwhen I was locked away.",
"Heh heh... See?\nThat's how they operate."],
'common_10':[
"Hi, long time no see!!\nBy the way,\nI have a favor to ask.",
"I'd really like you to come and see\nthe garden I've made, sometime soon!!",
"The keys to the garden\nare my seven hairs.\nI left them deep in caves and labyrinths.",
"My hair's long and hard to miss.\nYou'll know it when you see it!!\nI'll look forward to your visit."],
'd1_00':[
"Today's a little more serious.\nI kept this from you because\nI thought it would weigh on you...",
"Like you, I'm under\nthat oni's curse.\nProbably...",
"Probably!! If you defeat him,\nmy body will return to this world!!\nThen I could fight with you...",
"Huh...!? But if you beat that oni,\nwon't the whole war be over?\nHmm... What a shame.",
"I may not look it, but I'm pretty strong.\nHa ha... No, really.\nI mean it!! Ha ha ha...",
"As you are now, I know you can win!!\nI know how much you've been through.\nI believe in you!!"],
'd1_01':[
"The curse that oni placed on you\ngives you short lives.\nBut you have a loving family.",
"I'm stuck in this form,\nunable to die for all eternity,\nalways alone...",
"It may be wrong to say,\nbut sometimes\nI envy you terribly...",
"Apparently, I had an older sister...\nWe were separated as children,\nso I don't even remember her face.",
"If the curse is lifted,\nI think I'll look for her.\nShe might be closer than I imagine..."],
'd1_02':[
"You've grown even stronger\nsince we last met.\nThis time, you can beat that oni!!",
"Then my curse will surely break,\nand I can finally say goodbye\nto this see-through body!!",
"Ah...\nThe feel of wind and light on my cheeks...\nI want to remember it again..."],
'd1_03':[
"If you free my body\nfrom that oni,\nI'll invite you somewhere lovely as thanks.",
"A garden with little hills and a pond.\nPerfect for a stroll.\nI'll walk its paths with you...",
"Yes, of course...\non my own two legs,\nthe ones you brought back to me!!",
"Ah... I can't wait...\nIt's a promise, then."],
'd1_04':[
"Hi!!\nStill hard at work slaying oni, I see!!\n...Don't you have anything else to do?",
"Thanks to your meddling,\nI'm back in this embarrassing\nsee-through body...",
"Heaven's even duller than I'd heard.\nI'm so bored I could die.",
"So I'll sneak away from Mom and the others\nand come play now and then!!\nSee you around."],
'd1_05':[
"Oh, yes.\nThis place you're in now\nis called Hidden Kyoto in heaven.",
"They say they made it by reflecting Kyoto\nin a huge mirror. An exact copy.\nThe inhabitants are our familiar oni.",
"'Hiruko Taishoten is so generous,\nso noble, she shows mercy even to oni.'\nThat's her glowing reputation up there...",
"But I'm sure locking them up\nwas just easier than killing them all.\n...She's rather slapdash, you see."],
'd1_06':[
"The oni weren't going to obey\njust because someone cooed sweetly,\n'Come over here.'",
"So how did she gather\nall the oni in Hidden Kyoto?",
"She dangled bait in front of them.\nHeaven's highest goddess came down herself\nto this rubbish heap of Hidden Kyoto.",
"'Hiruko Taishoten is so brave,\nso wonderful, with no thought for her own safety!'\nYet another storm of praise up there!!",
"But really, she just wanted an excuse\nto get out of heaven.\n...It's better down here, after all."],
'd1_07':[
"My sister came down to Hidden Kyoto\nand became bait to gather the oni...\nI told you that story once, didn't I?",
"But two pieces of bait\nwork better than one.\nThat's what she realized.",
"'What shall I use for the second?\nHow about the humans the oni\nhate most of all?' Something like that."],
'd1_08':["She won't die even if you beat her,\nso there's no end to it however much you fight.\nWell, if you enjoy it, I won't stop you."],
'd1_09':["Whatever noble things she says,\nreally, she's just killing time.\n...There's such a thing as being too obliging."],
'd1_10':["Whether you believe me or my sister\nis entirely up to you.\n...Freedom. Such a convenient word."],
'd1_11':["Maybe beyond all this grand time-wasting\nthere's something you've never seen.\n...No, probably not."],
'd2_00':[
"Hi!!\nI've heard a story about a poor celestial maiden.\nWant to hear it?",
"Long ago... a celestial maiden fell in love\nwith a mortal man. As if that weren't enough,\nshe even had his children.",
"But she was found out\nand couldn't return to heaven...",
"Throwing her whole life away for a bit of romance.\nWomen...\nWhat can you do..."],
'd3_00':[
"Hi!! Today, let me introduce\ntwo great gods who contributed\nso much to human development!!",
"Long ago, on a snowy day,\ntwo gods looked down\nfrom above the clouds.",
"People were dying of cold and hunger.\nSo they taught humans how to make fire\nand how to control the wind...",
"Without consulting a single other god.\nQuietly, in secret!!",
"Whoops, this is getting too long.\nThe tragic fate of these kind gods\nwill have to wait until next time!!",
"Stay tuned!!"],
'd3_01':[
"Hi, how have you been!?",
"Today's story is about what became\nof those ever-so-kind gods\nwho taught humans to use fire and wind.",
"For teaching fire and wind to humans\non their own authority, those two gods\nwere imprisoned here in Kujuro.",
"But now, instead of cries of cold and hunger,\nthey could hear human laughter\neven inside this tower!!",
"So they didn't regret\nwhat they'd done...",
"Heh...\nA beautiful story so far, isn't it?",
"But they went without regrets for just one year,\nuntil humans started using that fire and wind\nto kill each other.",
"Well, it's a familiar ending."],
'd4_00':[
"Hi!! Today, let's talk about\nthe old shrine on this mountain,\nthe one called Inari Palace.",
"You'd never know it now,\nbut people once trusted this shrine deeply,\nand its grounds overflowed with worshippers.",
"Yes...\nuntil that dreadful\nincident...",
"A wife who couldn't have children prayed to Inari.\nOn the hundred-and-first day,\nshe found a baby outside the shrine.",
"From then on, her luck\nwas almost unbelievable!!",
"On a visit to give thanks, she happened to buy\na lottery ticket and won first prize: a thousand ryo!!\nThree times in a row, no less!!",
"But that was where the bad luck began.\nAfter that, it was a headlong slide into hell.",
"...And on that note,\nthe rest will have to wait."],
'd5_00':[
"There's a mermaid deep in this aqueduct.\nSo beautiful,\nyou'd hardly think she was of this world.",
"She's shy and rarely shows herself,\nbut really, she gets lonely.\nAn ordinary girl, like any other.",
"So you'll be fine!!\nI'm sure you'll make good friends."],
'd5_01':[
"When a certain princess grew old\nand fell ill, orders went out to gather\nrare medicines from across the land.",
"Knowing nothing of any of that,\nan unlucky mermaid was caught\nin a fisher's net off Tsuruga.",
"Legend says mermaid flesh cures every illness.\nEat it alive, and you gain eternal youth...\nPure superstition, of course.",
"Ha ha ha... Still, trying it anyway\nhas always been\na habit of you humans, hasn't it?"],
'd6_00':[
"Well, you did a good job finding this.\nAhead is a strange castle\nthat appears only in summer.",
"They say the souls of those who climbed\nMount Oe and never returned\nare wandering about with nowhere to go...",
"But you know,\nI just don't understand.",
"Are human lives so worthless\nthat you'd throw them away for petty pride\nor some flimsy notion of justice?",
"An ordinary samurai couldn't possibly\nbeat Shutendoji, however hard they tried...\nSurely they must know that."],
'd6_01':[
"Compared with the people here,\nmaybe you're the lucky ones?",
"Your ancestor at least made it\nto Shutendoji's bedchamber,\nand that's why the gods blessed you, right?",
"Well, hundreds die on Mount Oe each year,\nso perhaps the gods can't be bothered\nwith every little nobody?",
"I've never heard, but maybe\nheaven has a limit on places...\nDo they hold exams when it's full?",
"Whoops, whoa...!!\nFor pity's sake, don't tell anyone\nyou heard me say that.",
"I'd hate to annoy heaven's examiners\nand fail the interview.\nHa ha... You be careful too."],
'd6_02':[
"How are the oni in this castle?\nPlenty of backbone, aren't they?",
"After all, they were mighty warriors\nwho came to defeat me and died on Mount Oe.",
"Even so, the gods treated them terribly.",
"They mustered all their courage\nand gave their lives for peace, yet heaven's gates\nremain closed to them even now.",
"So I gave them\na place to rest instead.\nThat's what this castle is.",
"No one understands better than me\nhow it feels to be abandoned by the gods.",
"Ha ha ha... It was easy to build.\nI used their own bones.\nThere's no shortage!!"],
'd7_00':[
"Do you become a monster cat because you die\nhating the world, or hate the world\nbecause you're born a monster cat...?",
"Want the answer? Ask her yourself.\nThe Crimson Flame Shrine's commander is a cat-woman.\nHer nickname's Onatsu.",
"A cute female monster cat,\noriginally from heaven.",
"Apparently, she played with fire a little too much.\nAs punishment, they turned her into a cat\nand threw her down to earth."],
'd8_00':[
"About a hundred years ago,\nthe Emperor had an accomplished younger brother.\nThe people loved him...",
"So he was arrested on false charges\nand buried alive here.",
"Oh, he laid a magnificent curse on them!!\nThey panicked and built this\nridiculously enormous tomb.",
"Ha ha ha... As you can see,\nit did absolutely no good."],
'd9_00':[
"Countless mighty warriors\nfell to the oni Shuten on Mount Oe...\nThe gods abandoned them.",
"Yet they offered help to a helpless baby.\nHaven't you ever wondered\nwhy they did that?",
"Why was your founding ancestor alone\ngiven special treatment...?\nA divine whim? Or pity?",
"No, neither...",
"I'll tell you the secret next time.\nThere's plenty of time.\nThink it over slowly."],
'orochi_00':[
"I've been meaning to ask:\nwhat reason did the gods give\nfor lending you their power?",
"Knowing them, did they act all gracious\nand say it'd be a shame\nto let such an exceptional bloodline die out?",
"And look where that's got you!?",
"Your clan can't even\nrest in peace. You wander on and on\nthrough an endless nightmare.",
"Just like human history,\nso kindly created by the gods...\nOr their own history, for that matter."],
'orochi_01':[
"Have you heard this legend?\nLong before we were born,\nthe first humans appeared on earth...",
"They spent an unimaginable\namount of time and finally\nsucceeded in gaining eternal life.",
"Once they were immortal,\ngrowth and children lost all meaning...",
"And everything stopped.",
"Yes!! The fools thought\nthey'd gained eternal life,\nbut they'd actually met eternal death.",
"Heh heh... Compared with them,\nyou're much happier, aren't you?\nI wish you'd be more grateful to me."],
'orochi_02':[
"I told you once about that foolish clan\nthat gained eternal life, didn't I?\nWell, there's more to the story.",
"Their miscalculations went on.\nTheir bodies weren't eternal.\nIn despair, they left the earth...",
"But they were fools through and through!!\nThey still clung to the earth,\nand still believed themselves great.",
"They decided, all on their own, that humans\nwere their successors, and began poking their noses\ninto everything without being asked.",
"Eventually, even that became too much trouble,\nso they planned to install their own children,\nborn by chance, as rulers over humans.",
"What a nuisance...\nThere's no cure for stupidity."],
'orochi_03':[
"'These are the true messengers of the gods.\nFrom this moment, they rule over humanity.\nObey them!!'",
"Anyone who seriously obeyed\na divine command appearing out of nowhere\nlike that must have had a screw loose.",
"Especially when those rulers\nwere just a young girl\nand a newborn baby.",
"But having a screw loose is what humans do.\nQuite a crowd gathered,\nnever realizing they were being deceived.",
"The Emperor of the day couldn't let that stand.\nHe sent a hundred thousand soldiers against children!!\n...Humans really are mad."],
'orochi_04':[
"A baby proclaimed a child of the gods\nwithout being asked, then hated by humans,\nand finally made to watch his parents die...",
"The first word that child learned\nwas 'revenge'.\nYou can imagine how he grew up, can't you?",
"Ha ha ha... And he really was\na child of the gods,\nso he had power to spare!!",
"Heaven must have panicked.\nThey picked an oni whose only gift was toughness\nand locked him inside its body.",
"Getting out of there was hard.\nIf you hadn't come along,\nI'd probably still be inside him.",
"I'm grateful!!"],
'orochi_05':[
"You've begun to realize, haven't you?\nYour power is already\nabout to surpass the gods...",
"Yes, just like mine!!\nStrange, isn't it? A child of god and human\ncan far exceed even a god's power.",
"Those heavenly bastards knew that\nand used you\nto get rid of me.",
"It was their only option.\nIn other words, that's all\nthe gods amount to.",
"Ha ha ha... By the way!!\nSupposing you're lucky enough to beat me,\nwho do you think gets erased next?",
"Think hard.\nYou understand, don't you?"],
'orochi_06':[
"When you've two dolls you're bored with,\nmake them fight each other\nbefore throwing them away.",
"Saves you the trouble of breaking them,\nand since you aren't doing it yourself,\nit doesn't hurt your conscience much.",
"And bored as you may be,\nthese are toys you once loved, killing each other.\nHow could it fail to excite you?",
"Heh heh heh...\nThe perfect spectacle to pass the time.",
"Nothing like the battle\nbetween us oni and you humans, is it?\nDon't you agree?"],
'orochi_07':[
"You've finally gathered the keys!!\nAs promised, you're invited to my garden.\nYou should be able to see the entrance now.",
"My garden's small and rough,\nbut with hills and rivers, the scenery's guaranteed.",
"I built a new house in a corner too.\nThat's your destination. The stage\nfor our final showdown.",
"Come play as soon as you can!!\nIt's just Mom and me here,\nand I'm a little lonely..."]
}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args=ap.parse_args()
    c=json.loads((ROOT/'work/source/corpus.json').read_text(encoding='utf-8'))['rows']
    # Same speeches in alternate event variants, checked against complete source lists.
    for target,original in [('d2_01','d2_00'),('d3_02','d3_00'),('d3_03','d3_01'),('d4_01','d4_00'),('d6_03','d6_00')]:
        def texts(key):
            return [r['source_jp'] for r in c if r['file']=='ev_kitsuto_'+key+'.mlb']
        if texts(target)!=texts(original):
            raise ValueError('Alternate source is not identical: '+target)
        D[target]=D[original]
    batches=[]
    for key,translations in D.items():
        notes=[]
        if key=='common_07': notes.append('Long-life joke is immediately withdrawn because the clan is short-lived.')
        if key=='common_08': notes.append('Claim of fighting with the clan deliberately stops before the later revenge reveal; no hostile with-against ambiguity prematurely resolved.')
        if key=='d1_07': notes.append('Second bait is the clan, as the following postgame remarks settle; nested quotation retained.')
        if key.startswith('d2_'): notes.append("Sexist dismissal is Kitsuto's taunt, not an external narrator's factual judgment.")
        if key=='d7_00': notes.append('Playing with fire preserves the fire/romance idiom; exact transgression is not invented.')
        if key=='orochi_04': notes.append('Kitsuto is telling his own story in third person; source male referent is established by his following first-person admission.')
        batches.append(dict(file='ev_kitsuto_'+key+'.mlb',section=0,start=0,end=len(translations),
                            kind='event_dialogue',context='Kitsuto addresses the clan. Speaker tables identify him for every row. '
                            'Event-file order, tutorial variants and late-game revelations are distinct from chronological play order. '
                            'He is teasing, sardonic and increasingly accusatory; source uncertainty and deliberate fragments retained.',
                            review_notes=notes,translations=translations))
    rows=[r for r in c if r['file'].startswith('ev_kitsuto_') and r['category']=='dialogue_narration_subtitles']
    result=dict(version='0.2.2',batches=batches,dialogue_rows_examined_unique=len(rows),dialogue_slices=[
        dict(file='Kitsuto event dialogue group',file_group_prefix='ev_kitsuto_',start=start,rows_in_slice=80,
             rows_examined=examined,adjacent_context=context) for start,examined,context in [
            (0,84,'Dialogue-only source order, omitting separate voice-asset and speaker-name files. Following rows 80-83 examined; all speakers checked as Kitsuto.'),
            (80,86,'Rows 78-79 before and 160-163 after examined. Whole event files read together; repeated variants checked identical before reuse.'),
            (157,82,'Rows 155-156 before examined; end of dialogue group at 236. Final window overlaps by three rows; each record stored once.')]])
    print(json.dumps(dict(rows=sum(len(b['translations']) for b in batches),source_dialogue_rows=len(rows),
                          sample=batches[0]),ensure_ascii=True,indent=2))
    if args.write:
        (ROOT/'work/translation/en/events_kitsuto_001_input.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Seed written.' if args.write else 'DRY RUN: no files written.')


if __name__=='__main__':
    main()

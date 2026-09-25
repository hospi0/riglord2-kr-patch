# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_nj10.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '7a7e3be4e6': u'퇴각할까요？',
 '49eb930561': u'안 한다',
 '256f0dbbef': u'인사가 살벌하군요, 카다르 위해\n일할 마음 든 줄 알았더니・・・。%b',
 '11cfa998b4': u'카다르 위해 싸워？\n안 되는 소리.%b',
 '5c40c04f06': u'전 리그로드와 야마타이가・・・。%b',
 '7dde288dc0': u'하지만 당신은 손댈 수 없잖습니까？%b',
 'a13a9a1d4a': u'아니, 틀렸다.\n놈들 목숨은 내가 쥐고 있다.%b',
 '346cf843f9': u'인질 없이도 이길 수 있다는\n자신 말이죠.%b',
 'dc6dba7713': u'큭！\n후퇴한다！%b',
 '666bf57ce4': u'좋아, 부하들은 어디 있지？%b',
 '8f6ca0bd32': u'저 녀석들 목소리다？%b',
 'ad93581c66': u'아스카, 쓸쓸해 보이는 거야.\n나즈나가 있으니 괜찮은 거야～☆%b',
 '8b2c1bc075': u'화난 얼굴도 멋진 거야.%b',
 'dd7853cde7': u'그럼 좋겠는데・・・。%b',
 '9acb2e31e3': u'・・・아, 그래.\n맞는 말이군.%b',
 '2e77b4a999': u'【아마노자쿠 거울】 입수.%b',
 '63357896b7': u'나즈나 굴엔 없었던 거야.\n근데, 주력이 느껴지는 거야.%b',
 'b6cd5bb14d': u'그렇구나！%b',
 '52b86d8124': u'그럼 두 개 더 필요하단 거네.%b',
 '33454ed55c': u'나즈나인 거야.%b',
 'd3624b56c0': u'저쪽은 식신입니까？%b',
 'de59cbf126': u'아무래도,\n뿌리 없는 식신이 따르는 건\n부친을 닮은 모양이군요.%b',
 'a71d858376': u'운명의 만남인 거야.%b',
 '2676c5f3d9': u'그, 그게 운명이라굽쇼？%b',
 '48496787d3': u'헛소리 마！%b',
 '439568cf3c': u'그것보다, 앞으로 얘긴데.%b',
 'a6f436db8f': u'그럴 수가！%b',
 '0b5ec65650': u'힘에 굴하는 지배엔,\n난 약하지 않아！%b',
 'd1cae4b0cb': u'싫다는군！%b',
 'e791ff9dc2': u'아스카가 소중히 여기는 걸\n짓밟는 놈은 용서 못 해, 인 거야！%b',
}

n = 0
missing = []
for k, v in FIX.items():
    pat = re.compile(r"    '%s': '.*?',\n" % re.escape(k))
    m = pat.search(s)
    if not m:
        missing.append(k)
        continue
    s = s[:m.start()] + "    '%s': %r,\n" % (k, v) + s[m.end():]
    n += 1

io.open(p, 'w', encoding='utf-8', newline='').write(s)
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\nj10_budget_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_qh00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '95f7da79c8': u'파실 물건 가져오셨죠？\n',
 'f106d37bdf': u'많이는 못 드실 것 같은데요？%b',
 '24b0707c15': u'이번 이변은,\n리그로드 전역과 닮았다는 소문이야.%b',
 'f040384b19': u'아이고, 싫다.%b',
 'c87688d7c3': u'대체, 무슨 일이야？%b',
 '0b97473eb2': u'다들, 기대하고 있어요.%b',
 'b667fdf36a': u'왕자님, 저희 가문에 전해지는\n이 책을 쓰세요.%b',
 'e93e757081': u'우리 왕국에 영광 있으라！%b',
 '275ca06559': u'대체, 무슨 일이죠！？%b',
 '3996377193': u'성을 흙발로 더럽히다니！\n용서 못 해요！%b',
 'd032bcf79a': u'당신들이야말로, 세상의 구세주다！\n리그로드 전역 영웅들의 재림이야！%b',
 'f916c2cdbd': u'러스티 왕자！%b',
 '2c893e04b4': u'이럴 수가！\n라그로스 탑에서 돌아오셨다니！%b',
 'a6b1e6e103': u'당신들이 진짜 영웅이에요！%b',
 '9673c416d1': u'어떻게 생각해？%b',
 'fa7d86a09c': u'불로장수 보물\n신선의 옥을 지니면,%b',
 'e795c697a7': u'아, 부모님이・・・！%b',
 'b56e42dab0': u'용서 못 해・・・\n못 한다, 라그로스！！%b',
 'fe3138c8ca': u'사람들이 사랑해온 조각상이,\n무참히 부서져 있다.%b',
 '779605d213': u'・・・라그로스놈・・・。%b',
 'add00f9d8a': u'읽겠습니까？',
 '63a922b735': u'사랑 샘.%b%h',
 '5ebc14d00b': u'현재, 이 마을은 카다르군 지배하다.\n연락 있을 때까지, 외출을 삼갈 것！%b',
 'de985f4cfc': u'적의 강함에 따라\n대단한 상품을 받지.%b',
 '0d85c919fe': u'이 앞은, 라그로스 님이 계신\n탑이다.%b',
 '86e34e36b8': u'봐도 상관없지만,\n함부로 들어가선 안 된다！%b',
 'd418e53aaa': u'너희가 뭘 할 수 있을 것 같진 않지만,\n이상한 생각 말아라！%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\qh00_budget_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

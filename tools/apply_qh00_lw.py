# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_qh00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '47f794906e': u'러스티 왕자님 핏줄을 몇 대 거슬러\n오르면, 리그로드 전역의 영웅 아서\n님과 닿는다더군.%b',
 '6862d236e4': u'동방의 신비한 힘을 가진 천녀의\n날개옷이란, 어떤 건가염？%b',
 '0aa3d1366b': u'이젠, 아무도 러스티 님을 겁쟁이니,\n배꼽이 튀어나왔니, 발 냄새니,\n말하지 않지요, 그럼요.%b',
 '13d10919c8': u'러스티 왕자님, 들었어요！ 카다르\n놈들 코를 납작하게 해줬다면서요！%b',
 'e02eb85283': u'이제 국민들한테 우유부단하니,\n멍청이니, 바보니, 생각 없다느니,\n소리 안 들어도 되겠네요！%b',
 'eb570f43f2': u'라그로스 탑을 아는 자가 없습니다.%b',
 'afe49d71b4': u'뭐, 못난 자식이 예쁘다고,\n다들 왕자님 얘기하지만,%b',
 'd418e53aaa': u'너희가 뭘 할 수 있을 것 같진\n않지만, 이상한 생각 말아라！%b',
 'd3d27b8763': u'정말, 그 얼빠진 건, 핏줄이라니까.%b',
 'c3e4433858': u'어, 어, 어, 어, 어떻게 된\n거야, 어떻게 된 거냐고, 어이！%b',
 '236fd23f75': u'그런 마음으로, 현재, 예리하지만\n깊고 조용히 조사 중입니다.%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\qh00_lw_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_mh00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 'dc451103b7': '끝이다 세상 멸망하는 거야！%b',
 'c8a0883d10': '요즘, 그게 머리서 안 떠나서.\n넌 어떻게 생각해？%b',
 'd0915ff98c': '몇 번이나 야마타이 통일하고,\n타국을 침략한다.%b',
 'de92be8f34': '이 히가타를 거치는 것 말고는,\n다른 나라서 사람이나 물자 옮길 방법\n없을 텐데 대체 어떻게 된 건지.%b',
 'd708af069c': '야마타이는 예로부터\n내란 끊이지 않는 나라였으니까.%b',
 'a7545dec70': '취소',
 '9286effa42': '여긴, 항구도시 히가타\n야마타이 바다 관문이라 불려.%b',
 'd80dce040f': '전설검【사쿠라후부키】.%b',
 'a967f6f525': '부탁이야,\n그 사람한테 이 편지를 전해줘.%b',
 'aee3b5293a': '부탁이야, 그 사람한테 이 편지를 전해줘.\n그리고 전해줘・。%b',
 '016e8905ef': '마지막 정도는,\n좋아하는 사람과 있고 싶었는데・。%b',
 'a5e9d78de7': '바다를 서쪽・동쪽으로 가면\n머잖아 리그로드에 닿을 거야.%b',
 '10debb87e9': '또, 너희가\n리그로드에 있다고 치면,\n바다를 동쪽・서쪽으로 가면 야마타이에,%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_mh00_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

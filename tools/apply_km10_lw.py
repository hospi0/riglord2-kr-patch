# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_km10.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '5d4eb7eea4': '근데・ 지금 러스티는\n자기 정신력 이상 마법 쓰고 있어.%b',
 '65ce942572': '얘기 들어보면, 마을 안전을 위해,\n여자랑 아이들을 내준다는 것 같아.%b',
 '23b9b6d7bc': '・어쨌든 그 젊은이 예 갖추고 싶다.\n내 집으로 와다오.%b',
 '5b92878adf': '확실히 싸워서 그녀를 구하는 것 말고\n방법은 없을지도・。%b',
 '1df0247da7': '난 누구도 러스티 못 막게 할 거야.%b',
 '09ff9ce08b': '너무하네, 목숨 은인을 두고 가다니.%b',
}

n = 0
for k, v in FIX.items():
    pat = re.compile(r"    '%s': '.*?',\n" % re.escape(k))
    m = pat.search(s)
    if not m:
        raise SystemExit('MISSING %s' % k)
    s = s[:m.start()] + "    '%s': %r,\n" % (k, v) + s[m.end():]
    n += 1

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('patched', n)

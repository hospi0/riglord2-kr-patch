# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_ct10.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '922451420c': '너희 살아있었던 거야？！%b',
 'd7281ff49e': '그, 그 목소리는・',
 'aa086b503d': '그런 걸 나한테 가르쳐 어쩌자는 거야？\n나더러 뭘 하라는 거냐고？！%b',
 '29f3341d08': '그런 걸 나즈나한테 가르쳐서\n어쩌라는 거야 인 거야？！%b',
 '30879e4b7e': '이 몸은 날 위해 싸울 뿐이다～제！%b',
 '7b79169e23': '가파른 비탈인 거네！\n어떻게 내려갈지 문제인 거네！%b',
 '7e27a36309': '가파른 비탈.\n',
 'ccd1ca77b1': '흥\n가파른 비탈인 것이다～제！%b',
 'b604247db6': '붙잡혀 미끄러져 내려가거나\n지형 바꿀 수밖에 없네.%b',
 '126bd9c8ac': '새가 돼 동료를 붙잡고 내려가거나\n',
 '114c573beb': '지형 바꿔달라는 수밖에 없는 모양이군.%b',
 'cc92605b05': '놈들을 쓰러뜨릴 수밖에 없는 모양이군.\n그럼 가도록 하지.%b',
 '78f46d823e': '이게 마법구슬 같네.%b',
 '1fba6720e0': '마법구슬인 모양이군.%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_ct10_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

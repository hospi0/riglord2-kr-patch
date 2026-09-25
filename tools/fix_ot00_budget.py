# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_ot00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '190acbd318': '여기가 소인 가게이외다.\n잠시 기다려주소서.%b',
 '6e8b338a5a': '어머？\n파실 게 없으신 것 같네요.',
 'b313603c21': '그리 많이는 못 드실 것이오.',
 '6f4a9d37e6': '많이는 못 드실 것이오.\n무리 마심이 중요하오.',
 '8dcd3666d7': '어쨌든 경사스럽다！%b',
 'b9351c3c75': '이걸로, 코르베도 갈 수 있어.%b',
 '90025ab210': '헤에~！\n하늘 날아서！%b',
 'd21350b373': '옛날처럼 오르트마서\n자유롭게 배를 띄울 수 있게 되면%b',
 '8886573851': '어디 가겠습니까？',
 '03431de20b': '야마타이구나！\n그럼, 목적지는 항구도시 히가타네.%b',
 '3338cdb291': '그거 있으면\n하늘 나는 배 고쳐지는 거지？%b',
 '63fa92085f': '요금 필요없습니다요.%b',
 '74157a7948': '밖 나갈까요？',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_ot00_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_nj10.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '26685b5467': u'그러니까, 이게 있으면 결계굴 결계를\n깨고 게텐 성에 갈 수 있는 거잖아！%b',
 '79b3d72739': u'당신이 뮤 왕녀시군요. 갈자드 님께\n말씀은 익히 들었습니다・・・。%b',
 'd63c3e277f': u'이건, 뭔가 엄청난 골칫거리의 전조\n같은 기분이 들어 견딜 수가 없어.%b',
 '0197c3f5f5': u'괜찮아, 귀여운 나즈나가 있으니까,\n바람은 못 피는 거야, 인 거야.%b',
 '7dedcf543c': u'나도 잘은 모르겠지만, 그 모양\n어디선가 본 것 같단 말이지.%b',
 'f10773be1d': u'그것도, 뭔가를 막거나, 봉인하는\n듯한 주력인 거야, 인 거야.%b',
 '06a939ccf4': u'근데 내 기억이 맞다면, 구멍은 전부\n세 개 뚫려 있었을 텐데？%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\nj10_lw_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

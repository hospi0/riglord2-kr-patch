# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_rt20.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '7943a49122': '보라, 지금이야말로,\n차원의 문 봉인을 여는 때.%b',
 '1c27dab3ae': '멈춰！%b',
 'd2b41d292a': '여긴 저한테 맡기시죠！%b',
 'e5720ebc27': '방해자는 용서 못 한다！%b',
 'fe61b4d968': '멈춰, 인 거야！%b',
 'eebe7edf8c': '멈춰, 인 것이다～제！%b',
 '4fb0a2c949': '마법력도・ 무력도・ 인망도・ 뛰어난・,%b',
 'a20c73d257': '뭐 뭐야 저거！%b',
 'db6b64545d': '그들 생각은 사악해요.%b',
 '527d18456c': '허나, 하늘 말고는\n유현숲에 들어갈 길이 없어요.%b',
 'a1909335a1': '고대유적서\n아우 소재도 확인하리다.%b',
 '5898b8f055': '꺄악 인 거야！%b',
 'd012c97295': '뭐, 저거！%b',
 'f8104d2755': '뭐야 인 거야？%b',
 '812009af6a': '근데 지금 망가진 거야, 인 거야.\n못 나는 거야, 인 거네.%b',
 '9a7a79c06b': '그래도, 하늘 말고는\n유현숲에 들어갈 길이 없어요.%b',
 '818c28a20f': '루나가 문득 사라졌다.%b',
 '7eb12085da': '게다가, 이쪽은【고대유적의 열쇠】인가.%b',
 '428c5f5eac': '이게 있으면 고대유적서\n호크아이 동생 팔코의 소재도\n확인할 수 있어！%b',
 '7a54f38b83': '카오스게이트 이용할 수 있는 거군요！%b',
 'cbeda037b1': '이게 있으면 고대유적서\n아우 소재도 확인하리다.%b',
 'd85a762ea6': '특히, 나는 배에 관해선\n대륙 굴지의 학자인 거네.%b',
 '1f759aa34b': '게다가, 이쪽은\n【고대유적의 열쇠】인 것이다～제！%b',
 '77280e57af': '특히, 나는 배에 관해선\n대륙 굴지의 학자인 것이다～제！%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_rt20_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

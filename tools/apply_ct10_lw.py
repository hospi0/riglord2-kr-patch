# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_ct10.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 'ef4a8459cf': u'소인처럼 날 수 있는 자가 붙잡고\n내려가거나 지형을 바꿔주셔야 내려갈\n수 있을 것이오.%b',
 '7407f0c516': u'이 목소리는, 갈자드에 라그로스인\n거네？！ 너희, 살아있었던 거야？！%b',
 '40574ce6de': u'놈들 쓰러뜨릴 수밖엔 없는거다～제.\n다들 따라오는 것이다～제.%b',
 'ac5ea79a20': u'어째서, 그런 걸 나한테 가르치는\n거야！ 나더러 어쩌라는 거야？！%b',
 'c951f89488': u'이런 데서, 난 안 져！ 많은\n사람들한테 미소를 되찾아줄 거야！%b',
 '0ad352eba9': u'그 얼굴은, 아무래도, ７인위원회\n님이 이 자리에 안 계신 것에 대한%b',
 'aa086b503d': u'그런 걸 나한테 가르쳐 어쩌자는\n거야？ 나더러 뭘 하라는 거냐고？！%b',
 'cc92605b05': u'놈들을 쓰러뜨릴 수밖에 없는\n모양이군. 그럼 가도록 하지.%b',
 '09652c664e': u'천재인 이 몸에겐 이게 마법구슬이란\n걸 단숨에 알겠는 것이다～제！%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\ct10_lw_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

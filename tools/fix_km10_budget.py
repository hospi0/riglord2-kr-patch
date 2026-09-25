# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_km10.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '9bc8642224': '마을 갈까요？',
 '8bb4647e25': '기다려！%b',
 '814dd77c0c': '이것도 마을 위해서다 견뎌다오.%b',
 '70a83c9704': '지금까지, 많은 여자와 아이들이,\n인질이 되어 마을 지키려,\n성릉곽에 갔었어요.%b',
 'c4f5a4a24b': '그러니 이번 제 차례예요.%b',
 '65ce942572': '얘기 들어보면, 마을 사람 안전을 위해,\n여자랑 아이들을 내주고 있는 것 같아.%b',
 '4d170ca2c3': '그런가 배신인가.%b',
 '334ffc7378': '이 여자도, 성릉곽 인질도,\n목숨 없다고 생각해라！%b',
 '3efbd3b452': '우리 카달에 반항하면 어떻게 되는지,\n뼈저리게 느껴봐라！！%b',
 '51649b8d27': '지금이면 아직 신성마법으로\n어떻게든 될지도 몰라.%b',
 '23c264888d': '・살릴 수 있어！？%b',
 '696030811f': '나즈나도 다시 봤어, 인 거야.%b',
 'e751bf6c49': '부탁！%b',
 'b93b72c719': '그런 게 가능해？%b',
 '5ce8806859': '대체 어떻게 될까, 러스티는？%b',
 '1df0247da7': '난 누구도 러스티를 못 막게 할 거야.%b',
 'dbfb1316f8': '자, 손수건. 써, 인 거야.%b',
 '23b9b6d7bc': '・어쨌든, 그 젊은이에 예 갖추고 싶다.\n내 집으로 와다오.%b',
 '90a12d8566': '혼자 갈 줄 알았어, 인 거야！%b',
 'ed0c1946e5': '연장자든 뭐든,\n거짓말하는 사람 싫어.%b',
 '597a9abc8a': '카무이가 동료로 합류했다.%b',
 'f1ccc5e5e8': '괜찮아？%b',
 'bc27afdefa': '나즈나가 아파라 아파라 날아가라 하고\n해주는 거야 인 거네.%b',
 '60a148917a': '아파라 아파라 날아가라 인 거네！%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_km10_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

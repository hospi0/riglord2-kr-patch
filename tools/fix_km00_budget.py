# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_km00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 'b9d3f04843': '그런데,\n이 늙은이 젊었을 적 소문으로 들은\n토란이란 숨겨진 마을을 아는가？%b',
 'ab5704b292': '카무이 집',
 'b6a36bc2c5': '그녀도 지금은 자고 있다.%b',
 'b5e8947fcf': '거기 마사는,\n마을을 습격 안 하겠다고 약속해줬다.%b',
 'ff9e4559f5': '우린 하릴없이\n여자와 애들을 성릉곽에 보냈다・。%b',
 '8cb1691a49': '그래서, 카무이, 그 후 어찌 됐어？%b',
 'd4a1f6e5ce': '여자·애 인질은 반란 방지용이지？%b',
 'ee48ac7ede': '그럼, 마을 사람들에게 말하고,\n지금 바로 마을서 도망칠 수밖에・。%b',
 '3a6a551214': '뭐 못 느꼈어？%b',
 '06ddcb4e25': '그런가, 난 뭘 망설였던 거지！\n내 안에 잠든 짐승의 본능이 외친다！%b',
 '132eaa3106': '인질과 마을과 날 구하기 위해,\n지금은 너희 호의에 순순히 기대겠다.%b',
 '3ebd2e1854': '오늘은 이미 늦었다, 내일 일찍 출발하자.\n성릉곽까진 내가 안내한다.%b',
 '793c7ca534': '카무이코탄 황신이시여！\n저희를 지켜주소서！%b',
 'e58cc07d75': '이건, 카무이코탄\n전사들에 전해지는 기술 오의서다.%b',
 'd6a571770c': '그중에서도 타타라란 이니시에는,\n상당한 실력자라더군.%b',
 'f74f6bb5d1': '카무이코탄 황신 분노가 느껴진다.\n거대한 악이 세상을 더럽히려 하고 있다！%b',
 '1a15805df6': '카무이 힘은, 신의 힘.%b',
 'c84c457ac6': '신들 분노가 느껴져요.%b',
 'b2c4517324': '카무이 님이다！\n카무이 님 오셨다！%b',
 'fe2c786f04': '【히히이로카네】란\n특별 광석으로 만드는 카타나야.%b',
 '8e719b2ee1': '부탁이야, 그걸 나한테 줘.%b',
 '35c51198eb': '【히히이로카네】 가공할 수 있는 화로는,\n찾았나！？%b',
 '837caf905c': '카타나는 무기가 아니야.\n그건, 쥔 자 영혼 비추는 거울이야.%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_km00_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

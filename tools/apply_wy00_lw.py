# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_wy00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '2c64b7afc2': '괜찮아, 여의적이란 이름이 괜히 있는\n게 아니야. 실수 안 해.%b',
 'cb26eae147': '그 물 담을 통은, 창고 가장 안쪽에\n있다. 그럼, 부탁하네.%b',
 '8a6b06ceaa': '여인들은 아이 구출을 카무이에게\n부탁하고 마을로 돌아갔다.%b',
 '3f7690cad2': '이가 마을에서, 카달군한테 둘러싸여\n있던 시노비 소년이, 신경 쓰여.%b',
 '83c4790434': '너희가 이기면, 카달군도, 이런 항구\n마을 제압할 때가 아니겠지.%b',
 'ceaf36af92': '그러네. 근데, 그럼, 앞으로 어떻게\n할 거야？%b',
 'f71781c3cd': '미안하지만, 돈도 물건도 없다.\n대신, 너와 싸우는 걸로 답례할게.%b',
 'a7cac51ceb': '애들은 다른 방에 있는 모양이군.%b',
 '0078f19946': '이것저것 돈 드니 받아두는 게 어때？%b',
 '316b74950d': '이걸로 관문 자유롭게 지날 수 있어！%b',
 '75edd8f77a': '야마타이에 선조가 이주해오기 전부터\n있던 사람들을 원야마타이인이라 해.%b',
 'd11976abc4': '좋아 그럼, 항구도시 히가타로 가자.%b',
 'e3154ed496': '어이쿠, 이쪽은 그냥 창고 모양이다.%b',
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

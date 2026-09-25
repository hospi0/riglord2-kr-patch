# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_jg00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 'ebed689c51': '그들은 제어 가능하다 여기지만\n카오스 힘은 강대해요.%b',
 'f76a20b8f1': '그놈들을 살려두면,\n훗날, 세상 화근 될지도 모르옵니다.%b',
 '6efc25e55b': '%z그래.\n부끄러우니까 몇 번 말하게 하지 마.',
 'e636a3017a': '７인위원회가, 차원의 문을 열어서,\n카오스 힘이, 카칼클랜서 흘러들어와,%b',
 '2feb1ba6f5': '계속 계속, 기다리고 있을 테니까・。%b',
 '2d782961d6': '문을 열 때마다,\n이 세상에 카오스가 새는 거예요.%b',
 'be7870c886': '%z저, 정말인 거야？！\n정말 나즈나로 괜찮은 거야인 거야？',
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

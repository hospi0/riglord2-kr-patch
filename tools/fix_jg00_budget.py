# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_jg00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '3742ffadfd': '전 차원문 수호자, 루나예요.\n그리고 여기가, 차원의 문이에요.%b',
 'ebed689c51': '그들은 제어할 수 있다고 여기는 모양이지만\n카오스 힘은 강대해요.%b',
 '30488da06b': '나즈나도 아스카랑 같은 마음인 거네！%b',
 'fcae816867': '알렉트리아 대도서관\n무투사서 한 사람으로서,%b',
 '440bb3f39b': '그리고 약속해줘,\n반드시 살아 돌아오겠다고・。%b',
 '961e9294f1': '용서 못 한다～제！\n이 몸도 데려가는 것이다～제！%b',
 '78a9cd71ac': '단숨에 ７인위원회 쓰러뜨리는 건\n불가능한 것이다～제！%b',
 'ca416e87ed': '그럼, 차원문을 닫습니다.%b',
 'd2a73b1518': '%z저는, 이 유현숲을 다시 봉인할게요.',
 '913f685937': '어떻게 할까요？　　',
 'fbdea6905e': '시라나미 고른다',
 'b84846df9e': '나즈나 고른다',
 '50ff4d3350': '안 고른다',
 'b4aeab2326': '%z그래.\n불만？',
 '71fd761392': '%z・어라, 이상한 거야.\n눈에서 물이 나오는 거야, 인 거네.',
 '87be53be5d': '%z나즈나.\n너랑 떨어지긴 싫어.',
 'be7870c886': '%z저, 정말인 거야？！\n정말 나즈나로 괜찮은 거야, 인 거야？',
 '73d2c3c832': '%z아스카, 좋아하는 거야！',
 '638dcdd75e': '수많은 목숨 대신해\n감사 인사를 드려요.%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_jg00_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

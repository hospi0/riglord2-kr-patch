# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_ot00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '649c0236ed': '걱정 말라니까,\n오르트마서 배 자유롭게 띄우게 되면%b',
 'fcc5c99589': '재해서 중요한 건 침착함이에요.\n　　　　　　　　　　（오르트마 자치회）%b',
 'aa4c154b9b': '사모사구나！\n말해두는데, 거긴 아무것도 없어.%b',
 '39b67c8fce': '뭐라던가, 이 마을 북동 고대유적에,\n카달 놈들이 모은 마도사랑 학자들을\n가둬놓고, 뭔가 하는 모양이야.%b',
 'd97aded7ff': '뭘요, 괜찮아요,\n분명 어딘가서 잘 지낼 거예요.%b',
 'e875e2d391': '마을 사람들은 코르베츄어사란 여행사를\n자랑스러워하는 모양인데,\n내가 보기엔, 별거 아니던데.%b',
 '3b14107abb': '그래서 그 배는, 지금 어디 있는데？%b',
 '2d5d743672': '어서 옵쇼.\n디아느 선장님한테 얘기 들었습니다요.%b',
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

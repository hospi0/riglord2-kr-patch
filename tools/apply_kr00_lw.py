# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_kr00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 'f6f2fd61f8': '근데, 카달 놈들,\n유적서 사람 모아 뭔가 찾는 듯해.%b',
 '022659bb58': '신뢰・실적 １００년 전통을 자랑하는\n코르베츄어사를 이용해주세요.\n　　　　　　　　　　　（코르베츄어사）%b',
 'cb79b7949a': '뭐라던가 고대마법문명 연구하는\n마도사랑 학자들 모은다는 얘기야.%b',
 '8ee3515176': '뭐, 확실히,\n왕족이랑 아는 사이란 거짓말했으니.%b',
 '2b9f7d9777': '이 마을 남쪽엔, 고대유적이 있어서,\n아서왕이 싸운 리그로드 전쟁에서는,%b',
 '3430939a77': '와ー, 세상의 끝이다！\n이제 모든 게 엄청난 일 되는 거야！%b',
 '0d63e3c20c': '아, 이 하레하레갓콘이란 게,\n싫거나 무섭거나 화나는 일을\n나타내는 유행어야.%b',
 '7ac6051d8e': '보잘것없는 마을사람 불과한 저지만,\n세상을 성립시키는 건,%b',
 '1492e95bca': '코르베츄어사에서는,\n곧바로, 영웅들 발자취를 찾는 투어를\n기획 중이라더군요.%b',
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

# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_zm00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '5c4151a3cf': '얘기가 바뀌는데, 오르트마에서\n무기점이랑 방어구점을 하는 매인간은\n상당한 검술 실력자래요.%b',
 '37ea3b4709': '공주님, 이제 슬슬 모험 여행은\n그만두시고, 성에 자리 잡아주세요.%b',
 'f82f390337': '뮤 왕녀, 드래군성을 탈환！\n리그로드에서 카달의 그림자가 사라지는\n건 이제 시간문제！\n　　　　　　　　　　　　　（류샤）\n',
 'c1ef313e87': '근데, 그때는, 그렇게 하는 것\n말고는 방법이 없었어.%b',
 '04d7b9d6a2': '소문엔, 퀸즈랜드도, 여기랑 비슷하게\n심각한 상황이라던데요.%b',
 'bada8a7abe': '고대 자료라도 없는 한, 새 기술\n만들어내는 건 지난한 일이지.%b',
 'cefe44bab0': '독학이다 보니, 그 검로를 간파하는\n건 불가능하다고들 한대요.%b',
 '915711ec9f': '우리 방어구는, 자네들 안 맞을\n게야.\n',
 'efe30d9116': '아이고, 저희도, 그런 훌륭한 분께\n나라를 맡겨, 기뻐하고 있습니다.%b',
 '41034ed23b': '아니. 이것도, 위에 서는 자의・。%b',
 '185e9f5f40': '이, 이, 이건 어찌 된 일일까요.\n세상은, 펴 평화로워진 거 아녔나요？%b',
 '93a40debad': '어머, 어머어머어머어머어머어머어머,\n뮤 님 아니세요.%b',
 'd22cce6ae5': '↑뮤 님과 용기사 만세！\n어서 돌아오시길 기다려요.\n　　　　　　　　　（자르마 주민 일동）%b',
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

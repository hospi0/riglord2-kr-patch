# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_zm00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 'aeeb54743b': '근데, 야마타이로 향하는 이유를\n자르마 사람들한테 설명하면,\n공황 상태 될 것 같았어.%b',
 'af2e72ff33': '거짓말한 거야.%b',
 'f9e89a6f25': '거짓？%b',
 'a1aad5c77f': '남한테 이해받지 못하는 건,\n슬픈 일이지.%b',
 'efe30d9116': '아이고, 저희도, 그런 훌륭한 분께\n나라를 맡겨, 진심으로 기뻐하고 있습니다.%b',
 '36357ef936': '리그로드를 구할 이는 왕녀님뿐이에요.%b',
 'bada8a7abe': '고대 자료라도 없는 한,\n새 기술 만들어내는 건 지난한 일이지.%b',
 'daed704da6': '요즘, 서쪽 숲 괴물들이\n전보다 흉포해진 모양이다.%b',
 '4241206e50': '그런 달인이라면,\n가신으로 맞을까 해서요.%b',
 '6284f839bc': '뭐, 그만두나.\n다른 거 있나？',
 'c6da31b3b5': '뭐가 필요하냐？',
 'd111973974': '뭘 팔 거냐？',
 '05312af4c6': '어머, 그만두게.\n다른 거 있어？',
 '8c20272db9': '그래서 뭐 살 거야？',
 '021ec53253': '그래서 뭐 팔 거야？',
 '2d483435d6': '고마워.\n다른 거 살 거야？',
 'e0e238d0bb': '고마워.\n다른 거 팔 거야？',
 '8a5bc7636e': '구경만 하나.\n다른 거 있나？',
 '915711ec9f': '우리 방어구는, 자네들 안 맞을 게야.\n',
 'cce9bcd54f': '여긴 영광의 지름길, 투기장이야.%b',
 '110bf2b55f': '적의 강함에 따른\n짭짤한 상품 받을 수 있지.%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_zm00_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_iz00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 'c193eb97cf': '안내린다',
 '2523437938': '거기다 나즈나 러브러브 작전을\n방해하다니, 너무한 거야, 인 거야！%b',
 '47ec69ebbb': '아스카가 확실히 안 하니까\n이런 일이 벌어지는 거네！%b',
 '250ffc85ed': '허나 지금은 안 돼.%b',
 '23a1851ca1': '누군가가 누군가를 좋아하는 게,\n그렇게 중요한 건가？%b',
 '4384727b9a': '하나 묻겠는데 강해지고 싶냐, 아스카？%b',
 '75ef4290d3': '너와 함께 싸우고, 힘이 되고,\n돕고 싶다고 생각해서지.%b',
 '0414f6d45c': '고대마법문명 기술과 지식 전부가,\n지금 여기에！%b',
 'b0076c42f9': '그럼, 고칠 수 있네！%b',
 'ee35a012d0': '분부 받들겠나이다\n공주님.%b',
 '57726047b6': '그래서 원인이란 건？%b',
 '700e4f8f73': '그놈들이,\n유현숲을 지키는 봉인을 풀었사옵니다.%b',
 'a2b8c3d4e9': '그럼 대체 어떻게 하면 되는데？%b',
 'fb3a369ed3': '하오면, 뮤 공주님,\n아우 의견을 한번 고려해주소서.%b',
 'b2baa269d3': '라그로스탑에 카오스게이트 있사옵니다.%b',
 '9c0fc69e6f': '그렇지.%b',
 '6d718958d4': '어이쿠, 공주님！%b',
 '5074944e93': '바로 이거,\n익시즈 수리에 필수적인 물건.%b',
 '4fe20a93fa': '그렇소.\n오르트마는, 리그로드의 손꼽는 항구.%b',
 '01c50dae55': '광익선 익시즈,\n언제 출발할 수 있사옵니다！%b',
 '5dcdf565ae': '허나, 저희는,\n공주님이 최상 상태로 싸우게,%b',
 '6519598b2b': '리그로드 대륙 중앙\n차원의 문을 향해%b',
 'f77ded8cc6': '대체 무슨 일이 벌어지는 걸까？%b',
 '926cc34f4f': '대체 무슨 일이야？%b',
 '0646dc533b': '저도, 필사적으로 저항했지만,\n역부족으로, 그들에게 문이 열리고 말았어요.%b',
 '502214469a': '저는, 동쪽 유현숲\n차원의 문에서 기다릴게요.%b',
 'a57b397e5e': '어서 와주세요！%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_iz00_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

# -*- coding: utf-8 -*-
import io, re

p = r'C:\claude\project\riglord2-kr-patch\tools\trans_story_kr00.py'
s = io.open(p, encoding='utf-8').read()

FIX = {
 '77d8084785': '마을 나갈까요？',
 'cc9d6a9540': '뭘로 할까？',
 'd99b6ce61b': '그래서 뭘로 하실래요？',
 '8ba63b27c7': '파실 게 없는 것 같은데요？',
 'ddf6ea469e': '예전엔 고대마법문명 유산 잠들었었어.%b',
 'de20e20382': '고대유적 들어가려면,\n【고대유적의 열쇠】\n필요하다더라.%b',
 '2aa494d812': '드래군 뮤 공주님도 애용하시는\n코르베츄어사를 잘 부탁드립니다.\n　　　　　　　　　　　（코르베츄어사）%b',
 '99ab123ca4': '급한 도주에도,\n코르베츄어사를 부탁드립니다.\n　　　　　　　　　　　（코르베츄어사）%b',
 '022659bb58': '신뢰와 실적으로 １００년 전통을 자랑하는\n코르베츄어사를 이용해주세요.\n　　　　　　　　　　　（코르베츄어사）%b',
 'ebabab9b02': '당연히 체포・투옥・고문・사형이에요.%b',
 'd98307e590': '늙으신 부모님이랑 가축들이,\n제가 돌아오길 기다려서요.%b',
 'f6a6151492': '있잖아・。%b',
 '4c680fea84': '몇 번 말하게 하지 마.%b',
 'cfe5ec75ed': '안 되지요.\n뭐든 밀어붙임이 중요하죠！%b',
 '8525ae03f8': '이 마을은 정말 아무것도 없지만,\n여기 주민들은 다들 착한 놈들뿐이야.%b',
 'c6746668a9': '신뢰・실적 １００년 전통을 자랑하는,\n이 마을 자랑거리 여행사야.%b',
 '6cc8adf85b': '이 마을 자랑이야！%b',
 '69487b2232': '있잖아 너 믿을 수 있어？%b',
 '7ce24200ab': '나도 써줬으면 좋겠다~.%b',
 'ee55d14d95': '세상에 평화 돌아왔어요.\n다행이다 다행이야.%b',
 '93b60f155b': '지금 다시, 그 차원의 문이,\n유현숲에 나타났다던가・。%b',
 'dbec1527d8': '스스로 목숨으로 차원의 문에\n봉인을 걸었기 때문 아니냐,\n는 얘기였는데・。%b',
 '25ddc2592d': '큰일이다 큰일이다.%b',
 '45fe1b354a': '빨리 나아서,\n그 사람 웃는 얼굴 보고 싶다.%b',
 'd8b9e017cd': '이대로 세상 멸망하는 걸까・。%b',
 '21d8d93a28': '나다！\n타카오는 나다！%b',
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
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\fix_kr00_result.txt', 'w', encoding='utf-8')
out.write('patched %d/%d\n' % (n, len(FIX)))
if missing:
    out.write('missing: %s\n' % ', '.join(missing))
out.close()

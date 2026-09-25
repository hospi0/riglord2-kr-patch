# -*- coding: utf-8 -*-
import io

def size(t):
    n = 0
    for ch in t:
        n += 2 if u'\uAC00' <= ch <= u'\uD7A3' else len(ch.encode('cp932', 'replace'))
    return n

budgets = {
 '3996377193': 47, 'a6b1e6e103': 32, '9673c416d1': 18, 'fa7d86a09c': 35,
 '779605d213': 26, '63a922b735': 12, '86e34e36b8': 51,
}
cands = {
 '3996377193': u'성을 흙발로 더럽히다니！\n용서 못 해요！%b',
 'a6b1e6e103': u'당신들이 진짜 영웅이에요！%b',
 '9673c416d1': u'어떻게 생각해？%b',
 'fa7d86a09c': u'불로장수 보물\n신선의 옥을 지니면,%b',
 '779605d213': u'・・・라그로스놈・・・。%b',
 '63a922b735': u'사랑 샘.%b%h',
 '86e34e36b8': u'봐도 상관없지만,\n함부로 들어가선 안 된다！%b',
}
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\qh00_size_check2.txt', 'w', encoding='utf-8')
for k, t in cands.items():
    b = budgets[k]
    sz = size(t)
    flag = 'OK' if sz <= b else '*** OVER ***'
    out.write('%s\t%d/%d\t%s\t%s\n' % (k, sz, b, flag, t))
out.close()

# -*- coding: utf-8 -*-
import io

def size(t):
    n = 0
    for ch in t:
        n += 2 if u'\uAC00' <= ch <= u'\uD7A3' else len(ch.encode('cp932', 'replace'))
    return n

budgets = {
 '11cfa998b4': 37, 'dc6dba7713': 21, 'dd7853cde7': 24,
 'b6cd5bb14d': 14, '48496787d3': 14, 'd1cae4b0cb': 12,
}
cands = {
 '11cfa998b4': u'카다르 위해 싸워？\n안 되는 소리.%b',
 'dc6dba7713': u'큭！\n후퇴한다！%b',
 'dd7853cde7': u'그럼 좋겠는데・・・。%b',
 'b6cd5bb14d': u'그렇구나！%b',
 '48496787d3': u'헛소리 마！%b',
 'd1cae4b0cb': u'싫다는군！%b',
}
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\nj10_size_check3.txt', 'w', encoding='utf-8')
for k, t in cands.items():
    b = budgets[k]
    sz = size(t)
    flag = 'OK' if sz <= b else '*** OVER ***'
    out.write('%s\t%d/%d\t%s\t%s\n' % (k, sz, b, flag, t))
out.close()

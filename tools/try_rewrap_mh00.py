# -*- coding: utf-8 -*-
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shrink_ko as S
import trans_story_mh00 as M


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


jp = {}
with io.open(r'..\work\trans\strings.tsv', encoding='utf-8') as f:
    next(f)
    for line in f:
        a = line.rstrip('\n').split('\t')
        if len(a) >= 6:
            jp[a[0]] = unesc(a[5])

keys = ['81d52e4eee', 'aee3b5293a', '0824d8591b', '7a64631e91', '9ca246231f', '9c968fe152', '985e546f81',
        '6860640e72', '417e3a1e26', 'ff29cc923c', '509eabf2d2', '8cadfa251a', '7e2d04ba44', '2b1bddda9a',
        'd60a8af0a6', '1d024f5a65', '10debb87e9']
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\mh00_rewrap.txt', 'w', encoding='utf-8')
for k in keys:
    cur = M.TRANS[k]
    jt = jp.get(k, '')
    nlines = jt.count('\n') + 1
    new = S.rewrap(cur, 20, nlines)
    if new:
        out.write('AUTO %s\n  %r\n' % (k, new))
    else:
        out.write('MANUAL %s\n  cur: %r\n  jp:  %r\n' % (k, cur, jt))
out.close()

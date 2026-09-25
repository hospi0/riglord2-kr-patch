# -*- coding: utf-8 -*-
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manual_lw_fixes import FIX

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
TOKEN = re.compile(r'%[A-Za-z][0-9]*')


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


def L(s):
    return len(TOKEN.sub('', s))


jp = {}
with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
    next(f)
    for line in f:
        a = line.rstrip('\n').split('\t')
        if len(a) >= 6:
            jp[a[0]] = unesc(a[5])

out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\verify_manual.txt', 'w', encoding='utf-8')
n_bad = 0
for k, v in FIX.items():
    jt = jp.get(k, '')
    jl = jt.split('\n')
    kl = v.split('\n')
    if len(kl) > len(jl):
        out.write('%s LINES %d>%d\n' % (k, len(kl), len(jl)))
        n_bad += 1
        continue
    jp_max = max(L(x) for x in jl)
    if jp_max > 20:
        out.write('%s SKIP(jp_max=%d)\n' % (k, jp_max))
        continue
    for i, kline in enumerate(kl):
        kb = L(kline)
        if kb > 20:
            out.write('%s line%d %dB > 20B  %r\n' % (k, i, kb, kline))
            n_bad += 1
out.write('n_bad=%d\n' % n_bad)
out.close()

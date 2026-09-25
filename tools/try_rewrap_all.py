# -*- coding: utf-8 -*-
import io, os, sys, glob, importlib, pickle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shrink_ko as S

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
SCRATCH = r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad'


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
with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
    next(f)
    for line in f:
        a = line.rstrip('\n').split('\t')
        if len(a) >= 6:
            jp[a[0]] = unesc(a[5])

modmap = {}
for path in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trans_story_*.py'))):
    modname = os.path.splitext(os.path.basename(path))[0]
    mod = importlib.import_module(modname)
    for k, v in mod.TRANS.items():
        if v is None:
            continue
        modmap[k] = (modname, v)

bad_lines = io.open(os.path.join(SCRATCH, 'lw_all.txt'), encoding='utf-8').readlines()[1:]
keys = []
seen = set()
for line in bad_lines:
    a = line.rstrip('\n').split('\t')
    k = a[0]
    if k in seen:
        continue
    seen.add(k)
    keys.append(k)

out = io.open(os.path.join(SCRATCH, 'rewrap_attempt.txt'), 'w', encoding='utf-8')
auto_fixed = {}
manual_needed = []
for k in keys:
    if k not in modmap:
        out.write('%s NOT IN ANY MODULE\n' % k)
        continue
    modname, cur = modmap[k]
    jt = jp.get(k, '')
    nlines = jt.count('\n') + 1
    new = S.rewrap(cur, 20, nlines)
    if new is not None:
        auto_fixed[k] = (modname, cur, new)
        out.write('AUTO %s [%s]\n  old: %r\n  new: %r\n' % (k, modname, cur, new))
    else:
        manual_needed.append((k, modname, cur, jt))
        out.write('MANUAL %s [%s]\n  cur: %r\n  jp:  %r\n' % (k, modname, cur, jt))

out.write('\ntotal=%d auto=%d manual=%d\n' % (len(keys), len(auto_fixed), len(manual_needed)))
out.close()

pickle.dump((auto_fixed, manual_needed), open(os.path.join(SCRATCH, 'lw_fix.pkl'), 'wb'))

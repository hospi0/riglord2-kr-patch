# -*- coding: utf-8 -*-
import io, os, pickle, re

SCRATCH = r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad'
HERE = os.path.dirname(os.path.abspath(__file__))

auto_fixed, manual_needed = pickle.load(open(os.path.join(SCRATCH, 'lw_fix.pkl'), 'rb'))

by_mod = {}
for k, (modname, old, new) in auto_fixed.items():
    by_mod.setdefault(modname, []).append((k, old, new))

log = io.open(os.path.join(SCRATCH, 'apply_auto_result.txt'), 'w', encoding='utf-8')
for modname, items in by_mod.items():
    path = os.path.join(HERE, modname + '.py')
    s = io.open(path, encoding='utf-8').read()
    n = 0
    for k, old, new in items:
        pat = re.compile(r"    '%s': '.*?',\n" % re.escape(k))
        m = pat.search(s)
        if not m:
            log.write('MISSING %s in %s\n' % (k, modname))
            continue
        s = s[:m.start()] + "    '%s': %r,\n" % (k, new) + s[m.end():]
        n += 1
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    log.write('%s: %d/%d patched\n' % (modname, n, len(items)))
log.close()

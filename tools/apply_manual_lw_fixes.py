# -*- coding: utf-8 -*-
import glob, importlib, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from manual_lw_fixes import FIX

modmap = {}
for path in sorted(glob.glob(os.path.join(HERE, 'trans_story_*.py'))):
    modname = os.path.splitext(os.path.basename(path))[0]
    mod = importlib.import_module(modname)
    for k in mod.TRANS:
        modmap[k] = modname

by_mod = {}
for k, v in FIX.items():
    modname = modmap.get(k)
    if modname is None:
        continue
    by_mod.setdefault(modname, []).append((k, v))

log = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\apply_manual_result.txt', 'w', encoding='utf-8')
for modname, items in by_mod.items():
    path = os.path.join(HERE, modname + '.py')
    s = io.open(path, encoding='utf-8').read()
    n = 0
    for k, v in items:
        pat = re.compile(r"    '%s': '.*?',\n" % re.escape(k))
        m = pat.search(s)
        if not m:
            log.write('MISSING %s in %s\n' % (k, modname))
            continue
        s = s[:m.start()] + "    '%s': %r,\n" % (k, v) + s[m.end():]
        n += 1
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    log.write('%s: %d/%d patched\n' % (modname, n, len(items)))

missing_keys = set(FIX) - set(modmap)
if missing_keys:
    log.write('NOT IN ANY MODULE: %s\n' % sorted(missing_keys))
log.close()

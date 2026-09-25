# -*- coding: utf-8 -*-
import io, sys, importlib
sys.path.insert(0, r'C:\claude\project\riglord2-kr-patch\tools')
import shrink_ko

import trans_story_ct10
importlib.reload(trans_story_ct10)
TRANS = trans_story_ct10.TRANS

keys = ['ef4a8459cf', '7407f0c516', '40574ce6de', 'ac5ea79a20',
        'c951f89488', '0ad352eba9', 'aa086b503d', 'cc92605b05',
        '09652c664e']

out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\ct10_lw_rewrap.txt', 'w', encoding='utf-8')
for k in keys:
    t = TRANS[k]
    nlines = t.count('\n') + 1
    r = shrink_ko.rewrap(t, 20, nlines)
    out.write('%s | nlines=%d\n  ORIG: %r\n  REWRAP: %r\n\n' % (k, nlines, t, r))
out.close()
print('done')

# -*- coding: utf-8 -*-
import io, sys, importlib
sys.path.insert(0, r'C:\claude\project\riglord2-kr-patch\tools')
import shrink_ko

import trans_story_qh00
importlib.reload(trans_story_qh00)
TRANS = trans_story_qh00.TRANS

keys = ['47f794906e', '6862d236e4', '0aa3d1366b', '13d10919c8', 'e02eb85283',
        'eb570f43f2', 'afe49d71b4', 'd418e53aaa', 'd3d27b8763', 'c3e4433858',
        '236fd23f75']

out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\qh00_lw_rewrap.txt', 'w', encoding='utf-8')
for k in keys:
    t = TRANS[k]
    nlines = t.count('\n') + 1
    r = shrink_ko.rewrap(t, 20, nlines)
    out.write('%s | nlines=%d\n  ORIG: %r\n  REWRAP: %r\n\n' % (k, nlines, t, r))
out.close()
print('done')

# -*- coding: utf-8 -*-
import io, sys, importlib
sys.path.insert(0, r'C:\claude\project\riglord2-kr-patch\tools')
import shrink_ko

import trans_story_nj10
importlib.reload(trans_story_nj10)
TRANS = trans_story_nj10.TRANS

keys = ['26685b5467', '79b3d72739', 'd63c3e277f', '0197c3f5f5',
        '7dedcf543c', 'f10773be1d', '06a939ccf4']

out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\nj10_lw_rewrap.txt', 'w', encoding='utf-8')
for k in keys:
    t = TRANS[k]
    nlines = t.count('\n') + 1
    r = shrink_ko.rewrap(t, 20, nlines)
    out.write('%s | nlines=%d\n  ORIG: %r\n  REWRAP: %r\n\n' % (k, nlines, t, r))
out.close()
print('done')

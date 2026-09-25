# -*- coding: utf-8 -*-
import re, io
s = io.open('trans_story_nj10.py', encoding='utf-8').read()
pat = re.compile(u'[\u3130-\u318F\u00B7]')
lines = s.split('\n')
out = io.open(r'C:\Users\kbwor\AppData\Local\Temp\claude\C--claude\38c2e5b7-0f79-48ae-a13c-93c9376910de\scratchpad\nj10_jamo.txt', 'w', encoding='utf-8')
for i, l in enumerate(lines):
    if pat.search(l):
        out.write('%d\t%s\n' % (i+1, l))
out.close()

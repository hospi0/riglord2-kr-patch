# -*- coding: utf-8 -*-
"""문장부호 최종 정리 — normalize_numerals.py 뒤에 돌린다.

1. ★★반각 `,`(U+002C) 를 전각 `，`(U+FF0C, 폰트 0x8143 에 이미 있음)로 바꾼다.
   번역하면서 자연스러운 한국어 문장에 반각 쉼표를 580회 썼는데, 이 폰트엔
   반각 쉼표 글리프가 없다(코드표 최솟값이 0x8140 — 전각 전용).
2. 문장부호 **뒤** 공백을 지운다(전 프로젝트 대원칙,
   [[feedback_no_space_after_punct]]). 단어 사이 공백은 그대로 둔다.
"""
import io
import os
import re

PUNCT_TRAIL_SPACE = re.compile(r'([，、。！？…」』】）])[ 　]+')


def fix(s):
    s = s.replace(',', '，')
    s = PUNCT_TRAIL_SPACE.sub(r'\1', s)
    return s


if __name__ == '__main__':
    src = os.path.join('..', 'work', 'trans', 'ko_normalized.tsv')
    dst = os.path.join('..', 'work', 'trans', 'ko_final.tsv')
    n = 0
    with io.open(src, encoding='utf-8') as fi, io.open(dst, 'w', encoding='utf-8', newline='') as fo:
        fo.write(next(fi))
        for line in fi:
            a = line.rstrip('\n').split('\t')
            new = fix(a[1])
            if new != a[1]:
                n += 1
            fo.write('%s\t%s\n' % (a[0], new))
    print('문장부호 정리 %d행 변경 -> %s' % (n, dst))

# -*- coding: utf-8 -*-
"""**장소·시설 이름표**(`酒場` 등) 전수 조사 — 추출에서 빠진 것 찾기.

실기 제보: 술집 화면 상단이 「킨場」으로 깨져 나왔다. 원문은 `酒場` 인데
`corpus2.is_real()` 이 «가나가 없으면 4자 이상» 을 요구하는 바람에 2글자
한자 라벨이 통째로 노이즈로 버려졌다([[feedback_detector_ratio_per_string_not_per_region]]).
깨져 보이는 이유는 `酒` 가 도너로 뺏긴 칸이라서다.

이름표는 `.MAP` 안에서 **배경 파일명(`sakaba_c.p` 등) 바로 뒤**에 온다:
    `... %b\\x00` `sakaba_c.p\\x00` `酒場\\x00` `話を聞く\\x00` `家をでる\\x00\\x00`
그래서 정규식으로 «전각 라벨»을 긁지 않고, **파일명 앵커 뒤 한 조각**만
정확히 집어낸다(오탐 방지).
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

# 배경 파일명: 소문자/숫자/밑줄 + 확장자 .p 또는 .pra 등
FNAME = re.compile(rb'[a-z0-9_]{3,20}\.p[a-z]{0,3}\x00')
JP = re.compile(r'[぀-ヿ一-鿿]')


def labels_of(d):
    """-> [(오프셋, 라벨문자열)]"""
    out = []
    for m in FNAME.finditer(d):
        s = m.end()                       # 파일명 뒤 = 라벨 시작 후보
        e = d.find(b'\x00', s)
        if e < 0 or e - s == 0 or e - s > 24:
            continue
        try:
            t = d[s:e].decode('cp932')
        except UnicodeDecodeError:
            continue
        if not JP.search(t):
            continue
        if any(ord(c) < 0x20 for c in t):
            continue
        out.append((s, e, t))
    return out


def main():
    known = set()
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 6:
                known.add(a[5])

    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)
    found = {}                             # 라벨 -> [(파일, 오프셋)]
    for path, lba, size, oob in sorted(rows):
        if os.path.splitext(path)[1].upper() not in ('.MAP', '.MSG', '.MAT'):
            continue
        d = iso.read(lba, size)
        for s, e, t in labels_of(d):
            found.setdefault(t, []).append((path, s, e - s))

    miss = {t: v for t, v in found.items() if t not in known}
    print('이름표 후보 %d종 / 그중 strings.tsv 미등재 %d종'
          % (len(found), len(miss)))
    for t in sorted(miss, key=lambda x: -len(miss[x])):
        v = miss[t]
        print('  %-14r %3d곳 %2dB  예) %s' % (t, len(v), v[0][2], v[0][0]))


if __name__ == '__main__':
    main()

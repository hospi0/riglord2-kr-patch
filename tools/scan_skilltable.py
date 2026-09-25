# -*- coding: utf-8 -*-
"""`/1_RIG2.BIN` 안전구간의 **미번역 일본어 조각**을 전수 조사한다.

실기 제보: 기술 메뉴에 `ｳｨﾝﾄﾞ` 가 그대로 남고, 기술 명명 화면의 「放す」가
「덮す」로 깨져 나왔다. `上昇/下降/竜変化` 는 번역돼 있으므로 **같은 표 안에서
일부만** 빠진 것 — 즉 검출기 사각지대다.

여기서는 판정을 «검출기 재사용»이 아니라 **원본 디스크 바이트 직접 스캔 +
`ui_strings.tsv` 대조**로 한다([[feedback_untranslated_detector_byte_diff]]).
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

SAFE_LO, SAFE_HI = 0x7B1E4, 0x97E6A        # build_kr.py 가 쓰는 실측 안전구간
JP = re.compile(r'[぀-ヿ一-鿿ｦ-ﾝ]')


def segments(d, lo, hi):
    """NUL 로 끊어 읽되 앞뒤 0xFF 런을 벗겨낸다(세션3 후속의 확정 규약)."""
    out, i = [], lo
    while i < hi:
        j = d.find(b'\x00', i, hi)
        if j < 0:
            j = hi
        raw = d[i:j].strip(b'\xff')
        if raw:
            try:
                t = raw.decode('cp932')
            except UnicodeDecodeError:
                t = None
            if t and JP.search(t):
                out.append((i + (len(d[i:j]) - len(d[i:j].lstrip(b'\xff'))), raw, t))
        i = j + 1
    return out


def main():
    rows = {r[0]: r for r in load_list()}
    p, lba, size, oob = rows['/1_RIG2.BIN']
    d = Iso(TRACK1).read(lba, size)

    known = set()
    with io.open(os.path.join(WORK, 'trans', 'ui_strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 7:
                known.add(a[6])

    segs = segments(d, SAFE_LO, SAFE_HI)
    # ⛔코드·데이터가 우연히 디코드된 것을 걸러야 한다. 진짜 표기는
    #   «제어문자 없음 + 전부 일본어/전각/영숫자» 이고 2글자 이상이다.
    def real(t):
        if len(t) < 2:
            return False
        for c in t:
            o = ord(c)
            if o < 0x20:
                return False
            if 0xE000 <= o <= 0xF8FF:
                return False
            ok = (0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF
                  or 0xFF01 <= o <= 0xFF9F or o == 0x3000
                  or 0x2010 <= o <= 0x30FF or o < 0x80)
            if not ok:
                return False
        return bool(JP.search(t))

    missing = [(o, raw, t) for o, raw, t in segs if t not in known and real(t)]
    print('안전구간 일본어 조각 %d개 / 그중 ui_strings 에 없는 것 %d개'
          % (len(segs), len(missing)))
    for o, raw, t in missing:
        print('  0x%06X  %2dB  %r' % (o, len(raw), t))


if __name__ == '__main__':
    main()

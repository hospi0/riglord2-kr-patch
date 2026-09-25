# -*- coding: utf-8 -*-
"""**디스크 전체**에서 남은 미번역 일본어를 찾는다 — 파일 종류를 안 가린다.

실기 스샷에서 계속 새 미번역이 나온다(`ストライク` 기술명, `ﾏｯﾌﾟﾁｪｯｸ`,
속성 단일 한자 `闇`). 지금까지는 «어느 파일에 있을 것이다»라고 짐작해서
`.MAP/.MSG/.MAT` + `.OVL` + `1_RIG2.BIN` 만 봤는데, 그 짐작이 틀렸다
([[feedback_verify_which_asset_the_screen_uses]]).

여기서는 **빌드된 출력 디스크**를 통째로 훑어 아직 남아 있는 일본어를 센다.
빌드 결과를 보므로 «번역된 것»은 자동으로 빠진다 — 별도 대조표가 필요 없다
([[feedback_untranslated_detector_byte_diff]] 와 같은 발상).

★검출 기준을 세 갈래로 나눠 «놓치는 축»을 없앤다.
   full2  전각 가나/한자 2자 이상  (지금까지 쓰던 기준)
   full1  전각 **1자**           (속성 아이콘 `火` `闇` 같은 단일 글자)
   half   **반각 가타카나** 포함  (`ﾏｯﾌﾟﾁｪｯｸ` `ｷｬﾗ切替`)
"""
import os
import re
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, OUT_TRACK1
from peek import load_list

KANA = re.compile(r'[぀-ヿ]')
HAN = re.compile(r'[一-鿿]')


def is_lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def is_trail(b):
    return 0x40 <= b <= 0xfc and b != 0x7f


def is_halfkana(b):
    return 0xa1 <= b <= 0xdf


def is_gaiji_lead(b):
    return 0xf0 <= b <= 0xf9


def decode(seg):
    """(표시문자열, 전각 글자수, 반각가타카나 있음?) 또는 (None,0,False)."""
    out = []
    i, n = 0, len(seg)
    full = 0
    half = False
    while i < n:
        b = seg[i]
        if is_gaiji_lead(b) and i + 1 < n:
            out.append('{G:%02X%02X}' % (b, seg[i + 1]))
            i += 2
        elif is_lead(b) and i + 1 < n and is_trail(seg[i + 1]):
            ch = seg[i:i + 2].decode('cp932', 'replace')
            out.append(ch)
            if KANA.match(ch) or HAN.match(ch):
                full += 1
            i += 2
        elif is_halfkana(b):
            out.append(bytes([b]).decode('cp932', 'replace'))
            half = True
            i += 1
        elif b in (0x0a, 0x0d) or 0x20 <= b < 0x7f:
            out.append(chr(b))
            i += 1
        else:
            return None, 0, False
    return ''.join(out), full, half


def scan(data, min_len=2):
    out = []
    n = len(data)
    i = 0
    while i < n:
        if data[i] == 0:
            i += 1
            continue
        j = data.find(b'\x00', i)
        if j < 0:
            j = n
        raw = data[i:j]
        seg = raw.strip(b'\xff')
        off = i + (len(raw) - len(raw.lstrip(b'\xff')))
        i = j + 1
        if len(seg) < min_len or len(seg) > 400:
            continue
        t, full, half = decode(seg)
        if t is None:
            continue
        if full == 0 and not half:
            continue
        out.append((off, bytes(seg), t, full, half))
    return out


def main():
    disc = OUT_TRACK1 if os.path.exists(OUT_TRACK1) else TRACK1
    print('훑는 디스크: %s' % disc)
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(disc)

    per_file = collections.Counter()
    samples = collections.defaultdict(list)
    kinds = collections.Counter()
    total = 0
    for path, lba, size, oob in rows:
        if size > 8 << 20:
            continue
        d = bytes(iso.read(lba, size))
        for off, raw, t, full, half in scan(d):
            kind = 'half' if half else ('full1' if full == 1 else 'full2')
            per_file[path] += 1
            kinds[kind] += 1
            total += 1
            if len(samples[path]) < 6:
                samples[path].append((kind, off, t))

    print('\n남은 일본어 조각 %d개 / 파일 %d개' % (total, len(per_file)))
    print('갈래: %s' % dict(kinds))
    print('\n-- 파일별 상위 30 --')
    for path, n in per_file.most_common(30):
        print('  %-22s %5d' % (path, n))
        for kind, off, t in samples[path][:3]:
            print('        [%s] 0x%06X %r' % (kind, off, t[:44]))
    return per_file, samples


if __name__ == '__main__':
    main()

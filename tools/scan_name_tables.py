# -*- coding: utf-8 -*-
"""아이템·기술 **이름표를 구조로 훑어** 약칭·미번역·대사 불일치를 찾는다.

★★이름 필드는 «원문 길이»가 아니라 **고정 크기**다 — 그동안 원문 길이를 예산으로
  삼는 바람에 「공작석」처럼 억지로 줄인 이름이 생겼다. 실측 구조:

    아이템표  `/1_RIG2.BIN` 0x91E00~0x93000  스트라이드 40B  이름 필드 22B
    기술표    `/1_RIG2.BIN` 0x8F000~0x92000  스트라이드 36B  이름 필드 15B

  ⛔이름 뒤 NUL 은 «필드 패딩»이지 자유 공간이 아니다. 필드를 넘기면 다음
    필드(수치)를 덮어써 아이템이 망가진다.
"""
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

JP = re.compile(r'[぀-ヿ一-鿿ｦ-ﾟ]')
TABLES = [
    ('아이템', 0x91E00, 0x93000, 40, 22, 0x92CE8),   # 앵커 = マラカイト
    ('기술',   0x8F000, 0x92000, 36, 15, 0x90370),   # 앵커 = ｽﾙｰﾀﾞｲﾌﾞ
]


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def main():
    rows = {r[0]: r for r in load_list()}
    _, lba, sz, _ = rows['/1_RIG2.BIN']
    d = Iso(TRACK1).read(lba, sz)

    ko = {}
    with io.open(os.path.join(WORK, 'trans', 'ui_strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 8:
                ko[unesc(a[6])] = unesc(a[7])

    for name, lo, hi, stride, fld, anchor in TABLES:
        base = anchor - ((anchor - lo) // stride) * stride
        tot = miss = short = 0
        rep = []
        off = base
        while off < hi:
            raw = d[off:off + fld]
            nul = raw.find(b'\x00')
            if nul > 0:
                try:
                    t = raw[:nul].decode('cp932')
                except UnicodeDecodeError:
                    t = None
                if t and JP.search(t) and all(ord(c) >= 0x20 for c in t):
                    tot += 1
                    k = ko.get(t)
                    if k is None:
                        miss += 1
                        rep.append(('미번역', off, nul, t, ''))
                    elif size(k) < nul:
                        # 원문보다 짧다 = 약칭일 가능성. 필드 여유를 함께 본다
                        short += 1
                        rep.append(('약칭?', off, nul, t, k))
            off += stride
        print('== %s표: 이름 %d개 / 미번역 %d / 원문보다 짧은 번역 %d (필드 %dB)'
              % (name, tot, miss, short, fld))
        for kind, off, n, t, k in rep[:40]:
            print('   %-5s 0x%06X %2dB %-14r -> %r' % (kind, off, n, t, k))


if __name__ == '__main__':
    main()

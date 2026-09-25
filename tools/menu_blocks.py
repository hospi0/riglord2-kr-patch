# -*- coding: utf-8 -*-
"""`.MAP` 안의 **선택상자 목록 블록** 전수 열거.

실기 제보: 술집에서 「話を聞く / 家をでる」 두 항목이어야 하는데 한글판은
「듣기」 하나만 뜨고 B 버튼으로 못 나가 대화가 무한히 이어졌다.

구조 (실측, `/ZM01.MAP` 0x22BE8~)
    `sakaba_c.p\\x00`  배경 파일명 = 블록 시작 앵커
    `酒場\\x00`         장소 이름표
    `話を聞く\\x00`     ┐
    `もう一度聞く\\x00`  ├ 선택 항목
    `家をでる\\x00`     ┘
    `\\x00`            ← **빈 항목 = 목록 끝**

★★그래서 이 블록 안에서는 «번역이 원문보다 짧을 때 NUL 로 채우면» 그 자리에
  `\\x00\\x00` 이 생겨 목록이 조기 종료된다. 1바이트만 짧아도 잘린다.
  UI 표(`text 00 FF`)에서 이미 같은 사고가 있었고 거기선 공백 패딩으로 해결했다.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

FNAME = re.compile(rb'[a-z0-9_]{3,20}\.p[a-z]{0,3}\x00')
EXTS = ('.MAP', '.MSG', '.MAT')


def blocks_of(d):
    """-> [[(off, nbytes, text), ...]]  블록 하나 = 이름표+선택항목 목록."""
    out = []
    for m in FNAME.finditer(d):
        i = m.end()
        items = []
        while i < len(d):
            j = d.find(b'\x00', i)
            if j < 0 or j == i:            # 빈 항목 = 목록 끝
                break
            raw = d[i:j]
            # ★블록의 진짜 끝은 «빈 항목»뿐이다. 길이 상한이나 제어문자로 끊으면
            #   뒤쪽 항목이 공백패딩 대상에서 빠져 거기서 목록이 잘린다
            #   (실기: 도구점·무기점 대화가 3개만 나오고 끊겼다).
            #   상점 대화 줄은 `\n` 을 포함하므로 개행은 허용해야 한다.
            if len(raw) > 400:
                break
            try:
                t = raw.decode('cp932')
            except UnicodeDecodeError:
                break
            if any(ord(c) < 0x20 and c not in '\r\n' for c in t):
                break
            items.append((i, len(raw), t))
            i = j + 1
        if len(items) >= 2:
            out.append(items)
    return out


def scan():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)
    out = []
    for path, lba, size, oob in sorted(rows):
        if os.path.splitext(path)[1].upper() not in EXTS:
            continue
        d = iso.read(lba, size)
        for items in blocks_of(d):
            out.append((path, items))
    return out


_SLOTS = None


def slot_set():
    """-> {(파일경로, 오프셋)} — 공백 패딩을 써야 하는 자리.

    `build_kr.patch_plain` 이 이 집합으로 패딩 문자를 바꾼다.
    """
    global _SLOTS
    if _SLOTS is None:
        _SLOTS = {(path, off)
                  for path, items in scan()
                  for off, n, t in items}
    return _SLOTS


def main():
    import hashlib
    ko = {}
    with io.open(os.path.join(WORK, 'trans', 'ko_shrunk.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 2:
                ko[a[0]] = a[1]

    blks = scan()
    slots = sum(len(x[1]) for x in blks)
    print('선택상자 블록 %d개 / 슬롯 %d개' % (len(blks), slots))

    # 번역된 슬롯 중 «짧아진» 것 = 목록을 자르는 것
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    cache = {}
    broken = []
    untrans = []
    for path, items in blks:
        if path not in cache:
            _, lba, size, _ = rows[path]
            cache[path] = iso.read(lba, size)
        d = cache[path]
        for off, n, t in items:
            key = hashlib.sha1(d[off:off + n]).hexdigest()[:10]
            if key in ko:
                broken.append((path, off, n, t, ko[key]))
            else:
                untrans.append((path, off, n, t))
    print('  번역된 슬롯 %d개 (짧아지면 전부 목록을 자른다)' % len(broken))
    print('  미번역 슬롯 %d개' % len(untrans))
    import collections
    c = collections.Counter(t for _, _, _, t in untrans)
    print('  미번역 내용 상위:')
    for t, k in c.most_common(15):
        print('    %-12r %d곳' % (t, k))


if __name__ == '__main__':
    main()

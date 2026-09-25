# -*- coding: utf-8 -*-
"""세이브 화면의 **장소 이름표**(`/R2MDATA.OVL`) 중 미등재분을 등록·번역한다.

실기 제보: 세이브 데이터에 `リグロードワールドマップ` 가 일본어로 남아 있었다.

★누락 원인 — 이 표의 항목은 «지역명 + 세부위치»를 **TAB(0x09)** 으로 잇는다
  (`リグロード\\tワールドマップ`). 다른 항목은 반각 공백이라 정상 추출됐는데
  TAB 짜리만 «제어문자» 필터에 걸려 통째로 빠졌다.
  ⛔TSV 에 그대로 쓰면 열 구분자와 충돌하니 반드시 `esc()` 로 `\\t` 로 적을 것.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

FILE = '/R2MDATA.OVL'

# 예산 = 원문 바이트. 한글 1자=2B, TAB·반각 1B, 전각 기호 2B.
TRANS = {
    '星陵郭\tボスルーム': '세이료카쿠\t보스룸',            # 17B
    'イシスのピラミッド\tボスルーム': '이시스의 피라미드\t보스룸',  # 29B
    'リグロード\tワールドマップ': '리그로드\t월드맵',          # 25B
    # ⛔「시련의 미궁」(11B)은 17B 슬롯에 `\tＢ１Ｆ`(7B)까지 넣으면 1B 초과다.
    #   공백 하나를 뺀 「시련의미궁」으로 맞춘다.
    '試練の迷宮\tＢ１Ｆ': '시련의미궁\tＢ１Ｆ',
    '試練の迷宮\tＢ２Ｆ': '시련의미궁\tＢ２Ｆ',
    '試練の迷宮\tＢ３Ｆ': '시련의미궁\tＢ３Ｆ',
    '試練の迷宮\tＢ４Ｆ': '시련의미궁\tＢ４Ｆ',
}


def esc(s):
    return (s.replace('\\', '\\\\').replace('\r', '\\r')
             .replace('\n', '\\n').replace('\t', '\\t'))


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def main(write):
    rows = {r[0]: r for r in load_list()}
    _, lba, sz, _ = rows[FILE]
    d = Iso(TRACK1).read(lba, sz)

    found = {}
    for jp, ko in TRANS.items():
        raw = jp.encode('cp932')
        i = d.find(raw)
        offs = []
        while i >= 0:
            offs.append(i)
            i = d.find(raw, i + 1)
        if not offs:
            print('★원문을 못 찾음: %r' % jp)
            return
        found[jp] = (offs, raw, ko)

    bad = [(jp, ko, size(ko), len(raw))
           for jp, (offs, raw, ko) in found.items() if size(ko) > len(raw)]
    if bad:
        print('★예산 초과 — 아무것도 쓰지 않았다:')
        for jp, ko, a, b in bad:
            print('   %r -> %r  %dB > %dB' % (jp, ko, a, b))
        return

    have = set()
    with io.open(os.path.join(WORK, 'trans', 'ui_strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            have.add(line.split('\t', 1)[0])

    s_rows, r_rows = [], []
    for jp, (offs, raw, ko) in sorted(found.items()):
        k = hashlib.sha1(raw).hexdigest()[:10]
        if k in have:
            continue
        s_rows.append('%s\t%d\t%d\t%d\t\t0\t%s\t%s'
                      % (k, len(offs), len(raw), len(jp), esc(jp), esc(ko)))
        for o in offs:
            r_rows.append('%s\t%s\t%d\t%d' % (k, FILE, o, len(raw)))
        print('  %-28r -> %-22r %2dB/%2dB  %d곳'
              % (jp, ko, size(ko), len(raw), len(offs)))

    print('추가 예정: ui_strings %d / ui_refs %d' % (len(s_rows), len(r_rows)))
    if not write:
        print('[미리보기 — --write 로 기록]')
        return
    T = lambda n: os.path.join(WORK, 'trans', n)
    for name, lines in (('ui_strings.tsv', s_rows), ('ui_refs.tsv', r_rows)):
        with io.open(T(name), 'a', encoding='utf-8', newline='') as f:
            for l in lines:
                f.write(l + '\n')
    print('기록 완료')


if __name__ == '__main__':
    main('--write' in sys.argv)

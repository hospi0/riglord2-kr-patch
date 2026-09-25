# -*- coding: utf-8 -*-
"""**아이템 이름을 UI 표와 대사에서 하나로 통일**한다.

실기 제보: 소지품에는 「마나이슬」인데 대사는 「【마나의 물방울】」이었다.

★★핵심 발견 — 아이템 표(`/1_RIG2.BIN` 0x92B58~, **스트라이드 40B**)의
  **이름 필드는 22바이트**다(0x16 부터 수치 데이터). 그동안 예산으로 쓰던
  «원문 문자열 길이»는 실제 한계가 아니라 그냥 원문이 짧았을 뿐이다.
  덕분에 「공작석」 같은 **약칭을 쓸 필요가 없다** — 대사와 같은 온전한 이름이 들어간다.
  ⛔단, 이름 뒤 NUL 은 «필드 패딩»이지 자유 공간이 아니다. 22B 를 넘기면
    다음 필드(수치)를 덮어써 아이템이 망가진다.

  예외: `マナのしずく`(0x91EB8)는 뒤 NUL 이 3개뿐인 **다른 표**에 있어 14B 가 한계다.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

# (원문, 통일할 이름) — 대사·UI 양쪽에 같은 이름을 쓴다.
UNIFY = {
    'マナのしずく': '마나의물방울',
    'マラカイト': '말라카이트',
    '八坂の勾玉': '야사카의 곡옥',
    '蓬莱の珠': '호라이의 구슬',
    '天邪の鏡': '아마츠의 거울',
    '荒魂の宝剣': '아라미타마의 보검',
    '真実の指輪': '진실의 반지',
    '古代のカギ': '고대의 열쇠',
    'マナの結晶': '마나의 결정',
    'マナの水': '마나의 물',
    'ユーカリ': '유카리',
    # ★소지품에 실제로 뜨는 건 이 **반각 항목**이다(`{}`는 후리가나 마크업).
    #   전각 항목만 고치면 화면은 그대로라 갈린 채로 남는다. 필드 16B.
    'ﾏﾅ{ﾉｼｽﾞｸ}': '마나의물방울',
}

# 대사 쪽에서 바꿔야 할 표기(현재 → 통일). 아이템 대괄호 안팎 모두.
DLG = [
    ('마나의 물방울', '마나의물방울'),
    ('공작석', '말라카이트'),
    ('유칼립투', '유카리'),
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


def esc(s):
    return (s.replace('\\', '\\\\').replace('\r', '\\r')
             .replace('\n', '\\n').replace('\t', '\\t'))


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def field_room(d, off, n):
    """이름 뒤 NUL 을 포함한 **필드 전체 크기**. 마지막 NUL 하나는 종단자로 남긴다."""
    z = 0
    while off + n + z < len(d) and d[off + n + z] == 0:
        z += 1
    return n + z - 1


def main(write):
    rows = {r[0]: r for r in load_list()}
    _, lba, sz, _ = rows['/1_RIG2.BIN']
    d = Iso(TRACK1).read(lba, sz)

    T = lambda x: os.path.join(WORK, 'trans', x)
    ui = []
    with io.open(T('ui_strings.tsv'), encoding='utf-8') as f:
        head = next(f)
        for line in f:
            ui.append(line.rstrip('\n').split('\t'))

    plan, bad = [], []
    for a in ui:
        if len(a) < 8:
            continue
        jp = unesc(a[6])
        if jp not in UNIFY:
            continue
        ko = UNIFY[jp]
        raw = jp.encode('cp932')
        off = d.find(raw)
        room = field_room(d, off, len(raw)) if off >= 0 else int(a[2])
        if size(ko) > room:
            bad.append((jp, ko, size(ko), room))
            continue
        plan.append((a, jp, ko, room, off, len(raw)))

    print('아이템 이름 %d개' % len(plan))
    for a, jp, ko, room, off, n in plan:
        print('  %-12r 필드%2dB  %r -> %r (%dB)'
              % (jp, room, unesc(a[7]), ko, size(ko)))
    if bad:
        print('★필드 초과 — 아무것도 쓰지 않았다:')
        for jp, ko, s, r in bad:
            print('   %r -> %r  %dB > %dB' % (jp, ko, s, r))
        return
    if not write:
        print('[미리보기 — --write 로 기록]')
        return

    # 1) ui_strings 의 ko 와 bytes(=쓸 수 있는 길이) 갱신
    upd = {a[0]: (str(room), esc(ko)) for a, jp, ko, room, off, n in plan}
    lines = [head.rstrip('\n')]
    for a in ui:
        if a[0] in upd:
            a = list(a)
            a[2], a[7] = upd[a[0]]
        lines.append('\t'.join(a))
    io.open(T('ui_strings.tsv'), 'w', encoding='utf-8', newline='').write(
        '\n'.join(lines) + '\n')

    # 2) ui_refs 의 bytes 도 같이 늘려야 build 가 긴 이름을 허용한다
    rl = io.open(T('ui_refs.tsv'), encoding='utf-8').read().split('\n')
    out = [rl[0]]
    for l in rl[1:]:
        b = l.split('\t')
        if len(b) >= 4 and b[0] in upd:
            b[3] = upd[b[0]][0]
            l = '\t'.join(b)
        if l:
            out.append(l)
    io.open(T('ui_refs.tsv'), 'w', encoding='utf-8', newline='').write(
        '\n'.join(out) + '\n')

    # 3) 대사 표기 통일
    nch = 0
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        s = io.open(T(fn), encoding='utf-8').read()
        for a, b in DLG:
            nch += s.count(a)
            s = s.replace(a, b)
        io.open(T(fn), 'w', encoding='utf-8', newline='').write(s)
    print('기록 완료 (대사 표기 %d곳 치환)' % nch)


if __name__ == '__main__':
    main('--write' in sys.argv)

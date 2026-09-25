# -*- coding: utf-8 -*-
"""**아이템·기술 이름이 UI 표와 대사에서 갈렸는지** 전수 대조.

실기 제보: 소지품에는 「마나이슬」인데 대사는 「【마나의 물방울】」이었다.
같은 물건을 두 이름으로 부르면 플레이어가 못 알아본다.

방법 — UI 표의 원문 이름(`マナのしずく` 등)이 **대사 원문에 들어 있는 행**을 찾아,
그 대사의 번역이 **UI 표의 번역어를 그대로 쓰고 있는지** 본다.
⛔번역문끼리 비교하면 안 된다(무엇이 정답인지 모름) — **원문을 기준으로 짝을 짓는다.**
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

MARK = re.compile(r'[{}｛｝]')          # 반각 이름표의 마크업 제거용


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)


def load(fn, jpcol, kocol):
    out = {}
    with io.open(os.path.join(WORK, 'trans', fn), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) > max(jpcol, kocol) and a[kocol].strip():
                out[a[0]] = (unesc(a[jpcol]), unesc(a[kocol]))
    return out


def main():
    ui = load('ui_strings.tsv', 6, 7)
    jp_dlg = {}
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 6:
                jp_dlg[a[0]] = unesc(a[5])
    ko_dlg = {}
    with io.open(os.path.join(WORK, 'trans', 'ko_final.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 2 and a[1].strip():
                ko_dlg[a[0]] = unesc(a[1])

    # UI 이름 중 «고유명사처럼 생긴 것»만 — 3자 이상, 조사·서술이 없는 짧은 표기
    names = []
    for k, (jp, ko) in ui.items():
        j = MARK.sub('', jp)
        if 3 <= len(j) <= 12 and '\n' not in j and not re.search(r'[。、！？]', j):
            names.append((j, MARK.sub('', ko), k))

    bad = []
    for jp, ko, k in names:
        for dk, dj in jp_dlg.items():
            if jp not in dj or dk not in ko_dlg:
                continue
            if ko not in ko_dlg[dk]:
                bad.append((jp, ko, dk, ko_dlg[dk]))

    print('UI 이름 후보 %d개 / 대사와 표기가 갈린 자리 %d곳' % (len(names), len(bad)))
    seen = set()
    for jp, ko, dk, dko in bad:
        if (jp, ko) in seen:
            continue
        seen.add((jp, ko))
        n = sum(1 for x in bad if (x[0], x[1]) == (jp, ko))
        print('  %-14r UI=%-12r %d곳  예) %s %r' % (jp, ko, n, dk, dko[:56]))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""줄 단위 폭 검사 — 전체 예산은 맞아도 **한 줄**이 원문 그 줄보다 넓으면
게임 렌더러가 줄 중간에서 자동으로 다음 화면으로 넘겨버린다.

실기 제보: 「갈자드, 우리는... 라그로스를 거느리고 리그로드를」 까지만
나오고 「함락시키라고」가 딴 화면으로 밀려나 반짝하고 바로 넘어감.
원인 — JP 4번째 줄 `ラグロスを従えリグロードをおとせ、と。`(19자=38B) 인데
KO 4번째 줄 `라그로스를 거느리고 리그로드를 함락시키라고`(43B, 낱말 사이
반각 공백 3개가 더해짐)가 **그 줄만** 더 넓었다. 전체 문자열 총 바이트는
budget(107B) 안에 들어서 `shrink_ko.py`가 못 잡았다 — **총량 검사와 줄 단위
검사는 다른 제약**([[feedback_box_fit_two_conditions]]).

★반각 스페이스는 6px(전각의 절반)이므로 **바이트 수 = 시각 폭**의 근사치가
  거의 정확히 맞는다(전각 2B=12px, 반각 1B=6px, 둘 다 「6px 단위」로 나눠떨어짐).
  그래서 **줄마다 KO 바이트 ≤ JP 바이트** 인지만 확인하면 된다.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

TOKEN = re.compile(r'%[A-Za-z][0-9]*')


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def line_bytes(line):
    """★«글자 수». 바이트가 아니다 — 반각 공백도 한 칸을 차지한다(실측).
    수동 개행 대사의 한 줄 한계는 **20글자**."""
    return len(TOKEN.sub('', line))


def main():
    jp = {}
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            jp[a[0]] = unesc(a[5])

    ko = {}
    with io.open(os.path.join(WORK, 'trans', 'ko_shrunk.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 2 and a[1]:
                ko[a[0]] = unesc(a[1])

    bad = []
    for k, kt in ko.items():
        if k not in jp:
            continue
        jt = jp[k]
        jl = jt.split('\n')
        kl = kt.split('\n')
        # ★줄 수가 «줄어든» 것은 재조판(rewrap) 의 정상 결과 — 상자에 더
        #   여유가 생길 뿐이라 안전하다. «늘어난» 것만 문제다.
        if len(kl) > len(jl):
            bad.append((k, -1, 0, 0, '줄 수 늘어남(%d > %d)' % (len(kl), len(jl))))
            continue
        # ★대응하는 줄끼리만 비교하면 JP 쪽이 원래 짧았던 줄에서 오탐이 난다.
        #   그 문자열 안에서 **가장 긴 JP 줄**을 실제 창 폭 상한의 근사치로 쓴다
        #   (박스마다 폭이 다를 수 있지만, 같은 문자열의 4줄은 같은 박스다).
        # ★상한은 창의 실제 폭(20글자, 실측). jp_max > 20 인 것은 렌더러가
        #   자동 줄바꿈하는 일기·책 문장이라 줄 폭 제약이 없다.
        if max(line_bytes(x) for x in jl) > 20:
            continue
        cap = 20
        for i, kline in enumerate(kl):
            kb = line_bytes(kline)
            if kb > cap:
                bad.append((k, i, kb, cap, ''))

    bad.sort(key=lambda x: -(x[2] - x[3]) if x[1] >= 0 else 0)
    print('줄 단위 폭 초과 %d건' % len(bad))
    for k, i, kb, jb, why in bad[:60]:
        if i < 0:
            print('  %s  %s' % (k, why))
        else:
            print('  %s  줄%d  KO %dB > JP %dB (+%d)  %r'
                  % (k, i, kb, jb, kb - jb, ko[k].split(chr(10))[i][:40]))
    return bad


if __name__ == '__main__':
    main()

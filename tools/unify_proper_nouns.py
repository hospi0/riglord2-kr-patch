# -*- coding: utf-8 -*-
"""인명·지명 표기 흔들림을 **다수 표기로** 통일한다.

세션4 병합 때 넣은 용어 규칙은 «새로 병합한 행»에만 걸렸다. 그 이전부터 있던
행에는 옛 표기가 남아 `check_name_variants.py` 로 11종이 드러났다.

⛔`ドラグーン` 계열(드래군/드라군/드래곤)은 손대지 않는다 — **드라군(기병)과
  드래곤(용)은 완전히 별개**라 기계 치환하면 뜻이 망가진다(사용자 지시).
★치환으로 **길어지는 것**(아로스톤·화살돌 → 애로우스톤)은 행마다 예산을 다시
  확인하고, 넘치면 그 행은 건너뛰고 목록에 남긴다.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

# (틀린 표기, 통일 표기) — 긴 것부터 적용
RULES = [
    ('카카르크란', '카칼클랜'),
    ('애로스톤', '애로우스톤'),
    ('아로스톤', '애로우스톤'),
    ('마라카이트', '말라카이트'),
    ('칠인위원회', '７인위원회'),
    ('화살돌', '애로우스톤'),
    ('디아느', '디아네'),
    ('카다르', '카달'),
    ('자루마', '자르마'),
    ('아츄카', '아스카'),
    ('라스티', '러스티'),
    ('안주', '앙주'),
    ('고조', '고죠'),
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


def apply(t):
    for a, b in RULES:
        t = t.replace(a, b)
    return t


def main(write):
    T = lambda x: os.path.join(WORK, 'trans', x)
    budget = {}
    with io.open(T('strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 3:
                budget[a[0]] = int(a[2])

    ubudget = {}
    with io.open(T('ui_strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 3:
                ubudget[a[0]] = int(a[2])

    total, over = 0, []
    plans = {}
    for fn, kocol, bud in (('ko_final.tsv', 1, budget), ('ko_shrunk.tsv', 1, budget),
                           ('ui_strings.tsv', 7, ubudget)):
        lines = io.open(T(fn), encoding='utf-8').read().split('\n')
        out = [lines[0]]
        for l in lines[1:]:
            if not l.strip():
                continue
            a = l.split('\t')
            if len(a) > kocol and a[kocol].strip():
                old = unesc(a[kocol])
                new = apply(old)
                if new != old:
                    b = bud.get(a[0])
                    if b is not None and size(new) > b:
                        over.append((fn, a[0], size(new), b, new[:40]))
                    else:
                        total += 1
                        a = list(a)
                        a[kocol] = a[kocol].replace('\\', '\x00')  # 자리표시
                        a[kocol] = (new.replace('\\', '\\\\').replace('\n', '\\n')
                                       .replace('\r', '\\r').replace('\t', '\\t'))
                        l = '\t'.join(a)
            out.append(l)
        plans[fn] = out

    print('표기 통일 대상 %d행 / 예산 초과로 보류 %d행' % (total, len(over)))
    for fn, k, s, b, t in over:
        print('   %s %s  %dB > %dB  %r' % (fn, k, s, b, t))
    if not write:
        print('[미리보기 — --write 로 기록]')
        return
    for fn, out in plans.items():
        io.open(T(fn), 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
    print('기록 완료')


if __name__ == '__main__':
    main('--write' in sys.argv)

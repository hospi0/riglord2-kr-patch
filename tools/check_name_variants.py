# -*- coding: utf-8 -*-
"""**인명·지명 표기 흔들림**을 찾는다 — 같은 이름이 두 철자로 쓰인 자리.

방법: 원문에 가타카나(외래 고유명사)가 있는 행만 골라 그 번역문에서 한글 낱말을
모으고, **편집거리 1**인 짝을 묶는다. 「라스티/러스티」, 「디아느/디아네」처럼
한 글자만 다른 흔들림이 이 방식으로 잡힌다.

⛔번역문 전체를 대상으로 하면 평범한 낱말(있다/없다…)이 잔뜩 걸린다 —
  **가타카나가 든 행으로 한정**하는 게 핵심 필터다.
"""
import collections
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

KATA = re.compile(r'[ァ-ヺー]{3,}')
HANG = re.compile(r'[가-힣]{3,8}')
# 조사·어미가 붙은 형태를 잘라내기 위한 꼬리 목록(긴 것부터)
TAIL = ('에게서', '으로는', '이라는', '에서는', '한테는', '이라고', '라고', '에게',
        '한테', '으로', '에서', '까지', '부터', '와는', '과는', '이랑', '이나',
        '들의', '들이', '들을', '들은', '님의', '님이', '님을', '님은', '님께',
        '의', '이', '가', '을', '를', '은', '는', '도', '만', '과', '와', '로', '에')


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)


def stem(w):
    for t in TAIL:
        if len(w) - len(t) >= 2 and w.endswith(t):
            return w[:-len(t)]
    return w


def dist1(a, b):
    """편집거리가 정확히 1인가 (치환/삽입/삭제)."""
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


def main():
    jp = {}
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 6:
                jp[a[0]] = unesc(a[5])

    cnt = collections.Counter()
    with io.open(os.path.join(WORK, 'trans', 'ko_final.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) < 2 or not a[1].strip():
                continue
            if a[0] not in jp or not KATA.search(jp[a[0]]):
                continue
            for w in HANG.findall(unesc(a[1])):
                cnt[stem(w)] += 1

    words = [w for w, n in cnt.items() if n >= 1]
    words.sort()
    seen, pairs = set(), []
    for i, a in enumerate(words):
        for b in words[i + 1:]:
            if abs(len(a) - len(b)) > 1:
                continue
            if dist1(a, b) and (a, b) not in seen:
                seen.add((a, b))
                pairs.append((cnt[a] + cnt[b], a, cnt[a], b, cnt[b]))
    pairs.sort(reverse=True)

    print('가타카나 포함 행에서 뽑은 낱말 %d종 / 한 글자 차이 짝 %d개' % (len(words), len(pairs)))
    print('%-12s %5s   %-12s %5s' % ('표기A', '횟수', '표기B', '횟수'))
    for tot, a, na, b, nb in pairs:
        if min(na, nb) * 6 < max(na, nb) or min(na, nb) <= 3:
            mark = '★'          # 한쪽이 압도적 = 오타일 가능성이 높다
        else:
            mark = ' '
        print('%s%-12s %5d   %-12s %5d' % (mark, a, na, b, nb))


if __name__ == '__main__':
    main()

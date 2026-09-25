# -*- coding: utf-8 -*-
"""스토리 대사 회수 스크립트 공통 — `trans_story_*.py` 의 TRANS 를
`ko_final.tsv`/`ko_shrunk.tsv` 에 병합한다.

각 `trans_story_*.py` 는 `TRANS = {key: ko 또는 None}` 딕셔너리만 갖는다.
`None` = 노이즈(그래픽 우연 일치) — 번역 대상에서 뺀다.

사용: `python merge_story.py trans_story_gm00`
"""
import importlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK


def esc(s):
    """★TSV는 물리 줄 1개 = 레코드 1개(`load_ko()`가 `for line in f`로 읽는다).
    실개행을 그대로 쓰면 둘째 줄부터 잘려나간다 — 반드시 이스케이프."""
    return (s.replace('\\', '\\\\').replace('\n', '\\n')
             .replace('\r', '\\r').replace('\t', '\\t'))


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def main(modname):
    mod = importlib.import_module(modname)
    TRANS = mod.TRANS

    jp = {}
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 6:
                jp[a[0]] = int(a[2])

    have = set()
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        with io.open(os.path.join(WORK, 'trans', fn), encoding='utf-8') as f:
            next(f)
            for line in f:
                have.add(line.split('\t', 1)[0])

    missing_jp = [k for k in TRANS if k not in jp]
    if missing_jp:
        sys.exit('★strings.tsv 에 없는 key: %s' % missing_jp)

    over = []
    new_rows = []
    dup = 0
    for k, ko in TRANS.items():
        if ko is None:
            continue
        if k in have:
            dup += 1
            continue
        n = size(ko)
        budget = jp[k]
        if n > budget:
            over.append((k, n, budget, ko))
            continue
        new_rows.append((k, ko))

    if over:
        print('★예산 초과 %d건:' % len(over))
        for k, n, budget, ko in over:
            print('   %s  %d > %d B  %r' % (k, n, budget, ko[:40]))
        sys.exit(1)

    if dup:
        print('이미 있는 key %d개 — 건너뜀' % dup)

    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        p = os.path.join(WORK, 'trans', fn)
        with io.open(p, 'a', encoding='utf-8', newline='') as f:
            for k, ko in new_rows:
                f.write('%s\t%s\n' % (k, esc(ko)))

    total_noise = sum(1 for v in TRANS.values() if v is None)
    print('%s: 번역 %d개 추가 (노이즈 제외 %d개, 예산 초과 0)'
          % (modname, len(new_rows), total_noise))


if __name__ == '__main__':
    main(sys.argv[1])

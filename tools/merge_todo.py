# -*- coding: utf-8 -*-
"""`my files/transtodo/todo_*.tsv` 에 채워 넣은 번역을 `ko_final.tsv`/
`ko_shrunk.tsv` 에 병합한다. `export_untranslated.py` 가 만든 형식
(key file bytes lines token jp ko) 전용 — ko 열이 비어 있는 행은 그냥 건너뛴다.

사용: `python merge_todo.py`            (전체 todo_*.tsv 스캔)
      `python merge_todo.py todo_03.tsv` (특정 파일만)

검사(하나라도 걸리면 **아무것도 쓰지 않고** 목록만 출력하고 종료):
  - 예산 초과 (`size(ko) > bytes`, 한글 1자=2B 규칙)
  - 원문에 있던 token(`%b` `%z` `%h` 등)이 ko 안에서 사라짐
  - `ko_final.tsv`/`ko_shrunk.tsv` 에 이미 있는 key 재번역(중복) — 건너뛰기만, 실패 아님
  - `·`(U+00B7) · `・・・`(말줄임 2자 이상) 사용 — 프로젝트 금칙([[feedback_terra... 류]])
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

TODO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'my files', 'transtodo')
TOKEN_RE = re.compile(r'%[A-Za-z][0-9]*')


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


def esc(s):
    return (s.replace('\\', '\\\\').replace('\n', '\\n')
             .replace('\r', '\\r').replace('\t', '\\t'))


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def main(names=None):
    have = set()
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        with io.open(os.path.join(WORK, 'trans', fn), encoding='utf-8') as f:
            next(f)
            for line in f:
                have.add(line.split('\t', 1)[0])

    if names:
        paths = [os.path.join(TODO_DIR, n) for n in names]
    else:
        paths = sorted(
            os.path.join(TODO_DIR, n) for n in os.listdir(TODO_DIR)
            if n.startswith('todo_') and n.endswith('.tsv'))

    rows = []       # (key, ko) 를 쓸 목록
    dup = 0
    errors = []      # (key, reason)

    for p in paths:
        with io.open(p, encoding='utf-8') as f:
            header = next(f).rstrip('\n').split('\t')
            idx = {name: i for i, name in enumerate(header)}
            for lineno, line in enumerate(f, 2):
                a = line.rstrip('\n').split('\t')
                if len(a) <= idx['ko']:
                    continue
                k = a[idx['key']]
                ko_raw = a[idx['ko']]
                if not ko_raw.strip():
                    continue  # 아직 미번역
                if k in have:
                    dup += 1
                    continue

                ko = unesc(ko_raw)
                budget = int(a[idx['bytes']])
                jp = unesc(a[idx['jp']])
                tokens = a[idx['token']].split() if a[idx['token']] else []

                n = size(ko)
                if n > budget:
                    errors.append((k, '예산 초과 %d > %d B  %r' % (n, budget, ko[:40])))
                    continue
                missing = [t for t in tokens if t not in ko]
                if missing:
                    errors.append((k, 'token 누락 %s  %r' % (missing, ko[:40])))
                    continue
                if '\u00b7' in ko:
                    errors.append((k, "'·'(U+00B7) 금지 — '・'(U+30FB) 로 바꿀 것  %r" % ko[:40]))
                    continue
                if '\u30fb\u30fb' in ko:
                    errors.append((k, "'・・・' 금지 — '・' 한 글자만  %r" % ko[:40]))
                    continue

                rows.append((k, ko))
                have.add(k)

    if errors:
        print('★%d건 문제 있음 — 아무것도 병합하지 않았다:' % len(errors))
        for k, reason in errors:
            print('  %s  %s' % (k, reason))
        sys.exit(1)

    if not rows:
        print('병합할 신규 번역 없음 (중복 건너뜀 %d개)' % dup)
        return

    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        p = os.path.join(WORK, 'trans', fn)
        with io.open(p, 'a', encoding='utf-8', newline='') as f:
            for k, ko in rows:
                f.write('%s\t%s\n' % (k, esc(ko)))

    print('병합 완료: %d개 추가 (중복 건너뜀 %d개)' % (len(rows), dup))


if __name__ == '__main__':
    main(sys.argv[1:] or None)

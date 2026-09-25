# -*- coding: utf-8 -*-
"""남은 미번역 대사를 «사람이 번역할» TSV 로 내보낸다 -> `my files/transtodo/`.

형식(물리 줄 1개 = 레코드 1개, 헤더 1줄):
    key  file  bytes  lines  token  jp  ko

  key   : 번역표 병합용 해시. **절대 수정 금지**.
  file  : 어느 .MAP 에 나오는지(장면 파악용). 여러 곳이면 `+N` 이 붙는다.
  bytes : 예산 상한. 한글 1자=2B, 그 밖은 cp932 바이트 수.
  lines : 원문 줄 수. **이 줄 수를 넘기면 안 된다**(줄당 20자 상한).
  token : 원문에 든 제어 토큰 목록(공백 구분, 참고용). 아래 규칙대로
          ko 안에도 **그대로, 원문과 같은 자리에** 살아있어야 한다.
  jp    : 원문. 개행은 리터럴 `\\n` 두 글자로 이스케이프돼 있다.
  ko    : **빈 칸** — 여기에 번역을 채운다. jp 와 같은 규칙으로 쓴다.

★`%b` `%h` `%z` `%H` `%m0` `%V100` 같은 `%글자[숫자]` 토큰은 **제어코드**다.
  원문에 있는 그대로, 있던 자리에 그대로 남겨야 한다(글자 수에 안 세어진다).
★개행은 반드시 리터럴 `\\n`(역슬래시+n). 진짜 줄바꿈을 넣으면 병합이 깨진다.
★말줄임표는 `・` **한 글자**만 쓴다(`・・・` 금지).
★`·`(U+00B7) 금지 — cp932 에 없어서 빌드가 죽는다. 가운뎃점은 `・`(U+30FB).

번역 다 채운 뒤엔 `merge_todo.py` 로 `ko_final.tsv`/`ko_shrunk.tsv` 에 병합한다.
"""
import collections
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'my files', 'transtodo')
CHUNK = 30 * 1024


def esc(s):
    return (s.replace('\\', '\\\\').replace('\n', '\\n')
             .replace('\r', '\\r').replace('\t', '\\t'))


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


def main():
    have = set()
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        with io.open(os.path.join(WORK, 'trans', fn), encoding='utf-8') as f:
            next(f)
            for line in f:
                have.add(line.split('\t', 1)[0])

    strings = {}
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 6:
                strings[a[0]] = (int(a[2]), a[4], unesc(a[5]))

    files = collections.defaultdict(set)
    first = {}
    with io.open(os.path.join(WORK, 'trans', 'refs.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            k, fn, off = a[0], a[1], int(a[2])
            if k in have or k not in strings:
                continue
            files[k].add(fn)
            if k not in first or (fn, off) < first[k]:
                first[k] = (fn, off)

    # 장면 순서대로 읽히도록 «첫 등장 파일 -> 오프셋» 정렬
    keys = sorted(files, key=lambda k: first[k])

    rows = []
    for k in keys:
        budget, tokens, jp = strings[k]
        fn, _ = first[k]
        extra = len(files[k]) - 1
        label = fn.strip('/') + ('+%d' % extra if extra else '')
        nlines = jp.count('\n') + 1
        rows.append('%s\t%s\t%d\t%d\t%s\t%s\t\n' % (k, label, budget, nlines, tokens, esc(jp)))

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for old in os.listdir(OUT):
        if old.endswith('.tsv'):
            os.remove(os.path.join(OUT, old))

    header = 'key\tfile\tbytes\tlines\ttoken\tjp\tko\n'
    parts, cur, size = [], [], 0
    for r in rows:
        b = len(r.encode('utf-8'))
        if cur and size + b > CHUNK:
            parts.append(cur)
            cur, size = [], 0
        cur.append(r)
        size += b
    if cur:
        parts.append(cur)

    log = []
    for i, part in enumerate(parts, 1):
        p = os.path.join(OUT, 'todo_%02d.tsv' % i)
        with io.open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(header)
            f.writelines(part)
        log.append('todo_%02d.tsv  %d줄  %.1fKB'
                   % (i, len(part), os.path.getsize(p) / 1024.0))

    return len(rows), len(parts), log


if __name__ == '__main__':
    n, np_, log = main()
    out = io.open(sys.argv[1], 'w', encoding='utf-8') if len(sys.argv) > 1 else sys.stdout
    out.write('미번역 %d개 -> %d개 파일\n' % (n, np_))
    for l in log:
        out.write(l + '\n')
    if len(sys.argv) > 1:
        out.close()

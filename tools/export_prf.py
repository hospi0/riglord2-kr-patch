# -*- coding: utf-8 -*-
"""`.PRF` 캐릭터 프로필 103개를 사용자 수기번역용 TSV 로 뽑는다.

출력: `my files/prftodo/prf_01~NN.tsv`   헤더 `key file bytes lines jp ko`
  bytes : 예산 상한(원문 바이트). 한글 1자=2B, 그 밖은 cp932 바이트 수.
          ★꼬리 EOF 패딩(0x1A)이 2바이트뿐이라 **넘기면 안 된다**.
  jp/ko : 개행은 리터럴 `\\n`(역슬래시+n). ⛔진짜 개행을 쓰면 레코드가 쪼개져
          병합 때 뒷줄이 통째로 유실된다(세션3 후속4에서 1,654개가 그랬다).

원문은 `声／久川綾。` 같은 성우 표기 줄로 끝나는 경우가 많다 — 그 줄도 예산에
포함되니 같이 옮기거나 지울지 판단해서 채울 것.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, REPO
from peek import load_list
import prf_corpus

OUT = os.path.join(REPO, 'my files', 'prftodo')
CHUNK = 30 * 1024


def esc(s):
    return (s.replace('\\', '\\\\').replace('\r', '\\r')
             .replace('\n', '\\n').replace('\t', '\\t'))


def main():
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    out = []
    for path, s, e, t in prf_corpus.texts():
        if t is None:
            continue
        _, lba, size, _ = rows[path]
        d = iso.read(lba, size)
        raw = d[s:e]
        k = hashlib.sha1(raw).hexdigest()[:10]
        nlines = t.count('\n') + 1
        out.append('%s\t%s\t%d\t%d\t%s\t' % (k, path.strip('/'), len(raw), nlines, esc(t)))

    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    header = 'key\tfile\tbytes\tlines\tjp\tko\n'
    parts, cur, sz = [], [], 0
    for line in out:
        b = len(line.encode('utf-8')) + 1
        if cur and sz + b > CHUNK:
            parts.append(cur)
            cur, sz = [], 0
        cur.append(line)
        sz += b
    if cur:
        parts.append(cur)

    for i, part in enumerate(parts, 1):
        p = os.path.join(OUT, 'prf_%02d.tsv' % i)
        with io.open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(header)
            for line in part:
                f.write(line + '\n')
        print('  prf_%02d.tsv  %3d행  %.1fKB' % (i, len(part), os.path.getsize(p) / 1024.0))

    tot = sum(len(l.split('\t')[4]) for l in out)
    print('프로필 %d개 / 약 %d자 -> %s' % (len(out), tot, OUT))


if __name__ == '__main__':
    main()

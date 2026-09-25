"""번역표 가역성 검증 — 추출한 TSV 를 **그대로 되넣으면 원본과 바이트가 같아야 한다**.

★변환 경계는 수정 전에 검증한다. 여기서 실패하면 추출·이스케이프·참조 어딘가가 깨진 것이라
  번역을 시작하면 안 된다.

검사
  1. `strings.tsv` 의 jp 를 언이스케이프하면 원문 문자열과 정확히 같은가
  2. `refs.tsv` 의 (파일, 오프셋, 바이트)에 그 원문이 실제로 들어 있는가
  3. cp932 재인코딩이 원본 바이트와 동일한가 (왕복 무손실)
  4. 참조가 서로 겹치지 않는가 (같은 파일 안에서 구간 중복)
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list


def unesc(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            c = s[i + 1]
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(c, c))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def main():
    tdir = os.path.join(WORK, 'trans')
    jp = {}
    with open(os.path.join(tdir, 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            jp[a[0]] = (int(a[2]), unesc(a[5]))
    refs = []
    with open(os.path.join(tdir, 'refs.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            refs.append((a[0], a[1], int(a[2]), int(a[3])))
    print('문자열 %d개 / 참조 %d건' % (len(jp), len(refs)))

    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    cache = {}
    bad_enc = bad_pos = bad_len = 0
    per_file = collections.defaultdict(list)
    for key, path, off, n in refs:
        if path not in cache:
            _, lba, size, _ = rows[path]
            cache[path] = iso.read(lba, size)
        d = cache[path]
        budget, text = jp[key]
        # 3. cp932 왕복
        try:
            enc = text.encode('cp932')
        except Exception:
            bad_enc += 1
            continue
        if len(enc) != n:
            bad_len += 1
            continue
        # 2. 그 자리에 실제로 있는가
        if d[off:off + n] != enc:
            bad_pos += 1
        per_file[path].append((off, n))

    print('cp932 재인코딩 실패 %d' % bad_enc)
    print('길이 불일치      %d' % bad_len)
    print('★위치 불일치     %d   (0 이어야 한다)' % bad_pos)

    # 4. 구간 겹침
    overlap = 0
    for path, segs in per_file.items():
        segs.sort()
        prev_end = -1
        for off, n in segs:
            if off < prev_end:
                overlap += 1
            prev_end = max(prev_end, off + n)
    print('참조 구간 겹침    %d   (0 이어야 한다)' % overlap)

    ok = (bad_enc == 0 and bad_len == 0 and bad_pos == 0 and overlap == 0)
    print('\n%s' % ('✅가역성 통과 — 번역을 시작해도 된다'
                    if ok else '★실패 — 번역 시작 금지'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

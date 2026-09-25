# -*- coding: utf-8 -*-
"""선택상자 블록 안의 «번역은 있는데 참조가 없는 자리»를 찾아 `refs.tsv` 에 채운다.

★★같은 문구가 여러 곳에 있을 때 **key 는 하나**(원문 바이트 sha1)라서, 등록
  도구가 «이미 있는 key» 로 보고 건너뛰면 **새 자리는 영원히 안 들어간다.**
  실기: `武器屋` 를 한 번 등록했는데 다른 무기점 화면은 여전히 「땠器屋」로
  깨져 나왔다([[feedback_builder_silently_drops_unmatched_rows]] 계열).

  게다가 `menu_blocks.blocks_of()` 를 나중에 넓혔기 때문에(개행 허용·길이 상한
  완화), 그 전에 등록한 이름표는 좁은 스캔 기준이었다. 넓힌 뒤 다시 훑어야 한다.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list
import menu_blocks


def main(write):
    ko = set()
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        with io.open(os.path.join(WORK, 'trans', fn), encoding='utf-8') as f:
            next(f)
            for line in f:
                a = line.rstrip('\n').split('\t')
                if len(a) >= 2 and a[1].strip():
                    ko.add(a[0])

    have = set()
    with io.open(os.path.join(WORK, 'trans', 'refs.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 3:
                have.add((a[0], a[1], int(a[2])))

    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    cache, add = {}, []
    for path, items in menu_blocks.scan():
        if path not in cache:
            _, lba, sz, _ = rows[path]
            cache[path] = iso.read(lba, sz)
        d = cache[path]
        for off, n, t in items:
            k = hashlib.sha1(d[off:off + n]).hexdigest()[:10]
            if k in ko and (k, path, off) not in have:
                add.append((k, path, off, n, t))
                have.add((k, path, off))

    print('선택상자 슬롯 중 «번역 있는데 참조 없음» %d곳' % len(add))
    import collections
    c = collections.Counter(t for _, _, _, _, t in add)
    for t, v in c.most_common(12):
        print('   %-22r %d곳' % (t, v))
    if not write:
        print('[미리보기 — --write 로 기록]')
        return
    p = os.path.join(WORK, 'trans', 'refs.tsv')
    with io.open(p, 'a', encoding='utf-8', newline='') as f:
        for k, path, off, n, t in add:
            f.write('%s\t%s\t%d\t%d\n' % (k, path, off, n))
    print('참조 %d건 추가' % len(add))


if __name__ == '__main__':
    main('--write' in sys.argv)

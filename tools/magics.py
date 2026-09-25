"""모든 파일의 머리 16바이트를 모아 컨테이너 포맷을 분류한다.

`/ITEMHELP.MSG` 가 매직 `mato` + BE u32 오프셋 표였다. 같은 컨테이너를 쓰는
파일이 더 있는지 **확장자가 아니라 매직으로** 찾는다
(확장자를 정해 놓고 훑으면 통째로 놓친다).
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list


def main():
    rows = [r for r in load_list() if not r[3] and r[2] >= 16
            and not r[0].endswith('/')]
    iso = Iso(TRACK1)
    tally = collections.Counter()
    bypath = {}
    for path, lba, size, oob in rows:
        head = iso.read(lba, 16)
        m = head[:4]
        key = m.decode('ascii') if all(32 <= b < 127 for b in m) else m.hex().upper()
        tally[key] += 1
        bypath[path] = (key, head)
    print('파일 %d개 / 매직 %d종\n' % (len(rows), len(tally)))
    print('%-12s %5s  %s' % ('매직', '개수', '예시'))
    for k, c in tally.most_common(30):
        ex = [p for p, (kk, _) in bypath.items() if kk == k][:3]
        exts = collections.Counter(os.path.splitext(p)[1].upper()
                                   for p, (kk, _) in bypath.items() if kk == k)
        print('%-12s %5d  %-46s %s' % (k, c, ','.join(ex[:2]),
                                       dict(exts.most_common(4))))
    out = os.path.join(WORK, 'magics.tsv')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('path\tmagic\thead16\n')
        for p, (k, h) in sorted(bypath.items()):
            f.write('%s\t%s\t%s\n' % (p, k, h.hex().upper()))
    print('\n저장:', out)


if __name__ == '__main__':
    main()

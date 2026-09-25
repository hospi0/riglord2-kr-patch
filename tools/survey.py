"""디스크 파일 트리 전수 열거 — 초기 조사 1단계.

★확장자를 정해 놓고 훑으면 「없는 줄 알았던」 데이터를 통째로 놓친다
  (azel 세션2 의 `.EPK` 사례). 여기서는 **전부** 센다.
★ISO 디렉터리가 오디오 트랙 영역을 가리키면 읽기가 안 끝날 수 있으므로
  트랙1 섹터 수를 넘는 extent 는 «범위 밖»으로 표시만 하고 읽지 않는다.
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK


def main():
    iso = Iso(TRACK1)
    print('Track1 %s' % os.path.basename(TRACK1))
    print('  섹터 %d개 (%.1f MB raw)' % (iso.nsec, os.path.getsize(TRACK1) / 1024 / 1024))
    files = list(iso.walk()) if hasattr(iso, 'walk') else None
    if files is None:
        print('★iso9660.Iso 에 walk() 가 없다 — 인터페이스를 확인할 것')
        print('   가진 메서드:', [m for m in dir(iso) if not m.startswith('_')])
        return
    print('  파일 %d개\n' % len(files))

    rows = []
    for path, lba, size in files:
        end = lba + (size + 2047) // 2048
        rows.append((path, lba, size, end > iso.nsec))
    rows.sort(key=lambda r: -r[2])

    ext = collections.Counter()
    tot = 0
    for path, lba, size, oob in rows:
        e = os.path.splitext(path)[1].upper() or '(없음)'
        ext[e] += 1
        tot += size
    print('-- 확장자별 --')
    for e, c in ext.most_common():
        s = sum(r[2] for r in rows if (os.path.splitext(r[0])[1].upper() or '(없음)') == e)
        print('   %-10s %4d개 %12d B' % (e, c, s))
    print('   합계 %d개 %d B (%.1f MB)' % (len(rows), tot, tot / 1024 / 1024))

    print('\n-- 큰 파일 상위 25 --')
    for path, lba, size, oob in rows[:25]:
        print('   %-40s LBA %7d %11d B%s' % (path, lba, size, '  ★트랙범위밖' if oob else ''))

    oobs = [r for r in rows if r[3]]
    if oobs:
        print('\n★트랙1 범위를 넘는 extent %d개 — 오디오 트랙을 가리킨다' % len(oobs))

    os.makedirs(WORK, exist_ok=True)
    out = os.path.join(WORK, 'filelist.tsv')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('path\tlba\tsize\toob\n')
        for path, lba, size, oob in sorted(rows, key=lambda r: r[1]):
            f.write('%s\t%d\t%d\t%d\n' % (path, lba, size, int(oob)))
    print('\n저장:', out)


if __name__ == '__main__':
    main()

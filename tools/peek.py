"""파일 하나를 꺼내 머리·꼬리를 본다. 초기 조사용.

  python tools/peek.py /RIG2.MSG        헤더 덤프
  python tools/peek.py --ext .MSG       그 확장자 전부 목록
  python tools/peek.py --dump /X.MSG    work/ 로 통째 추출
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK


def load_list():
    p = os.path.join(WORK, 'filelist.tsv')
    rows = []
    with open(p, encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            rows.append((a[0], int(a[1]), int(a[2]), a[3] == '1'))
    return rows


def read_file(iso, lba, size):
    return iso.read(lba, size)


def hexdump(d, n=256, base=0):
    for r in range(0, min(n, len(d)), 16):
        chunk = d[r:r + 16]
        hx = ' '.join('%02x' % b for b in chunk)
        asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print('    %06X  %-47s  %s' % (base + r, hx, asc))


if __name__ == '__main__':
    rows = load_list()
    args = sys.argv[1:]
    iso = Iso(TRACK1)

    if args and args[0] == '--ext':
        e = args[1].upper()
        sel = [r for r in rows if r[0].upper().endswith(e)]
        print('%s : %d개' % (e, len(sel)))
        for path, lba, size, oob in sorted(sel, key=lambda r: -r[2]):
            print('   %-44s LBA %7d %10d B%s' % (path, lba, size, ' ★범위밖' if oob else ''))
        sys.exit()

    dump = args and args[0] == '--dump'
    if dump:
        args = args[1:]
    for target in args:
        hit = [r for r in rows if r[0].upper() == target.upper()]
        if not hit:
            hit = [r for r in rows if target.upper() in r[0].upper()]
        if not hit:
            print('없음:', target)
            continue
        for path, lba, size, oob in hit[:4]:
            print('== %s  LBA %d  %d B%s' % (path, lba, size, ' ★범위밖' if oob else ''))
            if oob:
                print('   (트랙 범위 밖 — 읽지 않는다)')
                continue
            d = read_file(iso, lba, size)
            if dump:
                out = os.path.join(WORK, 'dump', path.strip('/').replace('/', '_'))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                open(out, 'wb').write(d)
                print('   ->', out)
            else:
                hexdump(d, 192)
                if size > 256:
                    print('    ...')
                    hexdump(d[-64:], 64, size - 64)

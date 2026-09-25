"""폰트 사냥 v2 — 「잉크 비율」만으로는 코드와 안 갈린다.

v1(`glyphscan.ink_profile`)은 RIG2.OVL 같은 **SH-2 코드에서도 99.9%** 가 통과했다.
검출기에 음성 대조가 없으면 이런 걸 못 잡는다
([[feedback_scan_coverage_and_detectors]]).

v2 조건 — 1bpp 셀이 **글리프**라면
  1. 셀 테두리(첫·끝 행, 첫·끝 열)에 잉크가 거의 없다  ← 글자는 칸 안에 들어간다
  2. 잉크 비율이 적당하다 (0.05~0.55)
  3. 그런 셀이 **길게 연속**된다                        ← 폰트는 표로 배열된다

음성 대조: 코드·압축 데이터는 1을 거의 못 지킨다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato, MAGIC
from project import TRACK1
from peek import load_list

POP = [bin(i).count('1') for i in range(256)]


def cell_ok(d, base, cell):
    """(글리프다운가, 잉크비율)"""
    bpr = cell // 8
    ink = 0
    border = 0
    for y in range(cell):
        row = d[base + y * bpr: base + (y + 1) * bpr]
        if len(row) < bpr:
            return False, 0
        for b in row:
            ink += POP[b]
        if y == 0 or y == cell - 1:
            for b in row:
                border += POP[b]
        else:
            border += (row[0] >> 7) & 1
            border += row[-1] & 1
    r = ink / (cell * cell)
    return (border == 0 and 0.05 <= r <= 0.55), r


def best_run(d, cell):
    """가장 긴 «연속 글리프» 구간 (길이, 시작셀)."""
    bpr = cell // 8
    cb = cell * bpr
    n = len(d) // cb
    best = cur = 0
    bstart = cstart = 0
    for i in range(n):
        ok, _ = cell_ok(d, i * cb, cell)
        if ok:
            if cur == 0:
                cstart = i
            cur += 1
            if cur > best:
                best, bstart = cur, cstart
        else:
            cur = 0
    return best, bstart, n


def scan_file(d, cells=(12, 16)):
    out = []
    for c in cells:
        run, start, n = best_run(d, c)
        out.append((c, run, start, n))
    return out


if __name__ == '__main__':
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)
    only = sys.argv[1] if len(sys.argv) > 1 else None

    # 음성 대조 = SH-2 코드
    ctrl = [r for r in rows if r[0].upper() == '/RIG2.OVL'][0]
    d = iso.read(ctrl[1], ctrl[2])
    print('[음성대조] /RIG2.OVL (SH-2 코드)')
    for c, run, start, n in scan_file(d):
        print('   셀%d: 최장연속 %d칸 / 전체 %d칸' % (c, run, n))
    print()

    cand = []
    for path, lba, size, oob in rows:
        ext = os.path.splitext(path)[1].upper()
        if ext in ('.WAV', '.ADP', '.AVI', '.BGM', '.SE', '.CD'):
            continue
        if size > 3 * 1024 * 1024 or size < 2048:
            continue
        if only and only.upper() not in path.upper():
            continue
        d = iso.read(lba, size)
        # mato 면 블록별로도 본다
        chunks = [('', d)]
        if d[:4] == MAGIC:
            try:
                m = Mato(d, path)
                if m.n <= 32:
                    chunks += [('#%d' % i, m.block(i)) for i in range(m.n)]
            except Exception:
                pass
        for tag, cd in chunks:
            if len(cd) < 4096:
                continue
            for c, run, start, n in scan_file(cd):
                if run >= 64:
                    cand.append((run, path + tag, c, start, n, len(cd)))
    cand.sort(reverse=True)
    print('연속 64칸 이상 후보 %d건 (상위 25)' % len(cand))
    print('%-8s %-30s %-5s %-8s %s' % ('연속', '파일', '셀', '시작칸', '전체칸'))
    for run, path, c, start, n, sz in cand[:25]:
        print('%-8d %-30s %-5d %-8d %d' % (run, path, c, start, n))

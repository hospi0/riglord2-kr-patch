"""1bpp 글리프 사냥 — 폰트가 어디 있는지 «그려서» 찾는다.

★새턴은 1bpp 글리프를 VDP 로 블릿하는 경우가 많아 대사 차분으로는 원리상 안 잡힌다
  ([[feedback_saturn_read_prior_projects_first]]). 추측하지 말고 그린다
  ([[feedback_font_glyph_too_small_draw_pixels]]).

  python tools/glyphscan.py /RIG2.OVL 16      16x16 1bpp 로 전체 렌더
"""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list


def write_png(path, w, h, gray):
    rows = b''.join(b'\x00' + gray[y * w:(y + 1) * w] for y in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 0, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(rows, 9))
           + chunk(b'IEND', b''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(png)
    return path


def render_1bpp(data, cell, cols=32, offset=0, maxrows=64):
    """1bpp 셀을 격자로 배치해 그레이 비트맵으로."""
    cb = cell * cell // 8                      # 셀 하나의 바이트 수
    n = (len(data) - offset) // cb
    n = min(n, cols * maxrows)
    W, H = cols * cell, ((n + cols - 1) // cols) * cell
    if H <= 0:
        return None, 0, 0, 0
    buf = bytearray(W * H)
    for i in range(n):
        gx, gy = (i % cols) * cell, (i // cols) * cell
        base = offset + i * cb
        for y in range(cell):
            rowbytes = data[base + y * (cell // 8): base + (y + 1) * (cell // 8)]
            for xb, bv in enumerate(rowbytes):
                for bit in range(8):
                    if bv & (0x80 >> bit):
                        buf[(gy + y) * W + gx + xb * 8 + bit] = 255
    return bytes(buf), W, H, n


def ink_profile(data, cell, cols=32):
    """셀별 잉크 비율 — 폰트라면 «적당히 찬» 셀이 길게 이어진다."""
    cb = cell * cell // 8
    n = (len(data)) // cb
    good = 0
    for i in range(n):
        b = data[i * cb:(i + 1) * cb]
        ink = sum(bin(x).count('1') for x in b)
        r = ink / (cell * cell)
        if 0.08 <= r <= 0.65:
            good += 1
    return good, n


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else '/RIG2.OVL'
    cell = int(sys.argv[2]) if len(sys.argv) > 2 else 16
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    hit = [p for p in rows if p.upper() == target.upper()] or \
          [p for p in rows if target.upper() in p.upper()]
    if not hit:
        sys.exit('없음: %s' % target)
    path = hit[0]
    _, lba, size, oob = rows[path]
    d = iso.read(lba, size)
    good, n = ink_profile(d, cell)
    print('%s  %d B  셀 %dx%d -> %d칸 중 «글자다운» %d칸 (%.1f%%)'
          % (path, size, cell, cell, n, good, 100 * good / max(n, 1)))
    buf, W, H, cnt = render_1bpp(d, cell)
    if buf:
        out = os.path.join(WORK, 'glyph',
                           '%s_%d.png' % (os.path.basename(path).replace('.', '_'), cell))
        print('  ->', write_png(out, W, H, buf), '(%dx%d, %d칸)' % (W, H, cnt))

# -*- coding: utf-8 -*-
"""글리프 배정 전 실측 — ①FNTC 사본이 몇 개인가 ②도너 후보가 몇 칸인가 ③재삽입 대상 refs.

★[[feedback_verify_which_asset_the_screen_uses]] — 「파일 이름으로 단정하지 말 것」.
  FNTC 가 RIG2INIT/RIG2OP 두 곳뿐이라는 건 **전 파일 mato 블록 스캔**으로 확인한다.
★[[feedback_shared_text_needs_shared_font]] — 사본이 여럿이면 **같은 배정**으로 전부 덮는다.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from fntc import Fntc
from project import TRACK1, WORK
from peek import load_list

LEAD_MIN, LEAD_MAX = 0x88, 0x9F


def find_fonts(iso, rows):
    """디스크 전체에서 FNTC 블록을 찾는다. -> [(path, lba, size, block_idx, n, w, h)]"""
    out = []
    for path, lba, size, oob in rows:
        if oob or path.endswith('/') or size < 0x100 or size > 8 << 20:
            continue
        d = iso.read(lba, size)
        if b'FNTC' not in d:
            continue
        try:
            m = Mato(d, path)
        except Exception:
            out.append((path, lba, size, -1, 0, 0, 0))
            continue
        for i, b in enumerate(m.blocks()):
            if len(b) > 12 and b[8:12] == b'FNTC':
                try:
                    f = Fntc(b)
                    out.append((path, lba, size, i, f.n, f.w, f.h))
                except Exception as e:
                    out.append((path, lba, size, i, -1, 0, 0))
    return out


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
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)

    print('=== 1. FNTC 사본 전수 스캔 (%d 파일) ===' % len(rows))
    fonts = find_fonts(iso, rows)
    for path, lba, size, bi, n, w, h in fonts:
        print('  %-20s 블록%-3s 글자%-6s %sx%s' % (path, bi, n, w, h))
    print('  총 %d개' % len(fonts))

    # 글리프 바이트가 정말 같은지 대조
    if len(fonts) >= 2:
        gs = []
        for path, lba, size, bi, n, w, h in fonts:
            if n <= 0:
                continue
            f = Fntc(Mato(iso.read(lba, size), path).block(bi))
            gs.append((path, bi, f.codes, bytes(f.data[f.glyph_off:f.glyph_off + f.n * f.cb])))
        base = gs[0]
        for g in gs[1:]:
            print('  %s vs %s : 코드표 %s / 글리프 %s'
                  % (base[0], g[0],
                     '동일' if g[2] == base[2] else '★다름',
                     '동일' if g[3] == base[3] else '★다름'))

    # === 2. 도너 후보 ===
    path, lba, size, bi = fonts[0][0], fonts[0][1], fonts[0][2], fonts[0][3]
    f = Fntc(Mato(iso.read(lba, size), path).block(bi))
    cand = [i for i in range(f.n) if LEAD_MIN <= (f.codes[i] >> 8) <= LEAD_MAX]
    print('\n=== 2. 도너 후보 (리드 0x%02X~0x%02X) ===' % (LEAD_MIN, LEAD_MAX))
    print('  전체 %d칸 중 후보 %d칸' % (f.n, len(cand)))
    from collections import Counter
    c = Counter(f.codes[i] >> 8 for i in range(f.n))
    print('  리드바이트 분포: %s' % ' '.join('%02X:%d' % (k, v) for k, v in sorted(c.items())))

    # === 3. 번역문이 «그대로 쓰는» 문자 (도너로 뺏으면 안 된다) ===
    ko = {}
    with io.open(os.path.join(WORK, 'trans', 'ko_final.tsv'), encoding='utf-8') as fh:
        next(fh)
        for line in fh:
            a = line.rstrip('\n').split('\t')
            ko[a[0]] = unesc(a[1])
    import re
    TOKEN = re.compile(r'%[A-Za-z][0-9]*')
    keep, hangul = set(), set()
    for t in ko.values():
        for ch in TOKEN.sub('', t):
            if '가' <= ch <= '힣':
                hangul.add(ch)
            elif ch not in '\n\r\t' and f.index_of(ch) is not None:
                keep.add(ch)
    print('\n=== 3. 번역문 소요 ===')
    print('  한글 음절 %d종 (도너 필요)' % len(hangul))
    print('  번역문이 그대로 쓰는 폰트 문자 %d종 -> 도너 제외: %s' % (len(keep), ''.join(sorted(keep))))
    print('  가용 도너 = %d - %d = %d칸  (필요 %d)  %s'
          % (len(cand), len([1 for ch in keep if f.index_of(ch) is not None
                             and LEAD_MIN <= (f.codes[f.index_of(ch)] >> 8) <= LEAD_MAX]),
             len(cand) - len([1 for ch in keep if f.index_of(ch) is not None
                              and LEAD_MIN <= (f.codes[f.index_of(ch)] >> 8) <= LEAD_MAX]),
             len(hangul),
             'OK' if len(cand) >= len(hangul) + len(keep) else '★모자람'))

    # === 4. 재삽입 대상 refs ===
    refs = []
    with io.open(os.path.join(WORK, 'trans', 'refs.tsv'), encoding='utf-8') as fh:
        next(fh)
        for line in fh:
            a = line.rstrip('\n').split('\t')
            if a[0] in ko:
                refs.append((a[0], a[1], int(a[2]), int(a[3])))
    files = sorted(set(r[1] for r in refs))
    print('\n=== 4. 번역된 %d개 문자열의 참조 위치 ===' % len(ko))
    print('  참조 %d건 / 파일 %d개' % (len(refs), len(files)))
    from collections import Counter as C2
    fc = C2(r[1] for r in refs)
    for fn, n in fc.most_common(20):
        print('    %-18s %d건' % (fn, n))
    if len(fc) > 20:
        print('    ... 외 %d개 파일' % (len(fc) - 20))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""UI 파일에 **남아 있는 미번역 일본어**를 전수 검출한다.

★★전면 한글화에서는 «미검출 = 화면 파손»이다. 우리가 도너로 뺏은 한자 칸을
  미번역 원문이 그대로 가리키고 있으면 그 자리에 엉뚱한 한글이 찍힌다
  (실기: `練習場`→「곡겹場」, `号数`→「온휘」, `普通`→「먼월」).
  ([[feedback_embedded_font_no_spare_slots]] 와 같은 구조)

⛔`corpus2.is_real()` 은 여기서 쓰면 안 된다 — 「가나 없이 한자 4자 미만」을
  전부 노이즈로 버린다. UI 는 `普通` `最速` `号数` `練習場` 처럼 **짧은 한자어**가
  주력이라 그 필터에 통째로 걸린다(스토리 쪽 `承知！` 와 같은 함정).

여기서는 필터를 뒤집는다 — **가나든 한자든 전각 2자 이상이면 일단 후보**로 잡고,
이미 번역표에 있는 것만 빼고 남은 것을 전부 보여 준다. 노이즈 판정은 사람이 한다.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from project import TRACK1, WORK
from peek import load_list
import ui_corpus as U

KANA = re.compile(r'[぀-ヿ]')
HAN = re.compile(r'[一-鿿]')
HALFKANA = re.compile(r'[｡-ﾟ]')


def scan(data):
    """[(off, raw, text)] — 전각 일본어(가나/한자) 2자 이상인 NUL 구분 조각."""
    out = []
    n = len(data)
    i = 0
    while i < n:
        if data[i] == 0:
            i += 1
            continue
        j = data.find(b'\x00', i)
        if j < 0:
            j = n
        raw = data[i:j]
        seg = raw.strip(b'\xff')
        off = i + (len(raw) - len(raw.lstrip(b'\xff')))
        i = j + 1
        if len(seg) < 4 or len(seg) > 400:
            continue
        t, full, gaiji = U.decode_with_gaiji(seg)
        if t is None:
            continue
        body = re.sub(r'\{G:[0-9A-F]{4}\}', '', t)
        # 전각 가나/한자 **또는 반각 가타카나**가 2자 이상 있어야 «일본어 텍스트»다.
        # ★★반각(HALFKANA)을 안 세서 `ｼｮｰﾄｿｰﾄﾞ`처럼 반각으로만 된 문자열이
        #   통째로 빠졌다 — `ui_corpus.decode_with_gaiji()`(핵심 디코더)는
        #   반각을 이미 `full` 에 세도록 고쳤는데, 이 검출기 자체의 별도
        #   필터(KANA/HAN 정규식)에는 그 수정이 반영이 안 됐었다.
        if (len(KANA.findall(body)) + len(HAN.findall(body))
                + len(HALFKANA.findall(body))) < 2:
            continue
        out.append((off, bytes(seg), t))
    return out


def main():
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)

    known = set()
    p = os.path.join(WORK, 'trans', 'ui_strings.tsv')
    if os.path.exists(p):
        with io.open(p, encoding='utf-8') as f:
            next(f)
            for line in f:
                a = line.rstrip('\n').split('\t')
                known.add(a[0])

    import hashlib
    total_new = 0
    report = []
    targets = [(fn, bi) for fn in U.OVL_FILES for bi in (0, 1)]
    for fn in U.OVL_FILES:
        _, lba, size, _ = rows[fn]
        m = Mato(iso.read(lba, size), fn)
        for bi, blk in enumerate(m.blocks()):
            for off, raw, t in scan(bytes(blk)):
                key = hashlib.sha1(raw).hexdigest()[:10]
                if key in known:
                    continue
                report.append(('%s#%d' % (fn, bi), off, key, len(raw), t))
                total_new += 1

    for fn in getattr(U, 'PLAIN_FILES', []):
        _, lba, size, _ = rows[fn]
        for off, raw, t in scan(bytes(iso.read(lba, size))):
            key = hashlib.sha1(raw).hexdigest()[:10]
            if key in known:
                continue
            report.append((fn, off, key, len(raw), t))
            total_new += 1

    _, lba, size, _ = rows[U.BIN_FILE]
    d = bytes(iso.read(lba, size))
    for off, raw, t in scan(d):
        if not (U.BIN_SAFE_LO <= off <= U.BIN_SAFE_HI):
            continue
        key = hashlib.sha1(raw).hexdigest()[:10]
        if key in known:
            continue
        report.append((U.BIN_FILE, off, key, len(raw), t))
        total_new += 1

    print('★번역표에 없는 UI 일본어 %d개' % total_new)
    # 같은 원문은 한 번만
    seen = set()
    uniq = []
    for fn, off, key, n, t in report:
        if key in seen:
            continue
        seen.add(key)
        uniq.append((fn, off, key, n, t))
    print('   (고유 %d개)' % len(uniq))
    for fn, off, key, n, t in uniq:
        half = 'H' if HALFKANA.search(t) else ' '
        print('  %s %-18s 0x%06X %3dB  %r' % (half, fn, off, n, t))
    return uniq


if __name__ == '__main__':
    main()

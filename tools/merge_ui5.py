# -*- coding: utf-8 -*-
"""`trans_ui5.TRANS`(상태창 속성·무기종류 한 글자 아이콘)를 편입한다.

`ui_missing.scan()` 의 `len(seg) < 4` 필터에 걸려 한 번도 검출 안 됐던
1~3바이트짜리 조각이라 정규 스캔을 안 쓰고, **화이트리스트 raw 바이트와
정확히 일치**하는 NUL 구분 조각만 직접 찾는다(길이 필터 없음 = 노이즈
위험이 있으므로 정확 일치로만 막는다).
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from project import TRACK1, WORK
from peek import load_list
import ui_corpus as U
import trans_ui5


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def scan_exact(data, want):
    """[(off, raw)] — `want`(raw bytes 집합)와 정확히 일치하는 NUL 구분 조각."""
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
        if seg in want:
            out.append((off, seg))
    return out


def main():
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    TRANS = trans_ui5.TRANS
    want = set(TRANS)

    new_str, new_ref, seen = [], [], set()

    def add(fnlabel, off, raw):
        jp, ko = TRANS[raw]
        key = hashlib.sha1(raw).hexdigest()[:10]
        if key not in seen:
            seen.add(key)
            new_str.append((key, len(raw), len(jp), jp, ko))
        new_ref.append((key, fnlabel, off, len(raw)))

    for fn in U.OVL_FILES:
        _, lba, size, _ = rows[fn]
        m = Mato(iso.read(lba, size), fn)
        for bi, blk in enumerate(m.blocks()):
            for off, raw in scan_exact(bytes(blk), want):
                add('%s#%d' % (fn, bi), off, raw)

    for fn in U.PLAIN_FILES:
        _, lba, size, _ = rows[fn]
        d = bytes(iso.read(lba, size))
        for off, raw in scan_exact(d, want):
            add(fn, off, raw)

    _, lba, size, _ = rows[U.BIN_FILE]
    d = bytes(iso.read(lba, size))
    for off, raw in scan_exact(d, want):
        if U.BIN_SAFE_LO <= off <= U.BIN_SAFE_HI:
            add(U.BIN_FILE, off, raw)

    sp = os.path.join(WORK, 'trans', 'ui_strings.tsv')
    rp = os.path.join(WORK, 'trans', 'ui_refs.tsv')
    have = set()
    with io.open(sp, encoding='utf-8') as f:
        next(f)
        for line in f:
            have.add(line.split('\t')[0])

    n1 = n2 = 0
    with io.open(sp, 'a', encoding='utf-8', newline='') as f:
        for key, nb, chars, jp, ko in new_str:
            if key in have:
                continue
            f.write('%s\t1\t%d\t%d\t\t0\t%s\t%s\n' % (key, nb, chars, esc(jp), esc(ko)))
            n1 += 1
    with io.open(rp, 'a', encoding='utf-8', newline='') as f:
        for key, fnlabel, off, nb in new_ref:
            if key in have:
                continue
            f.write('%s\t%s\t%d\t%d\n' % (key, fnlabel, off, nb))
            n2 += 1
    print('ui_strings.tsv +%d개 / ui_refs.tsv +%d건' % (n1, n2))
    missing = [k for k in want if hashlib.sha1(k).hexdigest()[:10] not in seen]
    if missing:
        print('★디스크에서 못 찾은 항목 %d개: %s' % (len(missing), [trans_ui5.TRANS[k] for k in missing]))


if __name__ == '__main__':
    main()

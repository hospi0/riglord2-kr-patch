# -*- coding: utf-8 -*-
"""`trans_ui2.TRANS`(짧은 한자어 UI 134개)를 UI 코퍼스에 편입한다.

`ui_corpus.export()` 는 `corpus2.is_real()` 로 거르기 때문에 이 부류를 못 잡는다.
여기서는 `ui_missing.scan()`(전각 2자 이상이면 후보) 으로 다시 훑어
`ui_strings.tsv` / `ui_refs.tsv` 에 **추가**한다.

★★`export()` 를 다시 돌리면 이 추가분이 날아간다 — 순서는
   `ui_corpus.export()` -> `trans_ui.py` -> **`merge_ui2.py`** 여야 한다.
"""
import hashlib
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
import ui_missing
import trans_ui2


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def main():
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    TRANS = trans_ui2.TRANS
    EXCLUDE = trans_ui2.EXCLUDE

    new_str, new_ref, seen = [], [], set()

    def add(fnlabel, off, raw, t):
        if t in EXCLUDE or t not in TRANS:
            return
        key = hashlib.sha1(raw).hexdigest()[:10]
        if key not in seen:
            seen.add(key)
            body = re.sub(r'\{G:[0-9A-F]{4}\}', '', t)
            new_str.append((key, len(raw), len(body), t, TRANS[t]))
        new_ref.append((key, fnlabel, off, len(raw)))

    for fn in U.OVL_FILES:
        _, lba, size, _ = rows[fn]
        m = Mato(iso.read(lba, size), fn)
        for bi, blk in enumerate(m.blocks()):
            for off, raw, t in ui_missing.scan(bytes(blk)):
                add('%s#%d' % (fn, bi), off, raw, t)

    _, lba, size, _ = rows[U.BIN_FILE]
    d = bytes(iso.read(lba, size))
    for off, raw, t in ui_missing.scan(d):
        if U.BIN_SAFE_LO <= off <= U.BIN_SAFE_HI:
            add(U.BIN_FILE, off, raw, t)

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


if __name__ == '__main__':
    main()

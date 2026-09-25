# -*- coding: utf-8 -*-
"""회수 — `is_real()` 오탐으로 통째로 빠진 짧은 한자 전용 문자열.

사용자가 실기에서 발견: 라그로스 대사가 「承참!」로 나왔다 — 파손이 아니라
**「承知！」가 애초에 추출조차 안 된 원문**이 우리 도너 글리프(知 칸)와 충돌한
것이었다. [[feedback_recovered_entries_never_translated]] 류와 같은 함정.

★★원인 = `corpus2.is_real()`: 가나가 하나도 없으면 「한자+길이4자 이상」만
  인정한다. 「承知！」「応！」같은 **가나 없는 3자 미만 한자 감탄사·지문**은
  전부 노이즈로 버려졌다.
★`is_real()` 자체는 고치지 않는다 — 완화하면 전체 155개 파일에서 노이즈
  오탐이 다시 늘어날 위험이 있다([[feedback_scan_coverage_and_detectors]]).
  대신 **구두점(！？。) 또는 ［］ 화자태그**로 감싸인 것만 별도 규칙으로
  건져 올린다 — 노이즈(그래픽 우연 일치)는 구두점이 없다(실측: 譜織 등
  265건은 전부 구두점 없음, 진짜 16건은 전부 있음).

이 스크립트는 `strings.tsv`/`refs.tsv`/`ko_final.tsv` 에 **추가**한다
(같은 포맷 유지 — export_tsv.py 결과와 완전히 같은 파이프라인을 탄다).
"""
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list
from corpus import strings, payload
from corpus2 import is_real

KANA = re.compile(r'[぀-ヿ]')
HAN = re.compile(r'[一-鿿]')
TOKEN = re.compile(r'%[A-Za-z][0-9]*')

TRANS = {
    '%H%m1%V100［%m0男%m1］%V0%m0\n': '%H%m1%V100［%m0남%m1］%V0%m0\n',
    '%H%m1%V100［%m0声%m1］%V0%m0\n': '%H%m1%V100［%m0성%m1］%V0%m0\n',
    '%H%m1%V100［%m0女%m1］%V0%m0\n': '%H%m1%V100［%m0여%m1］%V0%m0\n',
    '%z出発！': '%z출발！',
    '%z承知！': '%z존명！',
    '御意。%b': '존명。%b',
    '御意！%b': '존명！%b',
    '式神。%b': '식신。%b',
    '兄者！%b': '형님！%b',
    '笑止！%b': '가소！%b',
    '遺跡？%b': '유적？%b',
    '応！%b': '응！%b',
    '大変！%b': '큰일！%b',
    '本当？%b': '정말？%b',
    '関所？%b': '관문？%b',
    '誰！？%b': '뉘！？%b',
}


def has_punct(p):
    return any(c in p for c in '！？。') or (p.startswith('［') and p.endswith('］'))


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def find_all(iso, rows):
    """[(key, raw, t, [(file, off)])] — TRANS 에 있는 원문의 전 출현 위치."""
    want = set(TRANS)
    hits = {}
    for path, lba, size, oob in rows:
        if not path.upper().endswith(('.MAP', '.MSG', '.MAT')):
            continue
        d = iso.read(lba, size)
        for off, raw, t in strings(d):
            if t in want:
                hits.setdefault(t, []).append((path, off, raw))
    return hits


def main():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)

    hits = find_all(iso, rows)
    missing_t = set(TRANS) - set(hits)
    if missing_t:
        sys.exit('★TRANS 에 있는데 디스크에서 못 찾은 원문: %s' % missing_t)

    sp = os.path.join(WORK, 'trans', 'strings.tsv')
    rp = os.path.join(WORK, 'trans', 'refs.tsv')
    kp = os.path.join(WORK, 'trans', 'ko_final.tsv')

    existing_keys = set()
    with io.open(sp, encoding='utf-8') as f:
        next(f)
        for line in f:
            existing_keys.add(line.split('\t', 1)[0])

    new_str_rows, new_ref_rows, new_ko_rows = [], [], []
    for t, locs in hits.items():
        raw0 = locs[0][2]
        key = hashlib.sha1(raw0).hexdigest()[:10]
        if key in existing_keys:
            print('  ⚠ 이미 있는 key(건너뜀): %s %r' % (key, t))
            continue
        for _, _, raw in locs:
            if raw != raw0:
                sys.exit('★같은 t 인데 raw 바이트가 다르다: %r' % t)
        n = len(raw0)
        chars = len(payload(t))
        tokens = ' '.join(dict.fromkeys(TOKEN.findall(t)))
        new_str_rows.append('%s\t%d\t%d\t%d\t%s\t%s\t\n'
                             % (key, len(set(p for p, o, r in locs)), n, chars, tokens, esc(t)))
        for path, off, raw in sorted(locs):
            new_ref_rows.append('%s\t%s\t%d\t%d\n' % (key, path, off, n))
        ko = TRANS[t]
        enc_len = len(ko.encode('utf-8'))  # 참고용, 실제 예산검사는 build_kr 이 함
        new_ko_rows.append((key, ko, t, n))
        print('  회수: %s  %r -> %r  (원문 %dB, %d회)' % (key, t, ko, n, len(locs)))

    if not new_str_rows:
        print('추가할 신규 항목이 없다 (이미 전부 반영됨)')
        return

    with io.open(sp, 'a', encoding='utf-8', newline='') as f:
        f.writelines(new_str_rows)
    with io.open(rp, 'a', encoding='utf-8', newline='') as f:
        f.writelines(new_ref_rows)
    with io.open(kp, 'a', encoding='utf-8', newline='') as f:
        for key, ko, t, n in new_ko_rows:
            f.write('%s\t%s\n' % (key, esc(ko)))

    print('\n회수 %d개 문자열 / 참조 %d건 추가' % (len(new_str_rows), len(new_ref_rows)))
    print('  -> %s (append)' % sp)
    print('  -> %s (append)' % rp)
    print('  -> %s (append)' % kp)


if __name__ == '__main__':
    main()

"""분량 재조사 — ★중복 제거와 노이즈 배제.

1차(`corpus.py`)는 `.MAP` 256,323자를 냈지만 그건 **파일별 합계**다.
`７人委員会` 한 문자열이 12개 `.MAP` 에서 동시에 발견된 걸 보면
`GT00/GT10/GT20`, `NT00/NT20/NT21/NT30` 처럼 **같은 지역의 변형 파일이
대사를 통째로 중복 포함**한다. 번역 작업량은 **고유 문자열** 기준이어야 한다.

노이즈도 더 엄격히 건다.
  · 전각 공백(　)·기호만인 것
  · 제어 토큰(%H %m1 …)을 빼면 남는 게 없는 것
  · 가나가 하나도 없는 것 → 일본어 문장이 아니다(그래픽·좌표가 우연히 전각으로 읽힌 것)
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list
from corpus import strings, payload

KANA = re.compile(r'[぀-ヿ]')
HAN = re.compile(r'[一-鿿]')


def is_real(t):
    """진짜 일본어 문장인가."""
    p = payload(t).replace('　', '').strip()
    if len(p) < 2:
        return False
    # 가나가 하나도 없으면 문장이 아니다(고유명사만인 짧은 것은 아래서 살린다)
    if not KANA.search(p):
        return len(p) >= 4 and bool(HAN.search(p)) and len(set(p)) >= 3
    return True


def main():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)

    uniq = {}                       # payload -> (첫 파일, 등장 파일 수)
    seen_files = collections.defaultdict(set)
    per_ext_raw = collections.Counter()
    per_ext_files = collections.Counter()
    dropped = 0

    for path, lba, size, oob in rows:
        ext = os.path.splitext(path)[1].upper()
        if ext not in ('.MAP', '.MSG', '.MAT'):
            continue
        d = iso.read(lba, size)
        for _, _, t in strings(d):
            p = payload(t)
            if not is_real(t):
                dropped += 1
                continue
            per_ext_raw[ext] += len(p)
            if p not in uniq:
                uniq[p] = path
            seen_files[p].add(path)
        per_ext_files[ext] += 1

    tot_u = sum(len(p) for p in uniq)
    tot_raw = sum(per_ext_raw.values())
    print('=== 중복 제거 전/후 ===')
    print('  파일별 합계   %8d자 (%s)' % (tot_raw, dict(per_ext_raw)))
    print('  ★고유 문자열  %8d개 / **%d자**' % (len(uniq), tot_u))
    print('  노이즈로 버린 문자열 %d개' % dropped)
    if tot_raw:
        print('  중복 배수 %.1f배' % (tot_raw / max(tot_u, 1)))

    # 확장자별 고유 분량 (첫 등장 파일 기준)
    byext = collections.Counter()
    byext_n = collections.Counter()
    for p, path in uniq.items():
        e = os.path.splitext(path)[1].upper()
        byext[e] += len(p)
        byext_n[e] += 1
    print('\n-- 고유 분량(첫 등장 파일 기준) --')
    for e, c in byext.most_common():
        print('   %-6s 문자열 %6d / %8d자' % (e, byext_n[e], c))

    # 몇 개 파일에 걸쳐 나오는가
    rep = collections.Counter(len(v) for v in seen_files.values())
    print('\n-- 한 문자열이 몇 개 파일에 나오나 --')
    for k in sorted(rep)[:12]:
        print('   %2d개 파일에 등장: %d개 문자열' % (k, rep[k]))
    many = sorted(seen_files.items(), key=lambda kv: -len(kv[1]))[:5]
    print('\n-- 가장 널리 중복된 문자열 --')
    for p, fs in many:
        print('   %3d개 파일 : %s' % (len(fs), p[:40].replace('\n', ' / ')))

    # 글리프 수요
    chars = collections.Counter()
    for p in uniq:
        chars.update(p)
    jp = {c: n for c, n in chars.items() if ord(c) > 0x2000}
    kana = {c for c in jp if 0x3040 <= ord(c) <= 0x30ff}
    kanji = {c for c in jp if 0x4e00 <= ord(c) <= 0x9fff}
    print('\n고유 전각 %d자 (가나 %d / 한자 %d / 기타 %d)'
          % (len(jp), len(kana), len(kanji), len(jp) - len(kana) - len(kanji)))

    out = os.path.join(WORK, 'corpus_unique.tsv')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('chars\tfiles\tfirst\ttext\n')
        for p, path in sorted(uniq.items(), key=lambda kv: -len(kv[0])):
            f.write('%d\t%d\t%s\t%s\n' % (len(p), len(seen_files[p]), path, p.replace('\n', '\\n')))
    print('\n저장:', out)


if __name__ == '__main__':
    main()

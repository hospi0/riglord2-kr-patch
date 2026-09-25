"""한글화 분량 확정 — `.MAP` 대사를 전수 추출한다.

`.MAP` 안의 대사는 **평문 cp932 + NUL 종단 + ASCII 제어 토큰**이다(NT21.MAP 실측).
    %H  %m0 %m1  %V0 %V100  %b   / 0x0A 개행 / 0x00 종단 / ［ ］ 로 화자 이름

★모집단을 «확정 / 하한 / 추정»으로 나눈다. 여기서 확정으로 치는 건
  「NUL 종단이고 전각 일본어를 실제로 담은」 문자열뿐이다.
⛔전각 바이트가 우연히 이어진 구간(그래픽·좌표)은 세면 안 된다 — 문자열 단위로 판정한다
  ([[feedback_detector_ratio_per_string_not_per_region]]).
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

# ★`\d` 는 전각 숫자(７ ２ …)까지 먹는다. 그러면 `%m0７人委員会` 의 「７」이
#   토큰에 딸려 들어가 본문 글자가 사라진다. **ASCII 숫자만** 쓴다.
TOKEN = re.compile(r'%[A-Za-z][0-9]*')


def is_lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def is_trail(b):
    return 0x40 <= b <= 0xfc and b != 0x7f


def strings(d):
    """[(오프셋, 원시바이트, 디코드문자열)] — NUL 종단, 전각 2자 이상 포함."""
    out = []
    n = len(d)
    i = 0
    while i < n:
        if d[i] == 0:
            i += 1
            continue
        j = d.find(b'\x00', i)
        if j < 0:
            j = n
        seg = d[i:j]
        i = j + 1
        if len(seg) < 4 or len(seg) > 512:
            continue
        # 전각 문자 수를 센다
        full = 0
        k = 0
        ok = True
        while k < len(seg):
            b = seg[k]
            if is_lead(b) and k + 1 < len(seg) and is_trail(seg[k + 1]):
                full += 1
                k += 2
            elif b in (0x0a, 0x0d) or 0x20 <= b < 0x7f:
                k += 1
            else:
                ok = False
                break
        if not ok or full < 2:
            continue
        try:
            t = seg.decode('cp932')
        except Exception:
            continue
        out.append((j - len(seg), seg, t))
    return out


def payload(t):
    """제어 토큰·개행을 뺀 «번역해야 할 글자»만."""
    return TOKEN.sub('', t).replace('\n', '').replace('\r', '')


def main():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)
    byext = collections.Counter()
    byext_n = collections.Counter()
    uniq = collections.Counter()
    total_n = total_c = 0
    per_file = []
    samples = {}

    for path, lba, size, oob in rows:
        ext = os.path.splitext(path)[1].upper()
        if ext in ('.WAV', '.ADP', '.AVI', '.BGM', '.SE', '.CD', '.KEP'):
            continue
        if size > 4 * 1024 * 1024:
            continue
        d = iso.read(lba, size)
        ss = strings(d)
        if not ss:
            continue
        c = sum(len(payload(t)) for _, _, t in ss)
        if c == 0:
            continue
        byext[ext] += c
        byext_n[ext] += len(ss)
        total_n += len(ss)
        total_c += c
        per_file.append((c, len(ss), path))
        for _, _, t in ss:
            uniq.update(payload(t))
        if ext not in samples:
            samples[ext] = (path, ss[0][2][:40])

    print('=== 확정 모집단 (NUL 종단 + 전각 2자 이상) ===')
    print('%-8s %8s %10s   %s' % ('확장자', '문자열', '글자', '예시'))
    for ext, c in byext.most_common():
        p, s = samples[ext]
        print('%-8s %8d %10d   %-34s %s' % (ext, byext_n[ext], c, s.replace('\n', ' / ')[:32], p))
    print('  합계 문자열 %d / **%d자**' % (total_n, total_c))

    jp = {c: n for c, n in uniq.items() if ord(c) > 0x2000}
    kana = {c: n for c, n in jp.items() if 0x3040 <= ord(c) <= 0x30ff}
    kanji = {c: n for c, n in jp.items() if 0x4e00 <= ord(c) <= 0x9fff}
    print('\n고유 전각 %d자  (가나 %d / 한자 %d / 기타 %d)'
          % (len(jp), len(kana), len(kanji), len(jp) - len(kana) - len(kanji)))

    print('\n-- 파일별 상위 15 --')
    for c, n, p in sorted(per_file, reverse=True)[:15]:
        print('   %-26s 문자열 %4d / %6d자' % (p, n, c))

    os.makedirs(WORK, exist_ok=True)
    out = os.path.join(WORK, 'corpus_summary.tsv')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('path\tstrings\tchars\n')
        for c, n, p in sorted(per_file, reverse=True):
            f.write('%s\t%d\t%d\n' % (p, n, c))
    print('\n저장:', out)


if __name__ == '__main__':
    main()

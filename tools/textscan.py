"""초기 분량 조사 — 현지화 대상 모집단을 «확정값 / 하한 / 추정치»로 나눈다.

★후보량을 그대로 번역 작업량으로 확정하지 않는다. 여기서 내는 건
  「어디에 얼마나 있는지」의 1차 지도이고, 소비 경계가 확정된 것만 확정값이다.

`.MSG` 는 구조가 확인됐다 — 블록 안이 **BE u32 절대 오프셋 표 + NUL 종단 cp932**.
`.EVE` 등 나머지는 아직 소비 규칙을 모르므로 **cp932 스캔 하한**으로만 센다.
"""
import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato, MatoError, MAGIC
from project import TRACK1, WORK
from peek import load_list


def is_lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def is_trail(b):
    return 0x40 <= b <= 0xfc and b != 0x7f


def scan_cp932(d, minchars=2):
    """[(오프셋, 문자열)] — 전각 2바이트가 minchars 자 이상 이어지는 구간."""
    out = []
    n = len(d)
    i = 0
    while i < n - 1:
        if is_lead(d[i]) and is_trail(d[i + 1]):
            j = i
            cnt = 0
            while j < n - 1 and is_lead(d[j]) and is_trail(d[j + 1]):
                j += 2
                cnt += 1
            if cnt >= minchars:
                try:
                    out.append((i, d[i:j].decode('cp932')))
                except Exception:
                    pass
            i = j
        else:
            i += 1
    return out


def parse_msg(d):
    """.MSG 확정 파서 — [(오프셋, 문자열)]. 오프셋 표는 파일 절대."""
    m = Mato(d)
    blk_start = m.off[0]
    first = struct.unpack_from('>I', d, blk_start)[0]
    if not (blk_start < first <= len(d)):
        raise MatoError('첫 오프셋 0x%X 가 범위 밖' % first)
    cnt = (first - blk_start) // 4
    offs = list(struct.unpack_from('>%dI' % cnt, d, blk_start))
    out = []
    for o in offs:
        if not (0 < o < len(d)):
            continue
        e = d.find(b'\x00', o)
        if e < 0:
            e = len(d)
        if e > o:
            try:
                out.append((o, d[o:e].decode('cp932')))
            except Exception:
                pass
    return out, cnt


def main():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)

    print('=== 확정: .MSG (구조 확인됨) ===')
    msg_chars = msg_strs = 0
    for path, lba, size, oob in sorted(rows):
        if not path.upper().endswith('.MSG'):
            continue
        d = iso.read(lba, size)
        try:
            items, cnt = parse_msg(d)
        except Exception as e:
            print('   %-20s 파싱 실패: %s' % (path, e))
            continue
        c = sum(len(t) for _, t in items)
        msg_chars += c
        msg_strs += len(items)
        print('   %-20s 표 %4d개 / 문자열 %4d / %6d자   예: %s'
              % (path, cnt, len(items), c, items[0][1][:22] if items else ''))
    print('   합계 문자열 %d / %d자' % (msg_strs, msg_chars))

    print('\n=== 하한: 그 밖 파일의 cp932 스캔 (소비 규칙 미확정) ===')
    byext = collections.Counter()
    byext_str = collections.Counter()
    samples = {}
    for path, lba, size, oob in rows:
        ext = os.path.splitext(path)[1].upper()
        if ext in ('.WAV', '.ADP', '.AVI', '.BGM', '.SE', '.CD'):
            continue
        if size > 4 * 1024 * 1024:
            continue
        d = iso.read(lba, size)
        hits = scan_cp932(d, minchars=3)
        if not hits:
            continue
        byext[ext] += sum(len(t) for _, t in hits)
        byext_str[ext] += len(hits)
        if ext not in samples and hits:
            samples[ext] = (path, hits[0][1])
    print('%-10s %8s %10s   %s' % ('확장자', '문자열', '글자', '예시'))
    tot = 0
    for ext, c in byext.most_common():
        p, s = samples.get(ext, ('', ''))
        print('%-10s %8d %10d   %-22s %s' % (ext, byext_str[ext], c, s[:20], p))
        tot += c
    print('   하한 합계 %d자' % tot)


if __name__ == '__main__':
    main()

"""한글 출력 PoC v2 — 대상 파일을 **화면 문구 전체**로 확정하고 4줄을 바꾼다.

v1 실패 원인: `機は熟したり。` 가 `NT21.MAP` 과 `NT31.MAP` 양쪽에 있는데
**첫 히트를 그냥 썼다.** 화면의 나머지 줄(`我ら委員会の計画を`)까지 대조하니
진짜 대상은 `NT31.MAP` 이었다(화자도 NT21 은 `７人委員会リーダー`로 다르다).
★대상 파일은 «화면에 보이는 문구 전부»가 한 곳에 연속으로 있는지로 고른다.

원문(/NT31.MAP 0x21907~)          번역 (문장부호 뒤 공백 없음)
    %z機は熟したり。\n       17B    %z때가무르익다。\n        17B
    今こそ、我ら委員会の計画を\n 27B   이제우리위원회의계획을\n  23B
    実行に移すとき。\n       17B    실행에옮길때다。\n        17B
    世界に覇をとなうべし！   22B    세계를제패하리라！        18B

★길이가 모자라면 **마침표를 가장 먼저** 지운다([[feedback_no_space_after_punct]]).
★제어 토큰(%z %b %H %m1 %V100)과 개행은 그대로 보존한다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from fntc import Fntc
from project import TRACK1, OUT_TRACK1
from peek import load_list
import krglyph
import discbuild

MAP_FILE = '/NT31.MAP'
FONT_FILE = '/RIG2INIT.DAT'
FONT_BLOCK = 1

# (원문, 번역) — 원문은 파일에 있는 그대로(토큰·개행 포함)
#
# ★★띄어쓰기 시험: 폰트 코드표에 **1바이트(반각) 코드가 0개**다(최소값 0x8140).
#   그런데 원문 몇 곳에 반각 스페이스가 `！ %b` 형태로 쓰인다.
#   렌더러가 반각 공백을 폭만 전진시켜 주는지 **한 화면에서 세 방식을 비교**한다.
#     1줄 반각 1개 / 2줄 반각 3개 / 3줄 전각 1개 / 4줄 붙여쓰기(대조군)
#   반각(1B)이 통하면 띄어쓰기 비용이 전각(2B)의 절반이라 20만자 예산이 크게 달라진다.
# ★길이가 모자란 1줄은 **마침표를 지웠다**([[feedback_no_space_after_punct]] 우선순위).
PAIRS = [
    ('%z機は熟したり。\n',        '%z때가 무르익다\n'),          # 반각 1개 (마침표 삭제)
    ('今こそ、我ら委員会の計画を\n', '이제 우리 위원회의 계획을\n'),   # 반각 3개
    ('実行に移すとき。\n',         '실행에　옮길때다\n'),           # 전각 1개
    ('世界に覇をとなうべし！',      '세계를제패하리라！'),           # 붙여쓰기(대조군)
]


# ★★리드 바이트는 **0x88~0x9F** 만 쓴다.
#   v2 는 코드표 뒤쪽(0xE1~0xE8)에서 골랐다가 실기에서 글자가 **두 배로 늘어나며 깨졌다** —
#   2바이트가 1바이트씩 쪼개져 렌더된 지문이다. 게임 렌더러가 전각 리드를
#   `0x81~0x9F` 로만 판정하는 것으로 보인다.
#   근거: 폰트 코드표의 0xE 영역은 **11자뿐**이고, 실제 대사 3만여 글자는
#         0x81~0x98 만 쓴다(0xE1·0xE3 각 1회뿐).
LEAD_MIN, LEAD_MAX = 0x88, 0x9F


def pick_donors(f, need, avoid_chars, disc_data):
    """글리프를 내줄 «희귀» 한자 인덱스.

    조건 1. 리드 바이트가 0x88~0x9F (렌더러가 전각으로 인정하는 범위)
    조건 2. 대상 파일에 그 코드가 안 쓰인다 (다른 대사가 깨지지 않게)
    ★뒤에서부터 = JIS 2수준(0x98~) 쪽부터 = 본문에 덜 쓰이는 한자부터.
    """
    out = []
    for i in range(f.n - 1, -1, -1):
        ch = f.char_of(i)
        if not ch or ch in avoid_chars:
            continue
        code = f.codes[i]
        if not (LEAD_MIN <= (code >> 8) <= LEAD_MAX):
            continue
        if bytes([code >> 8, code & 0xFF]) in disc_data:
            continue
        out.append(i)
        if len(out) == need:
            break
    return out


def main(dry):
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    mp, mlba, msize, _ = rows[MAP_FILE]
    mapd = bytearray(iso.read(mlba, msize))
    fp, flba, fsize, _ = rows[FONT_FILE]
    fontd = iso.read(flba, fsize)
    fm = Mato(fontd, FONT_FILE)
    f = Fntc(fm.block(FONT_BLOCK))

    # --- 원문 위치 확인 (전부 있어야 한다) ---
    spots = []
    for src, ko in PAIRS:
        b = src.encode('cp932')
        pos = mapd.find(b)
        if pos < 0:
            sys.exit('★원문을 못 찾았다: %r' % src)
        if mapd.find(b, pos + 1) >= 0:
            print('  ⚠ %r 가 파일에 두 번 이상 있다 — 첫 것만 바꾼다' % src[:14])
        spots.append((pos, b, src, ko))
    spots.sort()
    print('%s  대사 4줄 위치 0x%X ~ 0x%X' % (MAP_FILE, spots[0][0], spots[-1][0]))

    # --- 필요한 한글 음절 ---
    syll = []
    for _, ko in PAIRS:
        for c in ko:
            if '가' <= c <= '힣' and c not in syll:
                syll.append(c)
    miss = krglyph.coverage(''.join(syll))
    if miss:
        sys.exit('★BDF 에 없는 글자: %s' % miss)
    print('필요 음절 %d자: %s' % (len(syll), ''.join(syll)))

    avoid = set(''.join(s for _, _, s, _ in spots))
    idxs = pick_donors(f, len(syll), avoid, bytes(mapd))
    if len(idxs) < len(syll):
        sys.exit('★내줄 글리프가 모자란다 (%d < %d)' % (len(idxs), len(syll)))
    donor = {}
    for ko, i in zip(syll, idxs):
        donor[ko] = f.codes[i]
        f.set_glyph(i, krglyph.glyph(ko, f.w, f.h))
    print('글리프 %d칸 교체 (인덱스 %d~%d)' % (len(syll), min(idxs), max(idxs)))

    # --- 치환 ---
    print('\n%-30s %-6s %-30s %s' % ('원문', '바이트', '번역', '바이트'))
    for pos, b, src, ko in spots:
        out = bytearray()
        for c in ko:
            if c in donor:
                code = donor[c]
                out += bytes([code >> 8, code & 0xFF])
            else:
                out += c.encode('cp932')
        mark = 'OK' if len(out) <= len(b) else '★초과'
        print('%-30s %-6d %-30s %d  %s'
              % (src.replace('\n', '\\n')[:28], len(b), ko.replace('\n', '\\n')[:28], len(out), mark))
        if len(out) > len(b):
            sys.exit('★번역이 원문보다 길다')
        mapd[pos:pos + len(b)] = bytes(out) + bytes(len(b) - len(out))

    # --- 재조립 ---
    blocks = fm.blocks()
    blocks[FONT_BLOCK] = f.to_bytes()
    newfont = fm.rebuild(blocks)
    if len(newfont) != fsize or len(mapd) != msize:
        sys.exit('★크기가 바뀌었다')
    print('\n크기 유지 확인: 폰트 %d B / 맵 %d B' % (len(newfont), len(mapd)))

    if dry:
        print('[미리보기만 — 디스크는 안 건드렸다]')
        return
    print('원본 복사 -> %s' % OUT_TRACK1)
    discbuild.fresh_copy()
    with open(OUT_TRACK1, 'r+b') as fh:
        a = discbuild.write_file(fh, flba, newfont)
        b2 = discbuild.write_file(fh, mlba, bytes(mapd))
    print('  섹터 갱신: 폰트 %d + 맵 %d (EDC/ECC 재계산)' % (a, b2))
    print('\n완료. 오프닝 7인 위원회 장면을 볼 것.')


if __name__ == '__main__':
    main('--dry' in sys.argv)

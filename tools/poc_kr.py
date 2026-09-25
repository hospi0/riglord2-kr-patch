"""한글 출력 PoC — 「이 화면에 한글을 띄운다」 하나만 판정한다.

대상 = 오프닝 7인 위원회 장면. `NT21.MAP` 안의 평문 cp932 대사.

    원문  機は熟したり。          (14 B)
    번역  때가무르익다。          (6음절 12 B + 。2 B = 14 B) ← 같은 길이

방법
  1. `FNTC`(RIG2INIT.DAT 블록1)의 **희귀 한자 글리프 6칸**을 한글로 덮어그린다.
     코드 표는 그대로 두므로 그 한자 코드를 쓰면 한글이 그려진다.
  2. `NT21.MAP` 의 그 대사를 그 한자 코드로 **제자리 치환**(길이 초과 금지, 널 패딩).
  3. mato 재조립 → 두 파일 모두 **크기 유지** → Track1 제자리 덮어쓰기 + ECC 재계산.

★변수는 「폰트 + 그 한 문장」뿐이다. 카나리아 글자는 **화면에 실제로 보이는 것**이어야
  판정이 된다 ([[feedback_orta_only_openingdemo_works]] 에서 세 번 틀렸다).
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from fntc import Fntc
from project import TRACK1, OUT_TRACK1, WORK
from peek import load_list
import krglyph
import discbuild

SRC = '機は熟したり。'
KO = '때가무르익다。'
MAP_FILE = '/NT21.MAP'
FONT_FILE = '/RIG2INIT.DAT'
FONT_BLOCK = 1


def pick_codes(f, need, used_text, disc_data):
    """글리프를 내줄 «희귀» 한자 인덱스. 대상 파일에 안 쓰이는 코드만."""
    out = []
    for i in range(f.n - 1, -1, -1):          # 코드 표 뒤쪽 = NEC/IBM 확장, 거의 안 쓰인다
        ch = f.char_of(i)
        if not ch or ch in used_text:
            continue
        b = bytes([f.codes[i] >> 8, f.codes[i] & 0xFF])
        if b in disc_data:                    # 그 파일에 이미 쓰이면 다른 대사가 깨진다
            continue
        out.append(i)
        if len(out) == need:
            break
    return out


def main(dry):
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)

    # --- 대상 파일 읽기 ---
    mp, mlba, msize, _ = rows[MAP_FILE]
    mapd = bytearray(iso.read(mlba, msize))
    fp, flba, fsize, _ = rows[FONT_FILE]
    fontd = iso.read(flba, fsize)
    fm = Mato(fontd, FONT_FILE)
    f = Fntc(fm.block(FONT_BLOCK))
    print('폰트 %d자 %dx%d / %s %d B' % (f.n, f.w, f.h, MAP_FILE, msize))

    # --- 원문 위치 ---
    src_b = SRC.encode('cp932')
    pos = mapd.find(src_b)
    if pos < 0:
        sys.exit('★원문을 %s 에서 못 찾았다' % MAP_FILE)
    print('원문 0x%X  %d B  %r' % (pos, len(src_b), SRC))

    # --- 한글 음절과 커버리지 ---
    syll = [c for c in KO if '가' <= c <= '힣']
    miss = krglyph.coverage(''.join(syll))
    if miss:
        sys.exit('★BDF 에 없는 글자: %s' % miss)   # 인코딩 누락은 빌드 에러다

    # --- 글리프를 내줄 한자 고르기 ---
    idxs = pick_codes(f, len(syll), set(SRC), bytes(mapd))
    if len(idxs) < len(syll):
        sys.exit('★내줄 글리프가 모자란다')
    donor = {}
    for ko, i in zip(syll, idxs):
        donor[ko] = (i, f.char_of(i), f.codes[i])

    print('\n[글리프 교체] 희귀 한자 칸을 한글로')
    for ko, (i, ch, code) in donor.items():
        f.set_glyph(i, krglyph.glyph(ko, f.w, f.h))
        print('   %s ← %s (인덱스 %d, 코드 %04X)' % (ko, ch, i, code))

    # --- 치환 바이트열 ---
    out = bytearray()
    for c in KO:
        if c in donor:
            code = donor[c][2]
            out += bytes([code >> 8, code & 0xFF])
        else:
            out += c.encode('cp932')
    print('\n치환 %d B / 원문 %d B' % (len(out), len(src_b)))
    if len(out) > len(src_b):
        sys.exit('★번역이 원문보다 길다')
    mapd[pos:pos + len(src_b)] = bytes(out) + bytes(len(src_b) - len(out))

    # --- 재조립 (크기 유지) ---
    blocks = fm.blocks()
    blocks[FONT_BLOCK] = f.to_bytes()
    newfont = fm.rebuild(blocks)
    print('\nRIG2INIT.DAT %d B (원본 %d)  / NT21.MAP %d B (원본 %d)'
          % (len(newfont), fsize, len(mapd), msize))
    if len(newfont) != fsize or len(mapd) != msize:
        sys.exit('★크기가 바뀌었다')

    if dry:
        print('\n[미리보기만 — 디스크는 안 건드렸다]')
        return

    # --- 디스크 빌드 ---
    print('\n원본 복사 -> %s' % OUT_TRACK1)
    discbuild.fresh_copy()
    with open(OUT_TRACK1, 'r+b') as fh:
        a = discbuild.write_file(fh, flba, newfont)
        b = discbuild.write_file(fh, mlba, bytes(mapd))
    print('  섹터 갱신: 폰트 %d개 + 맵 %d개 (EDC/ECC 재계산 포함)' % (a, b))
    print('\n완료. 오프닝 7인 위원회 장면을 볼 것.')
    print('   기대: 「%s」 자리에 「%s」' % (SRC, KO))


if __name__ == '__main__':
    main('--dry' in sys.argv)

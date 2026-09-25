# -*- coding: utf-8 -*-
"""회수 — `/WAZAHELP.MSG` 에서 **추출 자체가 안 된** 기술 설명문 1개.

실기: 스킬 정보창 설명이 `업1쭉を鍛く소く技です。`(한글 잔해+일본어)로 나왔다.
파손이 아니라 **원문이 애초에 코퍼스에 없던 것**이다.

★★원인 = `/WAZAHELP.MSG` 앞머리 `0x3D0~0x3FF` 이 **BE 32비트 오프셋 표**인데
  마지막 항목이 `00 00 32 F0` 이라 **끝바이트가 0xF0(NUL 아님)** 이다. 문자열은
  바로 뒤 `0x400` 에서 시작하는데, NUL 순차 스캐너는 조각 시작을 `0x3FE` 로
  되짚어 잡아 `32 F0` 두 바이트를 앞에 달고 디코드했다 — `F0` 은 cp932 가이지
  선두바이트라 통째로 다른 글자가 돼 후보에서 탈락했다.
  (`ステータス<＞>` 탭 제목과 **완전히 같은 유착 패턴** — [[trans_ui6]] 참고.
  거긴 UI 포인터 표, 여긴 스토리 파일 오프셋 표였을 뿐이다.)
  `技です` 가 디스크에 35개인데 코퍼스엔 34개뿐인 것으로 확정했다.

예산 24B — 원문이 짧아 다른 설명문(58~78B)보다 훨씬 빠듯하다. 그래서
`～기술입니다` 정형을 못 쓰고 명사형으로 줄였다.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

FILE = '/WAZAHELP.MSG'
OFF = 0x400
JP = '敵１体を鋭く突く技です。'
KO = '적１체를 날카롭게 찌름'


def main():
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    _, lba, size, _ = rows[FILE]
    d = bytes(iso.read(lba, size))

    raw = JP.encode('cp932')
    if d[OFF:OFF + len(raw)] != raw:
        sys.exit('★%s 0x%X 의 바이트가 원문과 다르다' % (FILE, OFF))
    if d[OFF + len(raw)] != 0:
        sys.exit('★0x%X 뒤가 NUL 이 아니다 — 종단 확인 실패' % (OFF + len(raw)))

    key = hashlib.sha1(raw).hexdigest()[:10]
    n = len(raw)
    budget = len(KO.encode('cp932', 'replace'))  # 참고용
    ko_bytes = sum(2 if '가' <= c <= '힣' else 1 for c in KO)
    if ko_bytes > n:
        sys.exit('★예산 초과: %dB > %dB' % (ko_bytes, n))

    sp = os.path.join(WORK, 'trans', 'strings.tsv')
    rp = os.path.join(WORK, 'trans', 'refs.tsv')
    have = set()
    with io.open(sp, encoding='utf-8') as f:
        next(f)
        for line in f:
            have.add(line.split('\t')[0])
    if key in have:
        print('이미 반영됨 (%s)' % key)
        return

    with io.open(sp, 'a', encoding='utf-8', newline='') as f:
        f.write('%s\t1\t%d\t%d\t\t%s\t%s\n' % (key, n, len(JP), JP, KO))
    with io.open(rp, 'a', encoding='utf-8', newline='') as f:
        f.write('%s\t%s\t%d\t%d\n' % (key, FILE, OFF, n))
    for name in ('ko_final.tsv', 'ko_shrunk.tsv'):
        p = os.path.join(WORK, 'trans', name)
        if os.path.exists(p):
            with io.open(p, 'a', encoding='utf-8', newline='') as f:
                f.write('%s\t%s\n' % (key, KO))

    print('회수 %s  %r -> %r  (%dB -> %dB, %s 0x%X)'
          % (key, JP, KO, n, ko_bytes, FILE, OFF))


if __name__ == '__main__':
    main()

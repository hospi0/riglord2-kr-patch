# -*- coding: utf-8 -*-
"""배포용 xdelta 패치 — 프로젝트 루트에 만든다.

  python tools/make_xdelta.py

무수정 원본(F드라이브 **안쪽 중첩 폴더**) ↔ 패치본(바깥)을 견주어
`riglord2_kr_<VERSION>.xdelta` 를 만든다. 대상은 Track 1 뿐이다 —
Track 2~4 는 오디오라 손대지 않는다.

★크기가 바뀌지 않는 패치라, 사용자가 실수로 두 번 적용해도 xdelta 가
  원본 해시로 거른다.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import TRACK1, OUT_TRACK1

VERSION = '0.82'
XDELTA = r'C:\claude\utils\xdelta.exe'
OUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if not os.path.exists(XDELTA):
        raise SystemExit('xdelta 가 없다: %s' % XDELTA)
    for p in (TRACK1, OUT_TRACK1):
        if not os.path.exists(p):
            raise SystemExit('★없음: %s' % p)
    if os.path.getsize(TRACK1) != os.path.getsize(OUT_TRACK1):
        raise SystemExit('★크기가 다르다 — 원본/패치본이 뒤바뀌었을 수 있다')

    out = os.path.join(OUT_DIR, 'riglord2_kr_%s.xdelta' % VERSION)
    if os.path.exists(out):
        os.remove(out)
    r = subprocess.run([XDELTA, '-e', '-9', '-s', TRACK1, OUT_TRACK1, out],
                       capture_output=True)
    if r.returncode != 0:
        raise SystemExit('★xdelta 실패: %s'
                         % r.stderr.decode('utf-8', 'replace')[:300])
    print('원본  %s' % TRACK1)
    print('패치본 %s' % OUT_TRACK1)
    print('→ %s  %d B' % (os.path.basename(out), os.path.getsize(out)))


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""`/PRF_0/*.PRF` = 캐릭터 프로필(도감) 파일 — 초상화 그래픽 + **꼬리에 붙은 설명문**.

★★기존 코퍼스(`corpus2.py`)는 `.MAP/.MSG/.MAT` 만 훑었기 때문에 이 103개 파일이
  통째로 추출 범위 밖이었다. 실기에서 「러스티/뮤 프로필이 미번역인데다 글자가
  깨져 보인다」로 드러났다 — 원문이 그대로 남은 자리가 «도너로 뺏긴 한자 칸»을
  가리켜서 엉뚱한 한글로 찍힌 것([[feedback_reserve_fnt_slots_of_untranslated]]).

구조 (실측)
    파일 대부분 = 초상화 데이터
    꼬리        = cp932 설명문, CR/LF 로 줄바꿈, 끝에 0x1A 반복(EOF) 패딩
    설명문은 전각 공백(0x81 0x40)으로 시작한다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1
from peek import load_list

FW_SPACE = b'\x81\x40'
CTRL_OK = ('\r', '\n')


def _clean(t):
    """그래픽이 우연히 디코드된 것과 진짜 산문을 가른다."""
    for c in t:
        o = ord(c)
        if o < 0x20 and c not in CTRL_OK:
            return False
        if 0xFF61 <= o <= 0xFF9F:          # 반각 가타카나 — 산문엔 안 쓰인다
            return False
        if 0xE000 <= o <= 0xF8FF:          # 사용자정의 영역 = 그래픽 바이트
            return False
    return True


def find_text(d):
    """-> (start, end) 텍스트 바이트 구간. 못 찾으면 None.

    ★★«끝에서 한 바이트씩 거슬러 올라가기»는 쓰면 안 된다 — 2바이트 문자
      중간에서 자른 조각이 반각가타카나로 «성공적으로» 디코드돼서 그래픽으로
      오판된다(실제로 4바이트만 잡혔다). 대신 **시작 후보(전각 공백)를 잡고
      정방향으로 디코드**한다([[feedback_regex_string_start_backtrace]]).
    """
    end = len(d)
    while end > 0 and d[end - 1] == 0x1A:
        end -= 1
    if end == len(d):
        return None                        # EOF 마커가 없다 = 대상 아님

    # ⛔시작을 «전각 공백(0x81 0x40)»으로만 잡으면 안 된다 — 21개 파일은 곧바로
    #   본문으로 시작한다(`彼は…`, `プロフィール文なし。`). 그래서 꼬리 구간의
    #   **모든 오프셋**을 앞에서부터 훑어 «처음으로 끝까지 깨끗하게 디코드되는
    #   자리»를 시작점으로 삼는다. 그래픽 바이트(0x80 계열)는 cp932 디코드
    #   자체가 실패하므로 자연히 걸러진다.
    lo = max(0, end - 4096)
    # ①먼저 전각 공백 시작을 찾는다. 그래픽 바이트가 «희귀 한자»로 우연히
    #   디코드되는 구간(挾找抉抂扼…)이 본문 앞에 붙는 걸 막으려면 이 우선순위가
    #   필요하다 — 일반 스캔만 쓰면 PF_003 이 그래픽 꼬리를 물고 들어온다.
    j = lo
    while True:
        j = d.find(FW_SPACE, j, end)
        if j < 0:
            break
        try:
            t = d[j:end].decode('cp932')
        except UnicodeDecodeError:
            j += 2
            continue
        if _clean(t):
            return (j, end)
        j += 2
    # ②전각 공백으로 시작하지 않는 파일(21개)용 일반 스캔
    for i in range(lo, end):
        try:
            t = d[i:end].decode('cp932')
        except UnicodeDecodeError:
            continue
        if not _clean(t):
            continue
        if not any('぀' <= c <= 'ヿ' or '一' <= c <= '鿿' for c in t):
            continue                       # 가나·한자가 하나도 없으면 본문이 아니다
        return (i, end)
    return None


def texts():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)
    out = []
    for path, lba, size, oob in sorted(rows):
        if not path.upper().endswith('.PRF'):
            continue
        d = iso.read(lba, size)
        r = find_text(d)
        if not r:
            out.append((path, None, None, None))
            continue
        s, e = r
        out.append((path, s, e, d[s:e].decode('cp932')))
    return out


if __name__ == '__main__':
    rows = texts()
    ok = [r for r in rows if r[3] is not None]
    bad = [r for r in rows if r[3] is None]
    tot = sum(len(t) for _, _, _, t in ok)
    print('PRF %d개 / 텍스트 검출 %d개 / 미검출 %d개 / 총 %d자'
          % (len(rows), len(ok), len(bad), tot))
    for path, s, e, t in bad:
        print('  ★미검출 %s' % path)
    for path, s, e, t in ok[:4]:
        print('--- %s  0x%X~0x%X (%dB)' % (path, s, e, e - s))
        print(repr(t))

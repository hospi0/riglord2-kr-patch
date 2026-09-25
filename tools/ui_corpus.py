# -*- coding: utf-8 -*-
"""UI 텍스트(시스템 메뉴) 전수 추출 — `.OVL` mato 컨테이너용.

세션3 실기 스샷에서 옵션/전투메뉴/스킬메뉴/스테이터스 화면이 전부 미번역으로
확인됐다. 이 문자열들은 `.MAP/.MSG/.MAT` 가 아니라 **`.OVL` 오버레이**(mato 컨테이너)
안에 있다 — `corpus.py` 의 대상 확장자 밖이라 지금까지 안 뽑혔다.

★★기존 `corpus.strings()` 로는 못 잡는다 — 텍스트 **바로 앞에 아이콘 가이지
  바이트(리드 0xF8~0xF9, cp932 사용자 정의 영역)** 가 붙어 있어서
  `is_lead()`(0x81~0x9F/0xE0~0xEF) 판정에 걸려 전체 세그먼트가 통째로 버려졌다.
  예: `\xf8\xf3\xf8\xf3バトルアニメ` — 앞의 두 가이지(커서 아이콘)때문에
  기존 스캐너는 이 세그먼트를 "not ok" 로 버렸다.

여기서는 가이지 2바이트를 **불투명 토큰**(`{G:F8F3}`)으로 취급해 보존하고,
그 뒤의 진짜 번역 대상만 잡아낸다.

★★블록1 은 앞쪽 절반 이상이 **SH-2 실행 코드**다(mato 안에 (offset,size) 세그먼트
  표가 있고, 각 세그먼트도 코드+데이터가 섞여 있다). 무작정 스캔하면 코드 구간의
  우연한 바이트가 "그럴듯한 문자열"로 오검출될 위험이 있다 — `corpus2.is_real()` 로
  거른다(자소 반복·노이즈 판정).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from project import TRACK1, WORK
from peek import load_list
from corpus2 import is_real

TOKEN = re.compile(r'%[A-Za-z][0-9]*')
GAIJI_RE = re.compile(r'(|[-識])')   # 참고용, 실제 판정은 바이트 단위

# ★`/R2MDATA.OVL` 을 빠뜨리고 있었다 — 전투 지명(`練習場`)이 여기 있다.
#   「이 화면은 이 파일을 쓸 것이다」라는 짐작으로 목록을 좁힌 탓
#   ([[feedback_verify_which_asset_the_screen_uses]]).
OVL_FILES = ['/RIG2.OVL', '/RIG2MENU.OVL', '/RIG2EVE.OVL']

# /1_RIG2.BIN 은 mato 아닌 **순수 실행 바이너리**(SH-2 코드, 헤더 없음).
# ★★실측: `strings_ui()` 히트가 0x7B1E4~0x97E6A 구간에 **426/429개가 몰려** 있고
#   그 밖(0x00000~0x7B000)엔 가짜(코드 오검출) 3개뿐 — 이 구간이 시스템 UI
#   문자열이 사는 데이터 영역이라는 강한 증거다. ⛔그렇다고 「전부 텍스트」는 아니다 —
#   이 구간 안에도 파일명(`WAZA_000.WAZ`)·숫자표(`0123456789` 반복)·포인터표가
#   섞여 있다(72KB 짜리 빈틈 하나가 그거다). full>=2(가나/한자 최소 2자) 필터로
#   ASCII 전용 파일명은 걸러지지만, **번역 전에는 반드시 실기로 소규모 PoC 먼저**
#   ([[feedback_terra_methodology_2026-07-06]] 소규모 실험→별도 xdelta→실기→확장).
BIN_FILE = '/1_RIG2.BIN'
BIN_SAFE_LO, BIN_SAFE_HI = 0x7B1E4, 0x98000

# ★mato 가 아닌 **평문** 데이터 파일. `/R2MDATA.OVL` 은 확장자만 .OVL 이고
#   매직이 mato 가 아니다 — 전투 지명(`練習場`)이 여기 있다.
PLAIN_FILES = ['/R2MDATA.OVL']


def is_lead(b):
    return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xef


def is_gaiji_lead(b):
    return 0xf0 <= b <= 0xf9


def is_halfkana(b):
    """★★반각 가타카나(cp932 0xA1~0xDF, 1바이트).

    이걸 «모르는 바이트»로 취급해 문자열을 통째로 버리고 있었다. 그 결과
    `ｽﾃｰﾀｽ` `ｽﾄﾗｲｸ` `ｺｯﾄﾝｸﾞﾛｰﾌﾞ` `ﾏｯﾌﾟﾁｪｯｸ` 처럼 **UI·기술명·아이템명이
    반각으로 적힌 것**이 전부 추출에서 빠졌다(실기 스샷으로 발각).
    ⛔반각은 1바이트라 **한글(2바이트)로 바꾸면 글자수가 반으로 준다** —
      번역할 때 예산을 특히 조심해야 한다.
    """
    return 0xa1 <= b <= 0xdf


def is_trail(b):
    return 0x40 <= b <= 0xfc and b != 0x7f


def decode_with_gaiji(seg):
    """세그먼트를 (표시용 문자열, 페이로드 글자수, 가이지 존재?) 로.

    가이지 바이트는 `{G:XXXX}` 토큰으로 바꿔 cp932 로 디코드 가능하게 만든다.
    ★이 토큰은 TOKEN 정규식(`%X`)과 별개다 — 번역 시 원문 그대로 보존해야 한다.
    """
    out = []
    i = 0
    n = len(seg)
    gaiji = False
    full = 0
    while i < n:
        b = seg[i]
        if is_gaiji_lead(b) and i + 1 < n:
            out.append('{G:%02X%02X}' % (b, seg[i + 1]))
            gaiji = True
            i += 2
        elif is_lead(b) and i + 1 < n and is_trail(seg[i + 1]):
            out.append(seg[i:i + 2].decode('cp932', 'replace'))
            full += 1
            i += 2
        elif is_halfkana(b):
            out.append(bytes([b]).decode('cp932', 'replace'))
            full += 1                    # 반각 가타카나도 «일본어 글자»로 센다
            i += 1
        elif b in (0x0a, 0x0d) or 0x20 <= b < 0x7f:
            out.append(chr(b))
            i += 1
        else:
            return None, 0, False
        continue
    return ''.join(out), full, gaiji


def strings_ui(d):
    """[(오프셋, 원시바이트, 표시문자열, 가이지있음)]. NUL 종단, 전각 2자 이상.

    ★★진짜 항목 구분자는 `0x00 0xFF` **쌍**이다(포맷은 「text + 00 FF」 반복).
      단순히 0x00 으로만 자르면 앞 항목의 트레일러 0xFF 가 다음 조각 **맨 앞에
      한 바이트 남아** 디코드가 통째로 실패한다(선두 0xFF 는 가이지도 ASCII도
      아니다). 목록 구간 끝에는 `\\xff\\xff\\xff` 로 여러 바이트가 몰리기도 한다.
      → 자른 조각의 **앞뒤 0xFF 런을 벗겨내고** 디코드한다.
    """
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
        raw = d[i:j]
        seg = raw.strip(b'\xff')
        off = i + (len(raw) - len(raw.lstrip(b'\xff')))
        i = j + 1
        if len(seg) < 4 or len(seg) > 400:
            continue
        t, full, gaiji = decode_with_gaiji(seg)
        if t is None or full < 2:
            continue
        out.append((off, bytes(seg), t, gaiji))
    return out


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def export():
    """UI 문자열 전수를 `work/trans/ui_strings.tsv` 로.

    형식은 `strings.tsv` 와 같은 규약(key/files/bytes/chars/tokens/jp/ko).
    ★key 는 sha1(원문 바이트)[:10] — 단, 여기 원문 바이트는 **가이지 벗긴 뒤의
    표시용 문자열을 다시 cp932 로 인코드한 것**이 아니라 **원본 그대로**를 쓴다
    (가이지 토큰까지 포함해야 재삽입 때 자리를 정확히 찾는다).
    """
    import hashlib
    import io
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    uniq = {}
    refs = []

    def add(fn, off, raw, t, gaiji):
        key = hashlib.sha1(raw).hexdigest()[:10]
        payload = TOKEN.sub('', re.sub(r'\{G:[0-9A-F]{4}\}', '', t))
        if key not in uniq:
            uniq[key] = dict(key=key, bytes=len(raw), jp=t, chars=len(payload),
                             tokens=' '.join(dict.fromkeys(re.findall(r'\{G:[0-9A-F]{4}\}', t))),
                             files=set(), gaiji=gaiji)
        uniq[key]['files'].add(fn)
        refs.append((key, fn, off, len(raw)))

    for fn in OVL_FILES:
        p, l, s, _ = rows[fn]
        d = iso.read(l, s)
        m = Mato(d, fn)
        for bi, blk in enumerate(m.blocks()):
            for off, raw, t, gaiji in strings_ui(bytes(blk)):
                if not is_real(re.sub(r'\{G:[0-9A-F]{4}\}', '', t)):
                    continue
                add('%s#%d' % (fn, bi), off, raw, t, gaiji)

    p, l, s, _ = rows[BIN_FILE]
    d = bytes(iso.read(l, s))
    for off, raw, t, gaiji in strings_ui(d):
        if not (BIN_SAFE_LO <= off <= BIN_SAFE_HI):
            continue
        if not is_real(re.sub(r'\{G:[0-9A-F]{4}\}', '', t)):
            continue
        add(BIN_FILE, off, raw, t, gaiji)

    out_dir = os.path.join(WORK, 'trans')
    sp = os.path.join(out_dir, 'ui_strings.tsv')
    with io.open(sp, 'w', encoding='utf-8', newline='') as f:
        f.write('key\tfiles\tbytes\tchars\ttokens\tgaiji\tjp\tko\n')
        for u in sorted(uniq.values(), key=lambda x: (-x['chars'], x['key'])):
            f.write('%s\t%d\t%d\t%d\t%s\t%d\t%s\t\n'
                    % (u['key'], len(u['files']), u['bytes'], u['chars'],
                       u['tokens'], u['gaiji'], esc(u['jp'])))
    rp = os.path.join(out_dir, 'ui_refs.tsv')
    with io.open(rp, 'w', encoding='utf-8', newline='') as f:
        f.write('key\tfile\toffset\tbytes\n')
        for key, fn, off, n in sorted(refs):
            f.write('%s\t%s\t%d\t%d\n' % (key, fn, off, n))

    print('UI 고유 문자열 %d개 / 참조 %d건' % (len(uniq), len(refs)))
    print('  ->', sp)
    print('  ->', rp)
    tot_chars = sum(u['chars'] for u in uniq.values())
    print('번역 글자수 합계 %d자' % tot_chars)
    return uniq, refs


def main():
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    total = 0
    by_file = {}
    for fn in OVL_FILES:
        p, l, s, _ = rows[fn]
        d = iso.read(l, s)
        m = Mato(d, fn)
        hits = []
        for bi, blk in enumerate(m.blocks()):
            for off, raw, t, gaiji in strings_ui(bytes(blk)):
                if not is_real(TOKEN.sub('', t.encode('utf-8', 'ignore').decode('utf-8'))
                                if False else re.sub(r'\{G:[0-9A-F]{4}\}', '', t)):
                    continue
                hits.append((bi, off, raw, t, gaiji))
        by_file[fn] = hits
        total += len(hits)
        print('%-16s 블록%d개 -> 문자열 %d개' % (fn, m.n, len(hits)))

    print('\n합계 %d개 (참고: /1_RIG2.BIN 은 mato 아님 — 별도 조사 필요)' % total)

    print('\n표본 (파일당 앞 15개):')
    for fn in OVL_FILES:
        print(' --', fn)
        for bi, off, raw, t, gaiji in by_file[fn][:15]:
            mark = 'G' if gaiji else ' '
            print('   [%s] 블록%d 0x%05X (%2dB) %r' % (mark, bi, off, len(raw), t))

    return by_file


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""한글 패치 빌더 — 글리프 배정 + 전 참조 재삽입(본편+UI) + 디스크 굽기.

파이프라인에서의 자리
    export_tsv -> trans_*(수기) -> normalize_numerals -> punct_fix -> shrink_ko
    -> donorsurvey -> ui_corpus.export -> trans_ui -> **build_kr(여기)** -> (Track1 완성)

하는 일
  1. **본편(`ko_shrunk.tsv`) + UI(`ui_strings.tsv`) 양쪽의 한글 음절을 합쳐서**
     도너 코드를 배정한다. ★폰트 코드표는 **전역 공유 자원**이라(FNTC 두 벌뿐,
     본편·UI가 같은 코드를 같은 글자로 그린다) 반드시 **한 회차에 통합 배정**해야
     한다 — 따로 배정하면 같은 코드가 서로 다른 글자를 가리키게 된다
     ([[feedback_slot_reassign_all_builders]]).
     ★도너 = 리드바이트 0x88~0x9F. 코드표 뒤쪽(0xE1~0xE8)은 실기에서 글자가
       두 배로 늘어나며 깨졌다 — 렌더러가 전각 리드를 0x81~0x9F 로만 본다.
     ★번역문이 **그대로 쓰는** 문자(％，０-９［］~ 등)는 도너에서 제외한다.
     ★[[feedback_riglord2_glyph_donor_no_safety_check]] — 「이 한자가 다른 미번역
       파일에서도 쓰이나」는 **계산하지 않는다.** 최종 목표가 전면 한글화다.
  2. **FNTC 두 벌**(`/RIG2INIT.DAT` 블록1, `/RIG2OP.DAT` 블록3)에 **같은 배정**으로
     글리프를 굽는다. 두 사본은 코드표·글리프가 완전히 동일함을 실측했다
     ([[feedback_shared_text_needs_shared_font]]).
  3. 배정표를 `work/trans/charmap.tsv` 로 **빌드마다 스냅샷**한다
     ([[feedback_snapshot_charmap_with_build]] — 번역 한 줄만 고쳐도 배정이 밀린다).
  4. 본편 문자열을 **전 참조**(`refs.tsv`)에, UI 문자열을 **UI 참조**(`ui_refs.tsv`)에
     제자리 덮어쓴다.
     ★쓰기 전에 자리마다 **원문 바이트 sha1(=key) 정확 일치**를 확인한다.
       오탐 ref(그래픽이 우연히 SJIS 로 읽힌 자리)에 쓰면 인접 데이터가 깨진다.
     ★남는 자리는 NUL 로 채우되 **원문 seg 범위 안에서만** 채운다. 종단자는
       원본 것을 그대로 둔다([[feedback_padding_ate_voice_filename]] — 패딩이
       뒤 데이터를 먹으면 크래시한다).
     ★UI 문자열의 가이지 아이콘 바이트(`{G:XXXX}` 토큰)는 원본 raw 그대로 되살린다
       — 아이콘은 번역 대상이 아니라 커서/버튼 그림 코드다.
     ★UI 참조 중 `.OVL` 계열은 **mato 블록 안**(`경로#블록번호`)이라 mato 재조립이
       필요하고, `/1_RIG2.BIN`(메인 실행 바이너리, mato 아님)은 일반 파일처럼
       직접 오프셋에 쓴다. ★이 바이너리는 **데이터 구간으로 실측 확인된 범위
       (`ui_corpus.BIN_SAFE_LO~HI`)에 한정**해서만 쓴다 — 그 밖은 실행 코드일
       위험이 있다.
  5. 되읽기 검증 — 출력 디스크에서 다시 읽어 기대 바이트와 대조한다.

사용
    python build_kr.py            # 미리보기 (디스크 안 건드림)
    python build_kr.py --write    # 실제 빌드  ★사용자 허락 후에만
"""
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from fntc import Fntc
from project import TRACK1, OUT_TRACK1, WORK
from peek import load_list
import krglyph
import discbuild
import ui_corpus
import menu_blocks
import add_op_bin

TOKEN = re.compile(r'%[A-Za-z][0-9]*')
GAIJI_TOKEN = re.compile(r'\{G:([0-9A-F]{4})\}')

# ★실기 검증된 도너 대역. poc_kr2 참조 — 0xE 대역은 화면이 깨졌다.
LEAD_MIN, LEAD_MAX = 0x88, 0x9F

# (파일, mato 블록) — donorsurvey.py 전수 스캔으로 «이 둘뿐»임을 확인했다.
FONT_TARGETS = [('/RIG2INIT.DAT', 1), ('/RIG2OP.DAT', 3)]


def unesc(s):
    """★문자 단위로 되짚는다 — 순차 .replace() 체인은 순서에 따라 잘못 풀린다."""
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def payload(t):
    """도너 배정에 셀 글자만 — 제어토큰 · 가이지토큰 · 개행 제외."""
    return GAIJI_TOKEN.sub('', TOKEN.sub('', t)).replace('\n', '').replace('\r', '').replace('\t', '')


def load_ko(name=None):
    """본편 번역표. ★기본은 **축약본** `ko_shrunk.tsv` — 없으면 `ko_final.tsv`.
    `shrink_ko.py` 는 원본이 필요하므로 `load_ko('ko_final.tsv')` 로 부른다."""
    if name is None:
        name = ('ko_shrunk.tsv'
                if os.path.exists(os.path.join(WORK, 'trans', 'ko_shrunk.tsv'))
                else 'ko_final.tsv')
    ko = {}
    with io.open(os.path.join(WORK, 'trans', name), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 2 and a[1]:
                ko[a[0]] = unesc(a[1])
    return ko


def load_refs(keys):
    refs = []
    with io.open(os.path.join(WORK, 'trans', 'refs.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if a[0] in keys:
                refs.append((a[0], a[1], int(a[2]), int(a[3])))
    return refs


def load_jp():
    """key -> (원문, 예산 바이트). 예산 초과 보고에 원문을 같이 찍기 위해."""
    jp = {}
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            jp[a[0]] = (unesc(a[5]), int(a[2]))
    return jp


# ---------------------------------------------------------------- UI (시스템 메뉴)

def load_ui_ko():
    ko = {}
    p = os.path.join(WORK, 'trans', 'ui_strings.tsv')
    if not os.path.exists(p):
        return ko
    with io.open(p, encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 8 and a[7]:
                ko[a[0]] = unesc(a[7])
    return ko


def load_ui_jp():
    jp = {}
    p = os.path.join(WORK, 'trans', 'ui_strings.tsv')
    with io.open(p, encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            jp[a[0]] = (unesc(a[6]), int(a[2]))
    return jp


def load_ui_refs(keys):
    refs = []
    with io.open(os.path.join(WORK, 'trans', 'ui_refs.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if a[0] in keys:
                refs.append((a[0], a[1], int(a[2]), int(a[3])))
    return refs


def encode_ui(text, charmap):
    """UI 텍스트 인코딩. `{G:XXXX}` 가이지 토큰은 원본 2바이트로 되돌린다."""
    out = bytearray()
    i = 0
    n = len(text)
    while i < n:
        m = GAIJI_TOKEN.match(text, i)
        if m:
            code = int(m.group(1), 16)
            out += bytes([code >> 8, code & 0xFF])
            i = m.end()
            continue
        ch = text[i]
        if ch in charmap:
            code = charmap[ch][1]
            out += bytes([code >> 8, code & 0xFF])
        else:
            out += ch.encode('cp932')
        i += 1
    return bytes(out)


# ---------------------------------------------------------------- 글리프 배정

def assign_donors(f, *ko_dicts):
    """(charmap, 한글목록, 보존문자) — charmap: 한글 -> cp932 코드(u16).

    ★여러 코퍼스(본편+UI)를 **동시에** 받아 합집합으로 배정한다 — 폰트가
      전역 공유 자원이라 따로 배정하면 충돌한다.
    도너는 **코드가 큰 쪽부터** 고른다 = JIS 2수준(0x98~0x9F)의 희귀 한자부터.
    본문 대사는 0x81~0x98 만 쓰므로 눈에 띄는 손상이 가장 적다.
    """
    hangul, keep = set(), set()
    for ko in ko_dicts:
        for t in ko.values():
            for ch in payload(t):
                if '가' <= ch <= '힣':
                    hangul.add(ch)
                elif f.index_of(ch) is not None:
                    keep.add(ch)
    syll = sorted(hangul)                      # ★결정적 순서 (배정 재현성)

    keep_idx = set()
    for ch in keep:
        i = f.index_of(ch)
        if i is not None:
            keep_idx.add(i)

    cand = [i for i in range(f.n - 1, -1, -1)
            if LEAD_MIN <= (f.codes[i] >> 8) <= LEAD_MAX and i not in keep_idx]
    if len(cand) < len(syll):
        sys.exit('★도너가 모자란다 (%d < %d)' % (len(cand), len(syll)))

    charmap = {}
    for ch, i in zip(syll, cand):
        charmap[ch] = (i, f.codes[i])
    return charmap, syll, keep


def charmap_for(ko):
    """배정표만 필요한 도구(축약기 등)를 위한 헬퍼 — 폰트를 열어 배정까지 해 준다."""
    rows = {r[0]: r for r in load_list()}
    fpath, bi = FONT_TARGETS[0]
    _, lba, size, _ = rows[fpath]
    f = Fntc(Mato(Iso(TRACK1).read(lba, size), fpath).block(bi))
    cm, _, _ = assign_donors(f, ko)
    return cm


def snapshot_charmap(charmap, f, path):
    with io.open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write('hangul\tindex\tcode\tdonor_jp\n')
        for ch in sorted(charmap):
            i, code = charmap[ch]
            fh.write('%s\t%d\t%04X\t%s\n' % (ch, i, code, f.char_of(i) or '?'))


# ---------------------------------------------------------------- 인코딩

def encode(text, charmap):
    out = bytearray()
    for ch in text:
        if ch in charmap:
            code = charmap[ch][1]
            out += bytes([code >> 8, code & 0xFF])
        else:
            out += ch.encode('cp932')
    return bytes(out)


# ---------------------------------------------------------------- 파일 패치 헬퍼

# ★★가운데정렬은 «등장인물 이름표»에만 건다 — `/1_RIG2.BIN 0x7CC88` 의 이름
#   목록(`%sN` 토큰이 대사 이름칸에 끼워 넣는 것들). 이것만 이름 뒤 남는 공백이
#   화면에 「뮤　　」처럼 그대로 드러난다.
# ⛔절대 UI 전체에 걸지 말 것 — 짧아진 번역 앞에도 공백이 들어가 **모든 메뉴의
#   들여쓰기가 오른쪽으로 밀린다**(실기: 전투 메뉴 턴종료/후퇴/로드/옵션이
#   좌측정렬에서 계단식으로 흐트러졌다). 실제로 그렇게 배포한 적이 있다.
CENTER_KEYS = {
    '5a5eedd34e',  # ミュウ
    '1b50915d3b',  # ミュウ竜
    '50b7951017',  # ラスティ
    'e48539f691',  # アスカ
    '69744e0247',  # ナズナ
    'ccd4802233',  # シラナミ
    'a6ad45f34b',  # カムイ
    'e2587ba061',  # カムイ鳥
    'f4db7e32fd',  # カムイ熊
    '5ef8121c15',  # カムイ真似
    '1837c4f1eb',  # タタラ
    '719fa91d24',  # アンジュ
    '67bd7185b6',  # キング
    'b59bbdbc26',  # ホークアイ
}


# ⛔`$` 를 쓰면 안 된다 — 파이썬 정규식의 `$` 는 **끝의 개행 «앞»에서도** 매치해서
#   꼬리 `\n` 이 잘려 나가 슬롯 길이가 1바이트 줄어든다(파일 길이가 바뀐다).
#   꼬리의 **제어토큰과 개행**을 한 덩어리로 본다. 개행 뒤에 공백을 붙이면
#   빈 줄이 하나 더 생겨 이름표 상자가 벌어진다.
TOKEN_TAIL = re.compile(rb'((?:%[A-Za-z][0-9]*|[\r\n])+)\Z')


def pad_center(b, n, pad, key=None):
    """남는 자리를 채운다. **`key` 가 `CENTER_KEYS` 에 있을 때만** 앞뒤로 나눈다.

    ⛔`pad==b'\\x00'`(대사 파일) 은 어떤 경우에도 **뒤쪽에만** 채운다 — NUL 은
      종단자라 앞에 두면 그 자리에서 문자열이 즉시 끝나버린다.
    """
    extra = n - len(b)
    if pad != b' ':
        return b + pad * extra
    if key in CENTER_KEYS:
        left = extra // 2
        return pad * left + b + pad * (extra - left)
    # ★★공백 패딩은 **꼬리 제어토큰 앞**에 넣는다 — `%b` 뒤에 붙이면 그 제어코드가
    #   패딩을 인수로 먹어 매크로가 잘못 호출된다([[feedback_pad_before_trailing_control_code]]).
    m = TOKEN_TAIL.search(b)
    if m and extra:
        return b[:m.start()] + pad * extra + m.group(1)
    return b + pad * extra


def patch_plain(rows, iso, byfile, enc, pad=b'\x00', space_slots=frozenset()):
    """일반 파일(.MAP/.MSG/.MAT, /1_RIG2.BIN 등)에 제자리 덮어쓰기.

    ★★`pad` — 남는 자리를 무엇으로 채우는가. 이게 갈래마다 다르다.
      · 대사(.MAP/.MSG/.MAT) = `b'\\x00'`
        오프셋 표로 직접 참조하므로 NUL 로 일찍 끝내도 안전하다.
      · **UI 문자열 = `b' '`(공백)**
        UI 표는 `text 00 FF` 를 **순차로 훑는** 구조다(`行動終了？\\x00\\xff`
        `ターン終了？\\x00\\xff\\xff\\xff`). 짧아진 번역 뒤를 NUL 로 채우면
        게임이 **빈 엔트리를 여러 개 더 읽어** 이후 메뉴 항목이 통째로 밀린다
        (실기: 시스템 메뉴가 깨지고 C버튼에서 크래시). 반드시 **원문과 똑같은
        바이트 길이**를 유지해야 하므로 «보이지 않는 공백»으로 채운다.

    ★★`space_slots` = {(파일, 오프셋)} — `.MAP` 안이지만 **UI 목록과 같은
      구조**라 NUL 패딩을 쓰면 안 되는 자리(선택상자 블록, `menu_blocks.py`).
      선택상자는 `문자열 00` 을 순차로 읽다가 **빈 항목(`00 00`)에서 끝나므로**,
      번역이 1바이트만 짧아도 그 자리에 종료자가 생겨 뒤 항목이 통째로
      사라진다(실기: 술집에서 「나가기」가 없어져 대화가 무한 반복).
      ⛔대사 전체를 공백 패딩으로 바꾸면 안 된다 — 꼬리 `%b` 제어코드가 패딩을
        인수로 먹는다([[feedback_pad_before_trailing_control_code]]).

    -> (patched: {file: (lba, bytes, hit수)}, skipped: [(file, off, 사유)])
    """
    patched, skipped = {}, []
    for fn in sorted(byfile):
        if fn not in rows:
            skipped.append((fn, -1, 'ISO 목록에 없다'))
            continue
        _, lba, size, _ = rows[fn]
        d = bytearray(iso.read(lba, size))
        hit = 0
        for off, n, k in sorted(byfile[fn]):
            # ★/1_RIG2.BIN 은 실행 코드가 섞인 파일 — 실측으로 확인된 데이터
            #   구간 밖은 절대 쓰지 않는다(코드일 위험).
            if fn == ui_corpus.BIN_FILE and not (
                    ui_corpus.BIN_SAFE_LO <= off <= ui_corpus.BIN_SAFE_HI):
                skipped.append((fn, off, '안전구간 밖(실행코드 위험)'))
                continue
            # ★`/0_OP.BIN`(타이틀 담당)도 코드+데이터가 섞인 실행 바이너리다.
            if fn == add_op_bin.FILE and not (
                    add_op_bin.SAFE_LO <= off <= add_op_bin.SAFE_HI):
                skipped.append((fn, off, '안전구간 밖(실행코드 위험)'))
                continue
            seg = bytes(d[off:off + n])
            if hashlib.sha1(seg).hexdigest()[:10] != k:
                skipped.append((fn, off, '원문 불일치'))
                continue
            # ★종단자는 갈래마다 다르다 — 대사·UI 는 NUL, `.PRF`(캐릭터 프로필)는
            #   파일 꼬리라 **EOF 마커 0x1A** 가 온다. 둘 다 허용한다.
            if off + n >= len(d) or d[off + n] not in (0x00, 0x1A):
                skipped.append((fn, off, '종단자 없음'))
                continue
            b = enc[k]
            if len(b) > n:
                skipped.append((fn, off, '예산 초과(%d>%d)' % (len(b), n)))
                continue
            # ★★패딩 문자는 «원본의 구조»가 정한다 — 앵커 목록에 의존하면 샌다.
            #   종단자 **다음 바이트가 NUL 이 아니면** 바로 뒤에 다른 문자열이
            #   이어진다는 뜻이고, 그 자리에 NUL 패딩을 넣으면 `00 00` 이 생겨
            #   목록이 조기 종료된다(실기: 「예」만 남고 「아니오」가 사라짐,
            #   술집·민가에서 「나가기」가 안 나옴).
            #   원본이 이미 `00 00` 인 자리에서만 NUL 로 채운다.
            nxt = d[off + n + 1] if off + n + 1 < len(d) else 0
            p = b' ' if (nxt != 0 or (fn, off) in space_slots) else pad
            d[off:off + n] = pad_center(b, n, p, k)
            assert len(d) == size, '파일 길이가 바뀌었다'
            hit += 1
        if hit:
            patched[fn] = (lba, bytes(d), hit)
    return patched, skipped


def patch_ovl(rows, iso, entries, enc, pad=b'\x00'):
    """`entries` = [(key, path, block_idx, off, n)] — mato 블록 안 자리에 제자리 덮어쓰기.

    -> (patched: {경로: (lba, bytes, hit수)}, skipped)
    """
    patched, skipped = {}, []
    by_path = {}
    for key, path, bi, off, n in entries:
        by_path.setdefault(path, {}).setdefault(bi, []).append((off, n, key))

    for path, by_bi in sorted(by_path.items()):
        if path not in rows:
            skipped.append((path, -1, 'ISO 목록에 없다'))
            continue
        _, lba, size, _ = rows[path]
        raw = iso.read(lba, size)
        m = Mato(raw, path)
        blocks = m.blocks()
        hit = 0
        for bi, spots in by_bi.items():
            blk = bytearray(blocks[bi])
            for off, n, k in sorted(spots):
                seg = bytes(blk[off:off + n])
                if hashlib.sha1(seg).hexdigest()[:10] != k:
                    skipped.append(('%s#%d' % (path, bi), off, '원문 불일치'))
                    continue
                b = enc[k]
                if len(b) > n:
                    skipped.append(('%s#%d' % (path, bi), off, '예산 초과(%d>%d)' % (len(b), n)))
                    continue
                blk[off:off + n] = pad_center(b, n, pad, k)
                hit += 1
            blocks[bi] = bytes(blk)
        if hit:
            newd = m.rebuild(blocks)
            if len(newd) != size:
                sys.exit('★%s 크기가 바뀌었다 (mato 재조립)' % path)
            patched[path] = (lba, newd, hit)
    return patched, skipped


# ---------------------------------------------------------------- 메인

def main(write):
    rows = {r[0]: r for r in load_list() if not r[3] and not r[0].endswith('/')}
    iso = Iso(TRACK1)

    ko = load_ko()
    jp = load_jp()
    ko_ui = load_ui_ko()
    jp_ui = load_ui_jp()
    print('번역 본편 %d개 문자열 / UI %d개 문자열' % (len(ko), len(ko_ui)))

    # --- 폰트 로드 (기준 = 첫 번째) ---
    fonts = []
    for fpath, bi in FONT_TARGETS:
        if fpath not in rows:
            sys.exit('★폰트 파일이 없다: %s' % fpath)
        _, lba, size, _ = rows[fpath]
        raw = iso.read(lba, size)
        m = Mato(raw, fpath)
        fonts.append([fpath, lba, size, bi, m, Fntc(m.block(bi))])
    base = fonts[0][5]
    for e in fonts[1:]:
        if e[5].codes != base.codes:
            sys.exit('★폰트 사본의 코드표가 다르다: %s' % e[0])
    print('FNTC 사본 %d개: %s' % (len(fonts), ', '.join('%s#%d' % (e[0], e[3]) for e in fonts)))

    # --- 1. 배정 (본편 + UI 통합) ---
    charmap, syll, keep = assign_donors(base, ko, ko_ui)
    miss = krglyph.coverage(''.join(syll))
    if miss:
        sys.exit('★BDF 에 없는 한글: %s' % miss)
    idxs = [charmap[c][0] for c in syll]
    print('한글 %d종 통합배정 (인덱스 %d~%d / 코드 %04X~%04X), 보존문자 %d종'
          % (len(syll), min(idxs), max(idxs),
             min(charmap[c][1] for c in syll), max(charmap[c][1] for c in syll), len(keep)))
    cmp_path = os.path.join(WORK, 'trans', 'charmap.tsv')
    snapshot_charmap(charmap, base, cmp_path)
    print('  배정표 스냅샷 -> %s' % cmp_path)

    # --- 2. 글리프 굽기 (두 벌 동일) ---
    for e in fonts:
        f = e[5]
        for ch in syll:
            f.set_glyph(charmap[ch][0], krglyph.glyph(ch, f.w, f.h))

    # ★★말줄임표 글리프 재작화 — ★한 칸에 점 세 개를 다 그린다.★
    #   1차 시도(점 하나를 셀마다 따로 찍어 `・・・` 세 칸으로 늘어놓기)는
    #   사용자가 거부 — 「말줄임표 세 개를 한 칸에 그려야지」. 그래서
    #   `・`(0x8145) 하나의 글리프 자체를 **가로점 3개짜리 말줄임표**로 다시
    #   그리고, 본문의 `・・・`/`・・` 런은 전부 **단일 `・` 한 글자**로
    #   합친다(아래 COLLAPSE 단계). `。`(마침표) 와 바닥선 높이를 맞췄다.
    DOT_ROWS = [
        '0000000000000000',
        '0000000000000000',
        '0000000000000000',
        '0000000000000000',
        '0000000000000000',
        '0000000000000000',
        '0000000000000000',
        '0110011001100000',
        '0110011001100000',
        '0000000000000000',
        '0000000000000000',
        '0000000000000000',
    ]
    dot_idx = base.index_of('・')
    if dot_idx is None:
        sys.exit('★말줄임표 글리프(・) 를 폰트에서 못 찾았다')
    dot_gray = bytes(255 if c == '1' else 0
                      for row in DOT_ROWS for c in row)
    for e in fonts:
        e[5].set_glyph(dot_idx, dot_gray)

    def garea(f):
        return bytes(f.data[f.glyph_off:f.glyph_off + f.n * f.cb])
    g0 = garea(fonts[0][5])
    for e in fonts[1:]:
        if garea(e[5]) != g0:
            sys.exit('★두 사본의 글리프가 다르다: %s' % e[0])
    print('  글리프 %d칸 × 사본 %d = 두 벌 결과 동일 확인' % (len(syll), len(fonts)))

    # --- 3. 인코딩 + 예산 검사 (본편) ---
    enc, over = {}, []
    for k, t in ko.items():
        b = encode(t, charmap)
        budget = jp[k][1]
        if len(b) > budget:
            over.append((k, len(b), budget, t))
        enc[k] = b
    if over:
        print('\n★본편 예산 초과 %d건 — 번역을 줄여야 한다' % len(over))
        for k, n, bud, t in over[:20]:
            print('   %s  %d > %d B  %r' % (k, n, bud, t[:40]))
        sys.exit(1)
    used = sum(len(enc[k]) for k in enc)
    tot = sum(jp[k][1] for k in enc)
    print('본편 예산: %d / %d B 사용 (%.1f%%), 초과 0건' % (used, tot, 100.0 * used / tot))

    # --- 3b. 인코딩 + 예산 검사 (UI) ---
    enc_ui, over_ui = {}, []
    for k, t in ko_ui.items():
        b = encode_ui(t, charmap)
        budget = jp_ui[k][1]
        if len(b) > budget:
            over_ui.append((k, len(b), budget, t))
        enc_ui[k] = b
    if over_ui:
        print('\n★UI 예산 초과 %d건 — 번역을 줄여야 한다' % len(over_ui))
        for k, n, bud, t in over_ui[:20]:
            print('   %s  %d > %d B  %r' % (k, n, bud, t[:40]))
        sys.exit(1)
    if ko_ui:
        used_ui = sum(len(enc_ui[k]) for k in enc_ui)
        tot_ui = sum(jp_ui[k][1] for k in enc_ui)
        print('UI 예산: %d / %d B 사용 (%.1f%%), 초과 0건' % (used_ui, tot_ui, 100.0 * used_ui / tot_ui))

    # --- 4. 파일별 패치 계획 (본편) ---
    refs = load_refs(set(ko))
    byfile = {}
    for k, fn, off, n in refs:
        byfile.setdefault(fn, []).append((off, n, k))
    print('\n본편 재삽입: 참조 %d건 / 파일 %d개' % (len(refs), len(byfile)))

    # ★선택상자 블록은 «빈 항목 = 목록 끝» 구조라 NUL 패딩을 쓰면 안 된다.
    space_slots = menu_blocks.slot_set()
    print('  선택상자 슬롯 %d곳은 공백 패딩(목록 조기종료 방지)' % len(space_slots))

    patched, skipped = patch_plain(rows, iso, byfile, enc, space_slots=space_slots)
    nspots = sum(v[2] for v in patched.values())
    print('  자리 %d곳 교체 / 건너뜀 %d곳' % (nspots, len(skipped)))
    if skipped:
        print('  ★건너뛴 자리 (앞 10):')
        for fn, off, why in skipped[:10]:
            print('     %-18s 0x%X  %s' % (fn, off, why))

    # --- 4b. 파일별 패치 계획 (UI) ---
    if ko_ui:
        ui_refs = load_ui_refs(set(ko_ui))
        ovl_entries, byplain = [], {}
        for k, fn, off, n in ui_refs:
            if '#' in fn:
                path, bi = fn.rsplit('#', 1)
                ovl_entries.append((k, path, int(bi), off, n))
            else:
                byplain.setdefault(fn, []).append((off, n, k))
        print('\nUI 재삽입: 참조 %d건 (OVL블록 %d / 평문파일 %d)'
              % (len(ui_refs), len(ovl_entries), sum(len(v) for v in byplain.values())))

        ovl_patched, ovl_skipped = patch_ovl(rows, iso, ovl_entries, enc_ui, pad=b' ')
        plain_patched, plain_skipped = patch_plain(rows, iso, byplain, enc_ui, pad=b' ')

        ui_hit = sum(v[2] for v in ovl_patched.values()) + sum(v[2] for v in plain_patched.values())
        ui_skip = ovl_skipped + plain_skipped
        print('  UI 자리 %d곳 교체 / 건너뜀 %d곳' % (ui_hit, len(ui_skip)))
        if ui_skip:
            print('  ★UI 건너뛴 자리 (앞 10):')
            for fn, off, why in ui_skip[:10]:
                print('     %-18s 0x%X  %s' % (fn, off, why))

        for fn, v in ovl_patched.items():
            patched[fn] = v
        for fn, v in plain_patched.items():
            patched[fn] = v

    # --- 5. 폰트 재조립 ---
    for fpath, lba, size, bi, m, f in fonts:
        blocks = m.blocks()
        blocks[bi] = f.to_bytes()
        newd = m.rebuild(blocks)
        if len(newd) != size:
            sys.exit('★%s 크기가 바뀌었다 %d != %d' % (fpath, len(newd), size))
        patched[fpath] = (lba, newd, 0)
    print('\n  폰트 %d개 재조립 (크기 유지)' % len(fonts))

    total_sectors = sum((len(v[1]) + 2047) // 2048 for v in patched.values())
    print('\n쓰기 대상: 파일 %d개 / 약 %d 섹터' % (len(patched), total_sectors))

    if not write:
        print('\n[미리보기만 — 디스크는 안 건드렸다. 실제 빌드는 --write]')
        return

    # --- 6. 굽기 ---
    print('\n원본 복사 -> %s' % OUT_TRACK1)
    discbuild.fresh_copy()
    with open(OUT_TRACK1, 'r+b') as fh:
        for fn in sorted(patched):
            lba, data, _ = patched[fn]
            discbuild.write_file(fh, lba, data)
    print('  %d개 파일 기록 (EDC/ECC 재계산)' % len(patched))

    # --- 7. 되읽기 검증 ---
    out_iso = Iso(OUT_TRACK1)
    bad = 0
    for fn in sorted(patched):
        lba, data, _ = patched[fn]
        got = out_iso.read(lba, len(data))
        if got != data:
            bad += 1
            print('   ★되읽기 불일치: %s' % fn)
    print('되읽기 검증: 파일 %d개 중 불일치 %d' % (len(patched), bad))
    if bad:
        sys.exit(1)
    print('\n완료. 오프닝(7인위원회) + 기술/아이템 도움말 + 일기 + 옵션/전투/스킬 메뉴를 볼 것.')


if __name__ == '__main__':
    main('--write' in sys.argv)

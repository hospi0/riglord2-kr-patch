# -*- coding: utf-8 -*-
"""추출에서 빠졌던 두 갈래를 코퍼스에 등록하고 번역을 채운다.

① **시설 이름표**(`酒場` 등 7종) — `.MAP` 선택상자 블록의 첫 조각.
   `corpus2.is_real()` 이 «가나 없으면 4자 이상» 을 요구해 2글자 한자 라벨을
   통째로 노이즈로 버렸다. 실기에서 「킨場」으로 깨져 보였다.
② **기술표**(`/1_RIG2.BIN` 36바이트 레코드) 중 미등재분 — 이름 앞에 NUL 이
   없어 NUL 순차 스캐너가 조각 시작점을 못 잡은 자리들(세션3 후속2 버그4와 동형).

★자리는 스캔이 아니라 **원문 raw 바이트 정확 일치**로 잡는다. key 는
  `sha1(raw)[:10]` — `build_kr.patch_plain` 이 그대로 대조한다.
"""
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list
import menu_blocks

# ---------------------------------------------------------------- 번역표
# 예산 = 원문 바이트. 한글 1자=2B(도너 글리프).
PLACE = {
    '酒場': '술집',
    '民家': '민가',
    '闘技場': '투기장',
    '武器屋': '무기점',
    '防具屋': '방어점',      # 「방어구점」(8B)은 6B 슬롯에 안 들어간다
    '道具屋': '도구점',
    '雑貨屋': '잡화점',
}

# ★한자 항목은 도너로 뺏긴 칸을 가리켜 «깨져» 보인다 — 우선 처리 대상.
#   반각 가타카나는 1바이트 코드라 도너 영향이 없다(그냥 미번역).
SKILL = {
    # ⛔`技が完成した！` 는 넣지 않는다 — 이미 등록된 `新しい技が完成した！`(20B)의
    #   **부분 문자열**이라 자리가 겹쳐 뒤에 오는 쪽이 「원문 불일치」로 죽는다.
    '爆裂斬': '폭렬참',
    '放す': '놓기',
    'ｳｨﾝﾄﾞ': '윈드',
    'ﾌﾚｱｽﾄﾗｲｸ': '화염강타',
    'ﾀﾞｲﾌﾞｱﾀｯｸ': '강습공격',
    'ｱｰｽﾀﾞｲﾌﾞ': '대지강습',
    'ｿﾆｯｸﾀﾞｲﾌﾞ': '음속강습',
    'ﾃﾗｰﾎﾞｲｽ': '땅울림',
    'ﾌﾚｲﾑｱﾛｰ': '불화살',
    'ﾌﾞﾚｲｸｼｮｯﾄ': '파쇄사격',
    'ｸｪｲｸｽﾀﾝﾌﾟ': '지진밟기',
    'ﾋｰﾙｽﾀﾝﾌﾟ': '치유밟기',
    'ﾌﾚｲﾑｽﾛｰ': '화염구',
    'ｶﾞｽ': '독',
    'ｸﾞﾗﾋﾞﾃｨﾌﾟﾚｽ': '중력압',
    'ｼﾞｬｯｼﾞﾒﾝﾄ': '심판',
}

SKILL_LO, SKILL_HI, STRIDE, NAMELEN = 0x8F000, 0x92000, 36, 15
SKILL_ANCHOR = 0x90370                     # 실측 레코드 정렬 기준
JP = re.compile(r'[぀-ヿ一-鿿ｦ-ﾟ]')


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')


def collect_places():
    """-> {key: (jp, nbytes, [(file, off, n)])}"""
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    cache, out = {}, {}
    for path, items in menu_blocks.scan():
        if path not in cache:
            _, lba, sz, _ = rows[path]
            cache[path] = iso.read(lba, sz)
        d = cache[path]
        for off, n, t in items:
            if t not in PLACE:
                continue
            raw = d[off:off + n]
            k = hashlib.sha1(raw).hexdigest()[:10]
            out.setdefault(k, (t, n, []))[2].append((path, off, n))
    return out


def collect_skills():
    rows = {r[0]: r for r in load_list()}
    _, lba, sz, _ = rows['/1_RIG2.BIN']
    d = Iso(TRACK1).read(lba, sz)
    lo = SKILL_ANCHOR - ((SKILL_ANCHOR - SKILL_LO) // STRIDE) * STRIDE
    out = {}
    off = lo
    while off < SKILL_HI:
        raw = d[off:off + NAMELEN]
        nul = raw.find(b'\x00')
        if nul > 0:
            try:
                t = raw[:nul].decode('cp932')
            except UnicodeDecodeError:
                t = None
            if t and t in SKILL:
                r = raw[:nul]
                k = hashlib.sha1(r).hexdigest()[:10]
                out.setdefault(k, (t, nul, []))[2].append(('/1_RIG2.BIN', off, nul))
        off += STRIDE
    return out


def append(path, lines):
    with io.open(path, 'a', encoding='utf-8', newline='') as f:
        for l in lines:
            f.write(l + '\n')


def main(write):
    places = collect_places()
    skills = collect_skills()

    print('시설 이름표 %d종 / 참조 %d곳'
          % (len(places), sum(len(v[2]) for v in places.values())))
    print('기술표     %d종 / 참조 %d곳'
          % (len(skills), sum(len(v[2]) for v in skills.values())))

    bad = []
    for k, (jp, n, refs) in list(places.items()) + list(skills.items()):
        ko = PLACE.get(jp) or SKILL.get(jp)
        if size(ko) > n:
            bad.append((jp, ko, size(ko), n))
    if bad:
        print('★예산 초과 — 아무것도 쓰지 않았다:')
        for jp, ko, a, b in bad:
            print('   %r -> %r  %dB > %dB' % (jp, ko, a, b))
        return
    print('예산 초과 0건')

    # 이미 등록된 key 는 건너뛴다(중복 실행 안전)
    have_s, have_u = set(), set()
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            have_s.add(line.split('\t', 1)[0])
    with io.open(os.path.join(WORK, 'trans', 'ui_strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            have_u.add(line.split('\t', 1)[0])

    s_rows, r_rows, ko_rows = [], [], []
    for k, (jp, n, refs) in sorted(places.items()):
        if k in have_s:
            continue
        ko = PLACE[jp]
        s_rows.append('%s\t%d\t%d\t%d\t\t%s\t' % (k, len(refs), n, len(jp), esc(jp)))
        for fn, off, nb in refs:
            r_rows.append('%s\t%s\t%d\t%d' % (k, fn, off, nb))
        ko_rows.append('%s\t%s' % (k, esc(ko)))

    u_rows, ur_rows = [], []
    for k, (jp, n, refs) in sorted(skills.items()):
        if k in have_u:
            continue
        ko = SKILL[jp]
        u_rows.append('%s\t%d\t%d\t%d\t\t0\t%s\t%s'
                      % (k, len(refs), n, len(jp), esc(jp), esc(ko)))
        for fn, off, nb in refs:
            ur_rows.append('%s\t%s\t%d\t%d' % (k, fn, off, nb))

    print('추가 예정: strings %d / refs %d / ko %d / ui_strings %d / ui_refs %d'
          % (len(s_rows), len(r_rows), len(ko_rows), len(u_rows), len(ur_rows)))
    if not write:
        print('[미리보기 — --write 로 기록]')
        return

    T = lambda n: os.path.join(WORK, 'trans', n)
    append(T('strings.tsv'), s_rows)
    append(T('refs.tsv'), r_rows)
    append(T('ko_final.tsv'), ko_rows)
    append(T('ko_shrunk.tsv'), ko_rows)
    append(T('ui_strings.tsv'), u_rows)
    append(T('ui_refs.tsv'), ur_rows)
    print('기록 완료')


if __name__ == '__main__':
    main('--write' in sys.argv)

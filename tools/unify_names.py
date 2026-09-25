# -*- coding: utf-8 -*-
"""아이템·기술 이름을 **음차 우선**으로 되돌리고 필드 크기에 맞춰 등록한다.

★★그동안 «원문 문자열 길이»를 예산으로 삼는 바람에 `ｽﾄﾗｲｸ→타격`, `ﾏﾗｶｲﾄ→공작석`
  처럼 억지 의미역·약칭이 생겼다. 실제 한계는 표의 **고정 이름 필드**다:

    아이템표  0x91E00~0x93000  스트라이드 40B  이름 필드 **22B**
    기술표    0x8F000~0x92000  스트라이드 36B  이름 필드 **15B**

  ⛔필드를 넘기면 다음 필드(수치)를 덮어써 아이템이 망가진다.
★사용자 원칙: **가타카나 외래어는 음차 우선**([[feedback_translit_over_native_loanwords]]).
  한자·화어 이름(`剣の舞い`, `雄叫び`)은 뜻으로 옮긴다.
★`bytes` 를 필드 크기로 늘리면 `build_kr` 의 원문 검증 `sha1(d[off:off+n])` 이
  어긋나므로 **key 를 같은 범위로 다시 계산**해야 한다.
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

NAMES = {
    # ---- 기술: 타격/돌진 계열
    'ｽﾄﾗｲｸ': '스트라이크', 'ﾍﾋﾞｰｽﾄﾗｲｸ': '헤비스트라이크', 'Jｽﾄﾗｲｸ': 'J스트라이크',
    # 「플레어스트라이크」는 16B 라 14B 필드에 안 들어간다 — 끝 음절을 「잌」으로 줄여 7음절(14B)에 맞춘다
    'ﾌﾚｱｽﾄﾗｲｸ': '플레어스트라잌', 'ｽﾗｯｼｭ': '슬래시',
    'ﾄﾞﾗｲﾌﾞ': '드라이브', 'ﾋﾞｰﾄﾄﾞﾗｲﾌﾞ': '비트드라이브', 'ｼｬｲﾝﾄﾞﾗｲﾌﾞ': '샤인드라이브',
    'ｸﾗｯｼｭ': '크래시', 'ﾊｰﾄﾞｸﾗｯｼｭ': '하드크래시', 'ﾊﾞｽﾀｸﾗｯｼｭ': '버스터크래시',
    'ｿｰﾄﾞﾗｯｼｭ': '소드러시',
    # ---- 기술: 강습(ダイブ)·브레스
    'ﾀﾞｲﾌﾞｱﾀｯｸ': '다이브어택', 'ﾋﾞｰｽﾄﾀﾞｲﾌﾞ': '비스트다이브', 'ｿﾆｯｸﾀﾞｲﾌﾞ': '소닉다이브',
    'ﾊﾟﾆｯｸﾀﾞｲﾌﾞ': '패닉다이브', 'ﾊﾞｰｽﾄﾀﾞｲﾌﾞ': '버스트다이브', 'ﾎｰﾘｰﾀﾞｲﾌﾞ': '홀리다이브',
    'ｱｰｽﾀﾞｲﾌﾞ': '어스다이브', 'ｽﾙｰﾀﾞｲﾌﾞ': '스루다이브',
    'ﾄﾞﾗｺﾞﾝﾀﾞｲﾌﾞ': '드래곤다이브', 'ﾄﾞﾗｺﾞﾝﾌﾞﾚｽ': '드래곤브레스',
    'ﾃﾞｽﾌﾞﾚｽ': '데스브레스', 'ｱｰｸﾌﾞﾚｽ': '아크브레스',
    'ﾘﾄﾙｽﾄｰﾑ': '리틀스톰', 'ﾃﾗｰﾎﾞｲｽ': '테라보이스', 'ｳｨﾝﾄﾞ': '윈드',
    'ｳｨﾝﾄﾞｶｯﾀｰ': '윈드커터',
    # ---- 기술: 사격(ショット/アロー)
    'ｱﾛｰｼｮｯﾄ': '애로우샷', 'ｲﾅｽﾞﾏｼｮｯﾄ': '이나즈마샷', 'ﾛﾝｸﾞｼｮｯﾄ': '롱샷',
    'ｽﾊﾟｲﾗﾙｱﾛｰ': '스파이럴애로우', 'ﾌﾚｲﾑｱﾛｰ': '플레임애로우', 'ｵﾒｶﾞｱﾛｰ': '오메가애로우',
    'ﾏﾙﾁｼｮｯﾄ': '멀티샷', 'ﾎｰﾘｰｱﾛｰ': '홀리애로우', 'ﾊﾞｰｽﾄｼｮｯﾄ': '버스트샷',
    'ﾌﾞﾚｲｸｼｮｯﾄ': '브레이크샷',
    # ---- 기술: 타격(발톱·펀치·스탬프)
    'ｷﾙｸﾛｰ': '킬클로', 'ｷﾗｰﾌｧﾝｸﾞ': '킬러팽', 'ｽﾀﾝﾌﾟ': '스탬프',
    'ｸｪｲｸｽﾀﾝﾌﾟ': '퀘이크스탬프', 'ﾋｰﾙｽﾀﾝﾌﾟ': '힐스탬프',
    'ｷﾗｰﾊﾟﾝﾁ': '킬러펀치', 'ﾜｲﾙﾄﾞﾊﾟﾝﾁ': '와일드펀치',
    'ﾌﾚｲﾑｽﾛｰ': '플레임스로', 'ｶﾞｽ': '가스', 'ｶｳﾝﾀｰ': '카운터',
    # ---- 기술: 마법
    'ﾌｧｲｱﾎﾞｰﾙ': '파이어볼', 'ﾌｧｲｱﾌﾞﾗｽﾄ': '파이어블래스트', 'ﾍﾙｽﾞﾌｧｲｱ': '헬즈파이어',
    'ｻﾝﾀﾞｰ': '썬더', 'ｻﾝﾀﾞｰﾌﾞﾗｽﾄ': '썬더블래스트', 'ｻﾝﾀﾞｰｽﾄｰﾑ': '썬더스톰',
    'ﾌﾘｰｼﾞﾝｸﾞ': '프리징', 'ﾌﾘｰｽﾞﾌﾞﾗｽﾄ': '프리즈블래스트', 'ﾌﾘｰｽﾞｽﾄｰﾑ': '프리즈스톰',
    'ｸﾞﾗﾋﾞﾃｨﾌﾟﾚｽ': '그래비티프레스', 'ｼﾞｬｯｼﾞﾒﾝﾄ': '저지먼트',
    'ﾌﾞﾗｯｸｻﾊﾞｽ': '블랙사바스', 'ｽﾀｰﾗｲﾄ': '스타라이트', 'ﾀﾞｰｸﾏﾀｰ': '다크매터',
    'ｴﾅｼﾞｰﾄﾞﾚｲﾝ': '에너지드레인', 'ﾏｼﾞｯｸﾄﾞﾚｲﾝ': '매직드레인', 'ｻｸﾘﾌｧｲｽ': '새크리파이스',
    'ｽﾄﾛﾝｸﾞ': '스트롱', 'ｽﾄﾛﾝｸﾞﾙ': '스트롱글', 'ｽﾓｰﾗﾙ': '스모랄',
    'ﾑｰﾌﾞｸｨｯｸ': '무브퀵', 'ﾑｰﾌﾞｽﾛｰ': '무브슬로', 'ｽｺｰﾌﾟｱｲ': '스코프아이',
    'ﾌﾞﾛｯｸ': '블록', 'ﾌﾗｲｻｰ': '플라이서', 'ｸﾞﾗﾋﾞﾄﾝ': '그래비톤', 'ｽﾘｰﾌﾟ': '슬립',
    'ﾎｰﾘｰｷｭｱ': '홀리큐어', 'ｷｭｱﾋｰﾘﾝｸﾞ': '큐어힐링', 'ﾘﾊﾞｰｽｷｭｱ': '리버스큐어',
    'ﾋｰﾘﾝｸﾞ': '힐링', 'ﾒｶﾞﾋｰﾘﾝｸﾞ': '메가힐링', 'ｷﾞｶﾞﾋｰﾘﾝｸﾞ': '기가힐링',
    'ｱｰｸﾋｰﾘﾝｸﾞ': '아크힐링', 'ｵﾒｶﾞﾋｰﾘﾝｸﾞ': '오메가힐링',
    'ﾎｰﾘｰｳｪｰﾌﾞ': '홀리웨이브', 'ﾎｰﾘｰｱｰｸ': '홀리아크',
    '魔法ｼｰﾙﾄﾞ': '마법실드', '保護ｼｰﾙﾄﾞ': '보호실드', '回復ｼｰﾙﾄﾞ': '회복실드',
    # ---- 기술: 한자·화어는 뜻으로
    '剣の舞い': '검의 춤', '熊の踊り': '곰의 춤', '雄叫び': '함성', '気合い': '기합',
    '手投げ弾': '수류탄', '金を盗む': '돈 훔치기', '爆裂斬': '폭렬참', '放す': '놓기',
    # ---- 아이템
    'ﾊﾟﾜｰﾘｽﾄ': '파워리스트', 'ﾗｲﾄﾜｰﾄﾞ': '라이트워드', 'ｿｳﾙﾜｰﾄﾞ': '소울워드',
    'ﾏｲﾝﾄﾞﾜｰﾄﾞ': '마인드워드', 'ｽﾀｰﾜｰﾄﾞ': '스타워드', 'ﾌﾞﾗｯｸﾜｰﾄﾞ': '블랙워드',
    'ｱﾛｰｽﾄｰﾝ': '애로우스톤', 'ｶﾞﾝﾄﾚｯﾄ': '건틀렛', 'ﾑｰﾝｵｰﾌﾞ': '문오브',
    'ｶﾞﾙﾏﾝｵｰﾌﾞ': '갈만오브', 'ゲートキー': '게이트키', '風のﾒﾀﾞﾘｵﾝ': '바람의 메달리온',
    'アムリタ': '암리타', 'パール': '펄', '蒼のパール': '푸른 펄',
    'アメジスト': '아메지스트', 'オパール': '오팔', 'エメラルド': '에메랄드',
    '隠れ蓑の灰': '은신 도롱이 재', '身代{ﾜﾘﾉ}符': '대역의 부적', '空の水桶': '빈 물통',
}

# 대사 쪽 표기도 같이 맞춘다(현재 표기 → 통일 표기)
DLG = [
    ('스코프아이', '스코프아이'),          # 이미 일치 — 자리표시
    ('은신 도롱이 재', '은신 도롱이 재'),
]


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)


def esc(s):
    return (s.replace('\\', '\\\\').replace('\r', '\\r')
             .replace('\n', '\\n').replace('\t', '\\t'))


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def field_room(d, off, n):
    z = 0
    while off + n + z < len(d) and d[off + n + z] == 0:
        z += 1
    return n + z - 1              # 마지막 NUL 하나는 종단자로 남긴다


def main(write):
    rows = {r[0]: r for r in load_list()}
    _, lba, sz, _ = rows['/1_RIG2.BIN']
    d = Iso(TRACK1).read(lba, sz)

    T = lambda x: os.path.join(WORK, 'trans', x)
    head_s, ui = None, []
    with io.open(T('ui_strings.tsv'), encoding='utf-8') as f:
        head_s = next(f).rstrip('\n')
        for line in f:
            if line.strip():
                ui.append(line.rstrip('\n').split('\t'))

    # ui_refs 를 key -> [(줄인덱스)] 로
    rl = io.open(T('ui_refs.tsv'), encoding='utf-8').read().split('\n')
    refs = [x.split('\t') for x in rl[1:] if x.strip()]
    off_by_key = {}
    for a in refs:
        if len(a) >= 4 and a[1] == '/1_RIG2.BIN':
            off_by_key.setdefault(a[0], []).append(int(a[2]))

    plan, bad, same = [], [], 0
    for a in ui:
        if len(a) < 8:
            continue
        jp = unesc(a[6])
        if jp not in NAMES:
            continue
        ko = NAMES[jp]
        if unesc(a[7]) == ko:
            same += 1
            continue
        offs = off_by_key.get(a[0]) or []
        if not offs:
            continue
        room = min(field_room(d, o, int(a[2])) for o in offs)
        if size(ko) > room:
            bad.append((jp, ko, size(ko), room))
            continue
        plan.append((a[0], jp, unesc(a[7]), ko, room, offs))

    print('이름 %d개 변경 예정 (이미 일치 %d)' % (len(plan), same))
    for k, jp, old, ko, room, offs in plan:
        print('  %-16r 필드%2dB  %-14r -> %r' % (jp, room, old, ko))
    if bad:
        print('★필드 초과 — 아무것도 쓰지 않았다:')
        for jp, ko, s, r in bad:
            print('   %r -> %r  %dB > %dB' % (jp, ko, s, r))
        return
    if not write:
        print('[미리보기 — --write 로 기록]')
        return

    upd = {k: (room, ko) for k, jp, old, ko, room, offs in plan}
    # ui_strings 갱신 + key 재계산
    remap = {}
    out_s = [head_s]
    for a in ui:
        a = list(a)
        if a[0] in upd:
            room, ko = upd[a[0]]
            offs = off_by_key[a[0]]
            newk = hashlib.sha1(d[offs[0]:offs[0] + room]).hexdigest()[:10]
            remap[a[0]] = (newk, room)
            a[0], a[2], a[7] = newk, str(room), esc(ko)
        out_s.append('\t'.join(a))
    io.open(T('ui_strings.tsv'), 'w', encoding='utf-8', newline='').write(
        '\n'.join(out_s) + '\n')

    out_r = [rl[0]]
    for a in refs:
        a = list(a)
        if a[0] in remap:
            newk, room = remap[a[0]]
            a[0], a[3] = newk, str(room)
        out_r.append('\t'.join(a))
    io.open(T('ui_refs.tsv'), 'w', encoding='utf-8', newline='').write(
        '\n'.join(out_r) + '\n')
    print('기록 완료 (%d개)' % len(plan))


if __name__ == '__main__':
    main('--write' in sys.argv)

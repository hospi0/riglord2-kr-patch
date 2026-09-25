# -*- coding: utf-8 -*-
"""`my files/완료/todo_*.tsv`(사용자 수기 번역 완료본)를 정규화해서
`ko_final.tsv`/`ko_shrunk.tsv` 에 병합한다.

`merge_todo.py` 의 확장판 — 완료본에 실제로 있던 문제를 전부 처리한다.

★jp/bytes/token 은 **원본 `my files/transtodo/`** 를 정본으로 쓴다.
  완료본은 표계산기를 거치며 일부 행의 jp 열에 따옴표가 덧붙고(4행),
  ko 안의 CR 때문에 레코드가 물리줄로 쪼개진 것(3조각)이 있다.

처리 순서
  1. 스킵 판정 — 빈 ko / ko==jp(노이즈 원문 그대로) / 「[손상된 데이터…]」류
     번역불가 표기. 이 행들은 **아무것도 쓰지 않는다**(원문 바이트 유지).
  2. 토큰 교정 — 앞에 잘못 붙은 `%b`/`%z` 제거, 빠뜨린 꼬리 `%b` 복원.
  3. 문장부호 정규화 — 기존 코퍼스 관행에 맞춘다.
     `…`→`・`, `・{2,}`→`・`, `!`→`！`, `?`→`？`, `~`→`～`,
     `！？` 뒤 공백 삭제, 줄 끝 공백 삭제.
  4. 용어·인명 통일 — `GLOSSARY`(사용자 확정).
  5. 검사 — 예산·토큰·줄폭·cp932·금칙문자. 하나라도 걸리면 목록만 찍고 종료.

사용: `python merge_done.py`          (검사만)
      `python merge_done.py --write`  (통과 시 병합)
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK
from shrink_ko import rewrap
from rewrite_done import REWRITE

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'my files')
DONE_DIR = os.path.join(BASE, '완료')
ORIG_DIR = os.path.join(BASE, 'transtodo')

TOKEN_RE = re.compile(r'%[A-Za-z][0-9]*')
KANA = re.compile(r'[\u3040-\u309F\u30A0-\u30FA\u30FD-\u30FF\uFF66-\uFF9D]')
JAMO = re.compile(r'[\u1100-\u11FF\u3130-\u318F\uA960-\uA97F]')

# 번역불가·손상 표기 (사용자가 직접 적어 넣은 것) → 그 행은 원문 유지
UNTRANSLATABLE = re.compile(r'\[(손상된 데이터|원문 손상)')

# ---------------------------------------------------------------- 용어 통일
# ★사용자 확정(2026-08-16): ドラグーン=드래군 / ディアーネ=디아네 / マラカイト=말라카이트
#   나머지는 «기존 코퍼스 다수»를 따른다. 긴 표기부터 적용해야 부분치환이 안 난다.
GLOSSARY = [
    # (잘못 쓴 표기, 확정 표기)
    ('칠인 위원회', '７인위원회'),
    ('칠인위원회', '７인위원회'),
    ('7인 위원회', '７인위원회'),
    ('7인위원회', '７인위원회'),
    ('카카르크랑', '카칼클랜'),
    ('카카르크란', '카칼클랜'),
    ('크리카라', '쿠리카라'),
    ('오르토마', '오르트마'),
    ('올토마', '오르트마'),
    ('카오스 게이트', '카오스게이트'),
    ('갈만 오브', '갈만오브'),
    ('드라군', '드래군'),
    ('디아느', '디아네'),
    ('마라카이트', '말라카이트'),
    ('가르자드', '갈자드'),
    ('안쥬', '앙주'),
    ('라스티', '러스티'),
    ('카다르', '카달'),
    ('뮤우', '뮤'),
    ('잘마', '자르마'),
    ('자루마', '자르마'),
    ('봉래', '호라이'),
    ('아로스톤', '애로우스톤'),
    ('마른 나무', '고목'),         # HL00 枯木 — 예산이 빠듯해 짧은 한자어로(-6B/회)
    # 인물 말버릇 — 나즈나는 «인 거야»로 굳어 있다(기존 45곳)
    ('인 거다냐', '인 거야'),
    ('거다냐', '거야'),
]

# 개별 수정 — 기계 규칙으로 못 잡는 것(원문 잔재·낱자모)
MANUAL = {
    # `・・・か。` 의 `か` 가 번역 안 되고 남았다
    '6418692212': ('없어・・・か.', '없어・・・.'),
    # 낱자모 ㄴ 단독 사용 → cp932 인코딩 실패로 빌드가 죽는다
    '14ab0b4a55': ('헤헤~ㄴ다,', '헤헤~,'),
}


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def esc(s):
    return (s.replace('\\', '\\\\').replace('\n', '\\n')
             .replace('\r', '\\r').replace('\t', '\\t'))


def size(t):
    """cp932 바이트 수. 한글은 도너 글리프(2바이트)로 나간다."""
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def cells(line):
    """화면 칸 수 — 토큰은 안 찍히므로 뺀다(반각도 한 칸으로 센다: 실측 규약)."""
    return len(TOKEN_RE.sub('', line))


# ---------------------------------------------------------------- 읽기

def read_dir(d, keys=None):
    rows, stray = {}, []
    for n in sorted(os.listdir(d)):
        if not (n.startswith('todo_') and n.endswith('.tsv')):
            continue
        with io.open(os.path.join(d, n), encoding='utf-8') as f:
            hdr = next(f).rstrip('\n').split('\t')
            idx = {x: i for i, x in enumerate(hdr)}
            for lineno, line in enumerate(f, 2):
                a = line.rstrip('\n').split('\t')
                if len(a) < 6 or (keys is not None and a[idx['key']] not in keys):
                    stray.append((n, lineno, line.rstrip('\n')))
                    continue
                while len(a) < 7:
                    a.append('')
                rows[a[idx['key']]] = dict(
                    key=a[idx['key']], file=a[idx['file']], bytes=int(a[idx['bytes']]),
                    token=a[idx['token']], jp=unesc(a[idx['jp']]), ko_raw=a[idx['ko']])
    return rows, stray


# ---------------------------------------------------------------- 정규화

def strip_quotes(s):
    """표계산기가 덧씌운 CSV 따옴표 벗기기."""
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('""', '"')
    return s


def fix_tokens(ko, jp):
    """토큰 열을 원문과 같게 맞춘다. 실제로 나온 어긋남은 두 갈래뿐이다.
      · 앞에 없던 `%b`/`%z` 를 덧붙였다  → 앞의 여분 토큰 삭제
      · 꼬리 `%b` 를 빠뜨렸다            → 복원
    """
    jt = TOKEN_RE.findall(jp)
    # 1) 선두 여분 토큰
    while True:
        kt = TOKEN_RE.findall(ko)
        if len(kt) <= len(jt):
            break
        m = TOKEN_RE.match(ko)
        if not m:
            break
        ko = ko[m.end():]
    # 2) 꼬리 토큰 복원
    while TOKEN_RE.findall(ko) != jt:
        kt = TOKEN_RE.findall(ko)
        if len(kt) >= len(jt):
            break
        tail = jt[len(kt):]
        if tail != [jt[-1]] or not jp.endswith(jt[-1]):
            break
        ko += jt[-1]
    return ko


def normalize(ko):
    ko = ko.replace('\u2026', '\u30fb')             # … -> ・
    ko = re.sub('\u30fb{2,}', '\u30fb', ko)          # ・・・ -> ・
    ko = ko.replace('!', '！').replace('?', '？').replace('~', '～')
    ko = re.sub('([！？・」』】）])[ \u3000]+', r'\1', ko)      # ！？ 뒤 공백 삭제 (⛔`,`·`.` 는 제외 — 기존 코퍼스가 `, ` 를 2,373곳에 쓴다)
    ko = re.sub('[ ]+\n', '\n', ko)                  # 줄 끝 공백 삭제
    ko = re.sub('[ ]+$', '', ko)
    for a, b in GLOSSARY:
        ko = ko.replace(a, b)
    return ko


# ---------------------------------------------------------------- 예산 축약
# ★전프로젝트 원칙([[feedback_no_space_after_punct]])의 삭제 우선순위를 그대로 쓴다.
#   마침표 → 부호 뒤 공백 → 쉼표 → (그래도 안 되면) 수기 축약.
#   ⛔한꺼번에 다 지우지 않는다 — **맞을 때까지만** 깎아야 원문의 호흡이 덜 상한다.

# 상투 표현 축약(인물 어투가 안 바뀌는 것만). 긴 것부터.
PHRASE = [
    ('빠져나가시겠습니까？', '빠져나갈까요？'),
    ('나아가시겠습니까？', '나아갈까요？'),
    ('돌아가시겠습니까？', '돌아갈까요？'),
    ('들어가시겠습니까？', '들어갈까요？'),
    ('올라가시겠습니까？', '올라갈까요？'),
    ('내려가시겠습니까？', '내려갈까요？'),
    ('하시겠습니까？', '할까요？'),
]

# 문미 마침표 — 줄 끝 / 토큰 앞 / 문자열 끝. 소수점은 앞글자 조건으로 보호.
DOT = re.compile(r'(?<=[가-힣・！？」』】）])\.(?=$|\n|%)')
# ⛔쉼표를 «통째로» 지우면 낱말이 붙는다(`따위，긴`→`따위긴`,
#   [[feedback_no_space_after_punct]]). 그래서 지우는 건 **쉼표 뒤 공백**뿐이고,
#   쉼표 자체는 낱말 경계로 남긴다. 어느 쪽을 지워도 절약은 똑같이 1B 다.
COMMA_SP = re.compile(r'(?<=[가-힣]), ')          # 쉼표 + 공백 -> 쉼표


# 축약형 — 뜻도 말투도 안 바뀌는 한국어 준말만 넣는다. **맨 뒤부터 하나씩** 건다.
# ⛔인물의 말버릇(`～인 것이다～제`, `～인 거야` 등)을 건드리면 어투가 무너지므로
#   `것이다` 류는 뒤에 말버릇 꼬리가 붙지 않은 자리에서만 바꾼다(TIC 로 막는다).
TIC = ('～제', '인 거', '그런 거', '거다냐', '것이다냐')
CONTRACT = [
    ('끼워 넣었다', '꼈다'),        # KD00 아이템 삽입 연출 — 반복이 많아 -8B/회
    ('것 같습니다', '듯합니다'),
    ('것 같아요', '듯해요'),
    ('것 같군요', '듯하군요'),
    ('것 같다', '듯하다'),
    ('것 같은데', '듯한데'),
    ('것 같아', '듯해'),
    ('무엇인가', '뭔가'),
    ('무엇을', '뭘'),
    ('무엇이', '뭐가'),
    ('하고 있는', '하는'),
    ('하고 있다', '한다'),
    ('되어 있', '돼 있'),
    ('그렇게', '그리'),
    ('것입니다', '겁니다'),
    ('것이었', '거였'),
    ('것이에요', '거예요'),
    ('것이다', '거다'),
    ('것이야', '거야'),
    ('것이지', '거지'),
    ('것을', '걸'),
    ('것은', '건'),
]
# ⛔`것이`→`게` 는 넣지 않는다 — `것이었군요`가 `게었군요`가 된다(실제로 그랬다).


def _contract(t, budget):
    for a, b in CONTRACT:
        # 뒤에서부터 훑되, 말버릇 자리는 건너뛰고 그 앞 것을 계속 본다
        pos = len(t)
        while size(t) > budget:
            i = t.rfind(a, 0, pos)
            if i < 0:
                break
            if any(t[i + len(a):].startswith(x) for x in TIC):
                pos = i
                continue
            t = t[:i] + b + t[i + len(a):]
            pos = i
    return t


def _last_sub(pat, repl, t):
    """**맨 뒤 한 곳만** 치환. 없으면 None."""
    ms = list(pat.finditer(t))
    if not ms:
        return None
    m = ms[-1]
    return t[:m.start()] + repl + t[m.end():]


def shrink(t, budget):
    """예산에 맞을 때까지만 깎는다."""
    for a, b in PHRASE:
        if size(t) <= budget:
            break
        t = t.replace(a, b)
    for pat, repl in ((DOT, ''), (COMMA_SP, ',')):
        while size(t) > budget:
            n = _last_sub(pat, repl, t)
            if n is None:
                break
            t = n
    return _contract(t, budget)


# ⛔조사(를/을/가/이) 자동 생략은 넣지 않는다 — 정규식만으로는 «목적격 조사»와
#   «동사 관형형 어미(닿을·먹을 등)」·«명사 끝 글자」를 구분할 수 없어
#   「닿을 정도」→「닿 정도」, 「편이 좋다」→「편 좋다」처럼 문법을 깬다(실제로 발생).
#   남는 초과는 프로젝트 관례대로 **수기 표**(`rewrite_done.REWRITE`)로 처리한다.


# ---------------------------------------------------------------- 본체

def build():
    orig, _ = read_dir(ORIG_DIR)
    done, stray = read_dir(DONE_DIR, keys=set(orig))

    have = set()
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        with io.open(os.path.join(WORK, 'trans', fn), encoding='utf-8') as f:
            next(f)
            for line in f:
                have.add(line.split('\t', 1)[0])

    out, skipped, errors = [], [], []
    for k in sorted(orig):
        o = orig[k]
        jp = o['jp']
        ko = unesc(strip_quotes(done[k]['ko_raw'] if k in done else ''))

        if k in have:
            skipped.append((k, o['file'], '이미 병합됨'))
            continue
        if not ko.strip():
            skipped.append((k, o['file'], '빈칸(노이즈로 판단)'))
            continue
        if ko.strip() == jp.strip():
            skipped.append((k, o['file'], 'ko==jp(원문 그대로 = 노이즈)'))
            continue
        if UNTRANSLATABLE.search(ko):
            skipped.append((k, o['file'], '번역불가 표기'))
            continue

        if k in MANUAL:
            a, b = MANUAL[k]
            if a not in ko:
                errors.append((k, o['file'], 'MANUAL 패턴 없음 %r' % a))
                continue
            ko = ko.replace(a, b)

        ko = fix_tokens(ko, jp)
        ko = normalize(ko)
        if k in REWRITE:                 # 수기 재작성(축약 규칙으로 못 맞춘 것)
            ko = REWRITE[k]
        ko = shrink(ko, o['bytes'])
        # 줄폭 초과는 «같은 줄 수 안에서 재조판»으로 먼저 시도한다
        jl = jp.split('\n')
        if (max(cells(x) for x in jl) <= 20
                and (len(ko.split('\n')) > len(jl)
                     or any(cells(x) > 20 for x in ko.split('\n')))):
            rw = rewrap(ko, 20, len(jl))
            if rw is not None and size(rw) <= o['bytes']:
                ko = rw

        # --- 검사
        if KANA.search(ko):
            errors.append((k, o['file'], '가나 잔재 %r' % ko[:50]))
            continue
        if JAMO.search(ko):
            errors.append((k, o['file'], '낱자모 사용(빌드가 죽는다) %r' % ko[:50]))
            continue
        if '\u00b7' in ko:
            errors.append((k, o['file'], "'·'(U+00B7) 금지 %r" % ko[:50]))
            continue
        try:
            ''.join(c for c in ko if not ('가' <= c <= '힣')).encode('cp932')
        except UnicodeEncodeError as e:
            errors.append((k, o['file'], 'cp932 인코딩 불가 %s' % e))
            continue
        if TOKEN_RE.findall(ko) != TOKEN_RE.findall(jp):
            errors.append((k, o['file'], '토큰 불일치 %s -> %s'
                           % (TOKEN_RE.findall(jp), TOKEN_RE.findall(ko))))
            continue

        out.append(dict(key=k, file=o['file'], budget=o['bytes'], jp=jp, ko=ko,
                        over=size(ko) - o['bytes']))
    return out, skipped, errors, stray


def linewidth_bad(rows):
    bad = []
    for r in rows:
        jl = r['jp'].split('\n')
        kl = r['ko'].split('\n')
        if len(kl) > len(jl):
            bad.append((r, -1, len(kl), len(jl)))
            continue
        if max(cells(x) for x in jl) > 20:
            continue           # 자동 줄바꿈 창(일기·책) — 줄 폭 제약 없음
        for i, line in enumerate(kl):
            if cells(line) > 20:
                bad.append((r, i, cells(line), 20))
    return bad


def main(write):
    rows, skipped, errors, stray = build()
    print('완료본 %d행 → 병합대상 %d / 스킵 %d / 오류 %d'
          % (len(rows) + len(skipped) + len(errors), len(rows), len(skipped), len(errors)))
    if stray:
        print('★표계산기 손상으로 버려진 물리줄 %d개 (원본 transtodo 로 복원됨)' % len(stray))

    if errors:
        print('\n★오류 %d건:' % len(errors))
        for k, f, why in errors:
            print('   %s %-12s %s' % (k, f, why))

    over = [r for r in rows if r['over'] > 0]
    over.sort(key=lambda r: -r['over'])
    print('\n예산 초과 %d건' % len(over))
    for r in over[:40]:
        print('   %s %-12s +%dB (%d/%d)  %r'
              % (r['key'], r['file'], r['over'], r['budget'] + r['over'], r['budget'],
                 r['ko'][:60]))

    lw = linewidth_bad(rows)
    print('\n줄폭 초과 %d건' % len(lw))
    for r, i, a, b in sorted(lw, key=lambda x: -(x[2] - x[3]))[:40]:
        if i < 0:
            print('   %s %-12s 줄수 %d > %d' % (r['key'], r['file'], a, b))
        else:
            print('   %s %-12s 줄%d %d칸 > %d  %r'
                  % (r['key'], r['file'], i, a, b, r['ko'].split('\n')[i][:40]))

    if not write:
        return rows, over, lw
    if errors or over or lw:
        sys.exit('\n★문제가 남아 있어 병합하지 않았다.')

    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        p = os.path.join(WORK, 'trans', fn)
        with io.open(p, 'a', encoding='utf-8', newline='') as f:
            for r in rows:
                f.write('%s\t%s\n' % (r['key'], esc(r['ko'])))
    print('\n병합 완료: %d행 추가' % len(rows))
    return rows, over, lw


if __name__ == '__main__':
    main('--write' in sys.argv)

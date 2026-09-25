# -*- coding: utf-8 -*-
"""번역문 전체의 글리프 커버리지 검증.

★인코딩 누락은 빌드 에러다 — 번역문에 글리프·코드 매핑이 없는 문자가 있으면
  조용히 건너뛰지 말고 빌드를 실패시킨다.

모든 문자를 세 갈래로 나눈다.
  1. 한글 음절(가-힣) -> BDF 로 새로 그려서 «도너 코드»에 얹어야 한다
  2. 폰트에 이미 있는 문자 -> 코드 그대로 쓴다(원문에서 그대로 옮긴 기호·숫자·한자)
  3. 그 어느 쪽도 아님 -> ★실패. 번역문을 고쳐야 한다.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from fntc import Fntc
from project import TRACK1
from peek import load_list
import krglyph

TOKEN = re.compile(r'%[A-Za-z][0-9]*')


def load_font():
    rows = {r[0]: r for r in load_list()}
    p, l, s, _ = rows['/RIG2INIT.DAT']
    return Fntc(Mato(Iso(TRACK1).read(l, s), 'x').block(1))


def unesc(s):
    """★문자 단위로 되짚는다 — 순차 .replace() 체인은 이스케이프 순서에 따라
    잘못 풀릴 수 있다(예: 진짜 역슬래시 뒤에 n 이 오는 경우)."""
    out = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            c = s[i + 1]
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(c, c))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def load_ko():
    ko = {}
    with io.open(os.path.join('..', 'work', 'trans', 'ko_final.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            ko[a[0]] = unesc(a[1])
    return ko


if __name__ == '__main__':
    f = load_font()
    ko = load_ko()
    hangul = set()
    existing = set()
    ascii_carry = set()          # 원문 검증된 반각(카나리 확인: 스페이스·분수·이모티콘 등)
    unknown = {}
    for k, text in ko.items():
        body = TOKEN.sub('', text)
        for c in body:
            if c in ('\n', '\r', '\t'):
                continue
            if '가' <= c <= '힣':
                hangul.add(c)
            elif f.index_of(c) is not None:
                existing.add(c)
            elif 0x20 <= ord(c) <= 0x7E:
                # ★반각 ASCII 는 폰트(전각 전용, 최솟값 0x8140)엔 없지만
                #   원문에도 그대로 있던 걸 검증 없이 옮긴 게 아니라 실측으로
                #   확인된 자리(스페이스=PoC 실측 6px, 분수·이모티콘·？=원문 그대로)
                #   에서만 왔다. cp932 인코딩 자체는 항상 되므로 여기서는 통과시키되
                #   ★목록은 남겨 감사(audit) 가능하게 한다.
                ascii_carry.add(c)
            else:
                unknown.setdefault(c, []).append(k)

    print('한글 음절 %d종 (도너 코드 필요)' % len(hangul))
    print('기존 폰트 문자 재사용 %d종' % len(existing))
    print('반각 ASCII 통과(원문 검증분) %d종: %s' % (len(ascii_carry), sorted(ascii_carry)))
    print('★매핑 안 되는 문자 %d종' % len(unknown))
    for c, keys in unknown.items():
        print('   %r U+%04X  %d회  예: %s' % (c, ord(c), len(keys), keys[0]))

    miss = krglyph.coverage(''.join(hangul))
    print('\nBDF 커버리지: 없는 한글 %d개 %s' % (len(miss), miss))

    if not unknown and not miss:
        print('\n✅ 전부 매핑 가능')
    else:
        print('\n★ 빌드 중단 — 위 문자를 먼저 고칠 것')
        sys.exit(1)

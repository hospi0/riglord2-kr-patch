"""문장부호 실태 조사 — 어떤 부호가 얼마나 쓰이고, 폰트에 뭐가 있는지.

번역에서 부호를 어떻게 다룰지 정하려면 «빈도»와 «폰트 보유»를 같이 봐야 한다.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from fntc import Fntc
from project import TRACK1, WORK
from peek import load_list

TOKEN = re.compile(r'%[A-Za-z][0-9]*')


def unesc(s):
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


def is_word(c):
    o = ord(c)
    return (0x3040 <= o <= 0x30ff or 0x4e00 <= o <= 0x9fff
            or 0xff10 <= o <= 0xff5a or c.isalnum())


def main():
    cnt = collections.Counter()
    tot = 0
    with open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            t = TOKEN.sub('', unesc(a[5])).replace('\n', '')
            tot += len(t)
            for c in t:
                if not is_word(c):
                    cnt[c] += 1
    print('본문 %d자. 부호·기타 상위 24' % tot)
    print('%-4s %-8s %8s %7s  %s' % ('글자', '유니코드', '횟수', '비율', 'cp932'))
    for c, n in cnt.most_common(24):
        try:
            code = c.encode('cp932').hex().upper()
        except Exception:
            code = '-'
        print('%-4s U+%04X   %8d %6.2f%%  %s' % (c, ord(c), n, 100 * n / tot, code))

    # 폰트에 있는 «비문자» 글리프 목록
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    p, l, s, _ = rows['/RIG2INIT.DAT']
    f2 = Fntc(Mato(iso.read(l, s), 'x').block(1))
    syms = []
    for i in range(f2.n):
        ch = f2.char_of(i)
        if ch and not is_word(ch):
            syms.append((i, ch, f2.codes[i]))
    print('\n폰트가 가진 비문자 글리프 %d개 (앞 40):' % len(syms))
    print('   ' + ' '.join('%s(%04X)' % (c, k) for _, c, k in syms[:40]))
    return f2, syms


if __name__ == '__main__':
    main()

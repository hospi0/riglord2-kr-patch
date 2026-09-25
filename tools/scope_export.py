"""번역 범위(오프닝 프롤로그 NT계열 + UI 도움말) 원문을 서사 순서로 뽑는다.

범위 = NT00/10/20/21/30/31.MAP (7인위원회 오프닝 -> 뮤 감금 -> 갈자드 대결)
     + WAZAHELP/ITEMHELP/DIARY.MSG + STATHELP.MAT (UI 도움말)
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import WORK

TOKEN = re.compile(r'%[A-Za-z][0-9]*')

SCOPE_ORDER = ['/NT31.MAP', '/NT21.MAP', '/NT20.MAP', '/NT30.MAP', '/NT00.MAP', '/NT10.MAP',
              '/WAZAHELP.MSG', '/ITEMHELP.MSG', '/DIARY.MSG', '/STATHELP.MAT']


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


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def main():
    tdir = os.path.join(WORK, 'trans')
    byfile = {}
    with io.open(os.path.join(tdir, 'refs.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if a[1] in SCOPE_ORDER:
                byfile.setdefault(a[1], []).append((int(a[2]), a[0]))
    rows = {}
    with io.open(os.path.join(tdir, 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            rows[a[0]] = a

    seen = set()
    out = io.open(os.path.join(tdir, 'scope_jp.tsv'), 'w', encoding='utf-8', newline='')
    out.write('key\tfile\tbytes\tchars\ttokens\tjp\n')
    n = 0
    for fn in SCOPE_ORDER:
        for off, k in sorted(byfile.get(fn, [])):
            if k in seen:
                continue
            seen.add(k)
            r = rows[k]
            out.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (k, fn, r[2], r[3], r[4], r[5]))
            n += 1
    out.close()
    print('범위 문자열 %d개 -> work/trans/scope_jp.tsv' % n)


if __name__ == '__main__':
    main()

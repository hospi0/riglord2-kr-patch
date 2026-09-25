"""번역표 추출 — 고유 문자열 단위 TSV + 참조 위치 TSV.

산출물
  work/trans/strings.tsv   번역 대상. **한 줄 = 고유 문자열 하나**
      key      안정 식별자 (원문 바이트의 sha1 앞 10자리)
      files    이 문자열이 나오는 파일 수
      bytes    원문 바이트 수 = **제자리 덮어쓰기 예산**
      chars    번역해야 할 글자 수(제어 토큰·개행 제외)
      tokens   원문에 든 제어 토큰 목록 (번역문에 그대로 살려야 한다)
      jp       원문 (\\n \\t \\\\ 이스케이프)
      ko       번역 (빈 칸)
  work/trans/refs.tsv      key -> (파일, 오프셋). 재삽입 때 쓴다.

★`jp` 는 **번역표의 키**다. 절대 손대지 않는다.
★제어 토큰(`%z %b %H %m0 %m1 %V0 %V100` …)과 개행은 의미가 있으므로 보존한다.
★예산은 바이트 기준이다. 화면 폭(칸) 제약은 **별개**이며 실기로 실측해야 한다.
"""
import collections
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list
from corpus import strings, payload
from corpus2 import is_real

# ★ASCII 숫자만. `\d` 로 쓰면 전각 숫자를 먹어 `%m0７人委員会` 의 「７」이 토큰이 된다.
TOKEN = re.compile(r'%[A-Za-z][0-9]*')
TARGET_EXT = ('.MAP', '.MSG', '.MAT')


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def main():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)

    uniq = {}                       # key -> dict
    refs = []                       # (key, path, offset, bytes)
    for path, lba, size, oob in rows:
        if not path.upper().endswith(TARGET_EXT):
            continue
        d = iso.read(lba, size)
        for off, raw, t in strings(d):
            if not is_real(t):
                continue
            key = hashlib.sha1(raw).hexdigest()[:10]
            if key not in uniq:
                uniq[key] = dict(key=key, bytes=len(raw), jp=t,
                                 chars=len(payload(t)),
                                 tokens=' '.join(dict.fromkeys(TOKEN.findall(t))),
                                 files=set())
            u = uniq[key]
            u['files'].add(path)
            if u['bytes'] != len(raw):
                print('  ⚠ 같은 key 인데 바이트가 다르다: %s' % key)
            refs.append((key, path, off, len(raw)))

    out_dir = os.path.join(WORK, 'trans')
    os.makedirs(out_dir, exist_ok=True)
    sp = os.path.join(out_dir, 'strings.tsv')
    with open(sp, 'w', encoding='utf-8', newline='') as f:
        f.write('key\tfiles\tbytes\tchars\ttokens\tjp\tko\n')
        for u in sorted(uniq.values(), key=lambda x: (-x['chars'], x['key'])):
            f.write('%s\t%d\t%d\t%d\t%s\t%s\t\n'
                    % (u['key'], len(u['files']), u['bytes'], u['chars'],
                       u['tokens'], esc(u['jp'])))
    rp = os.path.join(out_dir, 'refs.tsv')
    with open(rp, 'w', encoding='utf-8', newline='') as f:
        f.write('key\tfile\toffset\tbytes\n')
        for key, path, off, n in sorted(refs):
            f.write('%s\t%s\t%d\t%d\n' % (key, path, off, n))

    tot_chars = sum(u['chars'] for u in uniq.values())
    print('고유 문자열 %d개 / 번역 글자 %d자' % (len(uniq), tot_chars))
    print('참조 %d건 (중복 배수 %.2f)' % (len(refs), len(refs) / max(len(uniq), 1)))
    print('  ->', sp)
    print('  ->', rp)

    # 검산 — 토큰·개행 분포
    tk = collections.Counter()
    for u in uniq.values():
        tk.update(TOKEN.findall(u['jp']))
    print('\n제어 토큰 종류 %d:' % len(tk))
    for k, v in tk.most_common(15):
        print('   %-8s %d회' % (k, v))
    nl = sum(u['jp'].count('\n') for u in uniq.values())
    print('개행 %d개, 개행 있는 문자열 %d개'
          % (nl, sum(1 for u in uniq.values() if '\n' in u['jp'])))

    # 이스케이프 왕복 검산
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
    bad = sum(1 for u in uniq.values() if unesc(esc(u['jp'])) != u['jp'])
    print('\n이스케이프 왕복 불일치 %d건 (0 이어야 한다)' % bad)


if __name__ == '__main__':
    main()

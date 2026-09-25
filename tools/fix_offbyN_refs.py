# -*- coding: utf-8 -*-
"""**시작점이 어긋난 참조**를 실제 문자열 자리로 바로잡고 번역을 채운다.

실기 제보: 소지품 첫 아이템(회복약) 설명이 일본어 그대로였다.

★세션2 는 이 행(`44f6c5cc75`)을 「오프셋 표 바이트가 SJIS 로 우연히 읽힌
  추출 오류」로 보고 **제외**했다. 실제로는 **시작이 2바이트 앞**이라 앞의
  오프셋 표 꼬리(`2D 9C`)를 문자열에 물고 들어온 것뿐이었고, 뒤는 멀쩡한
  본문이다([[feedback_regex_string_start_backtrace]]).
  ⇒ 「추출 오류」로 단정하기 전에 **원문 바이트를 직접 찾아** 시작점을 다시 잡아볼 것.

같은 계열: `.PRF` 두 행은 전각 공백으로 시작하지 않아 일반 스캔이 앞의 그래픽
바이트(`80 48 80 68`)까지 물었다. 그 4바이트를 잘라내 자리를 좁힌다.
"""
import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from project import TRACK1, WORK
from peek import load_list

# key -> (파일, 진짜 원문, 번역)  ※번역이 None 이면 자리만 바로잡는다
FIX = {
    '44f6c5cc75': ('/ITEMHELP.MSG',
                   'ＨＰを１００回復することができます。',
                   'ＨＰ를 １００ 회복할 수 있다'),
}
# `.PRF` 선두 그래픽 바이트를 잘라낼 행 (자리만 좁히고 번역은 기존 것을 다시 씀)
PRF_TRIM = ('68f267bc6f', 'a4c2c0b132')


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


def main(write):
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    T = lambda x: os.path.join(WORK, 'trans', x)

    plan = []
    for k, (path, jp, ko) in FIX.items():
        _, lba, sz, _ = rows[path]
        d = iso.read(lba, sz)
        raw = jp.encode('cp932')
        off = d.find(raw)
        if off < 0:
            print('★원문을 못 찾음: %r' % jp)
            return
        if size(ko) > len(raw):
            print('★예산 초과 %r %dB > %dB' % (ko, size(ko), len(raw)))
            return
        newk = hashlib.sha1(raw).hexdigest()[:10]
        plan.append((k, newk, path, off, len(raw), jp, ko))
        print('  %s -> %s  %s 0x%X %dB  %r -> %r'
              % (k, newk, path, off, len(raw), jp[:24], ko))

    if not write:
        print('[미리보기 — --write 로 기록]')
        return

    remap = {k: n for k, n, _, _, _, _, _ in plan}
    # strings.tsv
    lines = io.open(T('strings.tsv'), encoding='utf-8').read().split('\n')
    out = [lines[0]]
    for l in lines[1:]:
        if not l.strip():
            continue
        a = l.split('\t')
        if a[0] in remap:
            _, newk, path, off, n, jp, ko = next(x for x in plan if x[0] == a[0])
            a = [newk, '1', str(n), str(len(jp)), a[4] if len(a) > 4 else '', esc(jp), '']
            l = '\t'.join(a)
        out.append(l)
    io.open(T('strings.tsv'), 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')

    # refs.tsv
    lines = io.open(T('refs.tsv'), encoding='utf-8').read().split('\n')
    out = [lines[0]]
    for l in lines[1:]:
        if not l.strip():
            continue
        a = l.split('\t')
        if a[0] in remap:
            _, newk, path, off, n, jp, ko = next(x for x in plan if x[0] == a[0])
            l = '\t'.join([newk, path, str(off), str(n)])
        out.append(l)
    io.open(T('refs.tsv'), 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')

    # ko 두 벌 — 기존 행이 없으면 새로 추가
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        lines = io.open(T(fn), encoding='utf-8').read().split('\n')
        have = {l.split('\t', 1)[0] for l in lines if l.strip()}
        out, done = [lines[0]], set()
        for l in lines[1:]:
            if not l.strip():
                continue
            a = l.split('\t')
            if a[0] in remap:
                _, newk, path, off, n, jp, ko = next(x for x in plan if x[0] == a[0])
                l = '%s\t%s' % (newk, esc(ko))
                done.add(newk)
            out.append(l)
        for k, newk, path, off, n, jp, ko in plan:
            if newk not in done and newk not in have:
                out.append('%s\t%s' % (newk, esc(ko)))
        io.open(T(fn), 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
    print('기록 완료 (%d행)' % len(plan))


if __name__ == '__main__':
    main('--write' in sys.argv)

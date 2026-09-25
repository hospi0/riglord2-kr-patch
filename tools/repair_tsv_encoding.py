# -*- coding: utf-8 -*-
"""일회성 복구 — ko_final.tsv/ko_shrunk.tsv 를 «물리 줄 1개 = 레코드 1개»
정규 형식(개행은 리터럴 \\n 로 이스케이프)으로 통일한다.

`merge_story.py`가 진짜 개행 문자를 그대로 써버려서 `load_ko()`(물리 줄
단위로 읽음)가 둘째 줄부터 잘라먹던 문제를 고친다.
"""
import io
import os
import re

WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')


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


REC_RE = re.compile(r'^([0-9a-f]{10})\t(.*?)(?=\n[0-9a-f]{10}\t|\Z)', re.S | re.M)


def main():
    log_lines = []
    for fn in ('ko_final.tsv', 'ko_shrunk.tsv'):
        path = os.path.join(WORK, 'trans', fn)
        s = io.open(path, encoding='utf-8').read()
        lines = s.split('\n')
        header = lines[0]
        body = '\n'.join(lines[1:])
        out_lines = [header]
        n_fixed = 0
        seen = set()
        for m in REC_RE.finditer(body):
            k, raw_val = m.group(1), m.group(2)
            if k in seen:
                continue
            seen.add(k)
            if '\n' in raw_val:
                true_val = raw_val
                n_fixed += 1
            else:
                true_val = unesc(raw_val)
            out_lines.append(k + '\t' + esc(true_val))
        out = '\n'.join(out_lines) + '\n'
        io.open(path, 'w', encoding='utf-8', newline='').write(out)
        log_lines.append('%s: records=%d (multi-line-fixed=%d)' % (fn, len(seen), n_fixed))
    return log_lines


if __name__ == '__main__':
    for l in main():
        print(l)

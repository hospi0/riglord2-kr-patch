# -*- coding: utf-8 -*-
"""모든 trans_story_*.py 모듈을 ko_final.tsv/ko_shrunk.tsv에 재동기화.

각 모듈의 TRANS 딕셔너리 값으로 TSV의 해당 key 줄을 덮어쓴다(있으면 교체, 없으면 무시).
개별 파일 사후 수정이 TSV에 반영 안 되는 문제를 해결하기 위함.

★TSV는 물리 줄 1개 = 레코드 1개(`load_ko()`가 `for line in f`로 읽는다) —
실개행은 반드시 `esc()`로 이스케이프해서 쓴다.
"""
import glob, importlib, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TSVS = [
    os.path.join(HERE, '..', 'work', 'trans', 'ko_final.tsv'),
    os.path.join(HERE, '..', 'work', 'trans', 'ko_shrunk.tsv'),
]


def esc(s):
    return (s.replace('\\', '\\\\').replace('\n', '\\n')
             .replace('\r', '\\r').replace('\t', '\\t'))


def load_all_trans():
    merged = {}
    for path in sorted(glob.glob(os.path.join(HERE, 'trans_story_*.py'))):
        modname = os.path.splitext(os.path.basename(path))[0]
        mod = importlib.import_module(modname)
        for k, v in mod.TRANS.items():
            if v is None:
                continue
            merged[k] = v
    return merged


def resync(path, merged):
    lines = io.open(path, encoding='utf-8').readlines()
    n_replaced = 0
    for i, line in enumerate(lines):
        nl = '\n' if line.endswith('\n') else ''
        body = line[:-1] if nl else line
        if '\t' not in body:
            continue
        key, _, _ = body.partition('\t')
        if key in merged:
            new_line = key + '\t' + esc(merged[key]) + nl
            if new_line != line:
                lines[i] = new_line
                n_replaced += 1
    io.open(path, 'w', encoding='utf-8', newline='').writelines(lines)
    return n_replaced


def main():
    merged = load_all_trans()
    results = []
    for path in TSVS:
        n = resync(path, merged)
        results.append((path, n))
    return len(merged), results


if __name__ == '__main__':
    total_keys, results = main()
    log = io.open(sys.argv[1], 'w', encoding='utf-8') if len(sys.argv) > 1 else None
    msg_lines = ['모듈 병합 총 %d개 key' % total_keys]
    for path, n in results:
        msg_lines.append('%s: %d줄 교체' % (path, n))
    msg = '\n'.join(msg_lines)
    if log:
        log.write(msg + '\n')
        log.close()
    else:
        print(msg)

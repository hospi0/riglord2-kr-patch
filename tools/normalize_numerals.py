# -*- coding: utf-8 -*-
"""숫자·영문 표기를 원문과 일치시킨다.

★★버그: 번역문에 반각 `HP`/`100`/`1.5` 등을 썼는데, 원문은 **전각**
  `ＨＰ`/`１００`/`１．５`을 쓴다. 폰트 코드표 최솟값이 0x8140 이라
  반각 영숫자 글리프가 없을 수 있다(확인 전까지는 위험). 다만 원문 일부
  (분수 `1/4`, 이모티콘 `:-)`, 일기의 날짜)는 실제로 **반각**을 쓴다 —
  그건 이미 화면에 표시되는 원본 데이터이므로 손대지 않고 그대로 옮긴다.

방법: 원문·번역문에서 «숫자·영문·기호 나열 구간»을 같은 정규식으로 뽑아
개수가 같으면 **순서대로 원문 구간의 바이트를 번역문에 그대로 이식**한다.
번역이 숫자를 안 바꾸는 이상 개수는 항상 같아야 한다 — 다르면 사람이 봐야 한다.
"""
import io
import re
import sys

RUN = re.compile(r'[0-9０-９A-Za-zＡ-Ｚａ-ｚ%％./．／:：\-－()（）]+')


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


def fix(jp, ko):
    """ko 안의 숫자·영문 구간을 jp 의 같은 순번 구간으로 치환. (성공?, 결과)"""
    jruns = RUN.findall(jp)
    kruns = RUN.findall(ko)
    if len(jruns) != len(kruns):
        return False, ko
    out = []
    pos = 0
    it = iter(jruns)
    for m in RUN.finditer(ko):
        out.append(ko[pos:m.start()])
        out.append(next(it))
        pos = m.end()
    out.append(ko[pos:])
    return True, ''.join(out)


if __name__ == '__main__':
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from trans_dialogue import DIALOGUE
    from trans_diary import DIARY
    from trans_skills import SKILLS
    from trans_items import ITEMS, STAT

    jp = {}
    with io.open('../work/trans/scope_jp.tsv', encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            jp[a[0]] = unesc(a[5])

    ALL = {}
    ALL.update(DIALOGUE)
    ALL.update(DIARY)
    ALL.update(SKILLS)
    ALL.update(ITEMS)
    ALL.update(STAT)
    print('번역 항목 %d / 원문 항목 %d' % (len(ALL), len(jp)))

    missing = [k for k in jp if k not in ALL]
    extra = [k for k in ALL if k not in jp]
    print('번역 안 된 것 %d / 범위 밖 여분 %d' % (len(missing), len(extra)))
    if missing:
        for k in missing[:10]:
            print('   빠짐:', k, jp[k][:30])

    fixed = mismatch = 0
    out = {}
    for k, ko in ALL.items():
        if k not in jp:
            continue
        ok, new = fix(jp[k], ko)
        out[k] = new
        if ok:
            if new != ko:
                fixed += 1
        else:
            mismatch += 1
            print('   ★구간 개수 불일치:', k)
            print('      jp:', jp[k][:60])
            print('      ko:', ko[:60])

    print('\n숫자·영문 구간 교정 %d건 / 개수 불일치(수동 확인 필요) %d건' % (fixed, mismatch))

    outp = os.path.join('..', 'work', 'trans', 'ko_normalized.tsv')
    with io.open(outp, 'w', encoding='utf-8', newline='') as f:
        f.write('key\tko\n')
        for k, v in out.items():
            # ★\r 도 이스케이프해야 한다 — 안 하면 줄이 그 자리에서 끊긴다
            esc = (v.replace('\\', '\\\\').replace('\n', '\\n')
                    .replace('\r', '\\r').replace('\t', '\\t'))
            f.write('%s\t%s\n' % (k, esc))
    print('저장:', outp)

# -*- coding: utf-8 -*-
"""`/0_OP.BIN`(타이틀 화면 담당 실행 바이너리)의 UI 문자열을 등록한다.

실기 제보: 타이틀에서 들어가는 **LOAD 화면**만 일본어였다(`データなし`,
`リグロードワールドマップ`, 머리글 `［本体ＲＡＭ］`가 깨진 한글).

★원인 — 게임 내 세이브 화면은 `/RIG2MENU.OVL`·`/R2MDATA.OVL` 을 쓰는데,
  **타이틀의 LOAD 화면은 `/0_OP.BIN` 이 자체 사본을 따로 갖고 있다.**
  이 파일은 UI 코퍼스에 **한 줄도 등록돼 있지 않았다**(ui_refs 0건).
  같은 문구가 두 파일에 각각 있는 전형적인 «사본» 함정
  ([[feedback_shared_text_needs_shared_font]] 와 같은 계열).

★실행 코드가 섞인 바이너리라 **실측 안전구간 밖은 절대 건드리지 않는다**
  (`/1_RIG2.BIN` 과 같은 방침). 텍스트는 0x25000~0x27000 에 몰려 있다.
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

FILE = '/0_OP.BIN'
SAFE_LO, SAFE_HI = 0x25000, 0x27200        # 실측: 텍스트가 몰린 구간
JP = re.compile(r'[぀-ヿ一-鿿]')

# 이 파일에만 있는 문구(세이브 데이터 관리 메시지) — 예산은 원문 바이트.
NEW = {
    '本体ＲＡＭのバックアップの準備がまだできていません。':
        '본체ＲＡＭ 백업 준비가 아직 되지 않았습니다.',
    '本体ＲＡＭの全ての記録を消します。':
        '본체ＲＡＭ의 모든 기록을 지웁니다.',
    '初期化中です。しばらくお待ち下さい。':
        '초기화 중입니다. 잠시 기다려 주세요.',
    '本体ＲＡＭの全ての記録を消すことができませんでした。\nセガサターン本体の保存データ管理画面で全ての記録を消してください。':
        '본체ＲＡＭ의 모든 기록을 지울 수 없었습니다.\n세가새턴 본체의 저장 데이터 관리 화면에서 모든 기록을 지워 주세요.',
    '本体ＲＡＭの全ての記録を消しました。':
        '본체ＲＡＭ의 모든 기록을 지웠습니다.',
    'ＬボタンまたはＲボタンを押したままリセットボタンを押すと、セガサターン本体の保存データ管理画面へ進みます。':
        'Ｌ버튼 또는 Ｒ버튼을 누른 채 리셋 버튼을 누르면 세가새턴 본체의 저장 데이터 관리 화면으로 갑니다.',
    'カートリッジＲＡＭのバックアップの準備がまだできていません。':
        '카트리지ＲＡＭ 백업 준비가 아직 되지 않았습니다.',
    'カートリッジＲＡＭの\n内容が消えてしまいます':
        '카트리지ＲＡＭ의\n내용이 지워집니다',
    'カートリッジＲＡＭの全ての記録を消すことができませんでした。\nセガサターン本体の保存データ管理画面で全ての記録を消してください。':
        '카트리지ＲＡＭ의 모든 기록을 지울 수 없었습니다.\n세가새턴 본체의 저장 데이터 관리 화면에서 모든 기록을 지워 주세요.',
    'カートリッジＲＡＭの全ての記録を消しました。':
        '카트리지ＲＡＭ의 모든 기록을 지웠습니다.',
    'ＬボタンまたはＲボタンを押しながら、リセットボタンを押すと、保存データ管理画面が表示されます。':
        'Ｌ버튼 또는 Ｒ버튼을 누르면서 리셋 버튼을 누르면 저장 데이터 관리 화면이 표시됩니다.',
}


def esc(s):
    return (s.replace('\\', '\\\\').replace('\r', '\\r')
             .replace('\n', '\\n').replace('\t', '\\t'))


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append({'n': '\n', 'r': '\r', 't': '\t', '\\': '\\'}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i]); i += 1
    return ''.join(out)


def size(t):
    n = 0
    for ch in t:
        n += 2 if '가' <= ch <= '힣' else len(ch.encode('cp932', 'replace'))
    return n


def segments(d):
    out, i = [], SAFE_LO
    while i < SAFE_HI:
        j = d.find(b'\x00', i)
        if j < 0:
            break
        chunk = d[i:j]
        raw = chunk.strip(b'\xff')
        # ★앞쪽 0xFF 를 벗겨냈으면 **시작 오프셋도 그만큼 밀어야** 한다.
        #   안 하면 1바이트 어긋나 빌드가 「원문 불일치」로 전부 건너뛴다.
        off = i + (len(chunk) - len(chunk.lstrip(b'\xff')))
        if raw and len(raw) <= 300:
            try:
                t = raw.decode('cp932')
            except UnicodeDecodeError:
                t = None
            if t and JP.search(t) and all(ord(c) >= 0x20 or c in '\t\r\n' for c in t):
                # ⛔2바이트 희귀 한자 하나짜리는 그래픽·좌표가 우연히 읽힌 노이즈다
                if not (len(raw) == 2 and not re.search(r'[぀-ヿ]', t)):
                    out.append((off, raw, t))
        i = j + 1
    return out


def main(write):
    rows = {r[0]: r for r in load_list()}
    _, lba, sz, _ = rows[FILE]
    d = Iso(TRACK1).read(lba, sz)

    ko_by_jp, keys = {}, set()
    with io.open(os.path.join(WORK, 'trans', 'ui_strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            keys.add(a[0])
            if len(a) >= 8 and a[7].strip():
                ko_by_jp[unesc(a[6])] = unesc(a[7])
    have_ref = set()
    with io.open(os.path.join(WORK, 'trans', 'ui_refs.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            have_ref.add((a[0], a[1], a[2]))

    s_rows, r_rows, bad, reuse, fresh = [], [], [], 0, 0
    seen_new = set()
    for off, raw, t in segments(d):
        ko = ko_by_jp.get(t) or NEW.get(t)
        if ko is None:
            continue
        if size(ko) > len(raw):
            bad.append((t, ko, size(ko), len(raw)))
            continue
        k = hashlib.sha1(raw).hexdigest()[:10]
        if k not in keys and k not in seen_new:
            s_rows.append('%s\t1\t%d\t%d\t\t0\t%s\t%s'
                          % (k, len(raw), len(t), esc(t), esc(ko)))
            seen_new.add(k)
            fresh += 1
        elif k in keys:
            reuse += 1
        if (k, FILE, str(off)) not in have_ref:
            r_rows.append('%s\t%s\t%d\t%d' % (k, FILE, off, len(raw)))

    print('안전구간 문자열 %d개' % len(segments(d)))
    print('  기존 번역 재사용 %d / 신규 등록 %d / 참조 추가 %d' % (reuse, fresh, len(r_rows)))
    if bad:
        print('★예산 초과 — 아무것도 쓰지 않았다:')
        for t, ko, a, b in bad:
            print('   %dB > %dB  %r -> %r' % (a, b, t[:30], ko[:30]))
        return
    if not write:
        print('[미리보기 — --write 로 기록]')
        return
    T = lambda n: os.path.join(WORK, 'trans', n)
    for name, lines in (('ui_strings.tsv', s_rows), ('ui_refs.tsv', r_rows)):
        with io.open(T(name), 'a', encoding='utf-8', newline='') as f:
            for l in lines:
                f.write(l + '\n')
    print('기록 완료')


if __name__ == '__main__':
    main('--write' in sys.argv)

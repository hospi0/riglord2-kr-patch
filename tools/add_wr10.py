# -*- coding: utf-8 -*-
"""회수 — /WR10.MAP (드래군성 함락 직후: 자르마 마을 -> 오르트마 항구 -> 국경 마법벽).

DG21(드래군왕 튜토리얼) 바로 다음 장면. 사용자가 실기에서 위치 캡션
「リグロード참꼼、ドラグーン城。」(미추출 상태에서 도너 글리프와 충돌해 깨짐)를
지적해 발견 — `add_dg21.py` 와 같은 이유(SCOPE_ORDER 밖이라 번역만 누락)다.

★`a8955a5564`('DDDDDDDDD劔剩DDD')·`53a9622f4a`('腑5滷`') 는 `is_real()` 의
다른 허점(반복 문자 3종 이상이면 통과하는 조건)에 걸린 **노이즈** — 번역 제외.
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
from corpus import strings, payload
from corpus2 import is_real

EXCLUDE_NOISE = {'DDDDDDDDD劔剩DDD', '腑5滷`'}

TRANS = {
    '%zリグロード大陸、ドラグーン城。': '%z리그로드 대륙, 드래군성。',
    '%zミュウ・': '%z뮤・',
    '%z・お父様、\n・すぐに援軍を率いて戻って参ります！\nラスティ！':
        '%z・아버님,\n・바로 원군을 이끌고 돌아오겠습니다！\n러스티！',
    '%zうん！': '%z응！',
    '%zヤマタイへ行くわよ！\n目指すはイガの里！': '%z야마타이로 갈 거야！\n목표는 이가 마을！',
    '%z僕はいつでもミュウと一緒だよ。\n今までも、これからも・':
        '%z난 언제나 뮤와 함께야。\n지금까지도, 앞으로도・',
    '%zありがとう・\nまずはオルトマに行って\nヤマタイ行きの船に乗らなくちゃ。':
        '%z고마워・\n우선 오르트마로 가서\n야마타이행 배를 타야 해。',
    '%zでも、その前に、ザルマの町に寄って\nこの先の様子を探ったら？':
        '%z근데, 그전에, 자르마 마을에 들러\n앞쪽 상황을 살펴보는 게 어때？',
    '%zお父様あぁぁぁ！': '%z아버님!!!',
    'ミュウ、カダールが攻めてきたこと、\n町のみんなに知らせるのかい？%b':
        '뮤, 카달이 쳐들어온 거,\n마을 사람들에게 알릴 거야？%b',
    '・うん。%b\n': '・응。%b\n',
    'でも・%b': '근데・%b',
    'ザルマの町に入りますか？': '자르마 마을에 들어갈까요？',
    'オルトマの町に入りますか？': '오르트마 마을에 들어갈까요？',
    'ここが港町オルトマだよ。\nやっと着いたね、ミュウ。%b':
        '여기가 항구도시 오르트마야。\n드디어 도착했네, 뮤。%b',
    'うん。\nとにかくヤマタイに行く船をさがさなきゃ。%b':
        '응。\n어쨌든 야마타이로 가는 배를 찾아야 해。%b',
    'そういえば、ここにはディアーネって\n腕のいい船長がいるって話だよ。%b':
        '그러고 보니, 여기엔 디아느라는\n솜씨 좋은 선장이 있단 얘기야。%b',
    '確かに、ボクも聞いたことがあるよ。%b': '확실히, 나도 들은 적 있어。%b',
    'エヴァンおじいさまと一緒に\nリグロード戦役を戦った英雄の子孫だよ。%b':
        '에반 할아버님과 함께\n리그로드 전쟁을 치른 영웅의 후손이야。%b',
    '国境か・%b': '국경인가・%b',
    'ミュウ、国境を越える前に、\nザルマの町に寄って\nこの先の様子を探ったら？%b':
        '뮤, 국경을 넘기 전에,\n자르마 마을에 들러\n앞쪽 상황을 살펴보는 게 어때？%b',
    '・そうだね。%b': '・그러네。%b',
    'ザルマのみんなの様子も\n見ておかないと・%b':
        '자르마 사람들 상태도\n봐 둬야겠어・%b',
    '国境を通りますか？': '국경을 지나갈까요？',
    '・お父様、\nすぐに援軍を率いて戻って参ります！%b':
        '・아버님,\n바로 원군을 이끌고 돌아오겠습니다！%b',
    'ザルマの町に寄って\nこの先の様子を探ろうよ。%b':
        '자르마 마을에 들러\n앞쪽 상황을 살펴보자。%b',
    'カダールの兵隊がいる！%b': '카달 병사가 있다！%b',
    '見つからないうちに、\nここから離れようよ。%b':
        '들키기 전에,\n여기서 벗어나자。%b',
    'そうだね・%b': '그러네・%b',
    'これは・？%b': '이건・？%b',
    '魔法で作り出した壁みたいだけど、\n神聖魔法には無い技だよ。%b':
        '마법으로 만든 벽 같은데,\n신성마법엔 없는 기술이야。%b',
    'きっと、カダールとかいう連中が、\nリグロード大陸東西の\n通行を絶つために作ったんだよ！%b':
        '분명, 카달인지 뭔지 하는 놈들이,\n리그로드 대륙 동서\n통행을 끊으려 만든 거야！%b',
    'こんなところでグズグズしてられない、\n行こう！%b':
        '이런 데서 꾸물댈 시간 없어,\n가자！%b',
    'どうやら、\n魔法で作り出した壁みたいだね。%b':
        '아무래도,\n마법으로 만든 벽인 모양이네。%b',
    'きっと、カダールとかいう連中が、\nリグロード大陸東西の\n通行を絶つために作ったんだ！%b':
        '분명, 카달인지 뭔지 하는 놈들이,\n리그로드 대륙 동서\n통행을 끊으려 만든 거다！%b',
    'リグロードの東側にいる人達は\n無事かな・？%b':
        '리그로드 동쪽에 있는 사람들은\n무사할까・？%b',
    'だいじょうぶだよ・きっと・%b': '괜찮을 거야・분명・%b',
    'うん・\n行こう、ラスティ！%b': '응・\n가자, 러스티！%b',
}


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def main():
    rows = [r for r in load_list() if not r[3] and not r[0].endswith('/')]
    iso = Iso(TRACK1)

    want = set(TRANS)
    hits = {}
    for path, lba, size, oob in rows:
        if not path.upper().endswith(('.MAP', '.MSG', '.MAT')):
            continue
        d = iso.read(lba, size)
        for off, raw, t in strings(d):
            if t in want:
                hits.setdefault(t, []).append((path, off, raw))

    missing = want - set(hits)
    if missing:
        sys.exit('★디스크에서 못 찾은 원문 %d개: %s' % (len(missing), list(missing)[:3]))

    kp = os.path.join(WORK, 'trans', 'ko_final.tsv')
    strings_keys = set()
    with io.open(os.path.join(WORK, 'trans', 'strings.tsv'), encoding='utf-8') as f:
        next(f)
        for line in f:
            strings_keys.add(line.split('\t', 1)[0])
    ko_final_keys = set()
    with io.open(kp, encoding='utf-8') as f:
        next(f)
        for line in f:
            a = line.rstrip('\n').split('\t')
            if len(a) >= 2 and a[1]:
                ko_final_keys.add(a[0])

    new_rows, skipped = [], 0
    for t, locs in hits.items():
        raw0 = locs[0][2]
        for _, _, raw in locs:
            if raw != raw0:
                sys.exit('★같은 t 인데 raw 가 다르다: %r' % t)
        key = hashlib.sha1(raw0).hexdigest()[:10]
        if key in ko_final_keys:
            skipped += 1
            continue
        if key not in strings_keys:
            sys.exit('★strings.tsv 에 없다(진짜 미추출, 별도 처리 필요): %s %r' % (key, t))
        new_rows.append((key, TRANS[t], t, len(raw0), len(locs)))

    if not new_rows:
        print('추가할 신규 항목 없음 (이미 번역됨 %d)' % skipped)
        return

    with io.open(kp, 'a', encoding='utf-8', newline='') as f:
        for key, ko, t, n, cnt in new_rows:
            f.write('%s\t%s\n' % (key, esc(ko)))

    print('신규 %d개 ko_final.tsv 에 추가 (이미 번역됨 %d)' % (len(new_rows), skipped))
    for key, ko, t, n, cnt in new_rows:
        print('  %s %dB %d회  %r' % (key, n, cnt, ko[:30]))


if __name__ == '__main__':
    main()

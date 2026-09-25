"""문장부호 안 — 시안 렌더.

## 판단 근거 (실측)

원문 부호 빈도: `、` 7,463 / `。` 6,669 / `！` 2,479 / `　` 2,036 / `～` 300 /
                `「」` 168 / `（）` 145 / `【】` 134 / `？`·`…` 등
폰트 보유: `，`(8143) `．`(8144) `？`(8148) `！`(8149) `…`(8163) `“”`(8167/8168) 등 46종
반각: **글리프 없음.** 스페이스(0x20)만 렌더러가 폭 6px 로 처리한다.
      원문의 반각 `-` `/` `"` `:` 는 전부 노이즈 문자열이었다.

## 안 — 「코드는 원문 그대로, 글리프만 한국어식으로」

`。`(8142) `、`(8141) 코드를 **그대로 쓰고 그 칸의 그림만 바꾼다.**
  · 번역표에 원문 부호를 그대로 써도 되니 작업이 단순하다
  · 새 코드 배정이 없으니 **글리프 슬롯을 한 칸도 안 먹는다**
  · 전면 번역이므로 일본어 원문에 남을 일이 없다

  8142 `。` → 한국어 마침표 (베이스라인 작은 사각 점)
  8141 `、` → 한국어 쉼표     (= 이미 있는 `，`(8143) 글리프를 복사)

바꾸지 않는 것 (모양이 이미 맞다)
  `！`(8149) `？`(8148) `…`(8163) `（）`(8169/816A) `【】`(8179/817A) `～`(8160)

선택 사항
  `「」`(8175/8176) → `“”`(8167/8168) 로 **코드 치환**(글리프는 이미 있다).
  168회뿐이라 영향은 작다. 대사 인용에 한국어식 따옴표를 쓸지의 문제다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Iso
from mato import Mato
from fntc import Fntc
from project import TRACK1
from peek import load_list

# 12x12 시안 (행 문자열, '#'=잉크). 원본 부호의 세로 위치에 맞췄다.
PERIOD = [
    '............',
    '............',
    '............',
    '............',
    '............',
    '............',
    '............',
    '............',
    '............',
    '.##.........',
    '.##.........',
    '............',
]


def art_to_gray(art, w=16, h=12):
    out = bytearray(w * h)
    for y, row in enumerate(art[:h]):
        for x, c in enumerate(row[:12]):
            if c == '#':
                out[y * w + x] = 255
    return bytes(out)


def show(title, gray, w=16, h=12):
    print(title)
    for y in range(h):
        print('   ' + ''.join('#' if gray[y * w + x] else '.' for x in range(12)))


if __name__ == '__main__':
    rows = {r[0]: r for r in load_list()}
    iso = Iso(TRACK1)
    p, l, s, _ = rows['/RIG2INIT.DAT']
    f = Fntc(Mato(iso.read(l, s), 'x').block(1))

    print('=== 지금 (원문 일본어 부호) ===')
    for ch in ['。', '、']:
        show('%s (%04X)' % (ch, f.codes[f.index_of(ch)]), f.bitmap(f.index_of(ch)))
    print('\n=== 바꾼 뒤 (한국어식) ===')
    show('마침표 ← 8142 자리 (새로 그림)', art_to_gray(PERIOD))
    show('쉼표   ← 8141 자리 (기존 ，8143 글리프 복사)', f.bitmap(f.index_of('，')))
    print('\n=== 그대로 두는 것 ===')
    for ch in ['！', '？', '…']:
        show('%s (%04X)' % (ch, f.codes[f.index_of(ch)]), f.bitmap(f.index_of(ch)))

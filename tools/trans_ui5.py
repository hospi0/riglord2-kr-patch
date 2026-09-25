# -*- coding: utf-8 -*-
"""UI 5차 — 상태창 가운데 «회색 글자 줄»이 깨져 보이던 원인.

실기: 스테이터스 화면에서 내성/약점 줄 아래에 알아볼 수 없는 글자들이
찍혔다(쓸꿍퀸重合문덮짝小昇출 등). `ui_missing.scan()` 은 `len(seg) < 4` 인
조각을 전부 건너뛰는데, 이 줄은 **속성/무기종류 아이콘 한자 한 글자짜리**
문자열들(水 火 風 雷 闇 光 星 精 霊 / 剣 刀 本 槌 弓 無 兜 鎧 盾 飾 / 竜 槍)
이라 전부 그 필터에 걸려 한 번도 검출되지 않았다. 미번역 원문이 우리가
도너로 재배정한 글리프 칸을 그대로 가리켜서 엉뚱한 한글로 찍힌 것
([[feedback_reserve_fnt_slots_of_untranslated]] 류).

`/1_RIG2.BIN` 안전구간(0x7C510~0x7C5AC 근방)에서 실측한 raw 2~3바이트를
**정확히 일치**하는 것만 잡는다 — 길이 필터를 없애는 대신 화이트리스트로
노이즈를 막는다.
"""
TRANS = {
    bytes.fromhex('8c95'): ('剣', '검'),
    bytes.fromhex('9381'): ('刀', '도'),
    bytes.fromhex('967b'): ('本', '책'),
    bytes.fromhex('92c6'): ('槌', '망'),
    bytes.fromhex('8b7c'): ('弓', '활'),
    bytes.fromhex('96b3'): ('無', '무'),
    bytes.fromhex('8a95'): ('兜', '투'),
    bytes.fromhex('8a5a'): ('鎧', '갑'),
    bytes.fromhex('8f82'): ('盾', '방'),
    bytes.fromhex('8ffc'): ('飾', '장'),
    bytes.fromhex('bd926e'): ('ｽ地', 'ｽ땅'),
    bytes.fromhex('9085'): ('水', '수'),
    bytes.fromhex('89ce'): ('火', '화'),
    bytes.fromhex('9597'): ('風', '풍'),
    bytes.fromhex('978b'): ('雷', '뇌'),
    bytes.fromhex('88c5'): ('闇', '암'),
    bytes.fromhex('8cf5'): ('光', '빛'),   # ★사용자 지시: 「광」이 아니라 「빛」
    bytes.fromhex('90af'): ('星', '성'),
    bytes.fromhex('90b8'): ('精', '정'),
    bytes.fromhex('97ec'): ('霊', '영'),
    bytes.fromhex('97b3'): ('竜', '용'),
    bytes.fromhex('9184'): ('槍', '창'),

    # 2차 — 스테이터스 «회색 줄» 상태이상·증감 아이콘.
    # `/RIG2MENU.OVL#1 0xCEAC~0xCED4` + `/1_RIG2.BIN 0x7CE8C~0x7CEB0` 양쪽에 같은
    # 바이트로 있다. 1차에서 `/1_RIG2.BIN` 쪽만 훑어보고 끝내는 바람에 이 11자를
    # 통째로 놓쳤다 — 실기에서 회색 줄이 여전히 깨진 채 남았다.
    # ★표기는 기존 번역 `耐性 眠･操･乱` -> `내성 잠･조･란` 과 맞춘다.
    bytes.fromhex('9380'): ('凍', '동'),
    bytes.fromhex('9790'): ('乱', '란'),
    bytes.fromhex('9180'): ('操', '조'),
    bytes.fromhex('8f64'): ('重', '중'),
    bytes.fromhex('93a7'): ('透', '투'),
    bytes.fromhex('94f2'): ('飛', '비'),
    bytes.fromhex('96b0'): ('眠', '잠'),
    bytes.fromhex('91e5'): ('大', '대'),
    bytes.fromhex('8fac'): ('小', '소'),
    bytes.fromhex('8fb8'): ('昇', '승'),
    bytes.fromhex('92e1'): ('低', '저'),
    # 스킬 설명창 아래 「技Lv」의 技 (`/RIG2MENU.OVL#1 0x69D0` + `/1_RIG2.BIN 0x7C448`)
    bytes.fromhex('8b5a'): ('技', '기'),
    bytes.fromhex('8cae'): ('鍵', '키'),
    bytes.fromhex('926e'): ('地', '지'),

    # 3차 — 스킬 정보창 «사거리 N(X)» 의 괄호 안 사거리 종류표
    #   (`/RIG2MENU.OVL#1 0x693C~0x697C`).
    # ★★괄호까지 한 문자열이라 길이는 4B로 통과하는데 **한자가 «1자뿐»** 이라
    #   `ui_missing` 의 「가나/한자 2자 이상」 문턱에서 잘렸다. 그래서 실기에
    #   `사거리 2(조)` `3(잠)` 처럼 나왔다 — 「조」「잠」은 번역이 아니라
    #   `単`(도너→조) `地`(도너→잠) 의 **도너 칸이 그대로 찍힌 것**이다.
    #   즉 이 한 글자짜리 필터가 「미검출 = 화면 파손」을 그대로 만들어 냈다.
    # 예산 4B = `(` 1B + 한글 1자 2B + `)` 1B 로 정확히 맞는다.
    bytes.fromhex('288f7029'): ('(術)', '(술)'),
    bytes.fromhex('28925029'): ('(単)', '(단)'),
    bytes.fromhex('28915329'): ('(全)', '(전)'),
    bytes.fromhex('28897e29'): ('(円)', '(원)'),
    bytes.fromhex('2892bc29'): ('(直)', '(직)'),
    bytes.fromhex('2892bc3329'): ('(直3)', '(직3)'),
    bytes.fromhex('288ea929'): ('(自)', '(자)'),
    bytes.fromhex('28926e29'): ('(地)', '(지)'),
    bytes.fromhex('28949a3029'): ('(爆0)', '(폭0)'),
    bytes.fromhex('288b5a4c762020202b202020757029'): ('(技Lv   +   up)', '(기Lv   +   up)'),

    # 장비창 칸 라벨 — 한자 1자 + 반각 공백 25개(총 26B). 같은 필터에 걸렸다.
    bytes.fromhex('9590' + '20' * 25): ('武', '무'),
    bytes.fromhex('8a95' + '20' * 25): ('兜', '투'),
    bytes.fromhex('8a5a' + '20' * 25): ('鎧', '갑'),
    bytes.fromhex('8f82' + '20' * 25): ('盾', '방'),
    bytes.fromhex('95e2' + '20' * 25): ('補', '보'),

    # 크기·대상 표기 (전각공백 + 한자)
    bytes.fromhex('81408fac'): ('　小', '　소'),
    bytes.fromhex('81409286'): ('　中', '　중'),
    bytes.fromhex('814091e5'): ('　大', '　대'),
    bytes.fromhex('8ae28140'): ('岩　', '바위'),
    bytes.fromhex('93478140'): ('敵　', '적　'),
}

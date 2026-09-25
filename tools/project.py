"""공통 경로·상수. ★원본 자산은 저장소에 두지 않는다.

★★경로 규칙 (사용자 지정)
    무수정 원본 = F드라이브 **안쪽 중첩 폴더**  ← 조사·기준은 항상 여기서 읽는다
    패치 출력   = F드라이브 **바깥 폴더**       ← Track2~4 와 .cue 가 있는 곳
  건그리폰·Azel 과 같은 중첩 구조다. 안쪽을 덮어쓰면 무수정본을 잃는다.
"""
import os

_F = r'F:\hospi\roms\ss roms\Riglordsaga 2 (Japan) (2M)'
_NAME = 'Riglordsaga 2 (Japan) (2M)'

# --- 읽기 전용 원본 (안쪽 중첩) ---
ORIG_DIR = os.path.join(_F, _NAME)
TRACK1 = os.path.join(ORIG_DIR, '%s (Track 1).bin' % _NAME)
ORIG_CUE = os.path.join(ORIG_DIR, '%s.cue' % _NAME)

# --- 패치 출력 (바깥, 나머지 트랙이 있는 곳) ---
OUT_DIR = _F
OUT_TRACK1 = os.path.join(OUT_DIR, '%s (Track 1).bin' % _NAME)
OUT_CUE = os.path.join(OUT_DIR, '%s.cue' % _NAME)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, 'tools')
WORK = os.path.join(REPO, 'work')
DOCS = os.path.join(REPO, 'docs')

SECTOR = 2352          # MODE1/2352 (Track1 만 데이터, Track2~4 는 AUDIO)
DATA_OFF = 16          # sync(12) + header(4)
DATA_LEN = 2048

# 부트 헤더(IP.BIN) 실측: GS-9084 / V1.100 / 1996-10-13 / CD-1/1 / 지역 J
PRODUCT = 'GS-9084'
VERSION = 'V1.100'

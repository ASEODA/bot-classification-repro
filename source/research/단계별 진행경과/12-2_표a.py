#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
12-2_표a.py  (v2, 2026-09-27 적대 검증 반영)
────────────────────────────────────────────────────────────────────────────
판 기록
    v1  첫 판. 가짜 입력 시험 통과(sha256 5b3e05b7…).
    v2  적대 검증 결정 반영: 동질성·P12-2·혼합 문장의 주 판정을 같은 페르소나·같은 크기의
        완전 모방기 비교(교집합 재매칭, 페르소나id 순, 페르소나 부트스트랩)로 바꾸고 509 행
        차는 보조로 내림. 방향 = 유지 차 부트스트랩 하한 > 0 이면서 유지 75% 이상. 모델
        효과·P12-0은 12-1 짝 계정(둘 다 성공한 슬롯). P12-0 기준선 = 페르소나 안 짝 교환
        순열. 민감도판 귀무 = 106명 슬롯을 뺀 완전 모방기. 수위표에 판정불가·혼재 행.
        미완 표시, uid 서로소 관문, 정제 민감도 보조 행, 거절 슬롯 예시 특성.
    v3  뼈대 4절 v3.2.7 모방 예시 복사 규칙. 12-1 v3 사전의 "계정"(동일·≥0.9 복사 뺀 주 판)을
        모든 판정에 쓴다. 복사 민감도(≥0.8 뺌)와 복사 제외 없음(규칙 이전) 판을 주 판과 나란히
        (i)~(iii)과 참고 판정으로 보인다(판정·예측은 주 판만). 칸별 복사율 보고. 완전 모방기
        비교 행은 구성상 이 규칙과 무관하다(모방 예시 원문 그 자체).

한계 먼저
    · 이 파일은 표 (a)의 수치와 기계 판정(부트스트랩 구간의 부호)을 낸다. 원고에 쓸
      판정 문장은 연구자가 쓴다. 주장 수위표(뼈대 8절)의 행은 규칙대로 고르기만 한다.
    · 행마다 표 (a) 사람 640과 따로 캘리퍼 매칭한다. 한 사람이 여러 행의 짝이 될 수
      있다. 주 판정(귀무 대비·모델 효과)은 두 행을 페르소나 교집합으로 좁혀 같은 규칙으로
      다시 매칭하고 페르소나를 복원 추출한다(E16). 같은 글이면 차가 정확히 0이다. 보조로
      두는 509 행 차는 행마다 독립으로 뽑은 쌍이라 사람 공유 상관을 반영하지 않는다(E6).
    · 모방 충실도의 자질 거리는 슬롯 단위가 아니라 페르소나(계정) 단위다. 모방 예시
      2만 7천여 건을 문서마다 다시 파싱해야 슬롯 단위가 되는데, 12-1이 문서별 전체
      자질을 남기지 않는다(구현 결정 E12). 길이는 슬롯 단위로 본다.
    · 민감도 판(모방 저자 106명 제외)은 새 모델 행과, 12-1이 106명 슬롯을 빼고 다시 파싱한
      완전 모방기 비교 행으로 한다(E13).
    · 10 절차는 관문을 통과한 v1.3(원값 잔차 척도) 함수를 글자 그대로 옮겨 쓴다.
      F 척도의 상당 부분이 희소 단어 사용 여부에서 오므로 희소 제외 판을 항상 병기한다.

목적
    12 뼈대 v3.2 5절 2·3항(표 (a)와 귀무 대비 판정), 5절 9항 보조, 7절 예측
    P12-0·P12-1·P12-2, 8절 주장 수위표의 행 선택.

행 (8개 + 부분추출판 + 민감도판)
    새모델 ×4   12-1 계정사전의 MODEL_SLOT_1~4 칸(페르소나마다 배정 모델 하나)
    재생성      12-1의 gpt-4o-mini 재생성 칸(주 기준 행, 509 페르소나)
    원봇        13-0 사전의 원 봇 504(참고 행)
    완전모방기  13-0 사전의 완전 모방기 509(귀무 행)
    혼합        새 모델 4칸의 생존 계정에서 칸마다 같은 수(가장 작은 칸의 수)를 시드로
                뽑아 합친 행(E4)

열 절차 (행마다)
    0. [라벨 사용] 표 (a) 풀 640(13-0 사람, 역할 표a, 봉인 아님)과 캘리퍼 매칭.
       09-1 caliper_match 그대로: |log 토큰수_구두점제외 비| ≤ 0.10, 그리디, 봇을
       random.Random(20260926)으로 섞고 사람은 uid 오름차순에서 최근접.
    (i)  250자질 δ: F 172 · M형태 58 · M품사 17 · R 3. Cliff's δ(봇 = 그룹1),
         09-1 mann_whitney 그대로. 결측 칸은 그 자질에서만 뺀다(FMR compare와 같음).
         자질 원값은 10-1 build_features(05·07·08 규칙, 축 분류는 04 전체 고정값).
    (ii) 머리 자질 방향 유지 수: 머리 자질 = 재생성 행에서 |δ| ≥ 0.7인 자질. 축 보수
         쌍(대립값이 정확히 둘인 축의 두 값, 축 내부 비율이라 합이 1)은 이름순 앞의
         하나만 둔다(E7). 목록은 JSON에 고정해 적는다. 유지 = δ 부호가 재생성 행과
         같고 0이 아님.
    (iii) 10 v1.3 절차: 10-1 run_procedure 그대로(중심 → 잔차 → 척도 → z(상한 5) →
         블록 거리 → 비율 → 쌍 안 교환 순열 10,000회, 시드 20260926). 위쪽 단측 p.
         희소 제외 판(한 집단 계정의 절반 이상이 원값 0인 자질을 뺌, E8) 병기.
         상한에 걸린 칸의 비율(z = 5)을 집단별로 적는다. 작업 지시의 보조 열이다.
         뼈대 v3.2.3 ⑤는 5절 9의 "범위 밖 백분위 칸 비율"을 ver.1 적용(12-3) 쪽 값으로
         정했으므로 이 열은 그것을 대신하지 않는다.
    (iv) 가족별 Spearman ρ: F · M형태 · M품사 · R 가족마다 그 행의 δ와 재생성 행 δ.

판정 (뼈대 5절 3항. 부트스트랩 2,000회, 시드 고정, 백분위 95% 구간)
    동질성 = (모델 칸 비율 − 완전 모방기 비율)의 95% 하한 > 0. 주 판정은 같은 페르소나·
             같은 크기 비교다: 칸 계정과 같은 페르소나의 완전 모방기 계정을 교집합으로 좁혀
             각각 640과 다시 매칭(봇은 페르소나id 순)하고, 두 행 모두 매칭된 페르소나를
             복원 추출해 10 절차의 비율을 다시 계산(중심·척도까지)한 차의 구간이다(E16).
             P12-2는 F·M 두 블록으로 판정하고 R은 기록만 한다(E9). 509 행과의 독립 쌍
             부트스트랩 차(E6)는 보조 수치다.
    방향   = (모델 칸 유지 수 − 완전 모방기 유지 수)의 같은 페르소나 부트스트랩 95% 하한
             > 0 이면서 유지 수 ≥ 머리 자질 수의 75%. 머리 자질이 0개면 판정불가(E15).
    모델 효과 = 같은 페르소나에서 (모델 칸 − 재생성)의 짝 차이. 재생성 쪽은 그 칸 계정의
             페르소나만 모은 재생성 계정을 같은 규칙으로 640과 따로 매칭한 행이다(같은
             크기의 경쟁, E16). 두 행 모두에서 매칭된 페르소나를 복원 추출하는 페르소나
             부트스트랩으로 비율·유지 수·자질별 δ 차이의 구간을 낸다.
    판정불가 = 매칭 쌍 100 미만인 모델 칸, 또는 같은 페르소나 비교에서 두 행 모두 매칭된
             페르소나가 100 미만(뼈대 4절).
    혼합 문장 = 혼합 − 완전 모방기(같은 페르소나)의 F·M 하한이 둘 다 > 0이면 "좁다". 사람
             대비 순열 p는 기술용이다.
    보조 판: 판정불가가 아닌 행을 그 가운데 가장 작은 쌍 수로 시드 부분추출해 다시 낸다.

예측 (뼈대 7절, 실행 전 고정)
    P12-0  재생성 vs 원 봇(같은 페르소나, 짝 슬롯): 재생성은 13-0 원 봇 계정의 슬롯(복사
           슬롯·정제 탈락 제외)으로, 원 봇은 재생성이 성공한 슬롯으로 한정한 12-1 계정.
           250자질 중 |δ| ≥ 0.147이 25개 이하. 기준선 = 페르소나 안에서 두 계정을 확률
           1/2로 맞바꾸는 짝 교환 순열 1,000회(전체 크기)의 95번째 백분위. 뼈대의 "분할
           반쪽"은 참고로 병기한다. 빗나가면 "원 실행과의 연결" 문장을 쓰지 않는다.
    P12-1  새 모델 4개 각각에서 머리 자질 방향 유지 75% 이상이고 완전 모방기의 유지
           수를 넘는다.
    P12-2  새 모델 4개 각각과 혼합 행에서 F·M 비율 − 완전 모방기 비율의 95% 하한 > 0.

보조 (뼈대 5절 9항)
    모방 충실도(슬롯 단위 길이 · 페르소나 단위 자질 거리와 어긋난 짝 기준선), 칸별 주제
    구성과 CB·결측, 예시가 계획일 뒤인 슬롯의 Tense=Past 비율, 모델별 finish_reason
    분포(12-1이 호출 기록에서 센 값), 행별 상한 칸 비율(범위 밖 백분위 칸은 12-3 몫,
    뼈대 v3.2.3 ⑤). 민감도: 모방 저자가 ver.1 학습 사람 106명인 슬롯을 뺀 계정(12-1
    민감도 사전)으로 새 모델 행의 (i)~(iii)와 판정을 다시 낸다. 뼈대 5절 9의 민감도는
    4·5·7항(12-3) 대상이고, 표 (a) 민감도판은 작업 지시로 더한 것이다(E13).

관문 (하나라도 실패하면 결과 JSON을 쓰지 않고 멈춘다)
    G1 함수 승계: 10 v1.3 함수 22개(10-1 사본 경유)는 10 정본과, caliper_match·
       mann_whitney·ranks_with_ties·normal_cdf는 09-1과, build_features·run_procedure·
       p_lower·func_ast·module_consts는 10-1과 docstring 뺀 AST가 같다. 원 단계(04·05·
       07·08·옛 09)와도 대조. 앞 단계 상수(CAP 포함)도 대조. 이 파일에 줄표 없음.
    G2 손 예제: 10 v1.3 6계정(3쌍) × 3자질의 비율 17/6·교환 8가지·정확 p, 09-1 매칭
       손 예제, 벡터 δ = mann_whitney δ(결측·동점 포함 무작위 자료), Spearman = scipy.
    G3 입력: 10_동질성검정.py sha256 = 동결 v1.3 값, 10-1 1,000회 관문 통과(v1.3),
       13-0 사전 sha256 = 동결·관문통과, 12-1 사전 관문통과(본 실행이면 smoke·시험
       입력 아님), 표 (a) 풀 = 분할.json 표a 640 = 13-0 사람 표a, 봉인 0, 축 분류 =
       FMR 고정값, 형태 58·품사 17 = 07, 기능어 해시, 12-1 v2 구조(변형 계정 일곱 키).
       (v2) 12-1 G3 완결: 끝나지 않은 슬롯 합이 0이고 --allow-incomplete가 꺼져 있어야
       "완결"이다. 아니면 멈추지 않고 JSON 상태와 표 맨 위에 "미완"을 찍는다.
    G4 행 정합: (v2) uid 서로소(13-0 사람 640·원 봇·완전 모방기·12-1 재생성·새 모델 4칸이
       서로 겹치지 않고 12-1 uid가 13-0 uid와 겹치지 않음, 겹치면 중단), 봇 계정 라벨 bot·
       봉인 false, 새 모델 계정의 칸 = 페르소나 모델 슬롯, 행 안(변형은 칸 안) 페르소나
       중복 없음, 매칭 결정성(두 번 같은 쌍), 행마다 벡터 δ = mann_whitney δ(허용 1e-12),
       부트스트랩 결정성(같은 시드 두 번).

라벨 사용 지점 (로그에 [라벨 사용] 마커)
    · 표 (a) 사람 풀 정의(역할 표a, 라벨 human)와 매칭의 봇·사람 구분
    · (i) δ의 그룹 구분, (iii) 집단 중심·잔차와 쌍 안 교환 순열
    · P12-0의 두 무더기(재생성·원 봇 구분은 생성 출처라 라벨이 아니지만 같은 마커로 적음)
    · 부트스트랩(쌍 단위 재추출은 쌍의 봇·사람 자리를 유지)

구현 결정 (규격에 없어 이 파일을 쓰며 정한 것. JSON 설정에도 같은 목록)
    E1  자질 목록·축 분류는 10·10-1과 같게 04 전체 1,869계정에서 유도한다(형태 58 +
        품사 17, 축 분류 = FMR 고정값). 생성 계정에만 있는 키는 무시하고 수를 적는다.
    E2  매칭 시드는 작업 지시대로 20260926(09-1은 20260827). 사람 목록은 uid 오름차순,
        봇 목록은 행 안 uid 오름차순. uid 접두가 행 안에서 같으므로 순서 = 원 봇 uid 순.
    E3  δ 점추정은 09-1 mann_whitney, 부트스트랩은 같은 정의의 벡터 계산(평균 순위,
        scipy rankdata). 둘이 행마다 1e-12 안에서 같은지 관문 G4가 본다.
    E4  혼합 = 칸마다 n = min(칸별 생존 계정 수)개를 random.Random(20260926)으로 칸
        순서(MODEL_SLOT_1~4)대로 sample. 합친 크기는 4n.
    E5  부트스트랩 시드 = numpy default_rng([20260926, 단계 번호, 행 번호]). 단계 번호:
        쌍 부트스트랩 11, 페르소나 부트스트랩 12, 부분추출 13, 분할 반쪽 14, 민감도 15.
    E6  두 행 차이의 쌍 부트스트랩은 행마다 독립으로 뽑은 2,000개 추정치의 차다.
        같은 페르소나 판(동질성 보조, 모델 효과)은 두 행 모두에서 매칭된 페르소나를
        복원 추출한다.
    E7  축 보수 쌍 = 04 축 분류에서 값이 정확히 둘인 축의 두 자질(축 내부 비율이라 합이
        1). 이름순 앞의 것만 머리 자질 후보로 둔다. PUNCT(M품사)와 구두점_비율(R)은
        단조 변환 관계라 δ가 같다. 규칙(축 보수 쌍)에는 없으므로 둘 다 두되, 둘을
        하나로 친 유지 수를 병기한다.
    E8  희소 제외 판의 문턱 = 한 집단 계정 수의 절반 이상이 원값 0(10 결정 O의 256 =
        512 ÷ 2를 행의 쌍 수로 일반화). 결측은 0으로 세지 않는다.
    E9  P12-2와 수위표의 동질성은 F·M 두 블록 모두 하한 > 0. R은 뼈대가 "검정력 부족 시
        보류"라 적었으나 부족의 문턱이 없어 판정에 넣지 않고 하한만 적는다.
    E10 수위표 행 선택은 E18(v2)을 따른다. 판정 문장은 연구자가 쓴다.
    E11 P12-0 기준선(v2) = 짝 교환 순열(페르소나마다 두 계정을 1/2로 맞바꿈, 1,000회).
        분할 반쪽(같은 출처 앞·뒤 절반 비교)은 참고로 병기.
    E12 모방 충실도: 슬롯 단위 길이 = 성공 댓글 원문 글자수 ÷ 모방 예시 원문 글자수의
        log2 중앙값, 두 길이의 Spearman ρ, 0.5~2배 안 비율. 페르소나 단위 자질 거리 =
        그 칸 계정과 같은 페르소나 완전 모방기 계정의 250자질 거리(자질별 |차| ÷ 표 (a)
        640 MAD, 5에서 자름, 평균. MAD 0이면 평균 절대 편차, 그것도 0이면 뺌). 어긋난 짝
        기준선 = 같은 칸 안에서 페르소나 순서를 하나 밀어 짝지은 거리.
    E13 민감도 판은 12-1 민감도 사전의 새 모델 계정으로 매칭부터 다시 한다. 머리 자질
        목록과 재생성 기준 δ는 본 판 값을 쓴다. (v2) 귀무 비교 행은 12-1이 106명 슬롯을
        빼고 다시 파싱한 완전 모방기(완전모방기_106제외)이고 같은 페르소나 판으로 판정한다.
    E14 Tense=Past 점검: 12-1 문서별 요약에서 성공 문서의 Tense=Past 합 ÷ Tense 합을
        예시_계획일뒤 참·거짓으로 나눠 모델별로 적는다(적격 계정 문서만).
    E15 머리 자질이 0개면 방향 판정은 "판정불가(머리 자질 0)"이고 수위표는 "동질성만"을
        고르지 않는다(판정불가 행).
    E16 같은 페르소나 판의 비교 행(재생성·완전 모방기)은 표 (a)의 509 행을 쓰지 않고, 그
        칸 계정의 페르소나만 모은 계정을 따로 매칭해 만든다. 509 행에서는 봇 509이 사람을
        다투어 같은 페르소나라도 다른 사람과 짝지어진다. 그 차이가 모델 효과에 섞인다
        (시험 입력에서 봇 글이 같은 칸이 250자질 중 43개에서 0 밖 구간을 냈다). 같은
        크기의 경쟁으로 따로 매칭하면 봇 글이 같을 때 짝과 차이가 정확히 같아진다.
        (v2) 두 행 모두 페르소나 교집합으로 좁히고 봇을 페르소나id 순으로 넣는다. 주
        판정(동질성·방향·혼합 문장)과 모델 효과가 이 비교를 쓴다.
    E17 P12-1·P12-2는 칸 하나라도 판정불가면 "판정불가"(빗나감으로 치지 않음).
    E18 수위표(v2): 넷 모두 방향·동질성 → "4모델 모두". 하나 이상 둘 다 → "일부 모델만"
        (칸 나열). 그 밖에 판정불가 칸이 있으면 → "판정불가". 넷 모두 방향만 → "방향만",
        넷 모두 동질성만 → "동질성만", 넷 모두 둘 다 아님 → "모두 귀무를 넘지 못함",
        나머지 → "혼재". 판정불가·혼재는 뼈대 8절에 없는 행이라 문장 틀을 두지 않는다.
    E19 거절 슬롯 예시 특성: 호출 중 거절이 한 번이라도 있는 슬롯과 없는 슬롯의 모방 예시
        글자수와 욕설 목록(PROFANITY) 포함 비율. 보고만 한다.

실행 명령 (본 실행은 조정자가 12-1 본 실행 뒤에 한다)
    단계별 진행경과 폴더에서:
    PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u 12-2_표a.py
    화면 출력은 12_표a_출력.log에도 같이 쓴다.
    짧은 점검(부트스트랩 50회·순열 199회·분할 반쪽 50회, 산출은 --out-dir에):
    PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u 12-2_표a.py \\
        --smoke --out-dir /tmp/12-2_smoke
    시험 입력(12-1을 가짜 기록으로 돌린 사전)으로:
        ... 12-2_표a.py --acc121 <12-1_계정사전.json> --sum121 <12-1 요약.json> --out-dir <폴더> [--smoke]
    짧은 점검도 12-1 v2 사전(짝 계정·기준 칸)이 있어야 돈다.
    예상 소요: 약 25~35분(부트스트랩 2,000회 × 행 8 + 같은 페르소나 판 10 + 민감도 4 +
    정제 민감도 칸 수).

산출
    단계별 진행경과/12_표a.json      설정·해시·관문·행별 값·구간·판정·예측·보조·민감도
    단계별 진행경과/12_표a.md        표 (a)와 주장 수위표 행(판정 문장은 연구자가 쓴다)
    단계별 진행경과/12_표a_출력.log  화면 출력
"""

import argparse
import ast
import hashlib
import inspect
import json
import math
import os
import platform
import random
import re
import statistics
import sys
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime

import numpy as np

sys.dont_write_bytecode = True


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ════════════════════════════════════════════════════════════════════════
# [경로·인자]
# ════════════════════════════════════════════════════════════════════════
SCRIPT_PATH = nfc(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPT_PATH)                 # 단계별 진행경과
ROOT = os.path.dirname(HERE)                        # 연구주제
ARCHIVE = f"{ROOT}/# 07-12 실행분 보관 (미학습)"
FMR_DIR = f"{HERE}/09_FMR 통제 재검증"
DATA_DIR = nfc(os.path.expanduser("~/DM_LAB_data/12_OpenRouter"))
PREP_DIR = f"{HERE}/12_OpenRouter생성_준비"
SPLIT_JSON = f"{PREP_DIR}/분할.json"
LEDGER_JSONL = f"{PREP_DIR}/프롬프트대장.jsonl"
MODELID_JSON = f"{PREP_DIR}/모델ID표.json"
FREEZE_JSON = f"{PREP_DIR}/동결.json"
MIMIC_JSONL = f"{DATA_DIR}/완전모방기_문서.jsonl"
ACC130_JSON = f"{DATA_DIR}/13-0_계정사전.json"
ACC121_DEFAULT = f"{DATA_DIR}/12-1_계정사전.json"
SUM121_DEFAULT = f"{HERE}/12-1_생성댓글파싱_요약.json"
MEASURE_JSON = f"{HERE}/04_기능어측정.json"
FEATURE_JSON = f"{HERE}/07_형태자질비교.json"
FUNCWORDS_JSON = f"{HERE}/02_기능어목록.json"
FMR_JSON = f"{FMR_DIR}/FMR_세통제_결과.json"
PY10 = f"{HERE}/10_동질성검정.py"
PY101 = f"{HERE}/10-1_귀무오류율.py"
PY091 = f"{HERE}/09-1_분량통제.py"
GATE101_JSON = f"{HERE}/10-1_귀무오류율_1000회.json"
PREREG = f"{HERE}/12_OpenRouter생성_사전선언_뼈대.md"
ORIGINAL_SOURCES = {
    "compute_rates": f"{HERE}/05_사용률검수.py",
    "build_axis_map": f"{HERE}/07_형태자질비교.py",
    "axis_of": f"{HERE}/07_형태자질비교.py",
    "denom_kind_of": f"{HERE}/07_형태자질비교.py",
    "compute_ratios": f"{HERE}/07_형태자질비교.py",
    "compute_upos_ratios": f"{HERE}/07_형태자질비교.py",
    "coef_variation": f"{HERE}/08_R블록.py",
    "compute_features": f"{HERE}/08_R블록.py",
    "dense_vectors": f"{ARCHIVE}/09_산포검정.py",
    "normalize_apostrophe": f"{HERE}/04_기능어측정.py",
}
FROM_10 = ["compute_rates", "build_axis_map", "axis_of", "denom_kind_of", "compute_ratios",
           "compute_upos_ratios", "coef_variation", "compute_features", "dense_vectors",
           "normalize_apostrophe", "nanmedian_cols", "nanmean_cols", "centers", "residuals",
           "residual_scale", "scaled_residuals", "block_distances", "ratio_of", "perm_ratios",
           "p_values", "exact_p", "five"]
FROM_091 = ["caliper_match", "normal_cdf", "ranks_with_ties", "mann_whitney"]
FROM_101 = ["build_features", "run_procedure", "p_lower", "func_ast", "module_consts"]

ap = argparse.ArgumentParser()
ap.add_argument("--smoke", action="store_true", help="부트스트랩 50회·순열 199회·분할 반쪽 50회")
ap.add_argument("--acc121", default=ACC121_DEFAULT, help="12-1 계정사전(기본 DATA_DIR). 다르면 시험 입력")
ap.add_argument("--sum121", default=SUM121_DEFAULT, help="12-1 요약 JSON")
ap.add_argument("--out-dir", default=None, help="smoke·시험 입력 산출 폴더")
ARGS = ap.parse_args()
SMOKE = ARGS.smoke
ACC121_JSON = nfc(os.path.abspath(os.path.expanduser(ARGS.acc121)))
SUM121_JSON = nfc(os.path.abspath(os.path.expanduser(ARGS.sum121)))
TEST_INPUT = ACC121_JSON != ACC121_DEFAULT or SUM121_JSON != SUM121_DEFAULT
if SMOKE or TEST_INPUT:
    if TEST_INPUT and not ARGS.out_dir:
        sys.exit("시험 입력(--acc121·--sum121)에는 --out-dir를 주십시오.")
    OUT_DIR = nfc(os.path.abspath(ARGS.out_dir)) if ARGS.out_dir else nfc(tempfile.mkdtemp(prefix="12-2_smoke_"))
    if OUT_DIR in (HERE, DATA_DIR):
        sys.exit("smoke·시험 입력 산출을 볼트나 DATA_DIR에 쓰지 않습니다.")
    os.makedirs(OUT_DIR, exist_ok=True)
    tag = "_smoke" if SMOKE else ""
else:
    if ARGS.out_dir:
        sys.exit("--out-dir는 --smoke나 시험 입력과만 씁니다. 본 실행 산출 위치는 고정입니다.")
    OUT_DIR, tag = HERE, ""
OUT_JSON = f"{OUT_DIR}/12_표a{tag}.json"
OUT_MD = f"{OUT_DIR}/12_표a{tag}.md"
LOG_PATH = f"{OUT_DIR}/12_표a{tag}_출력.log"


class Tee:
    """화면과 로그 파일에 같이 쓴다."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
            st.flush()

    def flush(self):
        for st in self.streams:
            st.flush()


LOG_FH = open(LOG_PATH, "w", encoding="utf-8")
sys.stdout = Tee(sys.__stdout__, LOG_FH)


# ════════════════════════════════════════════════════════════════════════
# [설정] 뼈대 v3.2 5절·7절 수치와 작업 지시
# ════════════════════════════════════════════════════════════════════════
SEED = 20260926
CALIPER = 0.10                  # 09-1
N_PERM = 199 if SMOKE else 10_000
N_BOOT = 50 if SMOKE else 2_000
N_SPLIT = 50 if SMOKE else 1_000      # P12-0 짝 교환 순열 수(분할 반쪽 참고도 같은 수)
ALPHA = 0.05
DELTA_NOTABLE = 0.147           # 06·07·09 주목 문턱, P12-0
HEAD_DELTA = 0.7                # 뼈대 5절 2 (ii)
RETAIN_MIN = 0.75               # 뼈대 5절 3 방향
MIN_PAIRS = 100                 # 뼈대 4절 판정불가
P120_MAX = 25                   # P12-0
CI = (2.5, 97.5)
STAGE = {"쌍부트": 11, "페르소나부트": 12, "부분추출": 13, "분할반쪽": 14, "민감도": 15}

# ── 10·10-1 정본 상수 (G1이 원본과 대조) ──
RATE_DIGITS = 6
DENOM_AXIS = "축내부합"
DENOM_TOKEN = "토큰수_구두점제외"
MIN_SENTENCES_CV = 5
CAP = 5
RKEYS = ["문장당_토큰수", "구두점_비율", "문장길이_변동계수"]
BLOCKS = ["F", "M", "R"]
REL_TOL = 1e-12
HAND_TOL = 1e-9
EXPECT_ACCOUNTS = 1869
EXPECT_WORDS = 172
EXPECT_HASH = "382b68572f03bc23"
EXPECT_M_FEAT = 58
EXPECT_M_UPOS = 17
EXPECT_POOL = 640
DELTA_TOL = 1e-12

CELLS = ["MODEL_SLOT_1", "MODEL_SLOT_2", "MODEL_SLOT_3", "MODEL_SLOT_4"]
ROW_ORDER = CELLS + ["혼합", "재생성", "원봇", "완전모방기"]
ROW_CODE = {r: i for i, r in enumerate(ROW_ORDER)}
FAMILIES = ["F", "M형태", "M품사", "R"]
V2_KEYS = ["민감도_106제외", "짝_새모델쪽", "짝_재생성쪽", "짝_P12-0_재생성쪽", "정제민감도",
           "원봇_재생성성공슬롯", "완전모방기_106제외",
           "복사민감도", "복사제외없음", "짝_P12-0_재생성쪽_복사민감도", "짝_P12-0_재생성쪽_복사제외없음",
           "원봇_재생성성공슬롯_복사민감도", "원봇_재생성성공슬롯_복사제외없음"]   # 12-1 v3 사전의 변형 계정
COPY_VARS = {"주": "주 판(동일·≥0.9 복사 뺌, 판정·예측에 씀)", "복사민감도": "복사 민감도(≥0.8 뺌, 보조)",
             "복사제외없음": "복사 제외 없음(규칙 이전, 투명성 보조)"}
PROFANITY = ("fuck", "shit", "bitch", "bastard", "asshole", "cunt", "dick", "piss", "crap", "damn",
             "retard", "moron", "idiot", "scum")                  # E19 보고용 고정 목록

IMPL_DECISIONS = {
    "E1_자질목록": "04 전체 1,869계정에서 유도(형태 58 + 품사 17, 축 분류 = FMR 고정값). 생성 계정에만 있는 키는 무시하고 수를 적음.",
    "E2_매칭시드": "caliper 0.10, 시드 20260926(작업 지시). 사람 uid 오름차순, 봇 행 안 uid 오름차순.",
    "E3_델타": "점추정 09-1 mann_whitney, 부트스트랩은 같은 정의의 벡터 계산(평균 순위). 행마다 1e-12 안 일치 확인.",
    "E4_혼합": "칸마다 min(칸별 생존 계정 수)개를 random.Random(20260926)으로 MODEL_SLOT_1~4 순서대로 sample, 합침.",
    "E5_시드": "numpy default_rng([20260926, 단계, 행]). 단계: 쌍부트 11, 페르소나부트 12, 부분추출 13, 분할반쪽 14, 민감도 15.",
    "E6_차이구간": "(v2 보조) 509 행 대비 차는 행마다 독립으로 뽑은 쌍 부트스트랩 추정치의 차(사람 공유 상관 미반영). 주 판정은 E16.",
    "E7_머리자질": "재생성 행 |δ| ≥ 0.7. 값이 정확히 둘인 축의 두 자질(합 1) 중 이름순 앞의 것만. PUNCT·구두점_비율(단조 관계)은 규칙 밖이라 둘 다 두고 하나로 친 유지 수 병기.",
    "E8_희소문턱": "한 집단 계정의 절반 이상(2 × 0 계정 수 ≥ 쌍 수)이 원값 0인 자질을 뺌. 결측은 0이 아님.",
    "E9_R블록": "P12-2·수위표 동질성은 F·M 모두 하한 > 0. R은 하한만 기록(검정력 부족 문턱이 뼈대에 없음).",
    "E10_수위표": "E18(v2)을 따름. 판정 문장은 연구자가 씀.",
    "E11_분할반쪽": "(v2) P12-0 기준선은 짝 교환 순열. 분할 반쪽(같은 출처 앞·뒤 절반, 1,000회, 95번째 백분위)은 참고.",
    "E12_모방충실도": "슬롯 단위 길이(성공 댓글 원문 글자수 ÷ 예시 원문 글자수의 log2 중앙값, Spearman ρ, 0.5~2배 비율). 페르소나 단위 250자질 거리(|차| ÷ 표a 640 MAD, 상한 5, 평균)와 한 칸 밀어 짝지은 기준선.",
    "E13_민감도": "12-1 민감도 사전의 새 모델 계정으로 매칭부터 다시. 머리 자질·재생성 δ는 본 판. (v2) 귀무 비교 = 12-1 완전모방기_106제외(106명 슬롯 빼고 다시 파싱), 같은 페르소나 판.",
    "E14_과거시제": "12-1 문서별 요약의 Tense_Past 합 ÷ Tense 합을 예시_계획일뒤 참·거짓으로 나눠 모델별로(적격 계정 문서만).",
    "E15_머리자질0": "머리 자질 0개면 방향 판정불가(머리 자질 0). 수위표는 동질성만을 고르지 않음(판정불가 행).",
    "E16_같은페르소나_비교행": "(v2) 두 행을 페르소나 교집합으로 좁혀 각각 640과 다시 매칭(봇은 페르소나id 순), 두 행 모두 매칭된 페르소나를 복원 추출. 동질성·방향·혼합 문장의 주 판정과 모델 효과가 씀. 같은 글이면 차가 정확히 0.",
    "E17_예측판정불가": "P12-1·P12-2는 칸 하나라도 판정불가면 판정불가.",
    "E18_수위표v2": "넷 모두 둘 다 → 4모델 모두, 하나 이상 둘 다 → 일부 모델만(칸 나열), 그 밖에 판정불가 칸 → 판정불가, 넷 모두 방향만 → 방향만, 넷 모두 동질성만 → 동질성만, 넷 모두 둘 다 아님 → 모두 귀무를 넘지 못함, 나머지 → 혼재.",
    "E19_거절슬롯": "거절 호출이 있는 슬롯과 없는 슬롯의 모방 예시 글자수·욕설 목록 포함 비율(보고만).",
    "v2_방향": "유지 차(칸 − 완전 모방기, 같은 페르소나) 부트스트랩 하한 > 0 이면서 유지 ≥ 머리 자질의 75%.",
    "v2_모델효과": "12-1 짝 계정(짝_새모델쪽 대 짝_재생성쪽: 두 모델 모두 성공한 슬롯).",
    "v2_P12-0": "12-1 짝_P12-0_재생성쪽 대 원봇_재생성성공슬롯. 기준선 = 짝 교환 순열 95백분위.",
    "v3_복사규칙": "(뼈대 4절 v3.2.7) 12-1 '계정' = 모방 예시 복사(동일·≥0.9) 슬롯을 뺀 주 판. 모든 판정·예측은 주 판. 복사민감도(≥0.8 뺌)·복사제외없음(규칙 이전) 판은 새 모델 4칸·혼합·재생성 행의 (i)~(iii)과 참고 판정(같은 페르소나 완전 모방기 비교), P12-0 수를 나란히 보임. 혼합은 주 판과 같은 uid의 변형 계정. 완전 모방기 비교 행은 구성상 무관.",
    "보조_상한칸": "상한 칸(z = 5) 비율은 작업 지시의 보조 열. 뼈대 v3.2.3 ⑤는 범위 밖 백분위 칸을 12-3(ver.1 적용) 값으로 정함.",
    "민감도_범위": "뼈대 5절 9 민감도는 4·5·7항(12-3) 대상. 표 (a) 민감도판은 작업 지시로 더함.",
}

PREDICTIONS = {
    "P12-0": "gpt-4o-mini 재생성 vs 원 봇(같은 계정, 1차 댓글만): 250자질 중 |δ| ≥ 0.147이 25개 이하(분할 반쪽 기준선 95% 상한과 병기). 빗나가면 '원 실행과의 연결' 문장을 쓰지 않는다.",
    "P12-1": "새 모델 4개 각각에서 머리 자질 방향 유지가 75% 이상이고, 완전 모방기의 유지 수를 넘는다.",
    "P12-2": "새 모델 4개 각각과 혼합 행에서 F·M 비율 − 완전 모방기 비율의 95% 하한 > 0. R은 검정력 부족 시 보류.",
}
CLAIM_TABLE = {
    "4모델 모두": "BotSim 공개 코드를 바탕으로 재구성·통제한 댓글 생성 조건에서, 생성 모델·복호 조합을 ___로 바꿔도 차이의 방향과 봇 집단 동질성이 생성 절차만의 몫을 넘어 유지되었다(모델당 약 ___쌍, 댓글 한정, Reddit 2023~24 사람 고정)",
    "일부 모델만": "유지된 모델 이름으로 범위 한정. 모델·복호 조합을 함께 적음",
    "방향만": "방향은 모델을 넘지만 동질성은 생성 절차의 산물이다",
    "동질성만": "봇은 모델마다 다른 쪽으로 갈리되 각자 좁게 모인다",
    "모두 귀무를 넘지 못함": "동질성은 BotSim 생성 절차의 산물이며 모델 지문 주장은 철회한다",
    "판정불가": "(뼈대 8절에 없는 행) 판정불가 칸이 있어 수위표 문장을 고르지 않는다. 연구자가 범위를 정한다",
    "혼재": "(뼈대 8절에 없는 행) 칸마다 결과가 갈려 사전 수위표의 한 행에 들지 않는다. 연구자가 쓴다",
    "혼합 행": "여러 모델이 섞인 봇 집단도 사람보다 좁다 / 좁지 않다",
}


# ════════════════════════════════════════════════════════════════════════
# [복사한 함수] 10 v1.3(10-1 사본 경유) · 09-1 · 10-1. G1이 docstring 뺀 AST로 대조한다.
# ════════════════════════════════════════════════════════════════════════
def compute_rates(accounts):
    """[05 compute_rates, 10 정본 경유] 계정별 기능어 사용률. 분모 토큰수_구두점제외, 소수 6자리 반올림. 분모 0 계정은 따로 돌려준다."""
    rates, undefined = {}, []
    # uid 오름차순으로 담는다: 다시 돌려도 파일 순서가 같아야 비교가 쉽다.
    for uid in sorted(accounts):
        a = accounts[uid]
        denom = a["토큰수_구두점제외"]
        if denom == 0:
            undefined.append(uid)
            continue
        counts = a["기능어"]
        rates[uid] = {
            "총사용률": round(sum(counts.values()) / denom, RATE_DIGITS),
            "분모": denom,
            "사용률": {w: round(n / denom, RATE_DIGITS)
                     for w, n in counts.items()},
        }
    return rates, undefined


def build_axis_map(accounts):
    """[07 build_axis_map] 자료 전체에서 축별로 나타난 값 목록을 모은다. 반환 {축: 정렬된 값 목록}."""
    axis_values = {}
    for a in accounts.values():
        for key in a.get("자질", {}):
            axis, sep, val = key.partition("=")
            if not sep:
                # "="가 없는 키. UD 표기에서는 나올 일이 아니지만, 나온다면
                # 축 내부 비율을 정의할 방법이 없으므로 단일값 축으로 본다.
                axis, val = key, ""
            axis_values.setdefault(axis, set()).add(val)
    return {ax: sorted(vs) for ax, vs in axis_values.items()}


def axis_of(key):
    """[07 axis_of] 자질 키에서 축 이름만 떼어 낸다."""
    return key.split("=", 1)[0]


def denom_kind_of(key, axis_map):
    """[07 denom_kind_of] 대립값 2개 이상인 축은 축 내부 합, 아니면 토큰수_구두점제외를 분모로."""
    return DENOM_AXIS if len(axis_map.get(axis_of(key), [""])) >= 2 else DENOM_TOKEN


def compute_ratios(accounts, keys, axis_map):
    """[07 compute_ratios] 형태자질 비율. 없는 키는 0회, 분모 0은 결측(None). 반환 (판정용, 보조용, 출현계정수)."""
    kinds = {k: denom_kind_of(k, axis_map) for k in keys}
    ratios, aux, presence = {}, {}, {k: 0 for k in keys}

    for uid in sorted(accounts):
        a = accounts[uid]
        feats = a.get("자질", {})
        denom_tok = a.get("토큰수_구두점제외", 0)

        # 이 계정의 축별 총 출현수. 축 내부 비율의 분모가 된다.
        axis_total = {}
        for k, n in feats.items():
            ax = axis_of(k)
            axis_total[ax] = axis_total.get(ax, 0) + n

        row, arow = {}, {}
        for k in keys:
            cnt = feats.get(k, 0)          # ← 없는 키는 0회. 위 설명을 보라.
            if cnt:
                presence[k] += 1
            if kinds[k] == DENOM_AXIS:
                d = axis_total.get(axis_of(k), 0)
            else:
                d = denom_tok
            row[k] = None if d == 0 else cnt / d
            # 보조값은 언제나 전체 토큰이 분모다. 토큰수가 0인 계정(01의 적격
            # 기준상 나올 일이 없다)에서만 결측이 된다.
            arow[k] = None if denom_tok == 0 else cnt / denom_tok
        ratios[uid] = row
        aux[uid] = arow
    return ratios, aux, presence


def compute_upos_ratios(accounts, keys):
    """[07 compute_upos_ratios] 품사 비율. 분모는 토큰수_구두점제외."""
    ratios, presence = {}, {k: 0 for k in keys}
    for uid in sorted(accounts):
        a = accounts[uid]
        pos = a.get("UPOS", {})
        denom = a.get("토큰수_구두점제외", 0)
        row = {}
        for k in keys:
            cnt = pos.get(k, 0)            # ← 없는 키는 0회 (자질과 같은 규율)
            if cnt:
                presence[k] += 1
            row[k] = None if denom == 0 else cnt / denom
        ratios[uid] = row
    return ratios, presence


def coef_variation(lengths, min_n=MIN_SENTENCES_CV):
    """[08 coef_variation] 문장 길이 변동계수 = 표본표준편차 ÷ 평균. 문장 5개 미만이거나 평균 0이면 결측."""
    n = len(lengths)
    if n < min_n:
        return None
    mean = sum(lengths) / n
    if mean <= 0:
        return None
    return statistics.stdev(lengths) / mean


def compute_features(accounts):
    """[08 compute_features] R 자질 3종(문장당 토큰수, 구두점 비율, 문장 길이 변동계수). 분모 0은 결측."""
    out = {}
    for uid, a in accounts.items():
        tok = a["토큰수"]
        tok_np = a["토큰수_구두점제외"]
        n_sent = a["문장수"]
        lengths = a["문장길이"]

        row = {}
        # ① 문장당 토큰수: 분모는 문장수
        row["문장당_토큰수"] = (tok_np / n_sent) if n_sent > 0 else None
        # ② 구두점 비율: 분모는 전체 토큰수(구두점을 포함한 쪽이다)
        row["구두점_비율"] = ((tok - tok_np) / tok) if tok > 0 else None
        # ③ 문장 길이 변동계수: 문장 5개 미만은 결측
        row["문장길이_변동계수"] = coef_variation(lengths)
        out[uid] = row
    return out


def dense_vectors(uids, rates, words):
    """[옛 09 dense_vectors, 10 정본 경유] 계정마다 기능어 사용률 벡터. 없는 단어는 0.0."""
    return [[rates[u]["사용률"].get(w, 0.0) for w in words] for u in uids]


def normalize_apostrophe(s):
    """[04 normalize_apostrophe] 굽은 아포스트로피(U+2019)를 곧은 것(U+0027)으로 바꾼다."""
    return s.replace("’", "'")


def nanmedian_cols(M):
    """[10] 열별 중앙값. 열 전체가 nan이면 nan."""
    out = np.full(M.shape[1], np.nan)
    for j in range(M.shape[1]):
        v = M[:, j]
        v = v[~np.isnan(v)]
        if v.size:
            out[j] = np.median(v)
    return out


def nanmean_cols(M):
    """[10 v1.3] 열별 평균. 열 전체가 nan이면 nan. 척도 대체값에 쓴다."""
    out = np.full(M.shape[1], np.nan)
    for j in range(M.shape[1]):
        v = M[:, j]
        v = v[~np.isnan(v)]
        if v.size:
            out[j] = np.mean(v)
    return out


def centers(X, is_bot):
    """[10 v1.3 결정 B3] 집단별 자질 원값 중앙값. 반복 안에서는 가짜 라벨이다."""
    return nanmedian_cols(X[is_bot]), nanmedian_cols(X[~is_bot])


def residuals(X, is_bot, c_bot, c_hum):
    """[10 v1.3] 잔차 = 원값 - 자기 집단 중심. 결측은 결측."""
    C = np.where(is_bot[:, None], c_bot[None, :], c_hum[None, :])
    return X - C


def residual_scale(R):
    """[10 v1.3] 척도 = 두 집단 전 계정 |잔차| 중앙값. 0이면 평균, 평균도 0이거나 정의 2개 미만이면 제외(nan). 반환 (s, 종류 목록)."""
    A = np.abs(R)
    med, mean = nanmedian_cols(A), nanmean_cols(A)
    n_def = (~np.isnan(A)).sum(axis=0)
    s = np.full(R.shape[1], np.nan)
    kind = []
    for j in range(R.shape[1]):
        if n_def[j] < 2:
            kind.append("제외_정의2미만")
        elif med[j] > 0:
            s[j] = med[j]
            kind.append("중앙값")
        elif mean[j] > 0:
            s[j] = mean[j]
            kind.append("평균")
        else:
            kind.append("제외_0")
    return s, kind


def scaled_residuals(R, s):
    """[10 v1.3] z = min(|잔차| ÷ 척도, CAP). 제외 자질은 nan."""
    with np.errstate(invalid="ignore"):
        return np.minimum(np.abs(R) / s[None, :], CAP)


def block_distances(Z):
    """[10 v1.3] 계정별 블록 거리 = 정의된 자질의 z 평균. 사용 자질 수도 돌려준다."""
    used = (~np.isnan(Z)).sum(axis=1)
    with np.errstate(invalid="ignore"):
        d = np.nansum(Z, axis=1) / np.where(used > 0, used, np.nan)
    return d, used


def ratio_of(d_bot, d_hum):
    """[10] 비율 = 사람 거리 중앙값 ÷ 봇 거리 중앙값. 1보다 크면 봇이 더 좁다."""
    return float(np.median(d_hum)) / float(np.median(d_bot))


def perm_ratios(d_bot, d_hum, swaps):
    """[10] 쌍 안 교환 순열. swaps[k, i]가 참이면 k번째 순열에서 쌍 i의 두 거리 값을 맞바꾼다. 중심은 다시 만들지 않는다."""
    b = np.where(swaps, d_hum[None, :], d_bot[None, :])
    h = np.where(swaps, d_bot[None, :], d_hum[None, :])
    return np.median(h, axis=1) / np.median(b, axis=1)


def p_values(obs, perm):
    """[10] 위쪽 단측 p = (순열 ≥ 관측 횟수 + 1) ÷ (순열 수 + 1). 양측 p는 |log| 기준. 상대 허용오차 1e-12."""
    perm = np.asarray(perm, dtype=float)
    ge = int(np.sum(perm >= obs * (1 - REL_TOL)))
    lo = abs(math.log(obs))
    ge2 = int(np.sum(np.abs(np.log(perm)) >= lo * (1 - REL_TOL)))
    n = perm.size
    return (ge + 1) / (n + 1), (ge2 + 1) / (n + 1), ge, ge2


def exact_p(obs, all_ratios):
    """[10] 교환을 전부 늘어놓았을 때의 정확 p(+1 없음). 손 예제 전용."""
    r = np.asarray(all_ratios, dtype=float)
    lo = abs(math.log(obs))
    return (float(np.mean(r >= obs * (1 - REL_TOL))),
            float(np.mean(np.abs(np.log(r)) >= lo * (1 - REL_TOL))))


def five(v):
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    q1, q2, q3 = np.percentile(v, [25, 50, 75])
    return {"n": int(v.size), "최소": float(v.min()), "Q1": float(q1),
            "중앙": float(q2), "Q3": float(q3), "최대": float(v.max()),
            "평균": float(v.mean())}


def caliper_match(bot_ids, human_ids, logd, caliper, seed):
    """[09-1 caliper_match] |log 분모 차| ≤ caliper 그리디 1:1. 봇을 random.Random(seed)로 섞고 사람 목록 앞쪽이 동점에서 이긴다. 반환 (쌍 [(봇, 사람, 거리)], 탈락 봇, 쓰인 사람 집합)."""
    rng = random.Random(seed)
    order = list(bot_ids)
    rng.shuffle(order)

    used = set()
    pairs = []
    unmatched_bots = []
    for b in order:
        lb = logd[b]
        best, best_gap = None, None
        for h in human_ids:
            if h in used:
                continue
            gap = abs(logd[h] - lb)
            if gap > caliper:
                continue
            if best_gap is None or gap < best_gap:
                best, best_gap = h, gap
        if best is None:
            unmatched_bots.append(b)
        else:
            used.add(best)
            pairs.append((b, best, best_gap))
    return pairs, unmatched_bots, used


def normal_cdf(x):
    """[09-1 normal_cdf] 표준정규 누적확률. math.erf로 계산한다."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def ranks_with_ties(values):
    """[09-1 ranks_with_ties] 오름차순 평균 순위와 동점 묶음 크기 목록."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    sv = [values[i] for i in order]
    ranks = [0.0] * n
    ties = []
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sv[j + 1] == sv[i]:
            j += 1
        # order[i..j]가 같은 값이다. 이들이 차지한 자리 번호는 i+1 … j+1 이고
        # 그 평균은 ((i+1) + (j+1)) / 2 다.
        avg = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        if j > i:
            ties.append(j - i + 1)
        i = j + 1
    return ranks, ties


def mann_whitney(group1, group2):
    """[09-1 mann_whitney] Mann-Whitney U(양측, 동점·연속성 보정)와 Cliff's δ = 2·U1/(n1·n2) − 1. 그룹1 기준."""
    n1, n2 = len(group1), len(group2)
    ranks, ties = ranks_with_ties(group1 + group2)
    r1 = sum(ranks[:n1])
    u1 = r1 - n1 * (n1 + 1) / 2.0
    n = n1 + n2

    tie_term = sum(t ** 3 - t for t in ties) / (n * (n - 1))
    var = (n1 * n2 / 12.0) * ((n + 1) - tie_term)
    if var <= 0.0:
        return {"U": u1, "z": 0.0, "p": 1.0, "델타": 0.0, "시그마제곱": 0.0}

    delta = 2.0 * u1 / (n1 * n2) - 1.0
    mid = n1 * n2 / 2.0
    if u1 > mid:
        c = 0.5
    elif u1 < mid:
        c = -0.5
    else:
        c = 0.0
    z = (u1 - mid - c) / math.sqrt(var)
    p = min(1.0, 2.0 * (1.0 - normal_cdf(abs(z))))
    return {"U": u1, "z": z, "p": p, "델타": delta, "시그마제곱": var}


def build_features(accounts, ids, words, axis_map, feat_keys, upos_keys):
    """
    F·M·R 원값 행렬(라벨 없음). 행 순서 = ids. 계정마다 독립으로 계산되므로
    행을 뽑아 쓰는 것과 부분집합으로 다시 계산하는 것이 같은 값이다.
    F : 05 compute_rates(6자리 반올림) → dense_vectors, 없는 단어 0.0
    M : 07 compute_ratios(축 분류는 고정 axis_map) + compute_upos_ratios
    R : 08 compute_features (계정 사전에 문장길이 목록이 있어야 한다)
    10 build_blocks와 같은 조립이다. 관문 2가 10 정본 값 재현으로 확인한다.
    """
    sub = {u: accounts[u] for u in ids}
    rates, undefined = compute_rates(sub)
    if undefined:
        stop(f"F 분모 0 계정이 있습니다: {undefined[:5]}")
    XF = np.array(dense_vectors(ids, rates, words), dtype=float)
    mr, _, _ = compute_ratios(sub, feat_keys, axis_map)
    ur, _ = compute_upos_ratios(sub, upos_keys)
    XM = np.array([[np.nan if mr[u][k] is None else mr[u][k] for k in feat_keys]
                   + [np.nan if ur[u][k] is None else ur[u][k] for k in upos_keys]
                   for u in ids], dtype=float)
    rr = compute_features(sub)
    XR = np.array([[np.nan if rr[u][k] is None else rr[u][k] for k in RKEYS]
                   for u in ids], dtype=float)
    return {"F": XF, "M": XM, "R": XR}


def run_procedure(X, n, swaps):
    """
    10 절차 한 번(v1.3 결정 B3). X = 블록별 원값 행렬, 행 = 봇 n개 다음 사람 n개
    (같은 i가 같은 쌍).
      집단 중심(원값 중앙값) → 잔차 → 척도 s_j → z(상한 5) → 블록 거리 → 비율 →
      쌍 안 교환 순열
    손 예제·본 반복이 모두 이 함수를 지난다. 밑줄로 시작하는 키는 내부 배열이라
    JSON에 넣지 않는다.
    """
    is_bot = np.array([True] * n + [False] * n)
    out = {}
    for b in X:
        cb, ch = centers(X[b], is_bot)
        R = residuals(X[b], is_bot, cb, ch)
        s, kind = residual_scale(R)
        Z = scaled_residuals(R, s)
        d, used = block_distances(Z)
        d_bot, d_hum = d[:n], d[n:]
        with np.errstate(invalid="ignore"):
            over = int(np.sum(np.abs(R) / s[None, :] > CAP))
            g = np.abs(cb - ch) / s                                  # E13
        g = g[~np.isnan(g)]
        gap = float(g.mean()) if g.size else float("nan")
        scale = {"평균대체": kind.count("평균"), "제외": sum(1 for k in kind if k.startswith("제외"))}
        if np.isnan(d).any():
            out[b] = {"무효": "nan 거리", "척도": scale, "상한칸": over}
            continue
        if not np.median(d_bot) > 0:
            out[b] = {"무효": "봇 거리 중앙값 0", "척도": scale, "상한칸": over}
            continue
        r = ratio_of(d_bot, d_hum)
        pr = perm_ratios(d_bot, d_hum, swaps)
        p1, p2, ge, ge2 = p_values(r, pr)
        pl, le = p_lower(r, pr)
        out[b] = {"무효": None, "비율": r, "p_위": p1, "p_아래": pl, "p_양측": p2,
                  "위_횟수": ge, "아래_횟수": le, "양측_횟수": ge2,
                  "봇거리_중앙": float(np.median(d_bot)), "사람거리_중앙": float(np.median(d_hum)),
                  "중심차_평균": gap, "척도": scale, "상한칸": over,
                  "_R": R, "_s": s, "_Z": Z, "_c": (cb, ch), "_d": d, "_used": used, "_pr": pr}
    return out


def p_lower(obs, perm):
    """
    아래쪽 단측 p = (순열비율 ≤ 관측비율 횟수 + 1) ÷ (순열 수 + 1)   (E6)
    10 p_values의 위쪽 비교(≥ obs × (1 - 1e-12))를 거울로 뒤집은 것이다.
    """
    perm = np.asarray(perm, dtype=float)
    le = int(np.sum(perm <= obs * (1 + REL_TOL)))
    return (le + 1) / (perm.size + 1), le


def func_ast(src, name):
    """소스에서 함수 name의 AST를 docstring을 빼고 문자열로. 없으면 None. (13-0 방식)"""
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            body = n.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                n.body = body[1:]
            return ast.dump(n)
    return None


def module_consts(src, names):
    """소스 최상위의 단순 대입 상수를 literal_eval로 읽는다."""
    out = {}
    for n in ast.parse(src).body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            if n.targets[0].id in names:
                try:
                    out[n.targets[0].id] = ast.literal_eval(n.value)
                except ValueError:
                    pass
    return out


# ════════════════════════════════════════════════════════════════════════
# [공통 도구]
# ════════════════════════════════════════════════════════════════════════
def say(msg=""):
    print(msg, flush=True)


def line(title=""):
    say("─" * 74)
    if title:
        say(f"  {title}")
        say("─" * 74)


def label_marker(where):
    say(f"  [라벨 사용] {where}")


def stop(msg):
    """관문 실패. 본 계산에 들어가지 않고 JSON도 쓰지 않는다."""
    say()
    say(f"■ 중단 : {msg}")
    say("  관문을 통과하지 못했습니다. 산출 JSON을 쓰지 않고 끝냅니다.")
    sys.exit(1)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fnum(x):
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else x


def close(a, b, tol=HAND_TOL):
    if a is not None and math.isnan(float(a)):
        a = None
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= tol


def _np_default(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return [fnum(v) for v in o.tolist()]
    raise TypeError(f"JSON으로 쓸 수 없는 값: {type(o).__name__}")


def clean_json(o):
    """nan·numpy 값을 JSON에 넣을 수 있는 꼴로(결측은 null)."""
    if isinstance(o, dict):
        return {str(k): clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean_json(v) for v in o]
    if isinstance(o, np.ndarray):
        return [clean_json(v) for v in o.tolist()]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return fnum(o)
    return o


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(clean_json(obj), f, ensure_ascii=False, indent=1, allow_nan=False, default=_np_default)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def pct(v, qs=CI):
    """백분위 구간. 결측(nan) 추정치는 빼고, 남은 게 없으면 None."""
    v = np.asarray(v, dtype=float)
    v = v[~np.isnan(v)]
    if not v.size:
        return [None, None]
    lo, hi = np.percentile(v, qs)
    return [float(lo), float(hi)]


def pct_cols(M, qs=CI):
    """열마다 백분위 구간(결측 빼고). 반환 (하한 배열, 상한 배열)."""
    lo = np.full(M.shape[1], np.nan)
    hi = np.full(M.shape[1], np.nan)
    for j in range(M.shape[1]):
        v = M[:, j]
        v = v[~np.isnan(v)]
        if v.size:
            lo[j], hi[j] = np.percentile(v, qs)
    return lo, hi


# ════════════════════════════════════════════════════════════════════════
# [이 파일이 더하는 계산]
# ════════════════════════════════════════════════════════════════════════
def cliff_cols(A, B):
    """
    열마다 Cliff's δ = 2U/(n1·n2) − 1 (A = 그룹1). 평균 순위라 동점은 ½. 결측은 그
    열에서만 뺀다. 한쪽이 비면 nan. mann_whitney의 δ와 같은 정의다(E3, G4가 대조).
    """
    from scipy.stats import rankdata
    p = A.shape[1]
    out = np.full(p, np.nan)
    na, nb = np.isnan(A), np.isnan(B)
    full = ~(na.any(axis=0) | nb.any(axis=0))
    n1, n2 = A.shape[0], B.shape[0]
    if full.any() and n1 and n2:
        R = rankdata(np.vstack([A[:, full], B[:, full]]), axis=0)
        U = R[:n1].sum(axis=0) - n1 * (n1 + 1) / 2.0
        out[full] = 2.0 * U / (n1 * n2) - 1.0
    for j in np.where(~full)[0]:
        a, b = A[~na[:, j], j], B[~nb[:, j], j]
        if a.size and b.size:
            R = rankdata(np.concatenate([a, b]))
            U = R[:a.size].sum() - a.size * (a.size + 1) / 2.0
            out[j] = 2.0 * U / (a.size * b.size) - 1.0
    return out


def delta_point(Xb, Xh):
    """(i) 점추정: 자질마다 09-1 mann_whitney(봇 = 그룹1). 결측 칸은 뺀다."""
    out = np.full(Xb.shape[1], np.nan)
    for j in range(Xb.shape[1]):
        a = [float(v) for v in Xb[:, j] if not math.isnan(v)]
        b = [float(v) for v in Xh[:, j] if not math.isnan(v)]
        if a and b:
            out[j] = mann_whitney(a, b)["델타"]
    return out


def spearman(x, y):
    """Spearman ρ = 평균 순위(09-1 ranks_with_ties)의 Pearson 상관. 둘 다 정의된 칸만. 3개 미만·분산 0이면 None."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 3:
        return None
    rx, _ = ranks_with_ties(list(x[m]))
    ry, _ = ranks_with_ties(list(y[m]))
    rx, ry = np.asarray(rx), np.asarray(ry)
    sx, sy = rx.std(), ry.std()
    if sx == 0 or sy == 0:
        return None
    return float(np.mean((rx - rx.mean()) * (ry - ry.mean())) / (sx * sy))


def ratio_only(Xb, Xh, cols):
    """부트스트랩용: 10 v1.3 비율만(중심·척도·z·거리까지 다시). 정의 안 되면 nan."""
    n = Xb.shape[0]
    is_bot = np.array([True] * n + [False] * n)
    out = []
    for b in BLOCKS:
        X = np.vstack([Xb[:, cols[b]], Xh[:, cols[b]]])
        cb, ch = centers(X, is_bot)
        R = residuals(X, is_bot, cb, ch)
        s, _ = residual_scale(R)
        d, _ = block_distances(scaled_residuals(R, s))
        db, dh = d[:n], d[n:]
        if np.isnan(d).any() or not np.median(db) > 0:
            out.append(np.nan)
        else:
            out.append(ratio_of(db, dh))
    return np.array(out)


def homog(Xb, Xh, cols, n_perm):
    """
    (iii) 10 v1.3 절차 한 번(10-1 run_procedure) + 희소 제외 판(E8) + 상한 칸 비율.
    교환 행렬은 numpy default_rng(20260926).random((n_perm, 쌍 수)) < 0.5(10 결정 G).
    """
    n = Xb.shape[0]
    swaps = np.random.default_rng(SEED).random((n_perm, n)) < 0.5
    X = {b: np.vstack([Xb[:, cols[b]], Xh[:, cols[b]]]) for b in BLOCKS}
    res = run_procedure(X, n, swaps)
    out = {}
    for b in BLOCKS:
        r = res[b]
        if r["무효"]:
            out[b] = {"무효": r["무효"]}
            continue
        with np.errstate(invalid="ignore"):
            over = np.abs(r["_R"]) / r["_s"][None, :] > CAP
        defined = ~np.isnan(r["_Z"])
        cap = {"봇_상한칸": int(over[:n].sum()), "사람_상한칸": int(over[n:].sum()),
               "봇_정의칸": int(defined[:n].sum()), "사람_정의칸": int(defined[n:].sum())}
        cap["봇_비율"] = cap["봇_상한칸"] / cap["봇_정의칸"] if cap["봇_정의칸"] else None
        cap["사람_비율"] = cap["사람_상한칸"] / cap["사람_정의칸"] if cap["사람_정의칸"] else None
        zero = X[b] == 0
        zb, zh = zero[:n].sum(axis=0), zero[n:].sum(axis=0)
        drop = (2 * zb >= n) | (2 * zh >= n)
        sens = {"제외_자질수": int(drop.sum()), "남은_자질수": int((~drop).sum())}
        if (~drop).any():
            d, _ = block_distances(r["_Z"][:, ~drop])
            if not np.isnan(d).any() and np.median(d[:n]) > 0:
                rs = ratio_of(d[:n], d[n:])
                p1, p2, _, _ = p_values(rs, perm_ratios(d[:n], d[n:], swaps))
                sens.update({"비율": rs, "p_단측": p1, "p_양측": p2})
        out[b] = {"무효": None, "비율": r["비율"], "p_단측": r["p_위"], "p_양측": r["p_양측"],
                  "p_아래": r["p_아래"], "봇거리_중앙": r["봇거리_중앙"], "사람거리_중앙": r["사람거리_중앙"],
                  "척도": r["척도"], "상한": cap, "희소제외": sens}
    return out


def retention(delta, ref, head_idx):
    """유지 수 = 머리 자질 중 δ 부호가 재생성 행과 같고 0이 아닌 수."""
    return int(sum(1 for j in head_idx
                   if not math.isnan(delta[j]) and delta[j] != 0 and np.sign(delta[j]) == np.sign(ref[j])))


# ════════════════════════════════════════════════════════════════════════
# [관문 G1] 함수 승계
# ════════════════════════════════════════════════════════════════════════
def gate_copies():
    me = open(SCRIPT_PATH, encoding="utf-8").read()
    s10 = open(PY10, encoding="utf-8").read()
    s101 = open(PY101, encoding="utf-8").read()
    s091 = open(PY091, encoding="utf-8").read()
    rows = []
    for names, src, where in ((FROM_10, s10, "10_동질성검정.py"), (FROM_091, s091, "09-1_분량통제.py"),
                              (FROM_101, s101, "10-1_귀무오류율.py")):
        for name in names:
            a, b = func_ast(me, name), func_ast(src, name)
            rows.append({"함수": name, "대상": where, "같음": a is not None and a == b})
    cache = {}
    for name, path in ORIGINAL_SOURCES.items():
        if path not in cache:
            cache[path] = open(path, encoding="utf-8").read()
        a, b = func_ast(me, name), func_ast(cache[path], name)
        rows.append({"함수": name, "대상": os.path.relpath(path, ROOT), "같음": a is not None and a == b})
    bad = [r for r in rows if not r["같음"]]
    say(f"      함수 {len(rows)}건 대조: 10 {len(FROM_10)} · 09-1 {len(FROM_091)} · 10-1 {len(FROM_101)} · "
        f"원 단계 {len(ORIGINAL_SOURCES)}  {'모두 같음' if not bad else '다름: ' + str([r['함수'] for r in bad])}")
    names10 = ["RATE_DIGITS", "DENOM_AXIS", "DENOM_TOKEN", "MIN_SENTENCES_CV", "CAP", "RKEYS",
               "BLOCKS", "REL_TOL", "SEED", "EXPECT_ACCOUNTS", "EXPECT_WORDS", "EXPECT_HASH",
               "EXPECT_M_FEAT", "EXPECT_M_UPOS"]
    c10 = module_consts(s10, names10)
    const_rows = [{"상수": k, "10": c10.get(k), "이 파일": globals()[k], "같음": c10.get(k) == globals()[k]}
                  for k in names10]
    c091 = module_consts(s091, ["CALIPER"])
    const_rows.append({"상수": "CALIPER", "09-1": c091.get("CALIPER"), "이 파일": CALIPER,
                       "같음": c091.get("CALIPER") == CALIPER})
    c101 = module_consts(s101, ["HAND_TOL", "EXPECT_POOL"])
    for k in ("HAND_TOL", "EXPECT_POOL"):
        const_rows.append({"상수": k, "10-1": c101.get(k), "이 파일": globals()[k], "같음": c101.get(k) == globals()[k]})
    cbad = [r["상수"] for r in const_rows if not r["같음"]]
    say(f"      앞 단계 상수 {len(const_rows)}개  {'같음' if not cbad else '다름: ' + ', '.join(cbad)}")
    dash = [hex(c) for c in (0x2014, 0x2013) if chr(c) in me]
    say(f"      이 파일의 줄표·반각 대시  {'없음' if not dash else '있음'}")
    return {"함수": rows, "상수": const_rows, "줄표없음": not dash}, not bad and not cbad and not dash


# ════════════════════════════════════════════════════════════════════════
# [관문 G2] 손 예제
# ════════════════════════════════════════════════════════════════════════
HAND_IDS = ["B1", "B2", "B3", "H1", "H2", "H3"]
HAND_VALUES = {
    "a": {"B1": 3, "B2": 4, "B3": 5, "H1": 0, "H2": 6, "H3": 7},
    "b": {"B1": 10, "B2": 10, "B3": 20, "H1": 30, "H2": 5, "H3": 40},
    "c": {"B1": 0.5, "B2": 0.125, "B3": None, "H1": 0.875, "H2": 0.25, "H3": 0.75},
}
HAND_RATIO = 17 / 6
HAND_SWAPS = {
    (0, 0, 0): 17 / 6, (1, 0, 0): 2 / 3, (0, 1, 0): 2 / 3, (0, 0, 1): 17 / 6,
    (1, 1, 0): 6 / 17, (1, 0, 1): 3 / 2, (0, 1, 1): 3 / 2, (1, 1, 1): 6 / 17,
}
HAND_EXACT_P1 = 2 / 8
MATCH_BOT_DENOM = {"b1": 100, "b2": 1000, "b3": 103}
MATCH_HUM_DENOM = {"h1": 105, "h2": 900, "h3": 1100, "h4": 10000, "h5": 1050}


def gate_hand():
    """10 v1.3 손 예제(10·10-1 상수), 09-1 매칭 손 예제, 벡터 δ·Spearman 대조."""
    from scipy.stats import spearmanr
    fails = []
    feats = ["a", "b", "c"]
    X = np.array([[np.nan if HAND_VALUES[f][u] is None else HAND_VALUES[f][u] for f in feats]
                  for u in HAND_IDS], dtype=float)
    keys = list(HAND_SWAPS)
    res = run_procedure({"H": X}, 3, np.array(keys, dtype=bool))["H"]
    if not close(res["비율"], HAND_RATIO):
        fails.append(f"비율 {res['비율']} ≠ 17/6")
    for k, g in zip(keys, res["_pr"]):
        if not close(g, HAND_SWAPS[k]):
            fails.append(f"교환 {k}: {g}")
    e1, _ = exact_p(res["비율"], res["_pr"])
    if not close(e1, HAND_EXACT_P1):
        fails.append(f"정확 위쪽 p {e1}")
    r_only = ratio_only(X[:3], X[3:], {"F": [0, 1, 2], "M": [0, 1, 2], "R": [0, 1, 2]})
    if not close(r_only[0], HAND_RATIO):
        fails.append(f"ratio_only {r_only[0]}")
    say(f"      10 v1.3 손 예제: 비율 {res['비율']:.6f}(17/6) · 교환 8가지 · 정확 p {e1:.4f}(2/8) · "
        f"ratio_only {r_only[0]:.6f}  {'통과' if not fails else '실패'}")
    logd = {u: math.log(v) for u, v in MATCH_BOT_DENOM.items()}
    logd.update({u: math.log(v) for u, v in MATCH_HUM_DENOM.items()})
    pairs, unmatched, used = caliper_match(sorted(MATCH_BOT_DENOM), sorted(MATCH_HUM_DENOM), logd, CALIPER, SEED)
    got = {b: h for b, h, _ in pairs}
    m_ok = (len(pairs) == 2 and got.get("b2") == "h5" and "h2" not in used and len(unmatched) == 1
            and sum(1 for _, h, _ in pairs if h == "h1") == 1)
    if not m_ok:
        fails.append("매칭 손 예제")
    say(f"      09-1 매칭 손 예제: 쌍 {[(b, h) for b, h, _ in pairs]} · 탈락 {unmatched}  {'통과' if m_ok else '실패'}")
    rng = np.random.default_rng(SEED)
    A = np.round(rng.normal(size=(37, 9)), 1)
    B = np.round(rng.normal(0.3, 1.2, size=(29, 9)), 1)
    A[rng.random(A.shape) < 0.08] = np.nan
    B[rng.random(B.shape) < 0.08] = np.nan
    A[:, 8] = 0.0
    B[:, 8] = 0.0
    dv, dp = cliff_cols(A, B), delta_point(A, B)
    d_ok = bool(np.all(np.abs(dv - dp) <= DELTA_TOL))
    if not d_ok:
        fails.append("벡터 δ ≠ mann_whitney δ")
    x, y = rng.normal(size=40), rng.normal(size=40)
    x[3] = np.nan
    x[5:9] = 1.0
    m = ~np.isnan(x)
    s_ok = abs(spearman(x, y) - spearmanr(x[m], y[m]).statistic) <= 1e-12
    if not s_ok:
        fails.append("Spearman ≠ scipy")
    say(f"      벡터 δ = mann_whitney δ(결측·동점 포함 37×29×9) 최대차 {np.nanmax(np.abs(dv - dp)):.1e} · "
        f"Spearman = scipy {s_ok}  {'통과' if d_ok and s_ok else '실패'}")
    return {"실패": fails, "통과": not fails}, not fails


# ════════════════════════════════════════════════════════════════════════
# [관문 G3] 입력
# ════════════════════════════════════════════════════════════════════════
def load_words():
    raw = json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]
    words = sorted({normalize_apostrophe(w) for w in raw})
    return words, hashlib.sha256("\n".join(words).encode("utf-8")).hexdigest()[:16]


def gate_inputs():
    chk, info = {}, {}
    freeze = json.load(open(FREEZE_JSON, encoding="utf-8"))
    v13 = freeze.get("개정_v3.2.2", {}).get("10_v1.3", {})
    info["10_py_sha256"] = sha256_file(PY10)
    chk["10_v1.3_스크립트_=_동결"] = info["10_py_sha256"] == v13.get("스크립트")
    g = json.load(open(GATE101_JSON, encoding="utf-8"))
    chk["10-1_1000회_v1.3_통과"] = ("v1.3" in str(g["설정"].get("규칙")) and g["설정"].get("반복") == 1000
                                  and g["판정"].get("주판정") == "통과"
                                  and bool((g["판정"].get("이동불변_관문") or {}).get("통과")))
    info["10-1_1000회_sha256"] = sha256_file(GATE101_JSON)
    info["13-0_sha256"] = sha256_file(ACC130_JSON)
    chk["13-0_=_동결"] = info["13-0_sha256"] == freeze.get("13-0_계정사전.json")
    info["분할_sha256"] = sha256_file(SPLIT_JSON)
    chk["분할_=_동결"] = info["분할_sha256"] == freeze.get("분할.json")
    info["대장_sha256"] = sha256_file(LEDGER_JSONL)
    chk["대장_=_동결"] = info["대장_sha256"] == freeze.get("프롬프트대장.jsonl")
    info["완전모방기_sha256"] = sha256_file(MIMIC_JSONL)
    chk["완전모방기_=_동결"] = info["완전모방기_sha256"] == freeze.get("완전모방기_문서.jsonl")
    info["12-1_sha256"] = sha256_file(ACC121_JSON)
    info["12-1_요약_sha256"] = sha256_file(SUM121_JSON)
    d04 = json.load(open(MEASURE_JSON, encoding="utf-8"))
    fmr = json.load(open(FMR_JSON, encoding="utf-8"))
    d07 = json.load(open(FEATURE_JSON, encoding="utf-8"))
    acc04 = d04["계정"]
    chk["04_계정수_1869"] = len(acc04) == EXPECT_ACCOUNTS
    axis_map = build_axis_map(acc04)
    feat_keys = sorted({k for a in acc04.values() for k in a.get("자질", {})})
    upos_keys = sorted({k for a in acc04.values() for k in a.get("UPOS", {})})
    chk["축분류_=_FMR고정값"] = axis_map == fmr["설정"]["axis_map_fixed_to_baseline"]
    chk["형태58_=_07"] = len(feat_keys) == EXPECT_M_FEAT and feat_keys == sorted(d07["형태자질"])
    chk["품사17_=_07"] = len(upos_keys) == EXPECT_M_UPOS and upos_keys == sorted(d07["UPOS"])
    words, fw_hash = load_words()
    chk["기능어_172_해시"] = len(words) == EXPECT_WORDS and fw_hash == EXPECT_HASH
    del d04, fmr, d07
    return chk, info, axis_map, feat_keys, upos_keys, words


# [행 분석]
# ════════════════════════════════════════════════════════════════════════
CTX = {}          # 표 (a) 사람 풀: pool(uid 오름차순) · VH(자질) · logd_h


def fb(x, sign=True):
    """구간 끝 출력. 0.0도 그대로, 결측만 'nan'."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "nan"
    return f"{x:+.3f}" if sign else f"{x:.3f}"


def make_row(name, kind, uids, acc, Vb):
    """
    매칭(09-1 caliper_match) 뒤 쌍 순서의 봇·사람 250자질 행렬을 만든다. 봇 목록은
    (페르소나id, uid) 순이다(결정 E2·E16). 그래서 같은 페르소나 집합에 같은 글이면
    어느 행이든 섞는 순서와 짝이 같다.
    """
    order = sorted(uids, key=lambda u: (acc[u]["페르소나id"], u))
    logd = dict(CTX["logd_h"])
    logd.update({u: math.log(acc[u]["토큰수_구두점제외"]) for u in order})
    pairs, unmatched, _ = caliper_match(order, CTX["pool"], logd, CALIPER, SEED)
    b_ids = [b for b, _, _ in pairs]
    h_ids = [h for _, h, _ in pairs]
    width = len(CTX["VH"][CTX["pool"][0]])
    return {"이름": name, "종류": kind, "계정수": len(uids), "계정": order, "쌍": pairs, "탈락봇": unmatched,
            "봇": b_ids, "사람": h_ids, "페르소나": [acc[b]["페르소나id"] for b in b_ids],
            "Xb": np.array([Vb[u] for u in b_ids], dtype=float).reshape(len(b_ids), width),
            "Xh": np.array([CTX["VH"][u] for u in h_ids], dtype=float).reshape(len(h_ids), width)}


def row_point(row, cols, fam_cols):
    n = len(row["쌍"])
    d = delta_point(row["Xb"], row["Xh"])
    dv = cliff_cols(row["Xb"], row["Xh"])
    both = ~np.isnan(d)
    row["δ_벡터최대차"] = float(np.max(np.abs(d[both] - dv[both]))) if both.any() else 0.0
    row["δ_결측일치"] = bool(np.array_equal(np.isnan(d), np.isnan(dv)))
    row["δ"] = d
    row["주목수"] = {f: int(np.sum(np.abs(d[c]) >= DELTA_NOTABLE)) for f, c in fam_cols.items()}
    row["평균절대δ"] = {f: fnum(np.nanmean(np.abs(d[c]))) if (~np.isnan(d[c])).any() else None
                     for f, c in fam_cols.items()}
    row["10절차"] = homog(row["Xb"], row["Xh"], cols, N_PERM) if n >= 2 else None
    row["판정불가"] = n < MIN_PAIRS
    return row


def boot_row(row, cols, stage, code, B):
    """쌍 부트스트랩: 매칭 쌍을 복원 추출해 비율(F·M·R)과 250자질 δ를 다시 잰다."""
    rng = np.random.default_rng([SEED, stage, code])
    n = len(row["쌍"])
    R = np.full((B, 3), np.nan)
    D = np.full((B, row["Xb"].shape[1]), np.nan)
    if n < 2:
        return R, D
    for b in range(B):
        idx = rng.integers(0, n, n)
        Xb, Xh = row["Xb"][idx], row["Xh"][idx]
        R[b] = ratio_only(Xb, Xh, cols)
        D[b] = cliff_cols(Xb, Xh)
    return R, D


def persona_boot(rowA, rowB, cols, head_idx, ref_delta, code, B):
    """
    같은 페르소나 판(E6·E16): 두 행 모두에서 매칭된 페르소나를 복원 추출해 A − B의 비율·
    유지 수·δ 차이를 낸다. 점추정도 그 페르소나 집합에서 잰다. 두 행이 같은 글이면 모든
    추정치의 차가 정확히 0이다.
    """
    ia = {p: i for i, p in enumerate(rowA["페르소나"])}
    ib = {p: i for i, p in enumerate(rowB["페르소나"])}
    Q = sorted(set(ia) & set(ib))
    out = {"페르소나수": len(Q), "A_쌍": len(rowA["쌍"]), "B_쌍": len(rowB["쌍"])}
    if len(Q) < 2:
        return out
    a_idx = np.array([ia[q] for q in Q])
    b_idx = np.array([ib[q] for q in Q])

    def stats(sa, sb):
        Xa_b, Xa_h = rowA["Xb"][sa], rowA["Xh"][sa]
        Xb_b, Xb_h = rowB["Xb"][sb], rowB["Xh"][sb]
        ra, rb = ratio_only(Xa_b, Xa_h, cols), ratio_only(Xb_b, Xb_h, cols)
        da, db = cliff_cols(Xa_b, Xa_h), cliff_cols(Xb_b, Xb_h)
        return ra, rb, da, db
    ra, rb, da, db = stats(a_idx, b_idx)
    out["점추정"] = {"A_비율": ra, "B_비율": rb, "비율차": ra - rb,
                  "A_유지": retention(da, ref_delta, head_idx), "B_유지": retention(db, ref_delta, head_idx)}
    out["점추정"]["유지차"] = out["점추정"]["A_유지"] - out["점추정"]["B_유지"]
    out["δ차_점추정"] = da - db
    rng = np.random.default_rng([SEED, STAGE["페르소나부트"], code])
    RD = np.full((B, 3), np.nan)
    TD = np.full(B, np.nan)
    DD = np.full((B, len(da)), np.nan)
    for k in range(B):
        s = rng.integers(0, len(Q), len(Q))
        ra_, rb_, da_, db_ = stats(a_idx[s], b_idx[s])
        RD[k] = ra_ - rb_
        TD[k] = retention(da_, ref_delta, head_idx) - retention(db_, ref_delta, head_idx)
        DD[k] = da_ - db_
    out["비율차_구간"] = {b: pct(RD[:, i]) for i, b in enumerate(BLOCKS)}
    out["부트스트랩_무효추정치수"] = {b: int(np.isnan(RD[:, i]).sum()) for i, b in enumerate(BLOCKS)}
    out["유지차_구간"] = pct(TD)
    lo, hi = pct_cols(DD)
    out["δ차_구간"] = (lo, hi)
    out["δ차_구간이_0밖인_자질수"] = int(np.sum((lo > 0) | (hi < 0)))
    return out


def compare(name, accA, VA, accB, VB, cols, head_idx, ref, code, B, pids=None):
    """E16: 두 계정 집합을 페르소나 교집합으로 좁혀 각각 640과 다시 매칭하고 페르소나 부트스트랩."""
    pa = {a["페르소나id"]: u for u, a in accA.items()}
    pb = {a["페르소나id"]: u for u, a in accB.items()}
    P = sorted(set(pa) & set(pb) & (set(pids) if pids is not None else set(pa)))
    rowA = make_row(name + "|A", "비교", [pa[p] for p in P], accA, VA)
    rowB = make_row(name + "|B", "비교", [pb[p] for p in P], accB, VB)
    out = persona_boot(rowA, rowB, cols, head_idx, ref, code, B)
    out["교집합_페르소나"] = len(P)
    return out


def judge_vs_null(cmp, n_pairs_row, n_head):
    """
    동질성(주 판정) = 같은 페르소나 비교 행 차 F·M 하한 > 0. 방향 = 유지 차 하한 > 0 이면서
    유지 ≥ 머리 자질의 75%. 판정불가 = 표 행 쌍 < 100 또는 같은 페르소나 쌍 < 100.
    """
    bad = n_pairs_row < MIN_PAIRS or cmp.get("페르소나수", 0) < MIN_PAIRS
    lo = {b: ((cmp.get("비율차_구간") or {}).get(b) or [None, None])[0] for b in BLOCKS}
    homo_ok = all(lo[b] is not None and lo[b] > 0 for b in ("F", "M"))
    homo = "판정불가(쌍<100)" if bad else ("넘음" if homo_ok else "못 넘음")
    pt = cmp.get("점추정") or {}
    tlo = (cmp.get("유지차_구간") or [None, None])[0]
    if n_head == 0:
        dirj = "판정불가(머리 자질 0)"
    elif bad:
        dirj = "판정불가(쌍<100)"
    else:
        dirj = ("유지" if tlo is not None and tlo > 0 and pt.get("A_유지", 0) >= RETAIN_MIN * n_head
                else "아님")
    return {"판정불가": bad, "동질성": homo, "동질성_하한": lo, "방향": dirj,
            "유지": pt.get("A_유지"), "귀무유지": pt.get("B_유지"), "유지차_구간": cmp.get("유지차_구간"),
            "머리자질수": n_head, "유지율": (pt.get("A_유지") / n_head) if n_head and pt else None}


def say_cmp(name, cmp, label):
    pt = cmp.get("점추정")
    if not pt:
        say(f"      {name:<13} {label}: 교집합 페르소나 {cmp.get('교집합_페르소나')} (비교 불가)")
        return
    say(f"      {name:<13} {label}: 페르소나 {cmp['페르소나수']} · 비율차 " + " · ".join(
        f"{b} {fb(pt['비율차'][i])} [{fb(cmp['비율차_구간'][b][0])}, {fb(cmp['비율차_구간'][b][1])}]"
        for i, b in enumerate(BLOCKS)) +
        f" · 유지 {pt['A_유지']} − {pt['B_유지']} [{fb(cmp['유지차_구간'][0])}, {fb(cmp['유지차_구간'][1])}] · "
        f"δ차 구간 0 밖 {cmp['δ차_구간이_0밖인_자질수']}/250")


# ════════════════════════════════════════════════════════════════════════
# [본 절차]
# ════════════════════════════════════════════════════════════════════════
def main():
    t_start = time.time()
    say("=" * 74)
    say("12-2 표 (a) v2: 새 모델 4 · 혼합 · 재생성 · 원 봇 · 완전 모방기 × 표 (a) 사람 640")
    say("=" * 74)
    run_info = {"실행": datetime.now().astimezone().isoformat(timespec="seconds"),
                "python": platform.python_version(), "numpy": np.__version__,
                "스크립트_sha256": sha256_file(SCRIPT_PATH), "sys.flags.optimize": sys.flags.optimize,
                "smoke": SMOKE, "시험입력": TEST_INPUT, "12-1_사전": ACC121_JSON, "12-1_요약": SUM121_JSON,
                "순열": N_PERM, "부트스트랩": N_BOOT, "교환순열(P12-0)": N_SPLIT, "시드": SEED}
    for k, v in run_info.items():
        say(f"  {k}: {v}")
    say(f"  산출 {OUT_JSON}\n  표 {OUT_MD}\n  로그 {LOG_PATH}")

    # ── [1/9] G1 ────────────────────────────────────────────
    say("\n[1/9] G1 함수 승계(docstring 뺀 AST) · 상수")
    copy_res, copy_ok = gate_copies()
    if not copy_ok:
        stop("복사한 함수나 상수가 원본과 다릅니다.")

    # ── [2/9] G2 ────────────────────────────────────────────
    say("\n[2/9] G2 손 예제")
    hand_res, hand_ok = gate_hand()
    if not hand_ok:
        stop("손 예제 실패: " + "; ".join(hand_res["실패"]))

    # ── [3/9] G3 입력 ───────────────────────────────────────
    say("\n[3/9] G3 입력: 동결 해시 · 10-1 관문 · 13-0·12-1 사전 · 표 (a) 풀 · 자질 목록 · 완결")
    chk, info, axis_map, feat_keys, upos_keys, words = gate_inputs()
    acc130 = json.load(open(ACC130_JSON, encoding="utf-8"))
    acc121 = json.load(open(ACC121_JSON, encoding="utf-8"))
    sum121 = json.load(open(SUM121_JSON, encoding="utf-8"))
    st121 = acc121["설정"]
    chk["13-0_관문통과"] = acc130["설정"].get("관문통과") is True and acc130["설정"].get("smoke") is False
    chk["12-1_관문통과"] = st121.get("관문통과") is True
    if not (SMOKE or TEST_INPUT):
        chk["12-1_본실행"] = st121.get("smoke") is False and st121.get("시험입력") is False
    chk["12-1_요약_=_사전"] = (sum121.get("산출", {}).get("sha256") == info["12-1_sha256"])
    chk["12-1_v2_구조"] = all(k in acc121 for k in V2_KEYS)
    split = json.load(open(SPLIT_JSON, encoding="utf-8"))["분할"]
    roles = {r["uid"]: r["역할"] for r in split["사람"]["역할표"]}
    label_marker("표 (a) 풀 = 13-0 사람 중 역할 표a(라벨로 정의된 사람 풀의 분할), 봉인 제외")
    A130 = acc130["계정"]
    pool = sorted(u for u, a in A130.items() if a["집단"] == "사람" and "표a" in (a.get("역할") or []))
    pool_sp = sorted(u for u, r in roles.items() if "표a" in r)
    chk["표a_640_=_분할"] = len(pool) == EXPECT_POOL and pool == pool_sp
    chk["표a_봉인0_human"] = all(A130[u]["봉인"] is False and A130[u]["라벨"] == "human" for u in pool)
    for k, v in chk.items():
        say(f"      {k:<26} {'통과' if v else '실패'}")
    if not all(chk.values()):
        stop("입력 관문 실패: " + ", ".join(k for k, v in chk.items() if not v))
    g3c = (sum121.get("관문") or {}).get("G3_완결") or {}
    incomplete = bool(g3c.get("합", 1)) or bool(g3c.get("허용플래그", True))
    status = "미완(생성 미완결 슬롯 또는 --allow-incomplete)" if incomplete else "완결"
    say(f"      12-1 G3 완결: 끝나지 않은 슬롯 {g3c.get('합')} · 허용 플래그 {g3c.get('허용플래그')} → {status}")
    if incomplete:
        say("      ■ 미완: 결과 JSON과 표에 '미완'을 찍는다.")

    # ── [4/9] 자질 원값 · uid 서로소 ─────────────────────────────
    say("\n[4/9] 자질 원값: 10-1 build_features(05·07·08 규칙, 04 고정 축 분류) · 250자질 · uid 서로소")
    mid = json.load(open(MODELID_JSON, encoding="utf-8"))
    A121 = acc121["계정"]
    groups = {
        "사람": {u: A130[u] for u in pool},
        "원봇": {u: a for u, a in A130.items() if a["집단"] == "원봇"},
        "완전모방기": {u: a for u, a in A130.items() if a["집단"] == "완전모방기"},
        "재생성": {u: a for u, a in A121.items() if a["칸"] == "기준"},
    }
    for c in CELLS:
        groups[c] = {u: a for u, a in A121.items() if a["칸"] == c}
    names = list(groups)
    clash = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            x = set(groups[names[i]]) & set(groups[names[j]])
            if x:
                clash[f"{names[i]}∩{names[j]}"] = sorted(x)[:5]
    x = set(A121) & set(A130)
    if x:
        clash["12-1∩13-0"] = sorted(x)[:5]
    g_uid = {"겹침": clash, "통과": not clash}
    say(f"      uid 서로소(13-0 집단 · 12-1 칸): {'통과' if not clash else '실패 ' + str(clash)}")
    if clash:
        stop(f"uid가 집단 사이에서 겹칩니다: {clash}")
    var = {k: acc121[k] for k in V2_KEYS}
    V, extra = {}, Counter()
    VAR = {k: {} for k in V2_KEYS}

    def vecs(accs, target):
        if not accs:
            return
        ids = sorted(accs)
        X = build_features(accs, ids, words, axis_map, feat_keys, upos_keys)
        M = np.hstack([X["F"], X["M"], X["R"]])
        for i, u in enumerate(ids):
            target[u] = M[i]
            extra["형태"] += len(set(accs[u]["자질"]) - set(feat_keys))
            extra["품사"] += len(set(accs[u]["UPOS"]) - set(upos_keys))
    for g, accs in groups.items():
        vecs(accs, V)
    for k in V2_KEYS:
        vecs(var[k], VAR[k])
    n_f, n_m = len(words), len(feat_keys) + len(upos_keys)
    cols = {"F": list(range(0, n_f)), "M": list(range(n_f, n_f + n_m)),
            "R": list(range(n_f + n_m, n_f + n_m + 3))}
    fam_cols = {"F": np.arange(0, n_f), "M형태": np.arange(n_f, n_f + len(feat_keys)),
                "M품사": np.arange(n_f + len(feat_keys), n_f + n_m), "R": np.arange(n_f + n_m, n_f + n_m + 3)}
    keys250 = list(words) + feat_keys + upos_keys + list(RKEYS)
    CTX.update({"pool": pool, "VH": {u: V[u] for u in pool},
                "logd_h": {u: math.log(A130[u]["토큰수_구두점제외"]) for u in pool}})
    say(f"      자질 {len(keys250)} = F {n_f} + M형태 {len(feat_keys)} + M품사 {len(upos_keys)} + R 3 · "
        f"04 밖 키(무시) 형태 {extra['형태']} · 품사 {extra['품사']} (계정×키)")
    for g, accs in groups.items():
        say(f"      {g:<13} 계정 {len(accs)}")
    for k in V2_KEYS:
        say(f"      변형 {k:<18} 계정 {len(var[k])}")

    g4 = {"uid서로소": g_uid["통과"]}
    pinfo = {p["페르소나id"]: p for p in split["페르소나"]}
    for c in CELLS:
        g4[f"{c}_칸=모델슬롯"] = all(pinfo[a["페르소나id"]]["모델슬롯"] == c for a in groups[c].values())
    for g in ("원봇", "완전모방기", "재생성") + tuple(CELLS):
        accs = groups[g]
        g4[f"{g}_라벨bot_봉인아님"] = all(a["라벨"] == "bot" and a["봉인"] is False for a in accs.values())
        pids = [a["페르소나id"] for a in accs.values()]
        g4[f"{g}_페르소나중복없음"] = len(pids) == len(set(pids))
    for k in V2_KEYS:
        byc = defaultdict(list)
        for a in var[k].values():
            byc[a["칸"]].append(a["페르소나id"])
        g4[f"변형_{k}_칸안_페르소나중복없음"] = all(len(v) == len(set(v)) for v in byc.values())
    if not all(g4.values()):
        stop("G4 계정 정합 실패: " + ", ".join(k for k, v in g4.items() if not v))
    say(f"      G4 계정 정합 {len(g4)}항목 통과")

    # ── [5/9] 행 · 매칭 · 점추정 ──────────────────────────────
    say("\n[5/9] 행: 캘리퍼 매칭(0.10, 시드 20260926, 봇은 페르소나id 순) → (i) δ · (iii) 10 v1.3 절차")
    label_marker("매칭: 행의 봇과 표 (a) 사람 640을 짝지음 · δ 그룹 구분 · 10 절차 중심·순열")
    ncell = {c: len(groups[c]) for c in CELLS}
    n_each = min(ncell.values())
    rng_mix = random.Random(SEED)
    mix = []
    for c in CELLS:
        mix += rng_mix.sample(sorted(groups[c]), n_each)
    all_acc = {}
    for g in groups.values():
        all_acc.update(g)
    mix_acc = {u: all_acc[u] for u in mix}
    say(f"      혼합: 칸별 생존 {ncell} → 칸마다 {n_each} × 4 = {len(mix)}")
    rows = {}
    spec = [(c, "새모델", groups[c]) for c in CELLS] + [("혼합", "혼합", mix_acc)] + \
           [(g, g, groups[g]) for g in ("재생성", "원봇", "완전모방기")]
    for name, kind, accs in spec:
        t0 = time.time()
        row = make_row(name, kind, list(accs), accs, V)
        rows[name] = row_point(row, cols, fam_cols)
        h = rows[name]["10절차"] or {}

        def rs(b):
            x_ = h.get(b) or {}
            return f"{x_['비율']:.3f}(p {x_['p_단측']:.4f})" if x_.get("비율") is not None else "무효"
        say(f"      {name:<13} 계정 {row['계정수']:>4} · 쌍 {len(row['쌍']):>4} · 탈락 봇 {len(row['탈락봇']):>3} · "
            f"주목 {row['주목수']} · F {rs('F')} · M {rs('M')} · R {rs('R')} · "
            f"{'판정불가(쌍<100) · ' if row['판정불가'] else ''}{time.time() - t0:.1f}초")
    again = make_row("재확인", "비교", list(groups["완전모방기"]), groups["완전모방기"], V)["쌍"]
    g4["매칭결정성(완전모방기 두 번)"] = again == rows["완전모방기"]["쌍"]
    g4["δ벡터=mann_whitney(전 행)"] = all(r["δ_벡터최대차"] <= DELTA_TOL and r["δ_결측일치"] for r in rows.values())
    say(f"      매칭 결정성 {g4['매칭결정성(완전모방기 두 번)']} · 벡터 δ = mann_whitney(전 행) "
        f"{g4['δ벡터=mann_whitney(전 행)']} (최대차 {max(r['δ_벡터최대차'] for r in rows.values()):.1e})")
    if not (g4["매칭결정성(완전모방기 두 번)"] and g4["δ벡터=mann_whitney(전 행)"]):
        stop("G4 행 정합 실패")

    # (ii) 머리 자질 · (iv) ρ
    ref = rows["재생성"]["δ"]
    binary_axes = {ax: vs for ax, vs in axis_map.items() if len(vs) == 2}
    comp_drop, comp_check = set(), []
    for ax, vs in binary_axes.items():
        k1, k2 = f"{ax}={vs[0]}", f"{ax}={vs[1]}"
        if k1 in keys250 and k2 in keys250:
            comp_drop.add(keys250.index(max(k1, k2)))
            a, b = ref[keys250.index(k1)], ref[keys250.index(k2)]
            comp_check.append({"축": ax, "자질": [k1, k2], "δ": [fnum(a), fnum(b)],
                               "합": fnum(a + b) if not (math.isnan(a) or math.isnan(b)) else None})
    head_idx = [j for j in range(len(keys250)) if not math.isnan(ref[j]) and abs(ref[j]) >= HEAD_DELTA
                and j not in comp_drop]
    n_head = len(head_idx)
    punct_pair = [keys250.index("PUNCT"), keys250.index("구두점_비율")] if "PUNCT" in keys250 else []
    head = [{"자질": keys250[j], "가족": next(f for f, c in fam_cols.items() if j in c), "재생성δ": ref[j]}
            for j in head_idx]
    say(f"\n      (ii) 머리 자질(재생성 |δ| ≥ {HEAD_DELTA}, 축 보수 쌍 하나만): {n_head}개 "
        f"{[keys250[j] for j in head_idx][:20]}{' …' if n_head > 20 else ''}")
    for name, row in rows.items():
        row["유지"] = retention(row["δ"], ref, head_idx)
        both_p = all(j in head_idx for j in punct_pair) if punct_pair else False
        row["유지_구두점하나로"] = (row["유지"] - (1 if both_p and all(
            np.sign(row["δ"][j]) == np.sign(ref[j]) and row["δ"][j] != 0 for j in punct_pair) else 0))
        row["ρ"] = {f: spearman(row["δ"][c], ref[c]) for f, c in fam_cols.items()}

    # ── [6/9] 쌍 부트스트랩(표 구간 · 보조 509 행 차) ─────────────────
    say(f"\n[6/9] 쌍 부트스트랩 {N_BOOT:,}회(행마다 독립): 표의 구간과 보조 수치(509 행 대비 차)")
    label_marker("쌍 부트스트랩: 매칭 쌍 단위 재추출(봇·사람 자리 유지)")
    boots = {}
    for name, row in rows.items():
        t0 = time.time()
        R, D = boot_row(row, cols, STAGE["쌍부트"], ROW_CODE[name], N_BOOT)
        boots[name] = (R, D)
        T = np.array([retention(D[b], ref, head_idx) for b in range(N_BOOT)], dtype=float)
        row["구간"] = {"비율": {b: pct(R[:, i]) for i, b in enumerate(BLOCKS)}, "유지": pct(T), "δ": pct_cols(D)}
        row["부트_무효"] = {b: int(np.isnan(R[:, i]).sum()) for i, b in enumerate(BLOCKS)}
        row["_T"] = T
        say(f"      {name:<13} 비율 구간 " + " · ".join(
            f"{b} [{fb(row['구간']['비율'][b][0], False)}, {fb(row['구간']['비율'][b][1], False)}]" for b in BLOCKS)
            + f" · 유지 {row['유지']}/{n_head} · {time.time() - t0:.0f}초")
    Rm, Dm = boots["완전모방기"]
    Rr, Dr = boots["재생성"]
    for name, row in rows.items():
        R, D = boots[name]
        row["ρ_구간"] = {}
        for f, c in fam_cols.items():
            vals = [spearman(D[b][c], Dr[b][c]) for b in range(N_BOOT)]
            row["ρ_구간"][f] = pct(np.array([np.nan if v is None else v for v in vals], dtype=float))
    R_boot_check, _ = boot_row(rows["완전모방기"], cols, STAGE["쌍부트"], ROW_CODE["완전모방기"], min(N_BOOT, 5))
    g4["부트스트랩결정성"] = bool(np.array_equal(R_boot_check, Rm[:min(N_BOOT, 5)], equal_nan=True))
    say(f"      부트스트랩 결정성(같은 시드 두 번) {g4['부트스트랩결정성']}")
    if not g4["부트스트랩결정성"]:
        stop("부트스트랩이 결정적이지 않습니다.")
    mim = rows["완전모방기"]
    secondary = {}
    for name in CELLS + ["혼합"]:
        R, _ = boots[name]
        diff = R - Rm
        secondary[name] = {b: {"차_점추정": fnum(((rows[name]["10절차"] or {}).get(b) or {}).get("비율", np.nan)
                                              - ((mim["10절차"] or {}).get(b) or {}).get("비율", np.nan)),
                              "구간": pct(diff[:, i])} for i, b in enumerate(BLOCKS)}
        secondary[name]["유지차_구간"] = pct(rows[name]["_T"] - mim["_T"])

    # ── [7/9] 같은 페르소나 판: 주 판정(귀무 대비) · 모델 효과 ─────────
    say(f"\n[7/9] 같은 페르소나 판(페르소나 부트스트랩 {N_BOOT:,}회, 교집합 재매칭·페르소나id 순, E16)")
    label_marker("페르소나 부트스트랩: 두 행 모두 매칭된 페르소나를 재추출")
    judge, effects = {}, {}
    paired_new = var["짝_새모델쪽"]
    paired_base = var["짝_재생성쪽"]
    for k, name in enumerate(CELLS + ["혼합"]):
        t0 = time.time()
        accs = groups[name] if name in CELLS else mix_acc
        null_cmp = compare(f"{name}~완전모방기", accs, V, groups["완전모방기"], V, cols, head_idx, ref, 200 + k, N_BOOT)
        pa = {u: paired_new[u] for u in accs if u in paired_new}
        eff = compare(f"{name}~재생성(짝)", pa, VAR["짝_새모델쪽"], paired_base, VAR["짝_재생성쪽"],
                      cols, head_idx, ref, 100 + k, N_BOOT)
        j = judge_vs_null(null_cmp, len(rows[name]["쌍"]), n_head)
        j.update({"쌍": len(rows[name]["쌍"]), "보조_509행차": secondary[name]})
        judge[name] = j
        effects[name] = {"귀무비교": null_cmp, "모델효과": eff}
        say_cmp(name, null_cmp, "− 완전 모방기(주)")
        say(f"      {'':<13} → 동질성 {j['동질성']} · 방향 {j['방향']}")
        say_cmp(name, eff, "− 재생성(짝 계정, 모델 효과)")
        say(f"      {'':<13} ({time.time() - t0:.0f}초)")

    # ── [8/9] 부분추출판 · P12-0 · 민감도판 · 정제 민감도 ─────────────
    say("\n[8/9] 보조 판: 부분추출 · P12-0 · 민감도(106명 제외) · 정제 민감도")
    ok_rows = [r for r in ROW_ORDER if not rows[r]["판정불가"]]
    n_min = min(len(rows[r]["쌍"]) for r in ok_rows) if ok_rows else 0
    sub, sub_ref = {}, None
    for name in ["재생성"] + [r for r in ROW_ORDER if r != "재생성"]:
        row = rows[name]
        if name not in ok_rows or n_min < 2:
            sub[name] = {"제외": "판정불가 행(쌍 < 100)"}
            continue
        rng = np.random.default_rng([SEED, STAGE["부분추출"], ROW_CODE[name]])
        idx = np.sort(rng.choice(len(row["쌍"]), n_min, replace=False))
        Xb, Xh = row["Xb"][idx], row["Xh"][idx]
        d = delta_point(Xb, Xh)
        if name == "재생성":
            sub_ref = d
        h = homog(Xb, Xh, cols, N_PERM)
        sub[name] = {"쌍": n_min, "주목수": {f: int(np.sum(np.abs(d[c]) >= DELTA_NOTABLE)) for f, c in fam_cols.items()},
                     "유지": retention(d, ref, head_idx),
                     "ρ(부분추출 재생성 대비)": ({f: spearman(d[c], sub_ref[c]) for f, c in fam_cols.items()}
                                          if sub_ref is not None else None),
                     "10절차": h}
        say(f"      {name:<13} 쌍 {n_min} · 유지 {sub[name]['유지']}/{n_head} · " + " · ".join(
            f"{b} {fb(((h or {}).get(b) or {}).get('비율'), False)}" for b in BLOCKS))

    label_marker("P12-0: 재생성(원 봇 슬롯 한정)과 원 봇(재생성 성공 슬롯 한정) 두 무더기")
    rg_acc, ob_acc = var["짝_P12-0_재생성쪽"], var["원봇_재생성성공슬롯"]
    rg = {a["페르소나id"]: u for u, a in rg_acc.items()}
    ob = {a["페르소나id"]: u for u, a in ob_acc.items()}
    common = sorted(set(rg) & set(ob))
    XA = np.array([VAR["짝_P12-0_재생성쪽"][rg[p]] for p in common], dtype=float).reshape(len(common), len(keys250))
    XB = np.array([VAR["원봇_재생성성공슬롯"][ob[p]] for p in common], dtype=float).reshape(len(common), len(keys250))
    d0 = delta_point(XA, XB) if common else np.full(len(keys250), np.nan)
    cnt0 = int(np.sum(np.abs(d0) >= DELTA_NOTABLE))
    rng = np.random.default_rng([SEED, STAGE["분할반쪽"], 1])
    swap_cnt = []
    for _ in range(N_SPLIT):
        s = rng.random(len(common)) < 0.5
        A1 = np.where(s[:, None], XB, XA)
        B1 = np.where(s[:, None], XA, XB)
        swap_cnt.append(int(np.sum(np.abs(cliff_cols(A1, B1)) >= DELTA_NOTABLE)))
    rng = np.random.default_rng([SEED, STAGE["분할반쪽"], 0])
    half = len(common) // 2
    base_half = {"원봇": [], "재생성": []}
    for _ in range(N_SPLIT):
        perm = rng.permutation(len(common))
        a_i, b_i = perm[:half], perm[half:2 * half]
        for nm, M in (("원봇", XB), ("재생성", XA)):
            base_half[nm].append(int(np.sum(np.abs(cliff_cols(M[a_i], M[b_i])) >= DELTA_NOTABLE)))
    up_swap = float(np.percentile(swap_cnt, 95)) if swap_cnt else None
    p120 = {"페르소나": len(common), "|δ|≥0.147_자질수": cnt0, "문턱": P120_MAX,
            "가족별": {f: int(np.sum(np.abs(d0[c]) >= DELTA_NOTABLE)) for f, c in fam_cols.items()},
            "기준선_짝교환_95백분위": up_swap, "기준선_짝교환_평균": fnum(np.mean(swap_cnt)) if swap_cnt else None,
            "기준선_짝교환_반복": N_SPLIT,
            "참고_분할반쪽_95백분위": {nm: float(np.percentile(v, 95)) for nm, v in base_half.items()} if half else None,
            "짝": "재생성 = 13-0 원 봇 계정 슬롯으로 한정, 원 봇 = 재생성 성공 슬롯으로 한정(12-1 D11·D13)",
            "δ": dict(zip(keys250, d0)),
            "판정": "판정불가(페르소나 없음)" if not common else ("적중" if cnt0 <= P120_MAX else "빗나감")}
    p120["빗나감_시"] = "'원 실행과의 연결' 문장을 쓰지 않는다." if p120["판정"] == "빗나감" else None
    say(f"      P12-0 재생성 vs 원 봇(짝 슬롯) {len(common)} 페르소나: |δ| ≥ {DELTA_NOTABLE} 자질 {cnt0}개 "
        f"(문턱 ≤ {P120_MAX}) → {p120['판정']} · 짝 교환 기준선 95백분위 {up_swap} · 분할 반쪽(참고) "
        f"{p120['참고_분할반쪽_95백분위']}")

    sens = {}
    mim106 = var["완전모방기_106제외"]
    for k, c in enumerate(CELLS):
        sacc = {u: a for u, a in var["민감도_106제외"].items() if a["칸"] == c}
        if not sacc:
            sens[c] = {"계정수": 0}
            continue
        row = row_point(make_row(c + "_민감도", "민감도", list(sacc), sacc, VAR["민감도_106제외"]), cols, fam_cols)
        row["유지"] = retention(row["δ"], ref, head_idx)
        cmp = compare(f"{c}_민감도~완전모방기106", sacc, VAR["민감도_106제외"], mim106, VAR["완전모방기_106제외"],
                      cols, head_idx, ref, 300 + k, N_BOOT)
        j = judge_vs_null(cmp, len(row["쌍"]), n_head)
        sens[c] = {"계정수": len(sacc), "쌍": len(row["쌍"]), "주목수": row["주목수"],
                   "δ": dict(zip(keys250, row["δ"])), "유지": row["유지"], "10절차": row["10절차"],
                   "귀무비교(완전모방기 106 제외)": public_cmp(cmp, keys250), "판정": j}
        say(f"      민감도 {c:<13} 계정 {len(sacc)} · 쌍 {len(row['쌍'])} · 동질성 {j['동질성']} · 방향 {j['방향']}")

    clean_sens = {}
    csacc_all = var["정제민감도"]
    for k, c in enumerate(CELLS + ["기준"]):
        csacc = {u: a for u, a in csacc_all.items() if a["칸"] == c}
        if not csacc:
            continue
        row = row_point(make_row(c + "_정제", "정제민감도", list(csacc), csacc, VAR["정제민감도"]), cols, fam_cols)
        row["유지"] = retention(row["δ"], ref, head_idx)
        cmp = compare(f"{c}_정제~완전모방기", csacc, VAR["정제민감도"], groups["완전모방기"], V,
                      cols, head_idx, ref, 400 + k, N_BOOT)
        j = judge_vs_null(cmp, len(row["쌍"]), n_head)
        clean_sens[c] = {"계정수": len(csacc), "바뀐문서_계정수": sum(1 for a in csacc.values() if a.get("바뀐문서수")),
                         "쌍": len(row["쌍"]), "주목수": row["주목수"], "유지": row["유지"], "10절차": row["10절차"],
                         "귀무비교": public_cmp(cmp, keys250), "판정": j}
        say(f"      정제 민감도 {c:<13} 계정 {len(csacc)} · 쌍 {len(row['쌍'])} · 동질성 {j['동질성']} · 방향 {j['방향']}")

    # ── [8+/9] 복사 규칙 세 판 (뼈대 4절 v3.2.7) ─────────────────────
    say("\n[8+/9] 복사 규칙 세 판: 주 판 · 복사 민감도(≥0.8 뺌) · 복사 제외 없음(규칙 이전). 판정·예측은 주 판만")
    three = {}
    for k, name in enumerate(CELLS + ["혼합", "재생성"]):
        base_uids = rows[name]["계정"]
        three[name] = {"주": {"계정수": rows[name]["계정수"], "쌍": len(rows[name]["쌍"]),
                             "주목수": rows[name]["주목수"], "유지": rows[name]["유지"],
                             "10절차": rows[name]["10절차"],
                             "판정": {kk: judge[name][kk] for kk in ("동질성", "방향", "동질성_하한")} if name in judge else None}}
        for j_, vk in enumerate(("복사민감도", "복사제외없음")):
            vacc = {u: var[vk][u] for u in base_uids if u in var[vk]} if name == "혼합" else \
                   {u: a for u, a in var[vk].items() if a["칸"] == (name if name in CELLS else "기준")}
            if not vacc:
                three[name][vk] = {"계정수": 0}
                continue
            row = row_point(make_row(f"{name}_{vk}", vk, list(vacc), vacc, VAR[vk]), cols, fam_cols)
            row["유지"] = retention(row["δ"], ref, head_idx)
            ent = {"계정수": len(vacc), "쌍": len(row["쌍"]), "주목수": row["주목수"], "유지": row["유지"],
                   "10절차": row["10절차"], "δ": dict(zip(keys250, row["δ"]))}
            if name != "재생성":
                cmp = compare(f"{name}_{vk}~완전모방기", vacc, VAR[vk], groups["완전모방기"], V,
                              cols, head_idx, ref, 500 + 10 * k + j_, N_BOOT)
                jj = judge_vs_null(cmp, len(row["쌍"]), n_head)
                ent["판정(참고)"] = {kk: jj[kk] for kk in ("동질성", "방향", "동질성_하한", "유지차_구간")}
                ent["귀무비교"] = public_cmp(cmp, keys250)
            three[name][vk] = ent
        say(f"      {name:<13} " + " | ".join(
            f"{COPY_VARS[v_].split('(')[0]} 쌍 {three[name][v_].get('쌍')} 유지 {three[name][v_].get('유지')} F "
            f"{fb(((three[name][v_].get('10절차') or {}).get('F') or {}).get('비율'), False)} M "
            f"{fb(((three[name][v_].get('10절차') or {}).get('M') or {}).get('비율'), False)}"
            + (f" 동질성 {(three[name][v_].get('판정') or three[name][v_].get('판정(참고)') or {}).get('동질성')}"
               if name != "재생성" else "") for v_ in COPY_VARS))
    p120_three = {"주": {"자질수": cnt0, "페르소나": len(common)}}
    for vk in ("복사민감도", "복사제외없음"):
        ga, gb = var[f"짝_P12-0_재생성쪽_{vk}"], var[f"원봇_재생성성공슬롯_{vk}"]
        ra_ = {a["페르소나id"]: u for u, a in ga.items()}
        rb_ = {a["페르소나id"]: u for u, a in gb.items()}
        cm_ = sorted(set(ra_) & set(rb_))
        if cm_:
            XA_ = np.array([VAR[f"짝_P12-0_재생성쪽_{vk}"][ra_[p]] for p in cm_], dtype=float)
            XB_ = np.array([VAR[f"원봇_재생성성공슬롯_{vk}"][rb_[p]] for p in cm_], dtype=float)
            p120_three[vk] = {"자질수": int(np.sum(np.abs(delta_point(XA_, XB_)) >= DELTA_NOTABLE)), "페르소나": len(cm_)}
        else:
            p120_three[vk] = {"자질수": None, "페르소나": 0}
    say("      P12-0 자질 수(참고): " + " · ".join(f"{COPY_VARS[v_].split('(')[0]} {p120_three[v_]['자질수']}"
                                         f"({p120_three[v_]['페르소나']} 페르소나)" for v_ in COPY_VARS))
    copy_rep = (sum121.get("복사") or {}).get("칸별") or {}
    for c, r_ in copy_rep.items():
        say(f"      복사율 {c:<13} {r_.get('복사율') or 0:.2%} (동일 {r_['구간별']['동일']} · ≥0.9 {r_['구간별']['≥0.9']} · "
            f"0.8~0.9 {r_['구간별']['0.8~0.9']}) · 규칙으로 탈락한 계정 {r_.get('규칙으로_탈락한계정수')}")

    # ── [9/9] 보조 · 예측 · 수위표 · 저장 ───────────────────────
    say("\n[9/9] 보조 점검 · 예측 대조 · 주장 수위표 행 선택 · 저장")
    aux = auxiliary(acc121, sum121, mid, rows, groups, V, pool, keys250, A130)
    preds = []
    preds.append({"id": "P12-0", "문장": PREDICTIONS["P12-0"], "판정": p120["판정"],
                  "값": {"자질수": cnt0, "짝교환_95백분위": up_swap}})
    p121 = {c: judge[c]["방향"] for c in CELLS}
    preds.append({"id": "P12-1", "문장": PREDICTIONS["P12-1"],
                  "칸별": {c: {"유지": judge[c]["유지"], "귀무유지": judge[c]["귀무유지"], "머리자질수": n_head,
                              "유지차_구간": judge[c]["유지차_구간"], "판정": p121[c]} for c in CELLS},
                  "판정": overall(p121.values(), "유지")})
    p122 = {n: judge[n]["동질성"] for n in CELLS + ["혼합"]}
    preds.append({"id": "P12-2", "문장": PREDICTIONS["P12-2"],
                  "칸별": {n: {"하한": judge[n]["동질성_하한"], "판정": p122[n]} for n in CELLS + ["혼합"]},
                  "판정": overall(p122.values(), "넘음")})
    for p in preds:
        say(f"      {p['id']} → {p['판정']}")
    claim = select_claim(judge, mid)
    say(f"      주장 수위표 행: 「{claim['행']}」 · 혼합 문장 「{claim['혼합_행']}」 (판정 문장은 연구자가 쓴다)")

    out = {
        "상태": status,
        "설정": {"실행": run_info, "사전선언": "12_OpenRouter생성_사전선언_뼈대.md v3.2 5절 2·3·9항, 7절 P12-0·1·2, 8절",
               "사전선언_sha256": sha256_file(PREREG), "입력_sha256": info, "구현결정": IMPL_DECISIONS,
               "사전예측": PREDICTIONS, "수위표": CLAIM_TABLE, "모델ID표": mid,
               "자질": {"F": list(words), "M형태": feat_keys, "M품사": upos_keys, "R": list(RKEYS)},
               "축분류": axis_map, "상수": {"CALIPER": CALIPER, "N_PERM": N_PERM, "N_BOOT": N_BOOT,
                                        "N_SPLIT": N_SPLIT, "DELTA_NOTABLE": DELTA_NOTABLE,
                                        "HEAD_DELTA": HEAD_DELTA, "RETAIN_MIN": RETAIN_MIN,
                                        "MIN_PAIRS": MIN_PAIRS, "P120_MAX": P120_MAX, "CAP": CAP},
               "12-1_완결": g3c,
               "라벨_사용": ["표 (a) 풀 정의(역할 표a)", "매칭 봇·사람 구분", "δ 그룹 구분",
                         "10 절차 중심·잔차·순열", "쌍·페르소나 부트스트랩", "P12-0 두 무더기"]},
        "관문": {"G1_함수승계": copy_res, "G2_손예제": hand_res, "G3_입력": chk, "G4_행정합": g4, "uid서로소": g_uid},
        "머리자질": {"문턱": HEAD_DELTA, "목록": head, "축보수쌍_제외": [keys250[j] for j in sorted(comp_drop)],
                 "축보수쌍_δ합(재생성)": comp_check,
                 "PUNCT_구두점비율_둘다": bool(punct_pair) and all(j in head_idx for j in punct_pair)},
        "행별": {name: public_row(row, keys250, fam_cols) for name, row in rows.items()},
        "판정": judge, "같은페르소나": {n: {k: public_cmp(v, keys250) for k, v in e.items()} for n, e in effects.items()},
        "부분추출판": {"쌍": n_min, "제외행": [r for r in ROW_ORDER if r not in ok_rows], "행별": sub},
        "P12-0": p120, "민감도_106제외": sens, "정제민감도": clean_sens,
        "복사규칙_세판": {"이름표": COPY_VARS, "행별": three, "P12-0_자질수": p120_three,
                     "칸별_복사(12-1)": copy_rep, "안내": "판정·예측은 주 판만. 완전 모방기 비교 행은 구성상 규칙과 무관."},
        "보조": aux, "예측대조": preds, "주장수위표": claim, "소요초": time.time() - t_start,
    }
    write_json(OUT_JSON, out)
    write_markdown(out, rows, judge, n_head, claim, preds, p120, sens, clean_sens, n_min, sub, status, effects,
                   three, p120_three, copy_rep)
    say(f"\n  저장: {OUT_JSON}\n        {OUT_MD}\n  상태 {status} · ({time.time() - t_start:.0f}초)")


def overall(states, ok_word):
    """E17: 칸 하나라도 판정불가면 판정불가, 모두 통과면 적중, 그 밖은 빗나감."""
    states = list(states)
    if any(str(s).startswith("판정불가") for s in states):
        return "판정불가"
    return "적중" if all(s == ok_word for s in states) else "빗나감"


def public_row(row, keys250, fam_cols):
    lo, hi = row["구간"]["δ"]
    return {"종류": row["종류"], "계정수": row["계정수"], "쌍수": len(row["쌍"]), "판정불가": row["판정불가"],
            "쌍": [[b, h, g] for b, h, g in row["쌍"]], "탈락봇": row["탈락봇"],
            "δ": {k: {"점": row["δ"][j], "구간": [lo[j], hi[j]]} for j, k in enumerate(keys250)},
            "주목수(|δ|≥0.147)": row["주목수"], "평균절대δ": row["평균절대δ"],
            "10절차": row["10절차"], "비율구간": row["구간"]["비율"],
            "유지": row["유지"], "유지구간": row["구간"]["유지"], "유지_구두점하나로": row["유지_구두점하나로"],
            "ρ": row["ρ"], "ρ구간": row["ρ_구간"], "ρ_주의": {"R": "자질 3개(n = 3)라 참고만"},
            "δ_벡터최대차": row["δ_벡터최대차"], "부트스트랩_무효추정치수(비율)": row["부트_무효"]}


def public_cmp(e, keys250):
    d = dict(e)
    if "δ차_구간" in d:
        lo, hi = d.pop("δ차_구간")
        pt = d.pop("δ차_점추정")
        d["δ차"] = {kk: {"점": pt[j], "구간": [lo[j], hi[j]]} for j, kk in enumerate(keys250)}
    return d


def select_claim(judge, mid):
    """E10(v2): 수위표 행을 규칙대로 고른다. 판정 문장은 연구자가 쓴다."""
    d = {c: judge[c]["방향"] for c in CELLS}
    h = {c: judge[c]["동질성"] for c in CELLS}
    both = [c for c in CELLS if d[c] == "유지" and h[c] == "넘음"]
    undecided = [c for c in CELLS if d[c].startswith("판정불가") or h[c].startswith("판정불가")]
    if len(both) == len(CELLS):
        key = "4모델 모두"
    elif both:
        key = "일부 모델만"
    elif undecided:
        key = "판정불가"
    elif all(d[c] == "유지" for c in CELLS) and all(h[c] == "못 넘음" for c in CELLS):
        key = "방향만"
    elif all(h[c] == "넘음" for c in CELLS) and all(d[c] == "아님" for c in CELLS):
        key = "동질성만"
    elif all(d[c] == "아님" for c in CELLS) and all(h[c] == "못 넘음" for c in CELLS):
        key = "모두 귀무를 넘지 못함"
    else:
        key = "혼재"
    mj = judge["혼합"]
    if mj["동질성"].startswith("판정불가"):
        mix_s = "판정불가"
    else:
        mix_s = "좁다" if mj["동질성"] == "넘음" else "좁지 않다"
    return {"행": key, "틀": CLAIM_TABLE[key],
            "칸별": {c: {"모델": mid["표"][c], "방향": d[c], "동질성": h[c]} for c in CELLS},
            "방향·동질성_모두_넘은_칸": [mid["표"][c] for c in both],
            "판정불가_칸": [mid["표"][c] for c in undecided],
            "혼합_행": mix_s, "혼합_틀": CLAIM_TABLE["혼합 행"],
            "혼합_기준": "혼합 − 완전 모방기(같은 페르소나) F·M 하한 > 0. 사람 대비 순열 p는 기술용.",
            "안내": "판정 문장은 연구자가 쓴다. 이 행은 규칙(구현 결정 E10)으로만 골랐다."}


# ════════════════════════════════════════════════════════════════════════
# [보조] 뼈대 5절 9항
# ════════════════════════════════════════════════════════════════════════
def auxiliary(acc121, sum121, mid, rows, groups, V, pool, keys250, A130):
    aux = {}
    ledger = {r["슬롯id"]: r for r in (json.loads(l) for l in open(LEDGER_JSONL, encoding="utf-8"))}
    mim_text = {r["슬롯id"]: r["comment_body"] for r in (json.loads(l) for l in open(MIMIC_JSONL, encoding="utf-8"))}
    model_cell = {m: c for c, m in mid["표"].items()}
    model_cell[mid["기준_재생성_모델"]] = "기준"
    reports = acc121["설정"]["모델별"]
    prof = re.compile(r"\b(" + "|".join(PROFANITY) + r")\w*", re.I)
    # (1) 모방 충실도: 슬롯 단위 길이
    fid, refusal = {}, {}
    for m, tab in acc121["슬롯"].items():
        ci = {c: i for i, c in enumerate(tab["열"])}
        lens = [(r[ci["댓글글자수"]], len(mim_text[r[ci["슬롯id"]]] or ""))
                for r in tab["행"] if r[ci["상태"]] == "성공" and r[ci["댓글글자수"]]]
        lens = [(a, b) for a, b in lens if a > 0 and b > 0]
        if lens:
            lr = np.log2([a / b for a, b in lens])
            fid[m] = {"성공슬롯": len(lens), "log2_길이비_중앙": float(np.median(lr)),
                      "0.5~2배_비율": float(np.mean(np.abs(lr) <= 1)),
                      "길이_Spearman": spearman([a for a, _ in lens], [b for _, b in lens]),
                      "출력글자수_중앙": float(np.median([a for a, _ in lens])),
                      "예시글자수_중앙": float(np.median([b for _, b in lens]))}
        # (1c) 거절 슬롯의 예시 특성 (13 소항)
        grp_ = {"거절호출_있음": [], "거절호출_없음": []}
        for r in tab["행"]:
            t = mim_text[r[ci["슬롯id"]]] or ""
            grp_["거절호출_있음" if (r[ci["거절호출"]] or 0) > 0 else "거절호출_없음"].append(t)
        refusal[m] = {k: ({"슬롯": len(v), "예시글자수_중앙": float(np.median([len(t) for t in v])),
                           "예시글자수_평균": float(np.mean([len(t) for t in v])),
                           "욕설_포함_비율": float(np.mean([bool(prof.search(t)) for t in v])),
                           "욕설_평균개수": float(np.mean([len(prof.findall(t)) for t in v]))} if v else {"슬롯": 0})
                      for k, v in grp_.items()}
    aux["거절슬롯_예시특성"] = {"욕설목록": list(PROFANITY), "규칙": "단어 경계로 시작하는 목록 낱말(뒤에 글자 붙어도 셈, 대소문자 무시)",
                          "모델별": refusal}
    # (1b) 페르소나 단위 자질 거리
    H = np.array([V[u] for u in pool])
    med = np.nanmedian(H, axis=0)
    mad = np.nanmedian(np.abs(H - med), axis=0)
    mean_ad = np.nanmean(np.abs(H - med), axis=0)
    scale = np.where(mad > 0, mad, np.where(mean_ad > 0, mean_ad, np.nan))
    mim_by_pid = {a["페르소나id"]: u for u, a in A130.items() if a["집단"] == "완전모방기"}

    def dist(u, w):
        with np.errstate(invalid="ignore"):
            z = np.minimum(np.abs(V[u] - V[w]) / scale, CAP)
        return float(np.nanmean(z))
    pdist = {}
    for g in CELLS + ["재생성", "원봇"]:
        accs = groups[g]
        pairs = sorted((a["페르소나id"], u) for u, a in accs.items() if a["페르소나id"] in mim_by_pid)
        if len(pairs) < 2:
            continue
        same = [dist(u, mim_by_pid[p]) for p, u in pairs]
        shifted = [dist(u, mim_by_pid[pairs[(i + 1) % len(pairs)][0]]) for i, (p, u) in enumerate(pairs)]
        pdist[g] = {"페르소나": len(pairs), "같은짝_중앙": float(np.median(same)),
                    "어긋난짝_중앙": float(np.median(shifted)),
                    "같은짝<어긋난짝_비율": float(np.mean(np.array(same) < np.array(shifted)))}
    aux["모방충실도"] = {"슬롯_길이": fid, "페르소나_자질거리": pdist,
                     "척도": "표 (a) 640 MAD(0이면 평균 절대 편차, 그것도 0이면 제외), 상한 5",
                     "제외자질": int(np.isnan(scale).sum())}
    # (2) 칸별 주제 구성·CB·결측
    topics = {}
    split = json.load(open(SPLIT_JSON, encoding="utf-8"))["분할"]
    for m, tab in acc121["슬롯"].items():
        c = model_cell[m]
        ci = {k: i for i, k in enumerate(tab["열"])}
        by_topic = defaultdict(Counter)
        for r in tab["행"]:
            lt = ledger[r[ci["슬롯id"]]]
            kind = "계정주제" if lt["슬롯주제"] != "InternationNews" else "InternationNews"
            by_topic[kind][r[ci["상태"]]] += 1
        members = [p for p in split["페르소나"] if c == "기준" or p["모델슬롯"] == c]
        alive = {a["페르소나id"] for a in acc121["계정"].values() if a["생성모델"] == m}
        surv = defaultdict(lambda: [0, 0])
        for p in members:
            surv[p["주제"]][0] += 1
            surv[p["주제"]][1] += p["페르소나id"] in alive
        rep = reports.get(m, {})
        topics[m] = {"슬롯주제별_상태": {k: dict(v) for k, v in by_topic.items()},
                     "주제별_생존": {t: {"배정": a, "생존": b, "율": b / a if a else None} for t, (a, b) in surv.items()},
                     "CB_결측": rep.get("CB_결측"), "결측사유": rep.get("결측사유"), "차단": rep.get("차단"),
                     "거절호출_슬롯": rep.get("거절호출_슬롯"), "length발생_슬롯": rep.get("length발생_슬롯"),
                     "성공호출_원형파서실패_몫": rep.get("성공호출_원형파서실패_몫")}
    aux["칸별_주제·결측"] = topics
    aux["finish_reason"] = {"출처": "12-1이 호출 기록의 '호출' 줄에서 센 분포(슬롯 종료 기록에는 finish_reason이 없다)",
                            "모델별": {m: r.get("finish_reason분포") for m, r in reports.items()}}
    aux["상한칸_비율"] = {"안내": "z = 5 상한 칸 비율(작업 지시 보조 열). 범위 밖 백분위 칸은 12-3 몫(뼈대 v3.2.3 ⑤).",
                      "행별": {n: {b: ((r["10절차"] or {}).get(b) or {}).get("상한") for b in BLOCKS}
                             for n, r in rows.items()}}
    aux["정제보고(12-1)"] = sum121.get("정제보고")
    aux["langid경계(12-1)"] = sum121.get("langid경계")
    tense = {}
    dcols = acc121["문서별"]["열"]
    di = {c: i for i, c in enumerate(dcols)}
    for m, tab in acc121["슬롯"].items():
        ci = {k: i for i, k in enumerate(tab["열"])}
        after = {r[ci["슬롯id"]]: r[ci["예시_계획일뒤"]] for r in tab["행"]}
        acc = defaultdict(lambda: [0, 0, 0])
        for u, docs in acc121["문서별"]["계정"].items():
            if u not in acc121["계정"] or acc121["계정"][u]["생성모델"] != m:
                continue
            for d in docs:
                k = "예시_계획일뒤" if after.get(d[di["슬롯id"]]) else "예시_계획일전"
                acc[k][0] += 1
                acc[k][1] += d[di["Tense_Past"]]
                acc[k][2] += d[di["Tense_합"]]
        tense[m] = {k: {"문서": a, "Tense_Past": b, "Tense_합": t, "Past비율": b / t if t else None}
                    for k, (a, b, t) in acc.items()}
    aux["과거시제_점검"] = tense
    return aux


# ════════════════════════════════════════════════════════════════════════
# [Markdown]
# ════════════════════════════════════════════════════════════════════════
def write_markdown(out, rows, judge, n_head, claim, preds, p120, sens, clean_sens, n_min, sub, status, effects,
                   three, p120_three, copy_rep):
    def f3(x):
        return "" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.3f}"

    def ci(v):
        return "" if not v or v[0] is None else f"[{fb(v[0])}, {fb(v[1])}]"
    today = datetime.now().strftime("%Y-%m-%d")
    L = ["---", 'title: "12_표a"', 'rating: "☆☆☆☆☆"', 'aliases: ["12 표 (a)", "OpenRouter 생성 표 (a)"]',
         'status: "[[🚦refining]]"', 'MOC: "[[📚 203 Research]]"', 'type: "[[🔖 Experiment]]"',
         'index: "[[🏷️ misc]]"', "tags:", '  - "#category/001_연구방법론"', '  - "#봇탐지"', '  - "#문체분석"',
         'access: "[[🔒 private]]"', 'author: "[[👤손제홍]]"',
         f'source: "12-2_표a.py 자동 산출(스크립트 sha256 {out["설정"]["실행"]["스크립트_sha256"][:16]}, '
         f'smoke {SMOKE}, 시험입력 {TEST_INPUT}, 상태 {status})"',
         'source_url: ""', f'creation_date: "{today}"', f'modification_date: "{today}"', "---", "",
         "# 12 표 (a) : 새 모델 4 · 혼합 · 재생성 · 원 봇 · 완전 모방기", ""]
    if status != "완결":
        L += ["> [!danger] 미완", f"> {status}. 생성이 끝나지 않은 슬롯이 있거나 12-1을 --allow-incomplete로 돌렸다. "
              "이 표의 수치와 판정은 최종이 아니다.", ""]
    L += ["> [!warning] 판정 문장은 연구자가 쓴다", "> 이 파일은 12-2_표a.py가 만든 수치와 규칙 판정이다. 주장 수위표의 행은 "
          "구현 결정 E10으로 기계적으로 골랐을 뿐이며, 원고 문장은 연구자가 쓴다.", ""]
    if SMOKE or TEST_INPUT:
        L += ["> [!caution] 시험 산출", f"> smoke {SMOKE} · 시험입력 {TEST_INPUT}. 결과로 인용하지 않는다.", ""]
    L += ["## 표 (a)", "",
          f"머리 자질 {n_head}개(재생성 |δ| ≥ {HEAD_DELTA}, 축 보수 쌍 하나만). 비율 = 사람 거리 중앙값 ÷ 봇 거리 "
          f"중앙값(10 v1.3), p = 쌍 안 교환 {N_PERM:,}회 단측(기술용), 구간 = 쌍 부트스트랩 {N_BOOT:,}회 95%. "
          "R 가족 ρ는 자질 3개라 참고만 한다.", "",
          "| 행 | 계정 | 쌍 | 주목 δ F·M형태·M품사·R | 유지 | F 비율 [구간] p | M 비율 [구간] p | R 비율 [구간] p | ρ F·M형태·M품사·R |",
          "|---|---|---|---|---|---|---|---|---|"]
    for name in ROW_ORDER:
        r = rows[name]
        h = r["10절차"] or {}

        def cell(b):
            x = h.get(b) or {}
            if x.get("비율") is None:
                return "무효"
            v = r["구간"]["비율"][b]
            return f"{x['비율']:.3f} [{fb(v[0], False)}, {fb(v[1], False)}] {x['p_단측']:.4f}"
        nm = f"{name}{' (판정불가)' if r['판정불가'] else ''}"
        L.append(f"| {nm} | {r['계정수']} | {len(r['쌍'])} | " + "·".join(str(r['주목수'][f]) for f in FAMILIES) +
                 f" | {r['유지']}/{n_head} | {cell('F')} | {cell('M')} | {cell('R')} | " +
                 "·".join(f3(r['ρ'][f]) for f in FAMILIES) + " |")
    L += ["", "## 귀무 대비 판정 (뼈대 5절 3항, 주 판정 = 같은 페르소나 완전 모방기 비교)", "",
          "| 칸 | 쌍 | 같은 페르소나 | F 차 구간 | M 차 구간 | R 차 구간(기록) | 동질성 | 유지 − 귀무 [구간] | 방향 | 보조: 509 행 F·M 차 구간 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for n in CELLS + ["혼합"]:
        j = judge[n]
        cm = effects[n]["귀무비교"]
        bi = cm.get("비율차_구간") or {}
        L.append(f"| {n} | {j['쌍']} | {cm.get('페르소나수')} | {ci(bi.get('F'))} | {ci(bi.get('M'))} | {ci(bi.get('R'))} | "
                 f"{j['동질성']} | {j['유지']} − {j['귀무유지']} {ci(j['유지차_구간'])} | {j['방향']} | "
                 f"{ci(j['보조_509행차']['F']['구간'])} · {ci(j['보조_509행차']['M']['구간'])} |")
    L += ["", "## 모델 효과 (같은 페르소나, 짝 계정: 두 모델 모두 성공한 슬롯)", "",
          "| 칸 | 페르소나 | F 차 구간 | M 차 구간 | R 차 구간 | 유지 차 구간 | δ 차 구간이 0 밖인 자질 |", "|---|---|---|---|---|---|---|"]
    for n in CELLS + ["혼합"]:
        e = effects[n]["모델효과"]
        bi = e.get("비율차_구간") or {}
        L.append(f"| {n} | {e.get('페르소나수')} | {ci(bi.get('F'))} | {ci(bi.get('M'))} | {ci(bi.get('R'))} | "
                 f"{ci(e.get('유지차_구간'))} | {e.get('δ차_구간이_0밖인_자질수')} |")
    L += ["", "## 예측 대조", ""]
    for p in preds:
        L.append(f"- **{p['id']}** {p['판정']}: {p['문장']}")
        L.append("")
    L += [f"P12-0 세부: 페르소나 {p120['페르소나']} · |δ| ≥ {DELTA_NOTABLE} 자질 {p120['|δ|≥0.147_자질수']}개 · "
          f"짝 교환 기준선 95백분위 {p120['기준선_짝교환_95백분위']} · 분할 반쪽(참고) {p120['참고_분할반쪽_95백분위']}.", "",
          "## 주장 수위표 행 (뼈대 8절, 기계 선택)", "",
          f"- 선택된 행: **{claim['행']}**", "", f"- 틀: {claim['틀']}", "",
          f"- 방향·동질성을 모두 넘은 칸: {', '.join(claim['방향·동질성_모두_넘은_칸']) or '없음'}", "",
          f"- 판정불가 칸: {', '.join(claim['판정불가_칸']) or '없음'}", "",
          f"- 혼합 행: {claim['혼합_틀']} → **{claim['혼합_행']}** ({claim['혼합_기준']})", "",
          "- 판정 문장은 연구자가 쓴다.", "",
          "## 보조 판", "",
          f"부분추출판(판정불가 행을 뺀 가장 작은 쌍 수 {n_min}): " + " · ".join(
              f"{n} 유지 {sub[n].get('유지', '제외')}" for n in ROW_ORDER), "",
          "민감도(모방 저자 106명 제외, 귀무 = 같은 106명 슬롯을 뺀 완전 모방기): " + " · ".join(
              f"{c} 쌍 {sens[c].get('쌍')} 동질성 {(sens[c].get('판정') or {}).get('동질성')} 방향 "
              f"{(sens[c].get('판정') or {}).get('방향')}" for c in CELLS), "",
          "정제 민감도(따옴표·이름표 접두를 벗긴 계정, 1% 넘는 칸만): " + (" · ".join(
              f"{c} 쌍 {v['쌍']} 동질성 {v['판정']['동질성']} 방향 {v['판정']['방향']}" for c, v in clean_sens.items())
              or "만든 칸 없음"), "",
          "## 모방 예시 복사 (뼈대 4절 v3.2.7)", "",
          "생성 댓글이 그 슬롯의 모방 예시와 정규화 동일이거나 difflib 비율 ≥ 0.9면 복사로 보고 결측 처리했다(주 판). "
          "완전 모방기 비교 행은 모방 예시 원문 그 자체라 구성상 이 규칙의 영향을 받지 않는다. 판정·예측은 주 판만 쓴다.", "",
          "| 칸 | 성공 슬롯 | 동일 | ≥0.9 | 0.8~0.9 | 복사율(결측) | 규칙으로 탈락한 계정 |", "|---|---|---|---|---|---|---|"]
    for c, r_ in copy_rep.items():
        L.append(f"| {c} | {r_['성공슬롯']} | {r_['구간별']['동일']} | {r_['구간별']['≥0.9']} | {r_['구간별']['0.8~0.9']} | "
                 f"{(r_.get('복사율') or 0):.2%} | {r_.get('규칙으로_탈락한계정수')} |")
    L += ["", "세 판 나란히(주 판 = 판정에 씀, 나머지 둘은 참고):", "",
          "| 행 | 판 | 계정 | 쌍 | 주목 δ F·M형태·M품사·R | 유지 | F 비율 p | M 비율 p | R 비율 p | 동질성 | 방향 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, vs in three.items():
        for v_, lab in COPY_VARS.items():
            e = vs.get(v_) or {}
            if not e.get("쌍"):
                L.append(f"| {name} | {lab} | {e.get('계정수', 0)} | 0 |  |  |  |  |  |  |  |")
                continue
            h = e.get("10절차") or {}

            def bp(b):
                x = h.get(b) or {}
                return "무효" if x.get("비율") is None else f"{x['비율']:.3f} {x['p_단측']:.4f}"
            jd = e.get("판정") or e.get("판정(참고)") or {}
            L.append(f"| {name} | {lab} | {e['계정수']} | {e['쌍']} | " + "·".join(str(e['주목수'][f]) for f in FAMILIES) +
                     f" | {e['유지']}/{n_head} | {bp('F')} | {bp('M')} | {bp('R')} | {jd.get('동질성', '')} | {jd.get('방향', '')} |")
    L += ["", "P12-0 자질 수: " + " · ".join(f"{COPY_VARS[v_]} {p120_three[v_]['자질수']}" for v_ in COPY_VARS) + ".", "",
          "세부 수치(250자질 δ와 구간, 같은 페르소나 판, 모방 충실도, 거절 슬롯 예시 특성, 주제·결측, finish_reason, "
          "상한 칸 비율, 과거 시제 점검, langid 경계, 복사 규칙 세 판)는 12_표a.json에 있다.", ""]
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main()

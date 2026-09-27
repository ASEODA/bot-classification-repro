#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
12-1_생성댓글파싱.py  (v2, 2026-09-27 적대 검증 반영)
────────────────────────────────────────────────────────────────────────────
판 기록
    v1  첫 판. 가짜 호출 기록 시험 통과(sha256 56c004bb…).
    v2  적대 검증 결정 반영: 잠금 파일이 있으면 본 실행 거부, 호출 기록 관문 강화
        (종료 기록 중복은 바이트까지 같을 때만, 모르는 상태값·모드·설정해시 없음·댓글
        형식 오류는 중단), uid 서로소 관문, 짝 계정(뼈대 4절 "둘 다 산 슬롯"), 기준 칸
        두 개(원 봇 재생성 성공 슬롯 한정, 완전 모방기 106명 슬롯 제외), 정제 보고와 정제
        민감도 계정, langid 경계 계정 수.
    v3  뼈대 4절 v3.2.7(분석 전 선언): 모방 예시 복사 규칙. 성공 슬롯의 댓글이 그 슬롯의
        모방 예시와 정규화 동일이거나 difflib 비율 ≥ 0.9면 "모방 예시 복사"로 결측 처리
        (계정·짝 계정·P12-0 집합에서 모두 빠짐). 비율 ≥ 0.8까지 뺀 "복사 민감도" 변형을
        같은 파싱으로 더함. 규칙 이전 계정("복사제외없음")도 셋째 판으로 둔다. 파싱 목록은
        규칙 이전 계정의 문서이고 주 판·복사 민감도는 거기서 문서만 골라 만든다(G12).
        슬롯별 복사 표시·구간·예시 길이 저장, 칸별 보고, 관문 G11·G12.

한계 먼저
    · 이 파일은 생성 댓글로 계정 사전을 만들 뿐 판정을 하지 않는다. 표 (a)는
      12-2_표a.py가, 판별기 ver.2는 그 뒤 단계가 이 사전을 읽는다.
    · 생성 댓글에 붙이는 시각은 BotSim 공개 코드의 지연 규칙(가중 구간)으로 만든
      가상 시각이다. 계정당 성공 슬롯이 최대 101건이라 최근 200건 상한이 걸리지
      않는다. 그래서 시각은 문서 집합을 바꾸지 않고 파서에 넣는 순서만 바꾼다.
      13-0은 완전 모방기에 이 규칙을 쓰지 않고 계획일 문자열을 정렬 키로 썼다
      (13-0 결정 D3). 이 파일은 뼈대 5절 1항대로 지연 규칙을 쓴다(결정 D2).
    · 이 파일은 생성 기록 가운데 슬롯 종료 기록(상태 성공)의 댓글만 문서로 쓴다.
      결측·차단·슬롯중단 슬롯은 문서가 없다. 결측 사유는 보고만 한다.
    · 문장 경계는 stanza 토크나이저가 정한다(13-0과 같다).
    · langid는 계정의 문서를 이어 붙인 글 하나에 건다(13-0 select_group 그대로). 이음매의
      문자 n-gram이 순서에 따라 달라지므로, 문서 순서(시각 규칙)가 경계에 걸친 계정의
      판정을 원리상 뒤집을 수 있다. 그래서 정규화 확률의 1위와 2위 차가 0.05 미만인 계정
      수를 칸마다 적는다(결정 D14).
    · 뼈대 4절 정제 행의 "접두·따옴표·줄바꿈 제거"는 13-0과 이 파일 모두 하지 않는다
      (01 clean_doc만). 대신 따옴표로 감싼 문서와 이름표 접두 문서를 칸마다 세고, 1%를
      넘는 칸은 그것을 벗긴 "정제 민감도" 계정을 따로 만든다(결정 D12).

목적
    12 뼈대 v3.2 5절 1항. 생성 댓글을 13-0과 같은 규칙(정제·적격)과 같은 측정
    함수(stanza measure_account)에 통과시켜 댓글 한정 계정 사전을 만든다. 13-0이
    만든 사람 874·원 봇 504·완전 모방기 509 사전에 그대로 덧붙일 수 있는 구조다.

대상 칸 다섯 (집단·칸 열)
    새모델   MODEL_SLOT_1~4. 페르소나마다 배정된 모델 하나의 기록만 쓴다.
             uid = "G1_"~"G4_" + 원 봇 uid (13-0의 "MIM_" + 원 봇 uid와 같은 꼴).
    재생성   openai/gpt-4o-mini 재생성(주 기준 행). 509 페르소나 전부.
             uid = "G0_" + 원 봇 uid.
    모델 ID는 모델ID표.json에서 읽는다. 호출 기록 파일은
    ~/DM_LAB_data/12_OpenRouter/호출기록_<모델 id의 "/"를 "_"로>_<설정해시 앞 8자>.jsonl
    이고 모델마다 정확히 하나여야 한다.

절차
    [0] 입력 sha256을 동결.json과 대조한다(분할·대장·모델 ID 표·완전 모방기·13-0 사전).
    [1] 함수 동일성: 13-0에서 옮긴 함수의 AST, 01 정제 상수, BotSim 지연 규칙 상수.
    [2] 호출 기록 읽기. 실행시작 줄의 설정해시가 파일 안에서 하나이고 파일 이름의
        앞 8자와 같아야 한다(둘이면 거부). 슬롯 종료 기록("종류" 슬롯)은 슬롯 id마다
        마지막 것을 쓰고 중복 수를 센다. 모델별 보고: 배정·시도·성공·결측 사유·차단·
        슬롯중단·length·CB·거절·finish_reason·원형 파서 실패 몫.
    [3] 관문 G3: 슬롯 id가 대장의 "프롬프트 있음" 슬롯이고 그 모델에 배정된 슬롯인가,
        성공 댓글의 (게시물 id, 게시물 시각)이 그 슬롯의 창 안 사람 게시물인가.
    [4] 문서 만들기: 시각 = 게시물 시각 + BotSim 지연(결정 D2). 13-0 select_group
        그대로 정제(01 clean_doc) → 시각 오름차순 → 최근 200 → 10건 이상 → langid en.
    [5] 13-0 정합(G6)과 손 대조(G1), 결정성(G2), 측정(계정 단위 bulk_process),
        중간 저장·재개.
    [6] 사후 관문과 저장.

모방 예시 복사 (뼈대 4절 v3.2.7, 결정 D15)
    성공 슬롯마다 댓글과 그 슬롯의 모방 예시 원문(완전모방기_문서.jsonl)을 정규화(소문자,
    낱말·공백 아닌 문자 제거, 공백 하나로)해 (a) 같은가, (b) difflib.SequenceMatcher(None,
    a, b).ratio()를 본다. 두 길이가 30% 넘게 다르면 비율을 재지 않고 0.8 미만으로 친다.
    구간 = 동일 / ≥0.9 / 0.8~0.9 / <0.8. 동일 또는 ≥0.9 = "모방 예시 복사" → 그 슬롯은
    결측이다(계정 문서에서 빠지고, 짝 계정과 P12-0 집합에서도 "살지 않은 슬롯"). 완전
    모방기·원 봇·사람 계정은 이 규칙과 무관하다(13-0 사전 그대로, 모방106은 규칙 밖).
    세 판을 나란히 둔다: 주 판(계정, 동일·≥0.9 뺌, 판정·예측은 이것만), 복사민감도(≥0.8
    뺌), 복사제외없음(규칙 이전). 파싱은 규칙 이전 계정의 문서로 한 번만 하고, 주 판은 그
    가운데 복사 슬롯을 뺀 문서로 aggregate를 다시 한다. 200건 상한이 걸리지 않아(최대 101)
    이렇게 골라낸 목록은 복사를 뺀 문서로 select_group을 돌린 목록과 같다(G12가 대조).

변형 계정 (같은 파싱 결과에서 문서만 골라 aggregate를 다시 한다. 10건·langid 규칙 재적용)
    민감도_106제외     모방 저자가 ver.1 학습 사람 106명인 슬롯의 문서를 뺀 계정(D7).
    짝_새모델쪽        새 모델 계정을 재생성이 성공한 슬롯으로 한정(뼈대 4절 "모델 칸과
                       gpt-4o-mini 재생성이 둘 다 산 슬롯", D11).
    짝_재생성쪽        재생성 계정을 그 페르소나의 배정 모델이 성공한 슬롯으로 한정(D11).
    짝_P12-0_재생성쪽  재생성 계정을 13-0 원 봇 댓글 한정 계정의 슬롯(복사 슬롯·정제 탈락
                       제외)으로 한정(P12-0, D11).
    정제민감도         따옴표 감싸기·이름표 접두가 1%를 넘는 칸만. 그 문서만 벗겨 다시
                       정제·파싱(D12).
    복사민감도         (v3) 비율 0.8~0.9 슬롯까지 뺀 계정(생성 칸 전부). 짝 계정·P12-0
                       집합에도 같은 이름 꼬리(_복사민감도)의 변형을 둔다(D15).
기준 칸 두 개 (새로 파싱한다. 13-0 사전에는 문서별 측정치가 없다)
    원봇짝     13-0 원 봇 504 계정을 재생성이 성공한 슬롯으로 한정(P12-0 짝, D13).
               13-0과 같은 문서 선택(1차 댓글, 복사 슬롯 제외, 원 댓글 시각 순, 버킷
               "comment_1").
    모방106    13-0 완전 모방기 509 계정에서 106명 슬롯을 뺀 계정(표 (a) 민감도판의 귀무
               비교 행, D13). 계획일 순, 버킷 "모방".

측정 (13-0 measure_account 재사용)
    stanza tokenize,pos · use_gpu=False · download_method=None · 계정 단위
    bulk_process. aggregate는 13-0과 같은 코드. 버킷 키는 "생성"(결정 D5).
    같은 파싱 결과에서 문서별 요약(문장수·구두점 제외 토큰수·Tense=Past·Tense 합)과
    모방 저자 민감도 계정(결정 D7)도 만든다. 파싱은 한 번만 한다.

관문 (check()로 한다. python -O에서도 꺼지지 않는다)
    G0 입력 사슬: 분할.json·프롬프트대장.jsonl·모델ID표.json·완전모방기_문서.jsonl·
       13-0_계정사전.json sha256 = 동결.json. 13-0 사전 관문통과 = true.
    G1 손 대조(10계정): 칸마다 2계정을 시드로 골라 문서마다 단독 nlp(문서)로 다시
       파싱하고, aggregate와 다른 코드로 문서수·문장수·토큰수·구두점 제외·구두점·
       문장길이 목록·기능어·UPOS·자질을 다시 센다. bulk 측정과 모든 필드가 같아야
       한다. 본 측정 뒤 그 10계정의 본 측정치가 관문 때 값과 같아야 한다.
    G2 결정성: 문서 만들기를 두 번 돌려 코퍼스 해시가 같다. 부분집합(3계정)을 두 번
       파싱해 집계·문서별 요약이 같다.
    G3 완결: 모델마다 배정 슬롯이 모두 종료 기록(성공·결측·차단)을 가진다. 아니면 멈춘다
       (--allow-incomplete로만 넘어감).
    G3 대장·창: 모든 기록의 슬롯 id ∈ 대장 "프롬프트 있음" 슬롯이고 그 모델 배정
       슬롯이다. 창 재구성(페르소나 서브레딧 목록 × 창 양끝 제외 × 사람 게시물)의 게시물
       수 = 대장 창_사람게시물수, 첫 화면·재열람 id ⊂ 창. 성공 댓글의 (게시물 id, 시각)
       ∈ 그 슬롯의 창.
    G4 길이: 남은 문서는 모두 정제 뒤 20자 이상이다. 탈락 문서는 사유가 있고
       남은 수 + 탈락 수 = 입력 수.
    G5 수 맞추기: 모델마다 성공 슬롯 수(중복 제거 뒤) = 정제 전 문서 수. 계정마다
       정제 전 문서 수 = 그 페르소나의 성공 슬롯 수.
    G6 13-0 정합: 13-0 완전 모방기 계정 하나를 13-0 순서(계획일)로 다시 짓고 이
       파일의 측정 경로로 재어 13-0 사전 값과 모든 필드가 같다. stanza 버전·모델
       경로 = 13-0.
    G7 내부 관계(전 계정): len(문장길이) = 문장수 · sum(문장길이) = 구두점 제외 ·
       구두점토큰수 = 토큰수 − 구두점 제외 = UPOS PUNCT. 모든 변형 계정도 같다.
    G8 호출 기록 형식: 실행시작 줄은 모드 "본 생성"이고 설정해시(64자)가 있다. 종료 기록의
       상태는 성공·결측·차단뿐이다. 같은 슬롯의 종료 기록이 둘 이상이면 바이트까지 같아야
       한다. 성공 기록의 댓글·게시물id·게시물시각은 문자열이다. 본 실행에서는
       호출기록_*.jsonl.lock이 하나라도 있으면 시작하지 않는다(생성 진행 중).
    G9 uid 서로소: 생성 칸 uid와 13-0 사전 uid가 겹치지 않는다.
    G10 기준 칸 정합: 원봇짝·모방106 계정 가운데 한정으로 빠진 문서가 없는 계정은 13-0
       사전 값과 모든 필드가 같다.
    G12 주 판 골라내기: 파싱 목록에서 복사 슬롯을 뺀 목록 = 주 판 select_group 목록(전
       계정), 파싱 뒤 주 판 적격 여부 = select_group 적격 여부.
    G11 복사 규칙: 복사 표시를 두 번 따로 계산해 모든 슬롯의 구간·비율이 같다. 표시는 생성
       칸 성공 슬롯에만 붙는다. 13-0 사전 sha256이 시작과 끝에서 동결값과 같다(원 봇·사람·
       완전 모방기 계정 불변). 모방106 문서 목록은 복사 규칙을 끈 판과 해시가 같다.

라벨 규율
    생성 계정의 라벨은 "bot"이다(생성물이므로 정의상). Users.csv 라벨은 창 재구성
    (사람 게시물만)에만 쓴다. 로그에 [라벨 사용]을 단다. 문서 선택·정제·파싱에는
    라벨이 들어가지 않는다.

구현 결정 (규격에 없어 이 파일을 쓰며 정한 것. JSON 설정에도 적는다)
    D1. 칸 = (모델). 새 모델 계정은 페르소나의 모델 슬롯과 호출 기록 모델이 맞는
        것만 만든다. 다른 슬롯 페르소나의 기록이 있으면 G3 실패다.
    D2. 시각 = 슬롯 종료 기록의 게시물시각 + 지연. 지연은 BotSim reddit_agent.py
        comment_time_function(368~397행) 그대로: 8구간 가중치(3009·5060·2769·5727·
        5727·8472·9304·4818)로 구간을 random.choices로 고르고 그 구간 안 정수 초를
        random.randint(양끝 포함)로 뽑는다. 원 코드는 전역 random을 시드 없이 쓴다.
        여기서는 슬롯마다 random.Random(sha256("20260926|슬롯id|지연") 앞 16자리
        정수)로 같은 두 호출을 한다. 같은 슬롯은 모델이 달라도 같은 지연을 받는다.
        13-0은 이 규칙을 쓰지 않았다(13-0 D3). 문서 집합은 같고 순서만 다르다.
    D3. 같은 슬롯 id의 "슬롯" 기록이 둘 이상이면 파일의 마지막 것을 쓰고 수를 센다.
        "슬롯중단" 뒤 "슬롯"이 온 슬롯은 "슬롯"을 쓴다. "슬롯중단"만 있는 슬롯은
        미완으로 센다.
    D4. 정제는 13-0 select_group 그대로(01 clean_doc). 뼈대 4절 정제 행의 "접두·
        따옴표·줄바꿈 제거"는 따로 두지 않는다. 13-0이 사람·원 봇·완전 모방기에
        clean_doc만 썼으므로 "같은 함수" 조건을 지키려면 새 칸도 clean_doc만 써야
        한다. 줄바꿈은 clean_doc의 공백 정규화가 없앤다. 대괄호 목록의 따옴표는
        생성 스크립트 파서가 이미 벗긴다.
    D5. 버킷 키 = "생성"(13-0 D4처럼 진단용).
    D6. 손 대조 계정은 시드 20260926 random으로 칸마다 2개. smoke면 smoke 대상 안에서.
    D7. 모방 저자 민감도(뼈대 5절 9 민감도): 모방 저자가 ver.1 학습 사람 106명인 슬롯의
        문서를 뺀 계정. 106명 = 분할.json 사람 역할표에서 역할에 "모방"이 있고
        "09-1매칭_ver1학습"이 true인 사람(분할.json 사람.수 ver1학습_모방풀안 = 106과
        대조). 같은 파싱 결과에서 뺀 문서만 빼고 aggregate를 다시 한다. 뺀 뒤 10건
        미만이거나 langid가 en이 아니면 민감도 표본에서 빠진다.
    D8. 문서별 요약 = 문서마다 [슬롯id, 시각, 정제 글자수, 문장수, 구두점 제외 토큰수,
        Tense=Past 수, Tense 축 합]. 12-2의 보조 점검(예시가 계획일 뒤인 슬롯의 과거
        시제)에 쓴다. "예시_계획일뒤" = 모방 예시 댓글 시각 ≥ 계획일 00:00:00.
    D9. 중간 저장은 산출 JSON 옆(볼트 밖). 재개 지문 = 기능어 해시 + 측정 코드 해시 +
        stanza 버전 + 코퍼스 해시 + 106명 해시.
    D10. --run-dir를 기본값(DATA_DIR) 밖으로 주면 시험 입력이다. 그때는 --out-dir가
        있어야 하고 볼트·DATA_DIR의 정식 산출 경로에 쓰지 않는다.
    D11. 짝 계정은 "성공 슬롯"의 교집합으로 한정한다(생성 단계 성공 기준). 한쪽에서만
        정제로 빠진 문서는 그쪽에서만 빠진다. 한정 뒤 10건 미만·비영어면 짝에서 빠진다.
    D12. 감싸기 = 정제 문서의 양 끝이 같은 종류의 따옴표 쌍(" "·“ ”·' '·‘ ’). 접두 =
        정규식 WRAP_PREFIX(아래 설정, 굵게·대괄호를 허용한 영문 20자 이하 이름표 + 쌍점). 칸의 적격 문서 가운데 둘 중
        하나라도 해당하는 문서가 1%를 넘으면 그 칸의 정제 민감도 계정을 만든다. 벗기기 =
        접두 한 번 떼고 바깥 따옴표 한 쌍 떼기 → clean_doc 다시 → 그 문서만 다시 파싱.
    D13. 기준 칸은 측정 뒤 G10으로 13-0과 대조한다. 원봇짝은 13-0 원 봇 적격 504만,
        모방106은 13-0 완전 모방기 509만 대상으로 한다.
    D14. langid 경계 = langid.langid.LanguageIdentifier(norm_probs=True).rank의 1위 − 2위
        확률 < 0.05. 적격 계정(이어 붙인 정제 문서)에서 센다. 보고만 한다.
    D15. (v3) 모방 예시 복사. 비교는 정제 전 댓글 원문과 예시 원문. 길이 차 기준 =
        |len(a) − len(b)| > 0.30 × max(len(a), len(b))(정규화 뒤). 둘 다 빈 문자열이면
        동일. 칸별 보고: 구간별 수, 예시 길이 구간(0·50·100·150·200 이상 글자)별 복사 수,
        규칙을 켠 판과 끈 판의 적격 계정 수. 슬롯 표 열: 복사 · 복사구간 · 복사비율 ·
        모방예시글자수 · 문서포함.

실행 명령 (본 실행은 조정자가 생성이 끝난 뒤 한다)
    단계별 진행경과 폴더에서:
    PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u \\
        12-1_생성댓글파싱.py
    화면 출력은 12-1_생성댓글파싱_출력.log에도 같이 쓴다(tee 불필요).
    실제 기록으로 먼저 짧게 보기(칸마다 3계정, 산출은 --out-dir에):
    PYTHONDONTWRITEBYTECODE=1 /Users/son/.claude/venvs/audio-transcribe/bin/python -u \\
        12-1_생성댓글파싱.py --smoke --out-dir /tmp/12-1_smoke
    (smoke는 생성 중 잠금 파일이 있어도 경고만 하고 돈다. 본 실행은 거부한다.)
    시험 입력(가짜 호출 기록)으로:
        ... 12-1_생성댓글파싱.py --run-dir <가짜 기록 폴더> --out-dir <산출 폴더> [--smoke]
    venv: /Users/son/.claude/venvs/audio-transcribe/bin/python (stanza 1.14.0)
    예상 소요: 생성 칸 약 55,000건 + 기준 칸 약 51,000건(원봇짝 약 26,500 · 모방106 약
    24,500) + 정제 민감도의 바뀐 문서. 가짜 기록 시험 실측(v2)은 로그의 [6/7] 끝 줄과 요약
    JSON 속도 항목을 본다. 중간 저장이 있어 멈춰도 같은 명령으로 이어서 한다.
    생성이 덜 끝난 슬롯(미시도·슬롯중단 미완)이 있으면 G3 완결 관문에서 멈춘다. 알고도
    진행하려면 --allow-incomplete를 준다(요약 JSON에 기록된다).

산출
    ~/DM_LAB_data/12_OpenRouter/12-1_계정사전.json          계정별 측정치(대용량). 키: 계정 ·
        민감도_106제외 · 짝_새모델쪽 · 짝_재생성쪽 · 짝_P12-0_재생성쪽 · 정제민감도 ·
        복사민감도 · 복사제외없음 · 짝_{새모델쪽·재생성쪽·P12-0_재생성쪽}_{복사민감도·복사제외없음} ·
        원봇_재생성성공슬롯(·_복사민감도·_복사제외없음) · 완전모방기_106제외 · 변형_탈락 · 문서별 ·
        슬롯. "계정"이 주 판이다(설정.변형_이름표).
    ~/DM_LAB_data/12_OpenRouter/12-1_계정사전_진행.json     중간 저장. 끝나면 지운다.
    단계별 진행경과/12-1_생성댓글파싱_요약.json             모델별 보고·깔때기·관문·해시
    단계별 진행경과/12-1_생성댓글파싱_출력.log              화면 출력
"""

import argparse
import ast
import csv
import difflib
import hashlib
import json
import os
import platform
import random
import re
import statistics
import sys
import tempfile
import time
import unicodedata
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.dont_write_bytecode = True


def nfc(s):
    return unicodedata.normalize("NFC", s)


# ════════════════════════════════════════════════════════════════════════
# [경로] 모두 NFC로 둔다
# ════════════════════════════════════════════════════════════════════════
SCRIPT_PATH = nfc(os.path.abspath(__file__))
HERE = os.path.dirname(SCRIPT_PATH)              # …/연구주제/단계별 진행경과
ROOT = os.path.dirname(HERE)                     # …/연구주제
BOTSIM_DIR = f"{ROOT}/1. 원본데이터/2. BotSim Data/BotSim-24-Dataset"
POSTS_JSON = f"{BOTSIM_DIR}/user_post_comment.json"
USERS_CSV = f"{BOTSIM_DIR}/Users.csv"
AGENT_PY = f"{ROOT}/1. 원본데이터/2. BotSim Data/RedditBotSim/AgentDesicionCenter/reddit_agent.py"
PY01 = f"{HERE}/01_botsim_적격검열.py"
PY130 = f"{HERE}/13-0_댓글한정재파싱.py"
FUNCWORDS_JSON = f"{HERE}/02_기능어목록.json"
PREP_DIR = f"{HERE}/12_OpenRouter생성_준비"
SPLIT_JSON = f"{PREP_DIR}/분할.json"
LEDGER_JSONL = f"{PREP_DIR}/프롬프트대장.jsonl"
MODELID_JSON = f"{PREP_DIR}/모델ID표.json"
FREEZE_JSON = f"{PREP_DIR}/동결.json"
DATA_DIR = nfc(os.path.expanduser("~/DM_LAB_data/12_OpenRouter"))
MIMIC_JSONL = f"{DATA_DIR}/완전모방기_문서.jsonl"
ACC130_JSON = f"{DATA_DIR}/13-0_계정사전.json"

ap = argparse.ArgumentParser()
ap.add_argument("--smoke", action="store_true", help="칸마다 3계정만 파싱")
ap.add_argument("--run-dir", default=DATA_DIR, help="호출 기록 폴더(기본 DATA_DIR). 다른 폴더면 시험 입력")
ap.add_argument("--out-dir", default=None, help="smoke·시험 입력 산출 폴더")
ap.add_argument("--allow-incomplete", action="store_true",
                help="미시도·미완 슬롯이 있어도 진행(기본은 G3 완결 관문에서 멈춤)")
ARGS = ap.parse_args()
SMOKE = ARGS.smoke
RUN_DIR = nfc(os.path.abspath(os.path.expanduser(ARGS.run_dir)))
TEST_INPUT = RUN_DIR != DATA_DIR
if SMOKE or TEST_INPUT:
    if TEST_INPUT and not ARGS.out_dir:
        sys.exit("--run-dir를 DATA_DIR 밖으로 주면 --out-dir도 주십시오(결정 D10).")
    OUT_DIR = nfc(os.path.abspath(ARGS.out_dir)) if ARGS.out_dir else nfc(tempfile.mkdtemp(prefix="12-1_smoke_"))
    if OUT_DIR in (HERE, DATA_DIR):
        sys.exit("smoke·시험 입력 산출을 볼트나 DATA_DIR에 쓰지 않습니다(결정 D10).")
    os.makedirs(OUT_DIR, exist_ok=True)
    tag = "_smoke" if SMOKE else ""
    OUT_JSON = f"{OUT_DIR}/12-1_계정사전{tag}.json"
    PROGRESS_JSON = f"{OUT_DIR}/12-1_계정사전{tag}_진행.json"
    SUMMARY_JSON = f"{OUT_DIR}/12-1_생성댓글파싱_요약{tag}.json"
    LOG_PATH = f"{OUT_DIR}/12-1_생성댓글파싱_출력{tag}.log"
else:
    if ARGS.out_dir:
        sys.exit("--out-dir는 --smoke나 시험 입력과만 씁니다. 본 실행 산출 위치는 고정입니다.")
    OUT_JSON = f"{DATA_DIR}/12-1_계정사전.json"
    PROGRESS_JSON = f"{DATA_DIR}/12-1_계정사전_진행.json"
    SUMMARY_JSON = f"{HERE}/12-1_생성댓글파싱_요약.json"
    LOG_PATH = f"{HERE}/12-1_생성댓글파싱_출력.log"


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


def say(msg=""):
    print(msg, flush=True)


# ════════════════════════════════════════════════════════════════════════
# [설정]
# ════════════════════════════════════════════════════════════════════════
MIN_CHARS = 20          # [01] 정제 후 20자 미만 문서는 버린다
MIN_DOCS = 10           # [01] 적격 문서 10건 미만 계정 제외
MAX_DOCS = 200          # [01] 계정당 최근 200건
LANG_TARGET = "en"      # [01] 계정 단위 langid

SELF_REVEAL = re.compile(
    r"(as an ai language model"
    r"|i'?m sorry,? but (i cannot|as an ai)"
    r"|i cannot (comply|fulfill|browse)"
    r"|openai'?s? (content )?polic)", re.I)
RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
RE_URL = re.compile(r"(https?://\S+|www\.\S+)")
RE_MENTION = re.compile(r"@\w+")
RE_WS = re.compile(r"\s+")

SEED = 20260926
CHECKPOINT_EVERY = 100
SMOKE_N = 3
HAND_PER_CELL = 2
DET_ACCOUNTS = 3
EXPECT_FW_HASH = "382b68572f03bc23"
TIME_FMT = "%Y-%m-%d %H:%M:%S"
BUCKET = "생성"                                  # 결정 D5
BASE = "기준"                                    # 재생성 칸 이름(모델ID표의 기준 재생성)
UID_PREFIX = {"MODEL_SLOT_1": "G1_", "MODEL_SLOT_2": "G2_", "MODEL_SLOT_3": "G3_",
              "MODEL_SLOT_4": "G4_", BASE: "G0_"}
CELLS = ["MODEL_SLOT_1", "MODEL_SLOT_2", "MODEL_SLOT_3", "MODEL_SLOT_4", BASE]
MS_LOW, MS_HIGH = 28.86, 50.89   # 13-0 실측 ms/문서(원봇·완전모방기)
EXPECT_106 = 106
CB_MISSING = "재열람 뒤 다시 Continue browsing(BotSim 복사 경로, 재현 안 함)"
STATE_OK = ("성공", "결측", "차단")                # 생성 스크립트 run_slot의 종료 상태
REF_CELLS = ["원봇짝", "모방106"]                 # 결정 D13 기준 칸
REF_BUCKET = {"원봇짝": "comment_1", "모방106": "모방"}
WRAP_PREFIX = re.compile(r"^\s*(\*\*)?\[?[A-Za-z ]{1,20}\]?(\*\*)?\s*:")   # 결정 D12
QUOTE_PAIRS = (('"', '"'), ("\u201c", "\u201d"), ("'", "'"), ("\u2018", "\u2019"))
WRAP_MAX_FRAC = 0.01
LANGID_MARGIN = 0.05                              # 결정 D14
VARIANT_KEYS = ["복사제외없음", "복사민감도", "민감도_106제외",
                "짝_새모델쪽", "짝_새모델쪽_복사민감도", "짝_새모델쪽_복사제외없음",
                "짝_재생성쪽", "짝_재생성쪽_복사민감도", "짝_재생성쪽_복사제외없음",
                "짝_P12-0_재생성쪽", "짝_P12-0_재생성쪽_복사민감도", "짝_P12-0_재생성쪽_복사제외없음", "정제민감도"]
REF_VARIANTS = ["원봇_재생성성공슬롯", "원봇_재생성성공슬롯_복사민감도", "원봇_재생성성공슬롯_복사제외없음"]
VARIANT_LABEL = {"계정": "주 판: 모방 예시 복사(동일·비율 ≥ 0.9) 슬롯을 뺌(뼈대 4절 v3.2.7). 판정·예측은 이 판만",
                 "복사민감도": "복사 민감도: 비율 ≥ 0.8까지 뺌(보조)",
                 "복사제외없음": "복사 제외 없음: 규칙 이전 계정, 아무 슬롯도 빼지 않음(투명성 보조)"}
RE_NONWORD = re.compile(r"[^\w\s]")             # 결정 D15 정규화
COPY_HI, COPY_LO = 0.9, 0.8                     # 뼈대 4절 v3.2.7
COPY_LEN_TOL = 0.30
COPY_BINS = ("동일", "≥0.9", "0.8~0.9", "<0.8")
EX_LEN_EDGES = (50, 100, 150, 200)
FREEZE_KEYS = {"분할.json": SPLIT_JSON, "프롬프트대장.jsonl": LEDGER_JSONL,
               "완전모방기_문서.jsonl": MIMIC_JSONL, "13-0_계정사전.json": ACC130_JSON}

# ── BotSim 지연 규칙 (reddit_agent.py comment_time_function 그대로, 관문 G0이 원문과 대조) ──
DELAY_INTERVALS = {
    "less_than_1_min": (0, 60),
    "1_to_5_min": (60, 5 * 60),
    "5_to_10_min": (5 * 60, 10 * 60),
    "10_to_30_min": (10 * 60, 30 * 60),
    "30_min_to_1_hour": (30 * 60, 60 * 60),
    "1_to_3_hours": (60 * 60, 3 * 60 * 60),
    "3_to_10_hours": (3 * 60 * 60, 10 * 60 * 60),
    "10_to_24_hours": (10 * 60 * 60, 24 * 60 * 60),
}
DELAY_WEIGHTS = {
    "less_than_1_min": 3009,
    "1_to_5_min": 5060,
    "5_to_10_min": 2769,
    "10_to_30_min": 5727,
    "30_min_to_1_hour": 5727,
    "1_to_3_hours": 8472,
    "3_to_10_hours": 9304,
    "10_to_24_hours": 4818,
}

IMPL_DECISIONS = {
    "D1_칸": "새 모델 계정은 페르소나의 모델 슬롯과 호출 기록 모델이 맞는 것만. 다른 슬롯 페르소나 기록이 있으면 G3 실패.",
    "D2_시각": "게시물시각 + BotSim comment_time_function 지연(8구간 가중 random.choices → 구간 안 random.randint 양끝 포함). 슬롯마다 random.Random(sha256('20260926|슬롯id|지연') 앞 16자리). 같은 슬롯은 모델이 달라도 같은 지연. 13-0은 이 규칙을 쓰지 않았음(13-0 D3). 200건 상한 미도달이라 문서 집합 불변, 순서만 다름.",
    "D3_중복": "같은 슬롯 id의 '슬롯' 기록이 여럿이면 마지막 것, 수를 셈. '슬롯중단'만 있는 슬롯은 미완.",
    "D4_정제": "13-0 select_group 그대로(01 clean_doc). 뼈대 4절의 접두·따옴표·줄바꿈 제거는 따로 두지 않음(13-0이 세 집단에 clean_doc만 썼으므로 같은 함수 조건).",
    "D5_버킷": "버킷 키 '생성'(진단용).",
    "D6_손대조": "시드 20260926 random, 칸마다 2계정(smoke면 smoke 대상 안에서).",
    "D7_민감도": "모방 저자가 ver.1 학습 사람 106명(분할.json 역할 '모방' ∧ 09-1매칭_ver1학습)인 슬롯의 문서를 뺀 계정. 같은 파싱 결과로 aggregate 재계산, 10건 미만·langid 비영어면 제외.",
    "D8_문서별": "[슬롯id, 시각, 정제 글자수, 문장수, 구두점 제외 토큰수, Tense=Past, Tense 합]. 예시_계획일뒤 = 모방 예시 시각 ≥ 계획일 00:00:00.",
    "D9_중간저장": "산출 JSON 옆. 재개 지문 = 기능어·측정코드·코퍼스·106명 해시 + stanza 버전.",
    "D10_시험입력": "--run-dir가 DATA_DIR 밖이면 시험 입력. --out-dir 필수, 정식 산출 경로에 쓰지 않음.",
    "D11_짝계정": "성공 슬롯 교집합으로 한정(짝_새모델쪽: 재생성 성공 슬롯, 짝_재생성쪽: 배정 모델 성공 슬롯, 짝_P12-0_재생성쪽: 13-0 원 봇 계정 슬롯). 한정 뒤 10건·langid 재적용.",
    "D12_정제보고": "감싸기(같은 종류 따옴표 쌍) 또는 접두 정규식 ^\\s*(\\*\\*)?\\[?[A-Za-z ]{1,20}\\]?(\\*\\*)?\\s*: 문서를 칸마다 셈. 1% 넘는 칸은 접두 한 번·바깥 따옴표 한 쌍을 벗겨 clean_doc 다시, 그 문서만 다시 파싱한 정제민감도 계정.",
    "D13_기준칸": "원봇짝(13-0 원 봇 504를 재생성 성공 슬롯으로 한정, comment_1 버킷, 원 댓글 시각 순)과 모방106(13-0 완전 모방기 509에서 106명 슬롯 제외, 모방 버킷, 계획일 순)을 새로 파싱. 13-0 사전에 문서별 측정치가 없어서다. 빠진 문서가 없는 계정은 13-0과 대조(G10).",
    "D14_langid경계": "정규화 확률 1위 − 2위 < 0.05인 적격 계정 수(보고만). 이어 붙인 글에 거므로 문서 순서가 경계 계정을 원리상 뒤집을 수 있음.",
    "D15_모방예시복사": "(v3, 뼈대 4절 v3.2.7) 댓글 원문과 모방 예시 원문을 소문자·낱말공백 아닌 문자 제거·공백 하나로 정규화. 동일이거나 difflib.SequenceMatcher(None, a, b).ratio() ≥ 0.9면 복사 → 결측(계정·짝·P12-0 집합에서 빠짐). 길이 차 > 0.30 × 긴 쪽이면 비율 재지 않고 < 0.8. 둘 다 빈 문자열이면 동일. 비율 ≥ 0.8까지 뺀 복사민감도 변형(짝·P12-0 포함).",
}


# ════════════════════════════════════════════════════════════════════════
# [도구]
# ════════════════════════════════════════════════════════════════════════
class GateError(RuntimeError):
    pass


def check(cond, msg):
    """관문 판정. assert와 달리 python -O에서도 꺼지지 않는다."""
    if not cond:
        raise GateError(msg)


def line(title=""):
    say("\n" + "═" * 74)
    if title:
        say(title)
        say("═" * 74)


def label_marker(where):
    say(f"      [라벨 사용] {where}")


def write_json(path, obj, indent=None):
    """임시 파일에 쓰고 fsync 뒤 이름을 바꾼다. 중간에 멈춰도 이전 것 아니면 새 것."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def fmt_dur(sec):
    if sec < 90:
        return f"{sec:.0f}초"
    if sec < 5400:
        return f"{sec / 60:.1f}분"
    return f"{sec / 3600:.2f}시간"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path):
    return nfc(os.path.relpath(path, ROOT)) if path.startswith(ROOT) else path


# ════════════════════════════════════════════════════════════════════════
# [1] 정제·집계·문서 선택 (13-0에서 글자 그대로. G0이 AST로 확인한다)
# ════════════════════════════════════════════════════════════════════════
def clean_doc(text):
    """
    글 1건을 정제한다. [01_botsim_적격검열.py에서 가져옴, 12-0과 같음]
    통과하면 (정제 문자열, None, 절제여부), 탈락하면 (None, 사유, 절제여부).
    순서: 자기폭로 문장 절제 → URL·멘션 제거 → 길이 검사.
    """
    if not text:
        return None, "빈 문자열", False
    t = unicodedata.normalize("NFC", str(text))

    # (1) 자기폭로 문장만 도려내기
    excised = False
    if SELF_REVEAL.search(t):
        sents = RE_SENT_SPLIT.split(t)
        kept = [s for s in sents if s.strip() and not SELF_REVEAL.search(s)]
        t = " ".join(kept)
        excised = True
        if not t.strip():
            return None, "자기폭로 절제 후 내용 없음", True

    # (2) 링크·멘션 제거
    t = RE_URL.sub(" ", t)
    t = RE_MENTION.sub(" ", t)
    t = RE_WS.sub(" ", t).strip()

    # (3) 길이 검사
    if len(t) < MIN_CHARS:
        reason = ("자기폭로 절제 후 " if excised else "") + f"{MIN_CHARS}자 미만"
        return None, reason, excised
    return t, None, excised


def normalize_apostrophe(s):
    """굽은 아포스트로피(’)를 곧은 것(')으로. [12-0에서 가져옴]"""
    return s.replace("’", "'")


def aggregate(parsed, keys, funcword_set):
    """
    파싱된 문서 목록(한 계정분)을 받아 저장할 값 한 벌을 만든다. [12-0에서 가져옴]
      토큰        sent.words 의 원소 하나 (MWT 분해 뒤의 낱말 단위)
      구두점      UPOS == "PUNCT"
      문장 길이   문장마다 구두점을 뺀 토큰수 (08 정의)
      기능어      소문자 + 아포스트로피 정규화 표면형이 172종 목록에 있으면 1회
      자질        feats 문자열을 "|"로 끊어 "키=값" 단위로 센다
    """
    fw, upos, feats = Counter(), Counter(), Counter()
    buckets = {}
    sent_lens = []
    n_sent = n_tok = n_nopunct = n_punct = 0

    for doc, key in zip(parsed, keys):
        b = buckets.get(key)
        if b is None:
            b = buckets[key] = [0, 0, 0, 0]  # 문서수·문장수·토큰수·구두점제외
        b[0] += 1
        for sent in doc.sentences:
            n_sent += 1
            b[1] += 1
            sent_len = 0
            for w in sent.words:
                n_tok += 1
                b[2] += 1
                upos[w.upos] += 1
                if w.upos == "PUNCT":
                    n_punct += 1
                else:
                    n_nopunct += 1
                    b[3] += 1
                    sent_len += 1
                surface = normalize_apostrophe(w.text.lower())
                if surface in funcword_set:
                    fw[surface] += 1
                if w.feats:
                    for kv in w.feats.split("|"):
                        feats[kv] += 1
            sent_lens.append(sent_len)

    return {
        "문서수": len(parsed),
        "문장수": n_sent,
        "토큰수": n_tok,
        "토큰수_구두점제외": n_nopunct,
        "구두점토큰수": n_punct,
        "문장길이": sent_lens,
        "기능어": dict(fw.most_common()),
        "UPOS": dict(upos.most_common()),
        "자질": dict(feats.most_common()),
        "버킷별": {k: buckets[k] for k in sorted(buckets)},
    }


def measure_account(nlp, docs, keys, funcword_set):
    """계정 하나를 계정 단위 bulk_process로 파싱해 집계한다. [12-0에서 가져옴]"""
    parsed = nlp.bulk_process(docs)
    return aggregate(parsed, keys, funcword_set)


def relations_ok(a):
    """G7 내부 관계."""
    return (len(a["문장길이"]) == a["문장수"]
            and sum(a["문장길이"]) == a["토큰수_구두점제외"]
            and a["구두점토큰수"] == a["토큰수"] - a["토큰수_구두점제외"]
            and a["구두점토큰수"] == a["UPOS"].get("PUNCT", 0))


def hand_counts(doc):
    """aggregate와 별개의 코드로 문장수·구두점 제외 토큰수를 센다."""
    return (len(doc.sentences),
            sum(1 for s in doc.sentences for w in s.words if w.upos != "PUNCT"))


def select_group(accounts):
    """
    accounts: {uid: [(본문, 정렬키, 버킷키), ...]} (원본 순서).
    09-2와 같은 순서로 정제 → 정렬키 오름차순 안정 정렬 → 최근 MAX_DOCS건 →
    MIN_DOCS건 이상 → 계정 단위 langid en.
    반환: (work {uid: [(정제문, 버킷키), ...]}, 깔때기)
    """
    import langid
    drop = Counter()
    n_in = n_trim = n_exc = n_exc_kept = 0
    short, cand = [], {}
    for uid in sorted(accounts):
        rows = []
        for text, ts, key in accounts[uid]:
            n_in += 1
            cleaned, reason, excised = clean_doc(text)
            if excised:
                n_exc += 1
            if cleaned is None:
                drop[reason] += 1
                continue
            if excised:
                n_exc_kept += 1
            rows.append((ts, cleaned, key))
        rows.sort(key=lambda r: r[0])
        if len(rows) > MAX_DOCS:
            n_trim += len(rows) - MAX_DOCS
            rows = rows[-MAX_DOCS:]
        if len(rows) >= MIN_DOCS:
            cand[uid] = [(c, k) for _, c, k in rows]
        else:
            short.append({"uid": uid, "정제후문서수": len(rows)})
    work, nonen, langs = {}, [], Counter()
    for uid in sorted(cand):
        lang, _ = langid.classify(" ".join(c for c, _ in cand[uid]))
        langs[lang] += 1
        if lang == LANG_TARGET:
            work[uid] = cand[uid]
        else:
            nonen.append({"uid": uid, "lang": lang})
    funnel = {
        "대상계정수": len(accounts),
        "원본문서수": n_in,
        "문서탈락_사유별": dict(drop.most_common()),
        "문서탈락_합": sum(drop.values()),
        "자기폭로_절제문서수": n_exc,
        "자기폭로_절제후_생존문서수": n_exc_kept,
        "상한초과_절삭문서수": n_trim,
        "문서부족_탈락계정수": len(short),
        "문서부족_탈락계정": short,
        "언어판정_대상계정수": len(cand),
        "언어별_계정수": dict(langs.most_common()),
        "비영어_탈락계정수": len(nonen),
        "비영어_탈락계정": nonen,
        "적격계정수": len(work),
        "적격문서수": sum(len(v) for v in work.values()),
    }
    return work, funnel


def func_ast(src, name):
    """소스에서 함수 name의 AST를 docstring을 빼고 문자열로. 없으면 None."""
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            body = n.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                n.body = body[1:]
            return ast.dump(n)
    return None


def norm_text(s):
    """복사 슬롯 대조용: NFC + 공백 정규화. [12_OpenRouter생성.py 결정 AA와 같음]"""
    return " ".join(unicodedata.normalize("NFC", str(s or "")).split())


def wrapped(t):
    """정제 문서가 따옴표 쌍으로 감싸였거나 이름표 접두로 시작하는가(D12, 보고용)."""
    s = t.strip()
    quoted = len(s) >= 2 and any(s.startswith(a) and s.endswith(b) for a, b in QUOTE_PAIRS)
    return quoted or bool(WRAP_PREFIX.match(s))


def unwrap(t):
    """접두 한 번 떼고 바깥 따옴표 한 쌍을 뗀다(D12). 그 뒤 clean_doc을 다시 건다."""
    s = WRAP_PREFIX.sub("", t.strip(), count=1).strip()
    for a, b in QUOTE_PAIRS:
        if len(s) >= 2 and s.startswith(a) and s.endswith(b):
            s = s[len(a):len(s) - len(b)].strip()
            break
    return s


def measure_account_keep(nlp, docs, keys, funcword_set):
    """
    measure_account와 같은 두 줄(bulk_process → aggregate)에 파싱 결과를 함께
    돌려준다. 문서별 요약(D8)과 민감도 계정(D7)을 다시 파싱하지 않고 만들기 위해서다.
    G6이 13-0 사전 값과, G1이 measure_account 값과 같음을 확인한다.
    """
    parsed = nlp.bulk_process(docs)
    return aggregate(parsed, keys, funcword_set), parsed


def doc_summary(doc):
    """문서 하나의 요약(D8): 문장수, 구두점 제외 토큰수, Tense=Past 수, Tense 축 합."""
    n_sent = len(doc.sentences)
    n_np = past = tense = 0
    for s in doc.sentences:
        for w in s.words:
            if w.upos != "PUNCT":
                n_np += 1
            if w.feats:
                for kv in w.feats.split("|"):
                    if kv.startswith("Tense="):
                        tense += 1
                        if kv == "Tense=Past":
                            past += 1
    return n_sent, n_np, past, tense


def hand_aggregate(docs, funcword_set):
    """
    G1 손 대조용 독립 집계. aggregate를 부르지 않고 따로 짠 코드로 같은 필드를 센다.
    docs는 문서마다 단독 nlp(문서)로 파싱한 결과다.
    """
    out = {"문서수": 0, "문장수": 0, "토큰수": 0, "토큰수_구두점제외": 0, "구두점토큰수": 0,
           "문장길이": [], "기능어": {}, "UPOS": {}, "자질": {}}
    for d in docs:
        out["문서수"] += 1
        for s in d.sentences:
            out["문장수"] += 1
            ws = list(s.words)
            punct = [w for w in ws if w.upos == "PUNCT"]
            out["토큰수"] += len(ws)
            out["구두점토큰수"] += len(punct)
            out["토큰수_구두점제외"] += len(ws) - len(punct)
            out["문장길이"].append(len(ws) - len(punct))
            for w in ws:
                out["UPOS"][w.upos] = out["UPOS"].get(w.upos, 0) + 1
                t = w.text.lower().replace("’", "'")
                if t in funcword_set:
                    out["기능어"][t] = out["기능어"].get(t, 0) + 1
                for kv in (w.feats.split("|") if w.feats else []):
                    out["자질"][kv] = out["자질"].get(kv, 0) + 1
    return out


# ════════════════════════════════════════════════════════════════════════
# [2] BotSim 지연 규칙 (결정 D2)
# ════════════════════════════════════════════════════════════════════════
def delay_seed(slot_id):
    return int(hashlib.sha256(f"{SEED}|{slot_id}|지연".encode("utf-8")).hexdigest()[:16], 16)


def botsim_comment_time(post_time, slot_id):
    """
    reddit_agent.py comment_time_function과 같은 두 호출(random.choices → randint)을
    슬롯 시드 난수 생성기로 한다. 반환 (댓글 시각 문자열, 구간 이름, 지연 초).
    """
    rng = random.Random(delay_seed(slot_id))
    selected = rng.choices(list(DELAY_INTERVALS.keys()), weights=list(DELAY_WEIGHTS.values()), k=1)[0]
    lo, hi = DELAY_INTERVALS[selected]
    sec = rng.randint(lo, hi)
    t = datetime.strptime(post_time, TIME_FMT) + timedelta(seconds=sec)
    return t.strftime(TIME_FMT), selected, sec


def const_eval(node):
    """상수·튜플·사전과 +·−·× 식만 계산한다. 그 밖의 노드(이름·호출 등)는 관문 실패다."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(const_eval(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return {const_eval(k): const_eval(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Add, ast.Sub)):
        a, b = const_eval(node.left), const_eval(node.right)
        if isinstance(node.op, ast.Mult):
            return a * b
        return a + b if isinstance(node.op, ast.Add) else a - b
    raise GateError(f"BotSim 지연 규칙에 상수 식이 아닌 노드가 있습니다: {ast.dump(node)[:80]}")


def gate_delay_constants():
    """BotSim 원문 comment_time_function의 두 사전과 호출 모양을 이 파일 상수와 대조한다."""
    src = open(AGENT_PY, encoding="utf-8").read()
    fn = None
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.FunctionDef) and n.name == "comment_time_function":
            fn = n
    check(fn is not None, "reddit_agent.py에 comment_time_function이 없습니다.")
    found = {}
    for st in fn.body:
        if isinstance(st, ast.Assign) and isinstance(st.targets[0], ast.Name) \
                and st.targets[0].id in ("time_intervals", "weights"):
            # 원문의 곱셈 식(5*60 등)을 상수·튜플·사전·사칙 노드만 허용하는 평가기로 계산한다.
            found[st.targets[0].id] = const_eval(st.value)
    seg = ast.get_source_segment(src, fn)
    calls_ok = ("random.choices(list(time_intervals.keys()), weights=list(weights.values()), k=1)[0]" in seg
                and "random.randint(interval_range[0], interval_range[1])" in seg
                and "target_post_time + random_timedelta" in seg)
    same_i = found.get("time_intervals") == DELAY_INTERVALS and list(found.get("time_intervals", {})) == list(DELAY_INTERVALS)
    same_w = found.get("weights") == DELAY_WEIGHTS and list(found.get("weights", {})) == list(DELAY_WEIGHTS)
    say(f"      BotSim 지연 규칙: 구간 {'같음' if same_i else '다름'} · 가중치 {'같음' if same_w else '다름'} · "
        f"호출 모양(choices → randint, 게시물 시각 + 지연) {'같음' if calls_ok else '다름'}")
    check(same_i and same_w and calls_ok, "BotSim 지연 규칙이 원문과 다릅니다.")
    return {"원문": rel(AGENT_PY), "원문_sha256": file_sha256(AGENT_PY), "구간": same_i, "가중치": same_w,
            "호출모양": calls_ok, "통과": True}


# ════════════════════════════════════════════════════════════════════════
# [3] 관문 G0: 입력 사슬 · 함수 동일성
# ════════════════════════════════════════════════════════════════════════
COPIED_130 = ["clean_doc", "normalize_apostrophe", "aggregate", "measure_account", "relations_ok",
              "hand_counts", "select_group", "func_ast", "norm_text"]


def gate_function_identity():
    me = open(SCRIPT_PATH, encoding="utf-8").read()
    s01 = open(PY01, encoding="utf-8").read()
    s130 = open(PY130, encoding="utf-8").read()
    rows = []
    for name in COPIED_130:
        a, b = func_ast(me, name), func_ast(s130, name)
        rows.append({"함수": name, "대상": "13-0", "같음": a is not None and a == b})
    a, b = func_ast(me, "clean_doc"), func_ast(s01, "clean_doc")
    rows.append({"함수": "clean_doc", "대상": "01", "같음": a is not None and a == b})
    for r in rows:
        say(f"      {r['함수']:<22} = {r['대상']:<5} {'같음' if r['같음'] else '다름'}")
    # 정제 상수(13-0 gate_function_identity와 같은 대조)
    for const in ("MIN_CHARS = 20", "MIN_DOCS = 10", "MAX_DOCS = 200",
                  'RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\\s+|\\n+")',
                  'RE_URL = re.compile(r"(https?://\\S+|www\\.\\S+)")',
                  'RE_MENTION = re.compile(r"@\\w+")', 'RE_WS = re.compile(r"\\s+")'):
        same = const in s01 and const in me and const in s130
        rows.append({"상수": const, "01·13-0과같음": same})
    sr = re.compile(r"SELF_REVEAL = re\.compile\((.*?)re\.I\)", re.S)
    strip = lambda m: re.sub(r"#[^\n]*", "", m.group(1)).split() if m else None
    same_sr = strip(sr.search(s01)) is not None and strip(sr.search(s01)) == strip(sr.search(me))
    rows.append({"상수": "SELF_REVEAL", "01·13-0과같음": same_sr})
    say(f"      정제 상수(MIN_CHARS·MIN_DOCS·MAX_DOCS·정규식 5개) = 01·13-0  "
        f"{'같음' if all(r.get('01·13-0과같음', True) for r in rows) else '다름'}")
    dash = [hex(c) for c in (0x2014, 0x2013) if chr(c) in me]
    say(f"      이 파일의 줄표·반각 대시  {'없음' if not dash else '있음'}")
    ok = all(r.get("같음", r.get("01·13-0과같음")) for r in rows) and not dash
    check(ok, "함수 또는 상수가 01·13-0과 다르거나 줄표가 있습니다.")
    code_hash = sha16("\n".join(func_ast(me, n) for n in
                                ("clean_doc", "normalize_apostrophe", "aggregate", "measure_account",
                                 "measure_account_keep", "doc_summary")))
    return rows, code_hash


def gate_chain():
    freeze = json.load(open(FREEZE_JSON, encoding="utf-8"))
    rows = {}
    for k, p in FREEZE_KEYS.items():
        check(os.path.exists(p), f"입력 없음: {p}")
        got = file_sha256(p)
        rows[k] = {"경로": rel(p), "sha256": got, "동결": freeze.get(k), "같음": got == freeze.get(k)}
    mid = file_sha256(MODELID_JSON)
    rows["모델ID표.json"] = {"경로": rel(MODELID_JSON), "sha256": mid, "동결": freeze.get("모델ID표.json"),
                          "같음": mid == freeze.get("모델ID표.json")}
    for k, v in rows.items():
        say(f"      사슬 {k:<22} {v['sha256'][:16]}…  동결 {'같음' if v['같음'] else '다름'}")
    check(all(v["같음"] for v in rows.values()), "입력 sha256이 동결.json과 다릅니다.")
    return rows


# ════════════════════════════════════════════════════════════════════════
# [4] 호출 기록 읽기 (결정 D3)
# ════════════════════════════════════════════════════════════════════════
def find_run_file(model):
    slug = model.replace("/", "_")
    pat = re.compile(rf"호출기록_{re.escape(slug)}_([0-9a-f]{{8}})\.jsonl")
    hits = sorted((nfc(n), m.group(1)) for n in os.listdir(RUN_DIR)
                  for m in [pat.fullmatch(nfc(n))] if m)
    check(len(hits) == 1, f"{model}의 호출 기록 파일이 정확히 하나가 아닙니다: {[h[0] for h in hits]}")
    return f"{RUN_DIR}/{hits[0][0]}", hits[0][1]


CALL_KEEP = ("종류", "슬롯id", "요청모델", "설정해시", "판정", "원형파서", "finish_reason", "분류")


def read_rows(path):
    """
    JSON 줄을 한 줄씩 읽는다. 줄바꿈 없이 잘린 마지막 줄은 버리고 경고한다(생성 스크립트
    결정 Y와 같음). 호출 줄은 보고에 쓰는 열만 남긴다(본문·요청을 들고 있지 않아 메모리를 아낀다).
    """
    rows, cut = [], False
    with open(path, "rb") as f:
        for i, ln in enumerate(f):
            if not ln.endswith(b"\n"):
                if ln.strip():
                    cut = True
                break
            if not ln.strip():
                continue
            try:
                r = json.loads(ln.decode("utf-8"))
            except Exception as e:
                raise GateError(f"{os.path.basename(path)} {i + 1}번째 줄을 읽지 못했습니다: {e!r}")
            if r.get("종류") in ("호출", "탐색호출"):
                r = {k: r.get(k) for k in CALL_KEEP}
            rows.append(r)
    return rows, cut


def summarize_run(model, cell, path, hash8, rows, assigned):
    """
    모델 하나의 호출 기록을 요약한다. 슬롯 종료 기록은 슬롯 id마다 마지막 것(D3).
    반환: (보고 사전, 최종 슬롯 기록 {슬롯id: 기록}, 슬롯별 호출 통계)
    """
    starts = [r for r in rows if r.get("종류") == "실행시작"]
    check(starts, f"{model}: 실행시작 줄이 없습니다.")
    for r in starts:
        check(r.get("모드") == "본 생성",
              f"{model}: 실행시작 줄의 모드가 '본 생성'이 아닙니다({r.get('모드')!r}). 다른 기록이 섞였습니다(G8).")
        check(isinstance(r.get("설정해시"), str) and len(r["설정해시"]) == 64,
              f"{model}: 실행시작 줄에 설정해시(64자)가 없습니다(G8).")
    hashes = sorted({r.get("설정해시") for r in starts})
    check(len(hashes) == 1, f"{model}: 실행시작 줄의 설정해시가 {len(hashes)}개입니다 {hashes}. 거부합니다.")
    h = hashes[0]
    check(isinstance(h, str) and h[:8] == hash8, f"{model}: 설정해시 {h} 앞 8자가 파일 이름 {hash8}과 다릅니다.")
    other_hash = [r.get("종류") for r in rows if "설정해시" in r and r.get("설정해시") != h]
    check(not other_hash, f"{model}: 다른 설정해시 줄 {len(other_hash)}개가 섞여 있습니다.")
    wrong_model = [r.get("종류") for r in rows if "요청모델" in r and r.get("요청모델") != model]
    check(not wrong_model, f"{model}: 요청모델이 다른 줄 {len(wrong_model)}개가 있습니다.")
    kinds = Counter(r.get("종류") for r in rows)
    final, dup = {}, Counter()
    canon = lambda r: json.dumps(r, ensure_ascii=False, sort_keys=True)
    for r in rows:
        if r.get("종류") == "슬롯":
            check(isinstance(r.get("슬롯id"), str), f"{model}: 슬롯id가 없는 종료 기록이 있습니다(G8).")
            check(r.get("상태") in STATE_OK,
                  f"{model}: {r['슬롯id']} 종료 기록의 상태 {r.get('상태')!r}가 성공·결측·차단이 아닙니다(G8).")
            if r.get("상태") == "성공":
                bad = [k for k in ("댓글", "게시물id", "게시물시각") if not isinstance(r.get(k), str)]
                check(not bad, f"{model}: {r['슬롯id']} 성공 기록의 {bad}가 문자열이 아닙니다(G8).")
            if r["슬롯id"] in final:
                check(canon(r) == canon(final[r["슬롯id"]]),
                      f"{model}: {r['슬롯id']} 종료 기록이 둘 이상이고 내용이 다릅니다(G8). 거부합니다.")
                dup[r["슬롯id"]] += 1
            final[r["슬롯id"]] = r
    halted = Counter(r["슬롯id"] for r in rows if r.get("종류") == "슬롯중단")
    calls = [r for r in rows if r.get("종류") == "호출"]
    per_slot = defaultdict(Counter)
    for r in calls:
        c = per_slot[r["슬롯id"]]
        c["호출"] += 1
        c["판정:" + str(r.get("판정"))] += 1
    attempted = set(per_slot) | set(final) | set(halted)
    st = Counter(r.get("상태") for r in final.values())
    miss = Counter(r.get("사유") for r in final.values() if r.get("상태") == "결측")
    succ_calls = [r for r in calls if r.get("판정") == "성공"]
    unfinished = sorted(set(halted) - set(final))
    rep = {
        "모델": model, "칸": cell, "파일": os.path.basename(path), "설정해시": h,
        "실행시작_수": len(starts), "생성스크립트_sha256": sorted({str(r.get("스크립트sha256")) for r in starts}),
        "파일_sha256": file_sha256(path), "줄종류": dict(kinds),
        "배정슬롯": len(assigned), "시도슬롯": len(attempted), "미시도슬롯": len(set(assigned) - attempted),
        "종료기록_슬롯수": len(final), "종료기록_중복": sum(dup.values()), "중복슬롯": sorted(dup)[:50],
        "성공": st.get("성공", 0), "결측": st.get("결측", 0), "차단": st.get("차단", 0),
        "기타상태": {k: v for k, v in st.items() if k not in ("성공", "결측", "차단")},
        "결측사유": dict(miss.most_common()),
        "CB_결측": miss.get(CB_MISSING, 0),
        "슬롯중단_기록수": sum(halted.values()), "슬롯중단_뒤_완료": len(set(halted) & set(final)),
        "슬롯중단_미완": len(unfinished), "슬롯중단_미완_목록": unfinished[:50],
        "length발생_슬롯": sum(1 for r in final.values() if r.get("length발생")),
        "length표시_성공": sum(1 for r in final.values() if r.get("상태") == "성공" and r.get("length표시")),
        "max_tokens2배_슬롯": sum(1 for r in final.values() if r.get("max_tokens2배_사용")),
        "재열람화면_성공": sum(1 for r in final.values() if r.get("상태") == "성공" and r.get("화면") == 2),
        "호출수": len(calls), "탐색호출수": kinds.get("탐색호출", 0),
        "호출_판정분포": dict(Counter(str(r.get("판정")) for r in calls).most_common()),
        "호출_분류분포": dict(Counter(str(r.get("분류")) for r in calls).most_common()),
        "finish_reason분포": dict(Counter(str(r.get("finish_reason")) for r in calls).most_common()),
        "CB호출": sum(1 for r in calls if r.get("판정") == "Continue browsing"),
        "CB호출_슬롯": sum(1 for c in per_slot.values() if c["판정:Continue browsing"]),
        "거절호출": sum(1 for r in calls if r.get("판정") == "거절"),
        "거절호출_슬롯": sum(1 for c in per_slot.values() if c["판정:거절"]),
        "거절_결측슬롯": sum(1 for s, r in final.items()
                          if r.get("상태") == "결측" and per_slot[s]["판정:거절"]),
        "성공호출_원형파서": dict(Counter(str(r.get("원형파서")) for r in succ_calls).most_common()),
        "성공호출_원형파서실패_몫": (sum(1 for r in succ_calls if r.get("원형파서") != "성공") / len(succ_calls)
                              if succ_calls else None),
    }
    return rep, final, per_slot, set(halted)


# ════════════════════════════════════════════════════════════════════════
# [5] 관문 G3: 대장·창
# ════════════════════════════════════════════════════════════════════════
def build_post_index(data, labels):
    """[라벨 사용] 사람 게시물만 서브레딧별 시각순으로 모은다(12 생성 스크립트 build_indexes와 같은 거름)."""
    by_sub = defaultdict(list)
    for uid, v in data.items():
        if labels.get(uid) != "human":
            continue
        for p in v.get("posts") or []:
            by_sub[p["subreddit"]].append((datetime.strptime(p["created_utc"], TIME_FMT),
                                           p["submission_id"], p["created_utc"]))
    for s in by_sub:
        by_sub[s].sort(key=lambda t: (t[0], t[1]))
    times = {s: [t[0] for t in lst] for s, lst in by_sub.items()}
    return by_sub, times


def window_posts(by_sub, times, subs, begin, end):
    """창 (begin, end) 양끝 제외, 페르소나 서브레딧 목록 안의 사람 게시물 [(id, 시각 문자열)]."""
    b = datetime.strptime(begin, TIME_FMT)
    e = datetime.strptime(end, TIME_FMT)
    out = []
    for s in sorted(set(subs)):
        ts = times.get(s)
        if not ts:
            continue
        lo, hi = bisect_right(ts, b), bisect_left(ts, e)
        out.extend((pid, tstr) for _, pid, tstr in by_sub[s][lo:hi])
    return out


def gate_windows(ledger_prompted, pinfo_by_pid, by_sub, times, succ_by_slot):
    """G3의 창 부분. 대장 행마다 창을 다시 세워 수·첫 화면·재열람을 대조하고 성공 짝을 본다."""
    bad_count, bad_ids, bad_pairs = [], [], []
    n_pairs = 0
    for sid, r in ledger_prompted.items():
        p = pinfo_by_pid[r["페르소나id"]]
        posts = window_posts(by_sub, times, p["서브레딧목록"], r["창"][0], r["창"][1])
        ids = {pid for pid, _ in posts}
        if len(posts) != r["창_사람게시물수"] or len(ids) != len(posts):
            bad_count.append(sid)
        if not (set(r["게시물id5"]) <= ids and set(r.get("재열람_게시물id") or []) <= ids):
            bad_ids.append(sid)
        wants = succ_by_slot.get(sid)
        if wants:
            pairs = set(posts)
            for model, pair in wants:
                n_pairs += 1
                if pair not in pairs:
                    bad_pairs.append({"슬롯id": sid, "모델": model, "짝": list(pair)})
    say(f"      창 재구성 {len(ledger_prompted):,}슬롯: 게시물 수 = 대장 불일치 {len(bad_count)} · "
        f"첫 화면·재열람 id ⊄ 창 {len(bad_ids)}")
    say(f"      성공 댓글 (게시물 id, 시각) {n_pairs:,}건 ∈ 그 슬롯 창: 밖 {len(bad_pairs)}")
    return {"창재구성_슬롯": len(ledger_prompted), "게시물수_불일치": len(bad_count),
            "게시물수_불일치_예": bad_count[:20], "화면id_창밖": len(bad_ids), "화면id_창밖_예": bad_ids[:20],
            "성공짝": n_pairs, "성공짝_창밖": len(bad_pairs), "성공짝_창밖_예": bad_pairs[:20],
            "통과": not bad_count and not bad_ids and not bad_pairs}


# ════════════════════════════════════════════════════════════════════════
# [6] 문서 만들기 (결정 D2·D4)
# ════════════════════════════════════════════════════════════════════════
def build_accounts(finals, cell_of_model, personas, ledger_prompted, slot_order, skip=None):
    """
    칸마다 {uid: [(댓글, 시각, 슬롯id)]}를 만든다. 슬롯은 대장 순서(페르소나 안 슬롯 번호).
    성공이 하나도 없는 배정 페르소나도 빈 목록으로 넣는다(깔때기의 문서부족 탈락에 들어간다).
    skip: {모델: 뺄 슬롯 집합}(D15 모방 예시 복사). None이면 빼지 않는다(보고용 비교 판).
    """
    accs, meta, delays = {}, {}, Counter()
    for model, fin in finals.items():
        cell = cell_of_model[model]
        prefix = UID_PREFIX[cell]
        members = [p for p in personas if cell == BASE or p["모델슬롯"] == cell]
        acc = {prefix + p["원봇uid"]: [] for p in members}
        for p in members:
            meta[prefix + p["원봇uid"]] = (cell, model, p)
        for sid in slot_order:
            r = fin.get(sid)
            if r is None or r.get("상태") != "성공" or (skip is not None and sid in skip[model]):
                continue
            p = personas_by_pid[ledger_prompted[sid]["페르소나id"]]
            uid = prefix + p["원봇uid"]
            check(uid in acc, f"{model}: 배정 밖 페르소나의 성공 슬롯 {sid}")
            ts, interval, _ = botsim_comment_time(r["게시물시각"], sid)
            delays[interval] += 1
            acc[uid].append((str(r.get("댓글") or ""), ts, sid))
        accs[cell] = acc
    return accs, meta, delays


def norm_copy(s):
    """D15 정규화: 소문자, 낱말·공백이 아닌 문자 제거, 공백 하나로."""
    return " ".join(RE_NONWORD.sub("", str(s or "").lower()).split())


def copy_bin(out, ex):
    """D15: (구간, 비율). 동일이면 비율 1.0. 길이 차가 30% 넘으면 비율 없이 <0.8."""
    a, b = norm_copy(out), norm_copy(ex)
    if a == b:
        return "동일", 1.0
    la, lb = len(a), len(b)
    if abs(la - lb) > COPY_LEN_TOL * max(la, lb):
        return "<0.8", None
    r = difflib.SequenceMatcher(None, a, b).ratio()
    return ("≥0.9" if r >= COPY_HI else "0.8~0.9" if r >= COPY_LO else "<0.8"), r


def copy_flags(finals, ex_text):
    """모델마다 {슬롯id: (구간, 비율)}. 성공 슬롯만."""
    return {m: {sid: copy_bin(r.get("댓글"), ex_text[sid]) for sid, r in fin.items() if r.get("상태") == "성공"}
            for m, fin in finals.items()}


def ex_len_bin(n):
    for e in EX_LEN_EDGES:
        if n < e:
            return f"<{e}"
    return f"≥{EX_LEN_EDGES[-1]}"


def corpus_hash_of(work_all):
    return sha16("\n".join(f"{u}\t{k}\t{t}" for u in sorted(work_all) for t, k in work_all[u]))


# ════════════════════════════════════════════════════════════════════════
# [7] 관문 G6 13-0 정합 · G1 손 대조 · G2 결정성
# ════════════════════════════════════════════════════════════════════════
def gate_13_0(nlp, funcword_set, acc130, mimic_rows):
    """13-0 완전 모방기 계정 하나를 13-0 순서(계획일)로 다시 짓고 측정 경로로 잰다."""
    uids = sorted(u for u, a in acc130["계정"].items() if a["집단"] == "완전모방기")
    uid = random.Random(SEED).choice(uids)
    items = [(str(r.get("comment_body") or ""), r["계획일"], "모방") for r in mimic_rows if r["uid"] == uid]
    w, _ = select_group({uid: items})
    check(uid in w, f"13-0 정합: {uid}가 적격이 아닙니다.")
    got, _ = measure_account_keep(nlp, [t for t, _ in w[uid]], [k for _, k in w[uid]], funcword_set)
    old = acc130["계정"][uid]
    fields = ["문서수", "문장수", "토큰수", "토큰수_구두점제외", "구두점토큰수", "문장길이", "기능어",
              "UPOS", "자질", "버킷별"]
    rows = {f: got[f] == old[f] for f in fields}
    say(f"      13-0 완전 모방기 {uid}: 문서 {got['문서수']} · 문장 {got['문장수']} · 필드 "
        f"{sum(rows.values())}/{len(fields)} 같음")
    check(all(rows.values()), f"13-0 정합 실패: {[f for f, v in rows.items() if not v]}")
    return {"계정": uid, "필드별_같음": rows, "통과": True}


def gate_hand(nlp, funcword_set, work, cell_of_uid):
    """G1: 칸마다 2계정. 단독 파싱 + 독립 집계 = bulk 측정(버킷별 제외 모든 필드)."""
    rng = random.Random(SEED)
    rows, expect = [], {}
    fields = ["문서수", "문장수", "토큰수", "토큰수_구두점제외", "구두점토큰수", "문장길이", "기능어", "UPOS", "자질"]
    for cell in CELLS:
        uids = sorted(u for u in work if cell_of_uid[u] == cell)
        for uid in rng.sample(uids, min(HAND_PER_CELL, len(uids))):
            texts = [t for t, _ in work[uid]]
            agg, parsed = measure_account_keep(nlp, texts, [BUCKET] * len(texts), funcword_set)
            ref = measure_account(nlp, texts, [BUCKET] * len(texts), funcword_set)
            singles = [nlp(t) for t in texts]
            hand = hand_aggregate(singles, funcword_set)
            per_doc = [hand_counts(s) == hand_counts(b) for s, b in zip(singles, parsed)]
            same = {f: hand[f] == agg[f] for f in fields}
            ok = all(same.values()) and all(per_doc) and ref == agg and relations_ok(agg)
            rows.append({"칸": cell, "계정": uid, "문서수": len(texts), "필드별_같음": same,
                         "문서별_단독=bulk": sum(per_doc), "measure_account와_같음": ref == agg, "같음": ok})
            say(f"      {cell:<13} {uid:<16} 문서 {len(texts):>3} · 독립 집계 필드 {sum(same.values())}/{len(fields)} · "
                f"문서별 단독=bulk {sum(per_doc)}/{len(per_doc)} · measure_account {'같음' if ref == agg else '다름'}  "
                f"{'통과' if ok else '실패'}")
            check(ok, f"손 대조 실패: {cell} {uid}")
            expect[uid] = agg
    return rows, expect


# ════════════════════════════════════════════════════════════════════════
# [8] 측정 · 중간 저장 · 재개
# ════════════════════════════════════════════════════════════════════════
def load_progress():
    if not os.path.exists(PROGRESS_JSON):
        return None
    return json.load(open(PROGRESS_JSON, encoding="utf-8"))


def save_progress(done, fp, elapsed):
    write_json(PROGRESS_JSON, {
        "안내": "12-1 중간 저장. 측정이 끝나면 자동으로 지웁니다.",
        "지문": fp, "완료계정수": len(done), "누적소요초": round(elapsed, 1),
        "저장시각": time.strftime("%Y-%m-%d %H:%M:%S"), "계정": done})


def measure_one(nlp, funcword_set, items, variants, bucket=BUCKET):
    """
    계정 하나: 측정 + 문서별 요약 + 변형 계정(D7·D11·D12). 파싱은 한 번이다. 정제 민감도는
    바뀐 문서만 다시 파싱한다.
    variants: [(이름, 남길 슬롯 집합 또는 None, 벗기기 여부)]
    """
    import langid
    texts = [t for t, _ in items]
    sids = [k for _, k in items]
    agg, parsed = measure_account_keep(nlp, texts, [bucket] * len(texts), funcword_set)
    docs = [[sid, None, len(t), *doc_summary(d)] for (t, sid), d in zip(items, parsed)]
    out = {}
    for name, keep_set, strip in variants:
        keep = [i for i, s in enumerate(sids) if keep_set is None or s in keep_set]
        idx = [i for i in keep if wrapped(texts[i])] if strip else []
        if len(keep) == len(sids) and not idx:
            out[name] = {"상태": "같음(뺄 문서 없음)"}
            continue
        extra = {"뺀문서수": len(sids) - len(keep)}
        new_texts, dropped = {}, 0
        for i in idx:
            c, _, _ = clean_doc(unwrap(texts[i]))
            if c is None:
                dropped += 1
            else:
                new_texts[i] = c
        re_idx = sorted(new_texts)
        reparsed = dict(zip(re_idx, nlp.bulk_process([new_texts[i] for i in re_idx]))) if re_idx else {}
        seq_docs, seq_texts = [], []
        for i in keep:
            if i in reparsed:
                seq_docs.append(reparsed[i])
                seq_texts.append(new_texts[i])
            elif i not in idx:
                seq_docs.append(parsed[i])
                seq_texts.append(texts[i])
        if strip:
            extra.update({"바뀐문서수": len(idx), "벗긴뒤_탈락": dropped})
        if len(seq_docs) < MIN_DOCS:
            out[name] = {"상태": "제외", "사유": f"{len(seq_docs)}건(< {MIN_DOCS})", **extra}
            continue
        lang, _ = langid.classify(" ".join(seq_texts))
        if lang != LANG_TARGET:
            out[name] = {"상태": "제외", "사유": f"langid {lang}", **extra}
            continue
        out[name] = {"상태": "재집계", "집계": aggregate(seq_docs, [bucket] * len(seq_docs), funcword_set), **extra}
    return agg, docs, out


def run_measurement(nlp, work, order, funcword_set, fp, variants_of, bucket_of, cell_of_uid):
    done, prev = {}, 0.0
    prog = load_progress()
    if prog:
        if prog.get("지문") != fp:
            say(f"■ 중단: 중간 저장 지문이 다릅니다.\n  저장: {prog.get('지문')}\n  지금: {fp}")
            say(f"  기준이 다른 수치를 이어 붙이지 않습니다. {PROGRESS_JSON} 을(를) 지우고 다시 실행하십시오.")
            sys.exit(1)
        done, prev = prog["계정"], prog.get("누적소요초", 0.0)
        say(f"      중간 저장 발견: 완료 {len(done):,}계정 (누적 {fmt_dur(prev)}). 이어서 합니다.")
    else:
        say("      중간 저장 없음. 처음부터 시작합니다.")
    todo = [u for u in order if u not in done]
    todo_docs = sum(len(work[u]) for u in todo)
    say(f"      남은 계정 {len(todo):,} · 문서 {todo_docs:,}건 · 예상 "
        f"{fmt_dur(todo_docs * MS_LOW / 1000)}({MS_LOW} ms/문서) ~ "
        f"{fmt_dur(todo_docs * MS_HIGH / 1000)}({MS_HIGH} ms/문서)")
    t0 = time.time()
    docs_run = 0
    per_cell = defaultdict(lambda: [0, 0.0])
    for i, uid in enumerate(todo, 1):
        ta = time.time()
        agg, docs, var = measure_one(nlp, funcword_set, work[uid], variants_of(uid), bucket_of(uid))
        check(relations_ok(agg), f"내부 관계 위반: {uid}")
        for name, v in var.items():
            if v.get("집계") is not None:
                check(relations_ok(v["집계"]), f"변형 계정 내부 관계 위반: {name} {uid}")
        done[uid] = {"집계": agg, "문서별": docs, "변형": var}
        docs_run += len(work[uid])
        per_cell[cell_of_uid[uid]][0] += len(work[uid])
        per_cell[cell_of_uid[uid]][1] += time.time() - ta
        if i % CHECKPOINT_EVERY == 0 or i == len(todo):
            el = time.time() - t0
            save_progress(done, fp, prev + el)
            left = (todo_docs - docs_run) * el / max(docs_run, 1)
            say(f"      {len(done):,}/{len(order):,} 계정 · 경과 {fmt_dur(el)} · "
                f"{el / max(docs_run, 1) * 1000:.1f} ms/문서 · 잔여 추정 {fmt_dur(left)} · 저장")
    run_sec = time.time() - t0
    return done, run_sec, prev + run_sec, dict(per_cell)


def langid_margins(work, cell_of_uid, cells):
    """D14: 적격 계정의 이어 붙인 글에서 langid 정규화 확률 1위 − 2위 < 0.05인 계정 수."""
    from langid.langid import LanguageIdentifier, model
    li = LanguageIdentifier.from_modelstring(model, norm_probs=True)
    out = {}
    for c in cells:
        near, top_other = [], []
        for u in sorted(x for x in work if cell_of_uid[x] == c):
            r = li.rank(" ".join(t for t, _ in work[u]))
            if r[0][0] != LANG_TARGET:
                top_other.append(u)
            if r[0][1] - r[1][1] < LANGID_MARGIN:
                near.append({"uid": u, "1위": r[0][0], "차": r[0][1] - r[1][1]})
        out[c] = {"계정수": sum(1 for x in work if cell_of_uid[x] == c), "경계_계정수": len(near),
                  "경계_계정": near[:20], "정규화1위_비영어": len(top_other)}
    return out


# ════════════════════════════════════════════════════════════════════════
# [9] 본 흐름
# ════════════════════════════════════════════════════════════════════════
personas_by_pid = {}


def main():
    t_start = time.time()
    run_info = {
        "실행시각": time.strftime("%Y-%m-%d %H:%M:%S"),
        "스크립트": rel(SCRIPT_PATH), "스크립트_sha256": file_sha256(SCRIPT_PATH),
        "sys.flags.optimize": sys.flags.optimize, "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}", "smoke": SMOKE,
        "시험입력": TEST_INPUT, "호출기록_폴더": RUN_DIR, "allow_incomplete": ARGS.allow_incomplete,
        "경로_NFC": all(p == nfc(p) for p in (SCRIPT_PATH, OUT_JSON, SUMMARY_JSON, PROGRESS_JSON)),
    }
    line("12-1 생성 댓글 파싱 v2: 새 모델 4칸 · gpt-4o-mini 재생성 · 기준 칸 2 (뼈대 v3.2 5절 1항)")
    for k, v in run_info.items():
        say(f"  {k}: {v}")
    say(f"  산출 {OUT_JSON}\n  요약 {SUMMARY_JSON}\n  로그 {LOG_PATH}\n  중간 저장 {PROGRESS_JSON}")
    gates = {}
    summary = {"안내": "12-1 생성 댓글 파싱 요약. 계정별 측정치는 산출.계정사전 경로(볼트 밖).",
               "상태": "시작", "실행": run_info}

    def dump_summary(state):
        summary["상태"] = state
        summary["관문"] = gates
        write_json(SUMMARY_JSON, summary, indent=1)

    # ── [0/7] 입력 사슬 · 잠금 파일 ───────────────────────────────
    line("[0/7] 입력 sha256 = 동결.json (G0) · 생성 잠금 파일(G8)")
    locks = sorted(nfc(n) for n in os.listdir(RUN_DIR) if re.fullmatch(r"호출기록_.*\.jsonl\.lock", nfc(n)))
    say(f"      호출기록 잠금 파일 {len(locks)} {locks[:5]}")
    gates["G8_잠금파일"] = {"잠금": locks, "smoke": SMOKE, "통과": not locks or SMOKE}
    if locks and SMOKE:
        say("      경고: 생성이 진행 중입니다. smoke라 계속합니다(본 실행은 거부).")
    check(not locks or SMOKE, f"생성 잠금 파일이 있습니다 {locks}. 생성이 끝난 뒤 실행하십시오(G8).")
    chain = gate_chain()
    sha130_start = file_sha256(ACC130_JSON)
    acc130 = json.load(open(ACC130_JSON, encoding="utf-8"))
    ok130 = acc130["설정"].get("관문통과") is True and acc130["설정"].get("smoke") is False
    say(f"      13-0 계정사전 관문통과 {acc130['설정'].get('관문통과')} · smoke {acc130['설정'].get('smoke')}")
    check(ok130, "13-0 계정사전이 관문 통과 본 실행 산출이 아닙니다.")
    gates["G0_입력사슬"] = {"항목": chain, "13-0_관문통과": True, "통과": True}

    # ── [1/7] 함수 동일성 ────────────────────────────────────
    line("[1/7] 함수 동일성(G0): 13-0·01과 docstring 뺀 AST 비교 · BotSim 지연 규칙")
    fn_rows, code_hash = gate_function_identity()
    delay_gate = gate_delay_constants()
    funcwords = json.load(open(FUNCWORDS_JSON, encoding="utf-8"))["기능어"]
    funcwords = sorted({normalize_apostrophe(w) for w in funcwords})
    funcword_set = set(funcwords)
    fw_hash = sha16("\n".join(funcwords))
    say(f"      기능어 {len(funcwords)}종 · 해시 {fw_hash} (13-0 {EXPECT_FW_HASH})")
    check(fw_hash == EXPECT_FW_HASH and len(funcwords) == 172, "기능어 목록이 13-0과 다릅니다.")
    gates["G0_함수동일성"] = {"행": fn_rows, "측정코드_해시": code_hash, "지연규칙": delay_gate,
                          "기능어_해시": fw_hash, "통과": True}

    # ── [2/7] 분할·대장·호출 기록 ─────────────────────────────
    line("[2/7] 분할·대장·호출 기록 읽기 (결정 D3 · 관문 G8)")
    split = json.load(open(SPLIT_JSON, encoding="utf-8"))["분할"]
    personas = split["페르소나"]
    check(len(personas) == 509, "페르소나가 509가 아닙니다.")
    personas_by_pid.update({p["페르소나id"]: p for p in personas})
    mid = json.load(open(MODELID_JSON, encoding="utf-8"))
    cell_of_model = {m: s for s, m in mid["표"].items()}
    cell_of_model[mid["기준_재생성_모델"]] = BASE
    check(len(cell_of_model) == 5, f"모델ID표의 모델이 다섯이 아닙니다: {cell_of_model}")
    model_of_cell = {c: m for m, c in cell_of_model.items()}
    ledger = [json.loads(l) for l in open(LEDGER_JSONL, encoding="utf-8")]
    prompted = {r["슬롯id"]: r for r in ledger if r["상태"] == "프롬프트 있음"}
    slot_order = [r["슬롯id"] for r in ledger if r["상태"] == "프롬프트 있음"]
    say(f"      페르소나 {len(personas)} · 대장 {len(ledger):,}행 · 프롬프트 있음 {len(prompted):,}")
    roles = split["사람"]["역할표"]
    v1_mimic = sorted(r["uid"] for r in roles if "모방" in r["역할"] and r.get("09-1매칭_ver1학습") is True)
    say(f"      모방 풀 ∩ ver.1 학습 사람 {len(v1_mimic)} (분할.json 수 {split['사람']['수'].get('ver1학습_모방풀안')})")
    check(len(v1_mimic) == EXPECT_106 == split["사람"]["수"].get("ver1학습_모방풀안"), "106명 목록이 맞지 않습니다.")
    v1_set = set(v1_mimic)
    excl_slots = {sid for sid, r in prompted.items() if r["모방저자"] in v1_set}
    keep_106 = set(prompted) - excl_slots
    say(f"      민감도(D7) 대상 슬롯: 모방 저자 ∈ 106명 {len(excl_slots):,}/{len(prompted):,} "
        f"({len(excl_slots) / len(prompted):.1%})")

    assigned = {m: [s for s in slot_order if c == BASE
                    or personas_by_pid[prompted[s]["페르소나id"]]["모델슬롯"] == c]
                for m, c in cell_of_model.items()}
    reports, finals, per_slot_calls, halted_sets = {}, {}, {}, {}
    all_ids_bad = {}
    for cell in CELLS:
        m = model_of_cell[cell]
        path, hash8 = find_run_file(m)
        rows, cut = read_rows(path)
        rep, fin, per_slot, halted = summarize_run(m, cell, path, hash8, rows, assigned[m])
        halted_sets[m] = halted
        rep["잘린마지막줄"] = cut
        aset = set(assigned[m])
        ids_in_rows = {r["슬롯id"] for r in rows if r.get("종류") in ("호출", "슬롯", "슬롯중단")}
        all_ids_bad[m] = sorted(ids_in_rows - aset)
        reports[m], finals[m], per_slot_calls[m] = rep, fin, per_slot
        say(f"      {cell:<13} {m:<32} {os.path.basename(path)} · 줄 {len(rows):,}"
            f"{' (잘린 마지막 줄 버림)' if cut else ''}")
        say(f"         배정 {rep['배정슬롯']:,} · 시도 {rep['시도슬롯']:,} · 미시도 {rep['미시도슬롯']} · 성공 "
            f"{rep['성공']:,} · 결측 {rep['결측']:,} · 차단 {rep['차단']} · 슬롯중단 미완 {rep['슬롯중단_미완']} · "
            f"종료 중복(같은 바이트) {rep['종료기록_중복']}")
        say(f"         결측 사유 {rep['결측사유']}")
        say(f"         length 발생 슬롯 {rep['length발생_슬롯']} · CB 호출 {rep['CB호출']}({rep['CB호출_슬롯']}슬롯) · "
            f"CB 결측 {rep['CB_결측']} · 거절 호출 {rep['거절호출']}({rep['거절호출_슬롯']}슬롯, 결측 {rep['거절_결측슬롯']}) · "
            f"finish_reason {rep['finish_reason분포']}")
        so = rep["성공호출_원형파서실패_몫"]
        say(f"         성공 호출의 원형 파서 {rep['성공호출_원형파서']}"
            f"{'' if so is None else f' → 관용 파서로만 받은 몫 {so:.1%}'}")
        del rows
    gates["G8_기록형식"] = {"통과": True, "내용": "실행시작 모드·설정해시, 종료 상태값, 중복 동일성, 성공 기록 문자열 모두 통과"}
    summary["모델별"] = reports

    # ── [3/7] G3 대장·창 ─────────────────────────────────────
    line("[3/7] G3 완결·대장·창: 슬롯 id ∈ 배정 슬롯, 성공 (게시물 id, 시각) ∈ 창")
    for m, bad in all_ids_bad.items():
        say(f"      {m:<32} 배정 밖 슬롯 id {len(bad)}")
    ids_ok = not any(all_ids_bad.values())
    incomplete = {m: {"미시도": r["미시도슬롯"], "슬롯중단_미완": r["슬롯중단_미완"],
                      "종료기록없음": r["시도슬롯"] - r["종료기록_슬롯수"] - r["슬롯중단_미완"]}
                  for m, r in reports.items()}
    n_incomplete = sum(sum(v.values()) for v in incomplete.values())
    say(f"      완결: 끝나지 않은 슬롯 {n_incomplete} {incomplete if n_incomplete else ''}"
        f"{' (--allow-incomplete로 진행)' if n_incomplete and ARGS.allow_incomplete else ''}")
    gates["G3_완결"] = {"모델별": incomplete, "합": n_incomplete, "허용플래그": ARGS.allow_incomplete,
                      "통과": n_incomplete == 0 or ARGS.allow_incomplete}
    check(gates["G3_완결"]["통과"], "생성이 끝나지 않은 슬롯이 있습니다. 생성을 마치거나 --allow-incomplete를 주십시오.")
    data = json.load(open(POSTS_JSON, encoding="utf-8"))
    labels = {}
    with open(USERS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels[row["user_id"]] = "bot" if (row.get("character_setting") or "").strip() else "human"
    label_marker("창 재구성: 사람 게시물만(Users.csv 라벨, 12 생성 스크립트 build_indexes와 같은 거름)")
    by_sub, times = build_post_index(data, labels)
    succ_by_slot = defaultdict(list)
    for m, fin in finals.items():
        for sid, r in fin.items():
            if r.get("상태") == "성공":
                succ_by_slot[sid].append((m, (r.get("게시물id"), r.get("게시물시각"))))
    g3 = gate_windows(prompted, personas_by_pid, by_sub, times, succ_by_slot)
    g3["배정밖_슬롯id"] = {m: bad[:20] for m, bad in all_ids_bad.items()}
    g3["통과"] = g3["통과"] and ids_ok
    gates["G3_대장창"] = g3
    check(g3["통과"], "G3 실패: 배정 밖 슬롯 id, 창 재구성 불일치, 또는 창 밖 게시물 짝.")

    # 모방 예시 시각 (D8)
    need = {(r["모방저자"], r["모방예시id"]) for r in prompted.values()}
    ex_time = {}
    for (au, cid) in need:
        v = data.get(au) or {}
        for blk in ("comment_1", "comment_2"):
            for c in v.get(blk) or []:
                if c.get("comment_id") == cid:
                    ex_time[(au, cid)] = c.get("created_utc")
    ex_after = {sid: (ex_time.get((r["모방저자"], r["모방예시id"])) or "") >= r["계획일"] + " 00:00:00"
                for sid, r in prompted.items()}
    miss_ex = sum(1 for k in need if k not in ex_time)
    say(f"      모방 예시 시각: 찾음 {len(ex_time):,}/{len(need):,} (못 찾음 {miss_ex}) · 계획일 뒤 예시 슬롯 "
        f"{sum(ex_after.values()):,}")
    summary["모방예시시각"] = {"찾음": len(ex_time), "대상": len(need), "못찾음": miss_ex,
                          "계획일뒤_슬롯": sum(ex_after.values())}

    # 모방 예시 복사 (D15, 뼈대 4절 v3.2.7)
    mimic_rows = [json.loads(l) for l in open(MIMIC_JSONL, encoding="utf-8")]
    ex_text = {r["슬롯id"]: str(r.get("comment_body") or "") for r in mimic_rows}
    check(set(prompted) <= set(ex_text), "모방 예시가 없는 프롬프트 슬롯이 있습니다.")
    t0 = time.time()
    flags = copy_flags(finals, ex_text)
    flags2 = copy_flags(finals, ex_text)
    copy9 = {m: {sid for sid, (b, _) in f.items() if b in ("동일", "≥0.9")} for m, f in flags.items()}
    copy8 = {m: {sid for sid, (b, _) in f.items() if b == "0.8~0.9"} for m, f in flags.items()}
    only_success = all(finals[m].get(sid, {}).get("상태") == "성공" for m, f in flags.items() for sid in f)
    copy_rep = {}
    for m, f in flags.items():
        c = cell_of_model[m]
        lb = {k: Counter() for k in ("복사(동일·≥0.9)", "0.8~0.9", "성공 전체")}
        for sid, (b, _) in f.items():
            eb = ex_len_bin(len(ex_text[sid]))
            lb["성공 전체"][eb] += 1
            if b in ("동일", "≥0.9"):
                lb["복사(동일·≥0.9)"][eb] += 1
            elif b == "0.8~0.9":
                lb["0.8~0.9"][eb] += 1
        n = len(f)
        copy_rep[c] = {"모델": m, "성공슬롯": n, "구간별": {k: sum(1 for b, _ in f.values() if b == k) for k in COPY_BINS},
                       "복사_결측": len(copy9[m]), "복사율": len(copy9[m]) / n if n else None,
                       "0.8이상율": (len(copy9[m]) + len(copy8[m])) / n if n else None,
                       "예시길이구간별": {k: dict(sorted(v.items())) for k, v in lb.items()}}
        say(f"      복사(D15) {c:<13} 성공 {n:,} · 동일 {copy_rep[c]['구간별']['동일']} · ≥0.9 "
            f"{copy_rep[c]['구간별']['≥0.9']} · 0.8~0.9 {copy_rep[c]['구간별']['0.8~0.9']} → 결측 {len(copy9[m])} "
            f"({copy_rep[c]['복사율'] or 0:.2%}) · 예시 길이별 복사 {copy_rep[c]['예시길이구간별']['복사(동일·≥0.9)']}")
    g11 = {"두번계산_같음": flags == flags2, "성공슬롯에만": only_success, "초": round(time.time() - t0, 1)}
    say(f"      G11 복사 표시 두 번 계산 같음 {g11['두번계산_같음']} · 성공 슬롯에만 {only_success} · {g11['초']}초")
    check(g11["두번계산_같음"] and only_success, "G11 실패: 복사 표시가 결정적이지 않거나 성공 슬롯 밖에 붙었습니다.")
    del flags2

    # 성공 슬롯 집합 (D11). 모방 예시 복사는 살지 않은 슬롯이다(D15).
    succ = {m: defaultdict(set) for m in finals}
    succ8 = {m: defaultdict(set) for m in finals}
    rawsucc = {m: defaultdict(set) for m in finals}       # 복사 제외 없음(규칙 이전)
    for m, fin in finals.items():
        for sid, r in fin.items():
            if r.get("상태") == "성공":
                rawsucc[m][prompted[sid]["페르소나id"]].add(sid)
            if r.get("상태") == "성공" and sid not in copy9[m]:
                succ[m][prompted[sid]["페르소나id"]].add(sid)
                if sid not in copy8[m]:
                    succ8[m][prompted[sid]["페르소나id"]].add(sid)
    base_model = model_of_cell[BASE]

    # 기준 칸 문서(D13): 13-0과 같은 원 봇 문서 선택(복사 슬롯 제외) · 완전 모방기
    titles = {}
    for u, blk in data.items():
        for p in (blk.get("posts") or []):
            titles[str(p.get("submission_id"))] = norm_text(p.get("posts"))
    led_by_key = {(r["원봇uid"], r["원댓글id"], r["원댓글시각"]): r for r in ledger}
    A130 = acc130["계정"]
    ob_uids = sorted(u for u, a in A130.items() if a["집단"] == "원봇")
    mim_uids = sorted(u for u, a in A130.items() if a["집단"] == "완전모방기")
    pid_of_ob = {A130[u]["페르소나id"]: u for u in ob_uids}
    ob_items_full, ob_slotset = {}, {}
    n_copy = 0
    for u in ob_uids:
        full = []
        for c in (data[u].get("comment_1") or []):
            r = led_by_key[(u, c["comment_id"], str(c.get("created_utc") or ""))]
            target = c["link_id"].split("_", 1)[1]
            body_n = norm_text(c.get("comment_body"))
            if bool(r["원봇복사슬롯"]) or (bool(body_n) and target in titles and body_n == titles[target]):
                n_copy += 1
                continue
            full.append((str(c.get("comment_body") or ""), str(c.get("created_utc") or ""), r["슬롯id"]))
        ob_items_full[u] = full
        ob_slotset[A130[u]["페르소나id"]] = {sid for t, _, sid in full if clean_doc(t)[0] is not None}
    del data
    say(f"      원 봇 문서(13-0 선택 규칙): 계정 {len(ob_uids)} · 복사 제외 {n_copy} · 문서 "
        f"{sum(len(v) for v in ob_items_full.values()):,}")

    # ── [4/7] 문서 만들기 ─────────────────────────────────────
    line("[4/7] 문서 만들기: 시각 = 게시물 시각 + BotSim 지연(D2) → 13-0 select_group")
    accs, meta, delays = build_accounts(finals, cell_of_model, personas, prompted, slot_order, copy9)
    accs2, _, _ = build_accounts(finals, cell_of_model, personas, prompted, slot_order, copy9)
    accs_nocopy, _, _ = build_accounts(finals, cell_of_model, personas, prompted, slot_order, None)
    say(f"      지연 구간 분포(복사 뺀 성공 문서) {dict(delays)}")
    say("      파싱 목록 = 복사 제외 없음 계정의 문서(규칙 이전). 주 판·복사 민감도는 같은 파싱에서 문서만 골라 만든다.")
    work, cell_of_uid, funnels, funnels_nc = {}, {}, {}, {}
    work_main, work_nc = {}, {}
    for cell in CELLS:
        t0 = time.time()
        w, fn = select_group(accs[cell])
        w2, _ = select_group(accs2[cell])
        check(corpus_hash_of(w) == corpus_hash_of(w2), f"G2: {cell} 문서 만들기가 결정적이지 않습니다.")
        funnels[cell] = fn
        w_nc, fn_nc = select_group(accs_nocopy[cell])
        funnels_nc[cell] = fn_nc
        check(fn_nc["상한초과_절삭문서수"] == 0 and fn["상한초과_절삭문서수"] == 0,
              f"{cell}: 200건 상한 절삭이 있어 주 판을 복사 제외 없음 파싱에서 골라낼 수 없습니다.")
        work_main.update(w)
        work_nc.update(w_nc)
        for u in set(w) | set(w_nc):
            cell_of_uid[u] = cell
            work[u] = w_nc[u] if u in w_nc else w[u]
        copy_rep[cell]["적격계정_규칙적용"] = len(w)
        copy_rep[cell]["적격계정_규칙끔"] = len(w_nc)
        copy_rep[cell]["규칙으로_탈락한계정"] = sorted(set(w_nc) - set(w))[:30]
        copy_rep[cell]["규칙으로_탈락한계정수"] = len(set(w_nc) - set(w))
        say(f"      {cell:<13} 적격 계정: 복사 규칙 적용 {len(w)} · 규칙 끔 {len(w_nc)} → 규칙으로 탈락 "
            f"{len(set(w_nc) - set(w))}")
        say(f"      {cell:<13} 대상 {fn['대상계정수']:>4} · 원본문서 {fn['원본문서수']:>6,} · 문서탈락 "
            f"{fn['문서탈락_합']:>5,} {fn['문서탈락_사유별']} · 절삭 {fn['상한초과_절삭문서수']} · "
            f"문서부족 탈락 {fn['문서부족_탈락계정수']} · 비영어 탈락 {fn['비영어_탈락계정수']} → "
            f"적격 {fn['적격계정수']}계정 · {fn['적격문서수']:,}문서 ({time.time() - t0:.1f}초)")

    summary["복사"] = {"규칙": IMPL_DECISIONS["D15_모방예시복사"], "칸별": copy_rep, "변형_이름표": VARIANT_LABEL,
                     "규칙이전_깔때기": funnels_nc}

    # G9 uid 서로소
    gen_uids = {u for c in CELLS for u in accs[c]}
    clash = sorted(gen_uids & set(A130))
    gates["G9_uid서로소"] = {"생성칸_uid": len(gen_uids), "13-0_uid": len(A130), "겹침": clash[:20],
                          "통과": not clash}
    say(f"      G9 생성 칸 uid {len(gen_uids):,} ∩ 13-0 uid {len(A130):,} = {len(clash)}")
    check(not clash, f"G9 실패: 생성 칸 uid가 13-0 사전 uid와 겹칩니다 {clash[:5]}")

    # 기준 칸 (D13). 문서 키는 슬롯id(변형용), 버킷은 13-0과 같은 이름(bucket_of)
    ref_items = {"원봇짝": {}, "모방106": {}}
    ref_full_same = {"원봇짝": {}, "모방106": {}}
    base_pid_succ = rawsucc[base_model]         # 파싱 목록은 규칙 이전 성공 슬롯, 주 판은 변형으로
    for u in ob_uids:
        pid = A130[u]["페르소나id"]
        keep = [(t, ts, sid) for t, ts, sid in ob_items_full[u] if sid in base_pid_succ.get(pid, ())]
        ref_items["원봇짝"]["원봇짝:" + u] = keep
        ref_full_same["원봇짝"]["원봇짝:" + u] = len(keep) == len(ob_items_full[u])
    mim_by_uid = defaultdict(list)
    for r in mimic_rows:
        mim_by_uid[r["uid"]].append(r)
    for u in mim_uids:
        keep = [(str(r.get("comment_body") or ""), r["계획일"], r["슬롯id"]) for r in mim_by_uid[u]
                if r["슬롯id"] not in excl_slots]
        ref_items["모방106"]["모방106:" + u] = keep
        ref_full_same["모방106"]["모방106:" + u] = len(keep) == len(mim_by_uid[u])
    g11["모방106_규칙무관"] = True      # 모방106 문서 목록은 copy9·copy8을 읽지 않는다(아래 해시 대조)
    mim106_hash = sha16(json.dumps(ref_items["모방106"], ensure_ascii=False, sort_keys=True))
    for rc in REF_CELLS:
        w, fn = select_group(ref_items[rc])
        funnels[rc] = fn
        for u in w:
            cell_of_uid[u] = rc
        work.update(w)
        say(f"      기준 칸 {rc:<7} 대상 {fn['대상계정수']:>4} · 원본문서 {fn['원본문서수']:>6,} · 문서탈락 "
            f"{fn['문서탈락_합']:>5,} · 문서부족 탈락 {fn['문서부족_탈락계정수']} · 비영어 탈락 "
            f"{fn['비영어_탈락계정수']} → 적격 {fn['적격계정수']}계정 · {fn['적격문서수']:,}문서")

    # G5 수 맞추기
    g5 = {}
    for cell in CELLS:
        m = model_of_cell[cell]
        n_succ = reports[m]["성공"] - len(copy9[m])
        n_in = funnels[cell]["원본문서수"]
        succ_pid = Counter(prompted[s]["페르소나id"] for s, r in finals[m].items()
                           if r.get("상태") == "성공" and s not in copy9[m])
        per_acc_ok = all(len(accs[cell][uid]) == succ_pid.get(meta[uid][2]["페르소나id"], 0)
                         for uid in accs[cell])
        g5[cell] = {"성공슬롯": n_succ, "정제전문서": n_in, "계정별_일치": per_acc_ok,
                    "같음": n_succ == n_in and per_acc_ok}
        say(f"      G5 {cell:<13} 성공 슬롯 − 복사 {n_succ:,} = 정제 전 문서 {n_in:,} · 계정별 일치 {per_acc_ok}  "
            f"{'같음' if g5[cell]['같음'] else '다름'}")
    gates["G5_수맞추기"] = {"칸별": g5, "통과": all(v["같음"] for v in g5.values())}
    check(gates["G5_수맞추기"]["통과"], "G5 실패: 성공 슬롯 수와 문서 수가 다릅니다.")

    # G4 길이 (생성 칸)
    short = [u for u, items in work.items() for t, _ in items if len(t) < MIN_CHARS]
    dropped = sum(funnels[c]["문서탈락_합"] for c in CELLS)
    kept_elig = sum(len(v) for v in work_main.values())
    n_input = sum(funnels[c]["원본문서수"] for c in CELLS)
    lost_short_acc = sum(sum(x["정제후문서수"] for x in funnels[c]["문서부족_탈락계정"]) for c in CELLS)
    reason_ok = all(all(k for k in funnels[c]["문서탈락_사유별"]) for c in CELLS)
    nonen_clean = 0
    for c in CELLS:
        for x in funnels[c]["비영어_탈락계정"]:
            nonen_clean += sum(1 for t, _, _ in accs[c][x["uid"]] if clean_doc(t)[0] is not None)
    trimmed = sum(funnels[c]["상한초과_절삭문서수"] for c in CELLS)
    balance_ok = kept_elig + lost_short_acc + nonen_clean + trimmed + dropped == n_input
    g4 = {"남은문서_20자미만": len(short), "탈락문서": dropped, "탈락사유_모두있음": reason_ok,
          "입력": n_input, "적격계정문서": kept_elig, "문서부족계정의_정제후문서": lost_short_acc,
          "비영어계정의_정제후문서": nonen_clean, "상한절삭": trimmed, "합_일치": balance_ok,
          "통과": not short and reason_ok and balance_ok}
    say(f"      G4 남은 문서 중 20자 미만 {len(short)} · 탈락 {dropped:,}(사유 있음 {reason_ok}) · "
        f"적격 {kept_elig:,} + 문서부족 계정 {lost_short_acc:,} + 비영어 계정 {nonen_clean:,} + 탈락 {dropped:,} "
        f"= 입력 {n_input:,}  {'같음' if balance_ok else '다름'}")
    gates["G4_길이"] = g4
    check(g4["통과"], "G4 실패: 20자 미만 문서가 남았거나 수가 맞지 않습니다.")

    # G12 주 판 골라내기 정합: 파싱 목록에서 복사 슬롯을 뺀 목록 = 주 판 select_group 목록
    g12_bad = []
    for u, items in work.items():
        if cell_of_uid[u] not in CELLS:
            continue
        cell, m, p = meta[u][0], model_of_cell[meta[u][0]], meta[u][2]
        derived = [(t, sid) for t, sid in items if sid in succ[m].get(p["페르소나id"], ())]
        if u in work_main and derived != work_main[u]:
            g12_bad.append(u)
    gates["G12_주판골라내기"] = {"대상": sum(1 for u in work if cell_of_uid[u] in CELLS), "불일치": g12_bad[:20],
                            "주판만_적격(규칙 이전 부적격)": sorted(set(work_main) - set(work_nc))[:20],
                            "통과": not g12_bad}
    say(f"      G12 파싱 목록 − 복사 슬롯 = 주 판 목록: 불일치 {len(g12_bad)} · 주 판만 적격 "
        f"{len(set(work_main) - set(work_nc))}")
    check(not g12_bad, "G12 실패: 주 판 목록을 파싱 목록에서 골라낼 수 없습니다.")

    # 정제 보고 (D12) · langid 경계 (D14)
    wrap_rep, strip_cells = {}, []
    for c in CELLS:
        docs_c = [t for u, v in work_main.items() if cell_of_uid[u] == c for t, _ in v]
        q = sum(1 for t in docs_c if len(t.strip()) >= 2 and any(t.strip().startswith(a) and t.strip().endswith(b)
                                                                 for a, b in QUOTE_PAIRS))
        pfx = sum(1 for t in docs_c if WRAP_PREFIX.match(t.strip()))
        either = sum(1 for t in docs_c if wrapped(t))
        frac = either / len(docs_c) if docs_c else 0.0
        wrap_rep[c] = {"문서": len(docs_c), "따옴표감싸기": q, "이름표접두": pfx, "둘중하나": either,
                       "비율": frac, "정제민감도_만듦": frac > WRAP_MAX_FRAC,
                       "예": [t[:80] for t in docs_c if wrapped(t)][:5]}
        if frac > WRAP_MAX_FRAC:
            strip_cells.append(c)
        say(f"      정제 보고 {c:<13} 문서 {len(docs_c):,} · 따옴표 감싸기 {q} · 이름표 접두 {pfx} · "
            f"비율 {frac:.2%}{' → 정제 민감도 계정 만듦' if frac > WRAP_MAX_FRAC else ''}")
    summary["정제보고"] = {"규칙": IMPL_DECISIONS["D12_정제보고"], "칸별": wrap_rep, "민감도칸": strip_cells}
    lm = langid_margins({**work_main, **{u: v for u, v in work.items() if cell_of_uid[u] in REF_CELLS}},
                        cell_of_uid, CELLS + REF_CELLS)
    summary["langid경계"] = {"규칙": IMPL_DECISIONS["D14_langid경계"], "칸별": lm}
    say("      langid 경계(1위 − 2위 < 0.05) " + " · ".join(f"{c} {v['경계_계정수']}/{v['계정수']}" for c, v in lm.items()))

    # 변형 명세 (D7·D11·D12)
    def variants_of(uid):
        """변형 명세. 파싱 목록은 복사 제외 없음 계정(규칙 이전)이다. 이름 규칙은 VARIANT_KEYS."""
        c = cell_of_uid[uid]
        if c == "모방106":
            return []
        if c == "원봇짝":
            pid = A130[uid.split(":", 1)[1]]["페르소나id"]
            return [("원봇_재생성성공슬롯", succ[base_model].get(pid, set()), False),
                    ("원봇_재생성성공슬롯_복사민감도", succ8[base_model].get(pid, set()), False),
                    ("원봇_재생성성공슬롯_복사제외없음", None, False)]
        pid = meta[uid][2]["페르소나id"]
        m = model_of_cell[c]
        own, own8, ownr = (x[m].get(pid, set()) for x in (succ, succ8, rawsucc))
        bs, bs8, bsr = (x[base_model].get(pid, set()) for x in (succ, succ8, rawsucc))
        v = [("주", own, False), ("복사제외없음", None, False), ("복사민감도", own8, False),
             ("민감도_106제외", keep_106 & own, False)]
        if c == BASE:
            om = model_of_cell[personas_by_pid[pid]["모델슬롯"]]
            v += [("짝_재생성쪽", own & succ[om].get(pid, set()), False),
                  ("짝_재생성쪽_복사민감도", own8 & succ8[om].get(pid, set()), False),
                  ("짝_재생성쪽_복사제외없음", ownr & rawsucc[om].get(pid, set()), False)]
            if pid in pid_of_ob:
                v += [("짝_P12-0_재생성쪽", own & ob_slotset[pid], False),
                      ("짝_P12-0_재생성쪽_복사민감도", own8 & ob_slotset[pid], False),
                      ("짝_P12-0_재생성쪽_복사제외없음", ownr & ob_slotset[pid], False)]
        else:
            v += [("짝_새모델쪽", own & bs, False), ("짝_새모델쪽_복사민감도", own8 & bs8, False),
                  ("짝_새모델쪽_복사제외없음", ownr & bsr, False)]
        if c in strip_cells:
            v.append(("정제민감도", own, True))
        return v

    def bucket_of(uid):
        return REF_BUCKET.get(cell_of_uid[uid], BUCKET)

    # 대상 순서 (smoke면 칸마다 앞 3계정)
    order = []
    for cell in CELLS + REF_CELLS:
        us = sorted(u for u in work if cell_of_uid[u] == cell)
        order += us[:SMOKE_N] if SMOKE else us
    if SMOKE:
        work = {u: work[u] for u in order}
        say(f"      smoke: 칸마다 {SMOKE_N}계정 → {len(order)}계정 · {sum(len(v) for v in work.values()):,}문서")
    n_docs = sum(len(work[u]) for u in order)
    corpus_hash = corpus_hash_of({u: work[u] for u in order})
    var_hash = sha16(json.dumps({u: [(n, sorted(k & {sid for _, sid in work[u]}) if k is not None else None, s)
                                     for n, k, s in variants_of(u)] for u in order},
                                ensure_ascii=False, sort_keys=True))
    exp = {"문서수": n_docs, "하한_분": round(n_docs * MS_LOW / 60000, 1),
           "상한_분": round(n_docs * MS_HIGH / 60000, 1),
           "기준": f"{MS_LOW}~{MS_HIGH} ms/문서(13-0 원봇·완전모방기 실측)",
           "칸별_문서": {c: sum(len(work[u]) for u in order if cell_of_uid[u] == c) for c in CELLS + REF_CELLS}}
    summary["예상소요"] = exp
    summary["칸별_깔때기"] = funnels
    summary["민감도_대상슬롯"] = {"106명_해시": sha16("\n".join(v1_mimic)), "슬롯수": len(excl_slots)}
    say(f"      파싱 대상 {len(order):,}계정 · {n_docs:,}문서(기준 칸 "
        f"{sum(exp['칸별_문서'][c] for c in REF_CELLS):,}) · 예상 {exp['하한_분']}~{exp['상한_분']}분 · "
        f"코퍼스 해시 {corpus_hash} · 변형 해시 {var_hash}")
    dump_summary("문서 만들기 끝, 파이프라인 준비")

    # ── [5/7] 파이프라인 · 13-0 정합 · 손 대조 · 결정성 ───────────
    line("[5/7] 파이프라인: stanza tokenize,pos · use_gpu=False · 계정 단위 bulk_process")
    import stanza
    import torch
    torch.manual_seed(SEED)
    t0 = time.time()
    nlp = stanza.Pipeline(lang="en", processors="tokenize,pos", verbose=False,
                          use_gpu=False, download_method=None)
    model_paths = {name: proc.config.get("model_path") for name, proc in nlp.processors.items()}
    ref_pipe = acc130["설정"]["파이프라인"]
    same_models = model_paths == ref_pipe["모델경로"] and stanza.__version__ == ref_pipe["stanza"]
    say(f"      생성 {time.time() - t0:.1f}초 · stanza {stanza.__version__} · torch {torch.__version__} · "
        f"스레드 {torch.get_num_threads()} · 모델 경로·버전 = 13-0 {'같음' if same_models else '다름'}")
    check(same_models, "stanza 모델·버전이 13-0과 다릅니다.")
    pipe_info = {"stanza": stanza.__version__, "torch": torch.__version__,
                 "스레드": torch.get_num_threads(), "모델경로": model_paths,
                 "호출": 'stanza.Pipeline(lang="en", processors="tokenize,pos", verbose=False, '
                         'use_gpu=False, download_method=None) · 계정 단위 bulk_process'}
    summary["파이프라인"] = pipe_info

    line("[5/7] G6 13-0 정합: 13-0 완전 모방기 계정 하나를 이 파일의 측정 경로로")
    g6 = gate_13_0(nlp, funcword_set, acc130, mimic_rows)
    g6["파이프라인_같음"] = same_models
    gates["G6_13-0정합"] = g6
    del mimic_rows

    line("[5/7] G1 손 대조: 칸마다 2계정, 문서 단독 파싱 + 독립 집계 = bulk")
    hand_rows, hand_expect = gate_hand(nlp, funcword_set, {u: v for u, v in work.items() if cell_of_uid[u] in CELLS},
                                       cell_of_uid)
    gates["G1_손대조"] = {"행": hand_rows, "계정": sorted(hand_expect), "통과": True}

    line("[5/7] G2 결정성: 부분집합을 두 번 파싱(변형 포함)")
    gen_order = [u for u in order if cell_of_uid[u] in CELLS]
    det_uids = gen_order[-DET_ACCOUNTS:] if SMOKE else random.Random(SEED + 1).sample(sorted(gen_order), DET_ACCOUNTS)
    det_rows = []
    for uid in det_uids:
        a1 = measure_one(nlp, funcword_set, work[uid], variants_of(uid), bucket_of(uid))
        a2 = measure_one(nlp, funcword_set, work[uid], variants_of(uid), bucket_of(uid))
        same = a1 == a2
        det_rows.append({"계정": uid, "같음": same})
        say(f"      {uid:<16} 두 번 파싱 집계·문서별·변형 {'같음' if same else '다름'}")
        check(same, f"G2 결정성 실패: {uid}")
    gates["G2_결정성"] = {"문서만들기_두번": True, "부분집합": det_rows, "통과": True}
    dump_summary("관문 G0~G9 통과, 파싱 중")

    # ── [6/7] 파싱 ──────────────────────────────────────────
    line(f"[6/7] 파싱: {CHECKPOINT_EVERY}계정마다 중간 저장, 재개 가능")
    fp = {"기능어_해시": fw_hash, "측정코드_해시": code_hash, "stanza": stanza.__version__,
          "계정수": len(order), "문서수": n_docs, "코퍼스_해시": corpus_hash, "변형_해시": var_hash,
          "106명_해시": sha16("\n".join(v1_mimic))}
    say(f"      지문 {fp}")
    done, run_sec, total_sec, per_cell = run_measurement(nlp, work, order, funcword_set, fp,
                                                          variants_of, bucket_of, cell_of_uid)

    # ── [7/7] 사후 관문 · 저장 ────────────────────────────────
    line("[7/7] 사후 관문: G7 내부 관계 · G1 결정성 · G10 기준 칸 정합 · 저장")
    rel_bad = [u for u in order if not relations_ok(done[u]["집계"])
               or any(v.get("집계") is not None and not relations_ok(v["집계"]) for v in done[u]["변형"].values())]
    gates["G7_내부관계"] = {"대상": len(order), "위반계정수": len(rel_bad), "위반": rel_bad[:50],
                        "통과": not rel_bad}
    say(f"      G7 내부 관계 위반(변형 포함) {len(rel_bad)}/{len(order)}")
    det_bad = [u for u in hand_expect if done[u]["집계"] != hand_expect[u]]
    gates["G1_손대조"]["본측정_결정성_불일치"] = det_bad
    gates["G1_손대조"]["통과"] = not det_bad
    say(f"      G1 손 대조 계정의 본 측정 = 관문 때 값: 불일치 {len(det_bad)}/{len(hand_expect)}")
    g10 = {}
    fields = ["문서수", "문장수", "토큰수", "토큰수_구두점제외", "구두점토큰수", "문장길이", "기능어",
              "UPOS", "자질", "버킷별"]
    for rc in REF_CELLS:
        n_cmp, bad = 0, []
        for u in order:
            if cell_of_uid[u] != rc or not ref_full_same[rc].get(u):
                continue
            base_uid = u.split(":", 1)[1]
            n_cmp += 1
            if any(done[u]["집계"][f] != A130[base_uid][f] for f in fields):
                bad.append(base_uid)
        g10[rc] = {"대조계정": n_cmp, "불일치": bad[:20], "통과": not bad}
        say(f"      G10 {rc:<7} 빠진 문서 없는 계정 {n_cmp}개 = 13-0 사전(모든 필드): 불일치 {len(bad)}")
    gates["G10_기준칸정합"] = {"칸별": g10, "통과": all(v["통과"] for v in g10.values())}
    sha130_end = file_sha256(ACC130_JSON)
    mim106_nocopy = {}
    for u in mim_uids:
        mim106_nocopy["모방106:" + u] = [(str(r.get("comment_body") or ""), r["계획일"], r["슬롯id"])
                                        for r in mim_by_uid[u] if r["슬롯id"] not in excl_slots]
    g11.update({"13-0_sha256_시작=끝=동결": sha130_start == sha130_end == gates["G0_입력사슬"]["항목"]["13-0_계정사전.json"]["동결"],
                "모방106_규칙끈판과_해시같음": mim106_hash == sha16(json.dumps(mim106_nocopy, ensure_ascii=False,
                                                                             sort_keys=True))})
    g11["통과"] = all(v for k, v in g11.items() if k != "초")
    gates["G11_복사규칙"] = g11
    say(f"      G11 13-0 사전 sha256 시작 = 끝 = 동결 {g11['13-0_sha256_시작=끝=동결']} · 모방106 규칙 끈 판과 같음 "
        f"{g11['모방106_규칙끈판과_해시같음']}")

    out_acc = {}
    variants_out = {k: {} for k in VARIANT_KEYS}
    var_drop = {k: {} for k in VARIANT_KEYS + ["주", "주판부적격_변형생략"] + REF_VARIANTS}
    ref_out = {rc: {} for rc in REF_CELLS}
    ref_var_out = {k: {} for k in REF_VARIANTS}
    docs_out = {}
    g12_after = []

    def put(dst, drop, name, key, v, head, full):
        if v["상태"] == "재집계":
            dst[key] = {**head, **v["집계"], **{k: v[k] for k in ("뺀문서수", "바뀐문서수", "벗긴뒤_탈락") if k in v}}
        elif v["상태"].startswith("같음"):
            dst[key] = {**head, **full, "뺀문서수": 0}
        else:
            drop[name][key] = v["사유"]
    for u in order:
        c = cell_of_uid[u]
        if c in REF_CELLS:
            base_uid = u.split(":", 1)[1]
            b = A130[base_uid]
            head = {"집단": b["집단"], "칸": c, "라벨": "bot", "페르소나id": b["페르소나id"],
                    "원봇uid": base_uid[4:] if base_uid.startswith("MIM_") else base_uid, "쪽": b["쪽"],
                    "모델슬롯": b["모델슬롯"], "주제": personas_by_pid[b["페르소나id"]]["주제"], "봉인": False}
            if c == "모방106":
                ref_out[c][base_uid] = {**head, **done[u]["집계"]}
            for name, v in done[u]["변형"].items():
                put(ref_var_out[name], var_drop, name, base_uid, v, head, done[u]["집계"])
            continue
        cell, model, p = meta[u]
        head = {"집단": "재생성" if cell == BASE else "새모델", "칸": cell, "생성모델": model,
                "라벨": "bot", "페르소나id": p["페르소나id"], "원봇uid": p["원봇uid"], "쪽": p["쪽"],
                "모델슬롯": p["모델슬롯"], "주제": p["주제"], "봉인": False}
        var = done[u]["변형"]
        main_ok = var["주"]["상태"] != "제외"
        if main_ok != (u in work_main):
            g12_after.append(u)
        if u in work_main:
            tmp = {}
            put(tmp, var_drop, "주", u, var["주"], head, done[u]["집계"])
            if u in tmp:
                out_acc[u] = tmp[u]
        for name, v in var.items():
            if name == "주":
                continue
            need = work_nc if name.endswith("복사제외없음") else work_main
            if u not in need:
                var_drop["주판부적격_변형생략"][f"{name}|{u}"] = "기준 계정(주 판 또는 규칙 이전) 부적격"
                continue
            put(variants_out[name], var_drop, name, u, v, head, done[u]["집계"])
        own = succ[model_of_cell[cell]].get(p["페르소나id"], set())
        ts_map = {sid: ts for _, ts, sid in accs_nocopy[cell][u]}
        if u in work_main:
            docs_out[u] = [[d[0], ts_map.get(d[0])] + d[2:] for d in done[u]["문서별"] if d[0] in own]
    gates["G12_주판골라내기"]["파싱뒤_주판적격_일치"] = not g12_after
    gates["G12_주판골라내기"]["파싱뒤_불일치"] = g12_after[:20]
    gates["G12_주판골라내기"]["통과"] = gates["G12_주판골라내기"]["통과"] and not g12_after
    say(f"      G12 파싱 뒤 주 판 적격 = select_group 적격: 불일치 {len(g12_after)}")
    passed = all(v.get("통과") for v in gates.values())
    in_doc_pairs = {(u, sid) for u, v in work_main.items() for _, sid in v}
    slot_cols = ["슬롯id", "상태", "사유", "화면", "length발생", "호출수", "CB호출", "거절호출",
                 "댓글글자수", "예시_계획일뒤", "민감도_제외슬롯", "복사", "복사구간", "복사비율",
                 "모방예시글자수", "문서포함"]
    slots_out = {}
    for m, fin in finals.items():
        rows = []
        for sid in assigned[m]:
            r = fin.get(sid)
            c = per_slot_calls[m].get(sid, Counter())
            fl = flags[m].get(sid)
            if r is not None:
                state, why = r.get("상태"), r.get("사유")
                if sid in copy9[m]:
                    state, why = "결측", "모방 예시 복사(동일 또는 비율 ≥ 0.9)"
            elif sid in halted_sets[m]:
                state, why = "슬롯중단_미완", None
            else:
                state, why = ("미시도" if not c else "미완(종료 기록 없음)"), None
            uid = UID_PREFIX[cell_of_model[m]] + personas_by_pid[prompted[sid]["페르소나id"]]["원봇uid"]
            rows.append([sid, state, why, (r or {}).get("화면"), bool((r or {}).get("length발생")),
                         (r or {}).get("호출수"), c["판정:Continue browsing"], c["판정:거절"],
                         len(str((r or {}).get("댓글") or "")) if (r or {}).get("상태") == "성공" else None,
                         ex_after[sid], sid in excl_slots, sid in copy9[m], fl[0] if fl else None,
                         fl[1] if fl else None, len(ex_text[sid]), (uid, sid) in in_doc_pairs])
        slots_out[m] = {"열": slot_cols, "행": rows}
    say("      [라벨 사용] 생성 계정 라벨 'bot'을 결과 파일에 저장만 합니다(생성물 정의).")
    allc = CELLS + REF_CELLS
    agg_of = {**out_acc, **{u: done[u]["집계"] for u in order if cell_of_uid[u] in REF_CELLS}}
    grp = {c: {"계정수(주 판)": sum(1 for u in agg_of if cell_of_uid[u] == c),
               "문서수": sum(agg_of[u]["문서수"] for u in agg_of if cell_of_uid[u] == c),
               "문장수": sum(agg_of[u]["문장수"] for u in agg_of if cell_of_uid[u] == c),
               "토큰수_구두점제외": sum(agg_of[u]["토큰수_구두점제외"] for u in agg_of if cell_of_uid[u] == c),
               "파싱계정수": sum(1 for u in order if cell_of_uid[u] == c)}
           for c in allc}
    for c in CELLS:
        grp[c]["변형_계정수"] = {k: sum(1 for u in variants_out[k] if cell_of_uid[u] == c) for k in VARIANT_KEYS}
    rate = {c: {"문서수(이번 실행)": per_cell.get(c, [0, 0.0])[0],
                "초": round(per_cell.get(c, [0, 0.0])[1], 1),
                "ms_per_문서": (round(per_cell[c][1] / per_cell[c][0] * 1000, 2)
                               if per_cell.get(c) and per_cell[c][0] else None)}
            for c in allc}
    rate["기준칸_추가초"] = round(sum(per_cell.get(c, [0, 0.0])[1] for c in REF_CELLS), 1)
    wall = time.time() - t_start
    setting = {
        "실행": run_info, "smoke": SMOKE, "시험입력": TEST_INPUT, "관문통과": passed,
        "사전선언": "12_OpenRouter생성_사전선언_뼈대.md v3.2 5절 1항·9항 민감도, 4절 정제·주 분석 표본",
        "파이프라인": pipe_info, "시드": SEED, "모델ID표": mid, "칸": CELLS, "기준칸": REF_CELLS,
        "uid접두": UID_PREFIX,
        "정제규칙": {"MIN_CHARS": MIN_CHARS, "MIN_DOCS": MIN_DOCS, "MAX_DOCS": MAX_DOCS,
                 "LANG_TARGET": LANG_TARGET, "출처": "01 clean_doc(= 13-0), 13-0 select_group 순서"},
        "시각규칙": {"출처": rel(AGENT_PY) + " comment_time_function", "구간": DELAY_INTERVALS,
                 "가중치": DELAY_WEIGHTS, "시드": "random.Random(int(sha256('20260926|슬롯id|지연')[:16], 16))",
                 "분포": dict(delays)},
        "민감도_106명": v1_mimic, "정제보고": summary["정제보고"], "langid경계": summary["langid경계"],
        "복사": summary["복사"], "변형_이름표": VARIANT_LABEL,
        "라벨": "생성 계정 bot(생성물). Users.csv 라벨은 창 재구성에만.",
        "구현결정": IMPL_DECISIONS, "모델별": reports, "칸별_깔때기": funnels, "관문": gates,
        "칸별_합계": grp, "속도": rate,
        "소요": {"파싱_이번실행초": run_sec, "파싱_누적초": total_sec, "전체_이번실행초": wall},
        "입력": gates["G0_입력사슬"]["항목"],
    }
    write_json(OUT_JSON, {"설정": setting, "계정": out_acc, **variants_out, **ref_var_out,
                          "완전모방기_106제외": ref_out["모방106"],
                          "변형_탈락": var_drop,
                          "문서별": {"열": ["슬롯id", "시각", "정제글자수", "문장수", "토큰수_구두점제외",
                                           "Tense_Past", "Tense_합"], "계정": docs_out},
                          "슬롯": slots_out})
    out_sha = file_sha256(OUT_JSON)
    say(f"      저장 {OUT_JSON} ({os.path.getsize(OUT_JSON) / 1e6:.1f} MB) sha256 {out_sha[:16]}…")
    if os.path.exists(PROGRESS_JSON):
        os.remove(PROGRESS_JSON)
        say("      중간 저장 파일을 지웠습니다.")
    summary.update({"산출": {"계정사전": OUT_JSON, "sha256": out_sha,
                           "MB": round(os.path.getsize(OUT_JSON) / 1e6, 2), "로그": LOG_PATH},
                    "칸별_합계": grp, "속도": rate, "소요": setting["소요"], "관문통과": passed,
                    "구현결정": IMPL_DECISIONS})
    dump_summary("완료" if passed else "완료(관문 실패)")
    for c in allc:
        s_ = grp[c]
        say(f"      {c:<13} {s_['계정수(주 판)']:>4}계정 · {s_['문서수']:>6,}문서 · 문장 {s_['문장수']:>7,} · "
            f"{rate[c]['ms_per_문서']} ms/문서 · {rate[c]['초']}초")
    say(f"      기준 칸 추가 파싱 {fmt_dur(rate['기준칸_추가초'])}")
    line("끝")
    say(f"      관문 {'모두 통과' if passed else '실패 있음'} · 전체 {fmt_dur(wall)}")
    if not passed:
        say("■ 관문 실패: 12-2는 이 파일을 쓰면 안 됩니다(설정.관문통과=false).")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except GateError as e:
        say(f"\n■ 중단(관문): {e}")
        sys.exit(1)

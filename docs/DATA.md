# 데이터 설명

## 1. BotSim

- 원자료: `research/1. 원본데이터/2. BotSim Data/BotSim-24-Dataset/`
- `user_post_comment.json`: 계정별 제목·1차 댓글·2차 댓글 원문 및 시각·게시판 정보.
- `Users.csv`: 원 연구에서 제공한 계정 정보. 원 제공 문서에 따라 사람·봇 라벨을 읽는다.
- 출처: [QQQQQQBY/BotSim](https://github.com/QQQQQQBY/BotSim), 로컬 원본 커밋 `5c3558f4c8d63605b0400d0beb1f71c6c497e73e`.
- 연구 적격 표본: **봇 646 + 사람 1,223 = 1,869계정**. 문서 110,057개.
- 분량 매칭: 봇 512 + 사람 512. 댓글 한정: 봇 562 + 사람 874. politics 한정: 봇 290 + 사람 705.
- 계정 ID는 문자열로 취급한다. 라벨·계정명·프로필을 FMR 판별 자질에 넣지 않는다.

## 2. fox8

- 원자료: `research/1. 원본데이터/3. fox8 Data/fox8_23_dataset.ndjson.gz`
- 분석용 원문 DB: 같은 폴더의 `fox8_23_dataset.sqlite`.
- 출처: [fox8 원 연구 저장소](https://github.com/osome-iu/AIBot_fox8), 로컬 원본 커밋 `4f6bf49acbb3789f475969b99e64cf1f759aff17`; [Zenodo 원자료](https://doi.org/10.5281/zenodo.8035289).
- 적격 표본: 봇 1,094 + 사람 897 = 1,991계정, 문서 165,532개.
- SQLite의 `users`: `user_id, label, dataset, tweet_count`.
- SQLite의 `tweets`: 글 ID·계정 ID·라벨·시각·원문·RT/인용/답글 여부·참여 및 표기 메타데이터. FMR 측정에 쓰는 것은 정제한 글이다.
- 자기폭로 문구가 확인된 계정을 제외한 엄격 표본은 봇 117개이다. 최종 JSON에서 별도 결과로 구분한다.

NDJSON.gz부터 SQLite를 다시 만들 수 있다. 아래 명령은 새 파일만 만들며 기존 DB를 덮어쓰지 않는다.

```bash
.venv/bin/python scripts/import_fox8.py \
  "$PWD/work/research/1. 원본데이터/3. fox8 Data/fox8_23_dataset.ndjson.gz" \
  "$PWD/work/rebuilt_fox8.sqlite"
```

원자료에 같은 사람 계정 ID가 서로 다른 출처에서 등장할 수 있다. 제공 DB는 글을 입력 순서대로 모두 보존하고, `users`에는 해당 ID의 글 수를 합산하고 마지막 출처를 기록한다. 가져오기 코드도 이 규칙을 재현한다. RT 판정은 `retweeted_status` 또는 `RT @` 접두사다.

## 3. OpenRouter — 새 생성 없이 전달된 자료 사용

- `home/DM_LAB_data/12_OpenRouter/호출기록_*.jsonl`: 모델별 기존 응답·슬롯 기록. 생성 댓글 원문은 `종류=슬롯` 행의 `댓글` 및 개별 호출의 `본문`에 있다.
- `12-1_계정사전.json`: 생성 계정의 파싱 원카운트·모델·페르소나·시험/학습 구분·민감도 자료.
- `13-0_계정사전.json`: 대응하는 사람·원 BotSim 봇·완전모방기 계정의 측정값.
- `research/단계별 진행경과/12_OpenRouter생성_준비/분할.json`: 역할·분할.
- 같은 폴더의 `모델ID표.json`, `동결.json`, `프롬프트대장.jsonl`: 모델명·고정 입력 해시·슬롯 구성 추적용.
- `scripts/export_openrouter.py`: API 기록을 읽기 쉬운 슬롯별 JSONL로 추출. 네트워크 호출 없음.

새 모델 4종은 `anthropic/claude-haiku-4.5`, `openai/gpt-6-luna`, `google/gemini-3.5-flash-lite`, `deepseek/deepseek-v4.1-flash`이다. `openai/gpt-4o-mini` 재생성 대조군도 포함한다. 이는 **당시 저장된 모델 ID**이며 현재 API 가용성을 뜻하지 않는다.

핵심 보조 결과의 시험 표본은 새 모델 봇 252개와 사람 234개이다. 생성 전체 계정, 모델별 시험 묶음, 4종 합동 묶음, gpt-4o-mini 대조 묶음을 섞지 않는다. 개별 모델 점수와 합동 점수는 서로 다른 평가 묶음에서 계산된다.

API 키·개인 실행 쉘·새 생성 명령은 포함하지 않았다. 프롬프트 본문 전체의 별도 대용량 복사본과 파일럿 실행 기록도 분석 재실행에 필요하지 않아 제외했다. 원문 댓글과 분석 입력은 포함되어 있다.

## 4. UD 목록과 파싱 모델

- 동봉한 UD English-EWT의 train/dev/test `.conllu`를 합쳐 목록을 만든다. 최초 표면형 174개가 정규화 후 172개가 된다.
- `research/02_UD캐시/`의 파일 해시를 고정했다. 원 코드에 `master` URL이 있지만 이번 재현은 동봉 캐시를 사용한다.
- Stanza 1.14.0의 영어 tokenize·mwt·pos, pretrain, forward/backward charlm 파일과 `resources.json`을 동봉했다. 실행 시 `STANZA_RESOURCES_DIR`로 이 경로를 지정한다.
- BotSim 파싱 당시 Torch 2.11.0, 후기 fox8 분석 환경은 Torch 2.10.0이었다. `requirements-botsim.txt`와 `requirements.txt`로 구분했다.

## 5. 파일 무결성과 원자료 보존

- `scripts/manifests/files.json`: 각 파일의 원래 논리 경로·종류·크기·SHA-256.
- `scripts/manifests/assets.json`: 다운로드할 압축 파일의 SHA-256.
- 모든 원본은 그대로 보존했다. 실행은 내려받은 파일을 복사한 작업폴더에서 진행한다.
- 과거 결과 JSON의 머신 경로·실행 시각은 당시 기록이다. 그 경로에 파일을 설치할 필요는 없다.
- 전달 자료에 실제 공개 SNS 글과 계정 식별자가 포함되므로, 비공개 공동연구 범위로 취급한다. 이 저장소를 공개 배포로 전환하려면 별도 검토가 필요하다.

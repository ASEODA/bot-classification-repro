# bot-classification: 연구 데이터와 재현 코드

**손제홍 → 김송 연구 검토용 · 2026-09-27 최종 실행 기준 · 비공개 저장소**

계정이 쓴 여러 글에서 기능어(F), 문법·품사(M), 문장 길이·구두점(R)을 측정하고, 봇과 사람의 차이·집단 내부 동질성·계정 판별 성능을 확인한 연구 자료입니다.

**최종 판별기는 로지스틱 점수 + 이웃 밀도(k=10)의 순위 평균입니다.** 이전의 봇·사람 중심거리 판별기와 혼동하지 않도록, 변경 경위와 최종 결과를 구분했습니다.

## 먼저 볼 것

1. [핵심 결과와 해석](docs/RESULTS.md)
2. [실험 순서·코드·입출력](docs/PIPELINE.md)
3. [데이터 설명과 출처](docs/DATA.md)
4. [검증한 범위 / 남은 재현 점검](docs/VALIDATION.md)
5. [제3자 자료 및 공유 범위](NOTICE.md)

## 포함 범위

| 자료 | 전달 내용 | 재실행 범위 |
|---|---|---|
| BotSim | 원문 JSON·계정 CSV·UD 목록 원자료·파싱 모델·중간값 | 원문 정제 → FMR 측정 → 세 통제 → 동질성 → 판별기 학습 |
| fox8 | 원본 NDJSON.gz·분석용 SQLite·중간값 | 원문 선택·파싱 → 문체 차이·동질성·판별기 적용 |
| OpenRouter | 저장된 생성 댓글·모델/슬롯/분할 설정·파싱된 계정 사전 | **기존 데이터에 대한 분석만**. API 호출·새 생성은 제외 |
| 검증 자료 | 최신 결과 JSON·학습 모델·과거 비교용 의존 파일 | 새 실행 결과와 기준 수치 대조 |

코드는 Git에, 대용량 자료는 **이 비공개 저장소의 [Release](https://github.com/ASEODA/bot-classification-repro/releases/tag/data-20260927)**에 있습니다. `git clone`만으로 데이터를 받은 것은 아닙니다. 아래 `prepare --download`가 데이터·체크포인트·고정 Stanza 모델을 내려받고 SHA-256을 확인합니다.

## 설치 및 데이터 준비

macOS 또는 Linux, Python 3.13.7 기준입니다. GitHub CLI(`gh`)로 이 비공개 저장소에 접근할 수 있어야 합니다. 원문에서 재파싱하면 여러 시간이 걸릴 수 있으므로, 먼저 **분석 재실행**으로 환경을 확인하는 순서를 권합니다.

처음 받는 공동연구자는 저장소 초대를 수락하고 `gh auth login`으로 로그인한 뒤 실행합니다. GitHub의 **Download ZIP은 코드만** 포함하므로 데이터 준비 명령도 실행해야 합니다.

```bash
git clone https://github.com/ASEODA/bot-classification-repro.git
cd bot-classification-repro
uv venv --python 3.13.7 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python scripts/reproduce.py prepare --download
```

`uv` 대신 같은 Python 버전의 `venv`와 `pip`를 사용해도 됩니다. 이 저장소에는 API 키가 없으며, 아래 명령에는 OpenRouter API 키가 필요하지 않습니다.

### A. 파싱을 생략하고 분석 재실행

```bash
.venv/bin/python scripts/reproduce.py analysis
```

공유한 **측정 원카운트**에서 동질성·판별기 재학습·OpenRouter 보조 분석·fox8 평가를 실행합니다. 로지스틱 모델을 그대로 불러서 표만 출력하는 명령이 아닙니다. 마지막에 기준 결과와 수치를 비교합니다.

OpenRouter 보조 분석에는 반복 추출·재표집 계산이 있어 이 명령도 수십 분 걸릴 수 있습니다. 진행 상황은 출력에 표시된 `work/logs/`의 로그에서 확인할 수 있습니다.

### B. 원문부터 재실행

원래 BotSim 파싱과 이후 fox8 분석은 Torch 버전이 달랐으므로 환경을 두 개로 구분했습니다. 모델 파일은 동일하게 동봉한 파일을 씁니다.

```bash
uv venv --python 3.13.7 .venv-botsim
uv pip install --python .venv-botsim/bin/python -r requirements-botsim.txt
.venv/bin/python scripts/reproduce.py prepare --work work-full --download
.venv/bin/python scripts/reproduce.py raw --work work-full --botsim-python .venv-botsim/bin/python
```

이 명령은 BotSim 원문 정제·목록 생성·파싱·통제와 fox8 재파싱을 실제로 수행한 뒤 A의 분석을 이어갑니다. **OpenRouter 생성 댓글은 주어진 데이터로 사용**하며 다시 생성하지 않습니다. 과거 비교값과 사전 고정 분할은 검증용 참조로 남깁니다.

- 원문·배포 코드에는 쓰지 않고 `work-full/` 안에서만 실행합니다.
- 단계별 로그: `work-full/logs/`
- 실행 이력: `work-full/validation/runs.jsonl`
- 최종 수치 대조: `work-full/validation/result-comparison.json`
- 중단 시 실패 단계 로그를 확인하십시오. 자동으로 오류를 무시하거나 다음 단계로 넘어가지 않습니다.
- 전체 `raw` 완료 여부와 실제 검증 범위는 반드시 [VALIDATION](docs/VALIDATION.md)을 확인하십시오.

### C. OpenRouter 댓글만 읽기 좋은 파일로 꺼내기

```bash
.venv/bin/python scripts/export_openrouter.py \
  work/home/DM_LAB_data/12_OpenRouter work/data/openrouter_generated_comments.jsonl
```

슬롯별 모델·게시물·생성 댓글·성공 상태를 꺼냅니다. 이는 저장된 슬롯 기록이며, 파서의 복사 제외·언어 판정을 통과한 최종 분석 표본과는 구분합니다.

## 폴더 구성

```text
scripts/       다운로드·작업폴더 준비·실행·결과 대조
source/        계산 코드를 바꾸지 않은 연구 스크립트 및 고정 계획
manifests/     배포 파일 해시·Release 자산 해시·기준 수치
docs/          자료 설명·방법·결과·재현 안내
validation/    전달 전 실제 검증 기록
.assets/       내려받은 대용량 압축 파일 (Git 제외)
work*/         재실행 전용 사본과 실행 로그 (Git 제외)
```

원래 코드의 함수 대조·파일 해시 검사를 유지하기 위해 `source/research/` 아래의 내부 파일명은 보존했습니다. 실행기는 필요한 상대 경로를 구성합니다. **과거 판별기 파일은 일부 검증 코드의 입력이지, 현재 최종 결과가 아닙니다.**

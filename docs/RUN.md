# 실행 안내

## 처음 준비하기

실제 검증 환경은 **macOS Apple Silicon / Python 3.13.7**입니다. 실행기는 macOS·Linux의 Bash를 대상으로 합니다. Linux·Windows에서의 동일성 검증은 아직 하지 않았습니다. 원본 연구 폴더나 Obsidian은 필요하지 않습니다.

1. 이 비공개 GitHub 저장소의 초대를 수락합니다.
2. [uv 설치 안내](https://docs.astral.sh/uv/getting-started/installation/)와 [GitHub CLI 설치 안내](https://github.com/cli/cli#installation)에 따라 `uv`, `gh`를 설치합니다. Homebrew가 있는 Mac에서는 `brew install uv gh`를 사용할 수 있습니다.
3. `gh auth login`으로 저장소에 접근 가능한 계정에 로그인합니다. [공식 로그인 안내](https://cli.github.com/manual/gh_auth_login)
4. README의 clone 명령을 실행하거나 Code → Download ZIP을 받아 압축을 풉니다. 이후 명령은 `run.sh`가 있는 폴더에서 실행합니다.

데이터·모델 압축 파일은 합계 약 **437 MB**입니다. 압축 해제, Python 라이브러리, 재실행 결과를 위해 디스크 공간도 필요합니다. 처음 설치할 때는 인터넷 연결이 필요하며, Python 3.13.7이 없으면 uv가 준비합니다.

## 기본 실행 — 먼저 이것으로 환경 확인

```bash
bash run.sh
```

| 순서 | 하는 일 |
|---|---|
| 환경 설치 | `.venv/`에 Python과 고정 버전 라이브러리 준비 |
| 자료 준비 | GitHub Release의 원자료·중간값·파싱 모델 다운로드, SHA-256 확인, `work/` 구성 |
| 동질성 | 제공된 계정별 측정값에서 집단 내부의 퍼짐 재계산 |
| 판별기 | BotSim 판별기 재학습과 내부 평가 |
| 외부 적용 | 저장된 OpenRouter 자료 및 fox8 평가 |
| 수치 대조 | AUC·혼동행렬·동질성 비율 등을 제공 기준과 비교 |

기본 실행은 **측정 이후의 핵심 분석**입니다. 원문 정제·전량 파싱·FMR 통제 계산은 다시 하지 않고 제공된 결과를 사용합니다. 측정 모델과 입력도 함께 받으므로 아래 전체 실행으로 확장할 수 있습니다.

설치·다운로드를 제외한 기본 계산은 이 Mac의 앞선 검증에서 약 2~3분이 걸렸습니다. 컴퓨터에 따라 달라집니다. 같은 폴더에서 `bash run.sh`를 다시 실행하면 다운로드 자료를 재사용하고 핵심 분석을 다시 계산합니다. 작업폴더의 해당 결과 파일은 갱신됩니다.

## 전체 실행 — 원문에서 다시 계산

```bash
bash run.sh full
```

기본 실행을 먼저 할 필요는 없습니다. 별도 `work-full/`을 준비하고 다음을 수행합니다.

1. fox8 압축 원문에서 분석용 SQLite 재구성
2. BotSim 적격 계정 선별·UD 기능어 목록 생성
3. F·M 측정, 비교, R 확장 측정·비교
4. 글 분량·댓글 유형·게시판의 세 통제와 목록 민감도
5. FMR 통합 통제, 동질성 귀무 오류율 모의
6. fox8 전량 재파싱
7. 기본 실행의 동질성·판별기 학습·외부 평가·기준 수치 대조

원 BotSim 파싱과 후기 fox8 파싱의 Torch 버전이 달라 `.venv-botsim/`도 별도로 설치합니다. **여러 시간이 걸릴 수 있습니다.** 이 경로의 전량 연속 실행은 아직 검증 완료가 아니며, 실제 확인한 단계는 [검증 기록](VALIDATION.md)에 구분했습니다.

OpenRouter는 생성된 데이터와 측정값을 사용합니다. 새 API 생성은 어느 명령에도 없습니다.

## 결과는 어디에 생기나?

| 찾는 것 | 기본 실행 위치 |
|---|---|
| 수치 대조 통과 여부 | `work/validation/result-comparison.json` |
| 단계별 로그 | `work/logs/` |
| 실행 순서·종료 코드·소요시간 | `work/validation/runs.jsonl` |
| 실험별 상세 결과 | `work/research/단계별 진행경과/` |
| BotSim·fox8 원자료 | `work/research/1. 원본데이터/` |
| OpenRouter 생성 기록 | `work/home/DM_LAB_data/12_OpenRouter/` |

전체 실행은 위의 `work/` 대신 `work-full/`입니다. 실험 코드·결과 파일의 대응 관계는 [PIPELINE](PIPELINE.md), 주요 결과의 뜻은 [RESULTS](RESULTS.md)를 참고합니다.

## 오류가 나거나 중단되면

- **`uv` 또는 `gh`가 없음:** 위 설치 안내를 따른 뒤 다시 실행합니다.
- **인증 오류·404:** 비공개 저장소 초대 수락 여부와 `gh auth status`의 로그인 계정을 확인합니다. 키를 코드에 적지 않습니다.
- **자료 준비 도중 중단:** 불완전한 폴더를 정상 입력으로 사용하지 않도록 시작 파일이 멈춥니다. 파일을 지우지 말고 새 폴더에 저장소를 내려받아 시작하거나, 중단한 자료를 확인한 뒤 수동 준비 명령을 사용합니다.
- **전체 실행 중단:** `work-full/`을 자동 삭제하거나 처음부터 덮어쓰지 않습니다. 로그의 실패 단계와 산출물을 확인하고 그 단계부터 재개합니다. 같은 작업폴더에 두 실행을 동시에 시작하지 않습니다.
- **`FAIL numerical result comparison`:** 결과를 성공으로 간주하지 말고 `differences`와 해당 로그를 확인합니다.

예: 판별기 단계부터 다시 실행할 때

```bash
.venv/bin/python scripts/reproduce.py step --work work-full \
  --script 11_판별기.py --args --overwrite
```

이 명령은 지정한 단계 하나만 실행합니다. 이어지는 단계도 [실행 순서](PIPELINE.md)에 따라 실행해야 합니다. 새 작업폴더에서 전체 실행을 시작하는 수동 명령은 다음과 같습니다. 먼저 `bash run.sh full`의 환경 설치가 끝나 있어야 합니다.

```bash
.venv/bin/python scripts/reproduce.py prepare --work work-another --download
.venv/bin/python scripts/reproduce.py raw --work work-another --botsim-python .venv-botsim/bin/python
```

## 선택 작업

### OpenRouter 댓글을 읽기 쉬운 파일로 추출

```bash
.venv/bin/python scripts/export_openrouter.py \
  work/home/DM_LAB_data/12_OpenRouter work/data/openrouter_generated_comments.jsonl
```

저장된 슬롯 기록을 꺼내며, 복사 제외·언어 판정을 통과한 최종 분석 표본과는 구분합니다.

### OpenRouter 표 a의 보조 민감도 분석

```bash
.venv/bin/python scripts/reproduce.py step --script 12-2_표a.py
```

수십 분 이상 걸릴 수 있어 기본 실행에서는 제외했습니다. 코드와 기존 결과는 모두 제공하며 새 API 호출은 없습니다.

### 준비와 계산을 따로 실행

`run.sh`가 연결하는 기존 명령입니다. 환경을 직접 관리하는 경우 사용할 수 있습니다.

```bash
uv venv --python 3.13.7 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python scripts/reproduce.py prepare --download
.venv/bin/python scripts/reproduce.py analysis
```

`prepare`는 새 작업폴더에만 실행합니다. 준비 직후 `verify`는 배포 원본 해시를 확인하고, 분석 후 `check_results.py`는 재계산한 수치를 확인합니다. 실행 시각·모형 파일 등이 갱신되므로 분석 후 원본 파일 해시가 달라지는 것 자체는 정상입니다.

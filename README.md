# 문체적 지문을 활용한 봇 분류

BotSim-24와 fox8-23을 이용한 봇 분류 실험의 코드와 데이터다. 계정별 문체 특성과 계정 간 유사성을 활용하여 로지스틱 분류기(**L**), 최근접 이웃 점수(**G**), 두 점수의 동일 가중 순위 결합(**S**)을 비교한다.

특성 표현은 기능어, 형태론, 품사, 리듬으로 구성된 250개 FMR 특성이다. 주 분석·학습·평가에는 BotSim과 fox8을 사용한다. OpenRouter 생성 자료는 별도의 보충 자료이며, 주 실행 경로에는 사용하지 않는다.

## 실행 방법

저장소를 내려받아 압축을 푼 뒤, 저장소 루트에서 실행한다. Python 3.13을 권장하며 패키지 버전은 `requirements.txt`에 고정되어 있다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash run.sh
```

기본 실행은 제공된 계정별 특성표를 사용하여 통계 분석, 모델 학습, 평가를 수행하고 `expected/`의 기준 결과와 대조한다. 원자료 다운로드나 생성 모델 API 호출은 수행하지 않는다.

- 결과 요약: `results/summary.md`
- 세부 결과: `results/analysis.json`, `results/training.json`, `results/evaluation.json`
- 기준 결과 대조: `results/verification.json`

## 실험 구성

| 실험 | 구현 | 산출물 |
|---|---|---|
| 원문에서 FMR 특성 250개 추출 | `code/features.py`, `code/common.py` | `results/features/*.csv`, `results/raw_check.json` |
| 봇·사람 간 차이와 세 가지 독립 통제 분석 | `code/analysis.py` | `results/analysis.json` |
| F·M·R 블록별 집단 내 동질성 | `code/analysis.py` | `results/analysis.json` |
| BotSim 매칭 512쌍의 로지스틱 분류 | `code/train.py` | `results/training.json`, `results/model.joblib` |
| fox8에서 L·G·S 비교 | `code/evaluation.py` | `results/evaluation.json` |
| 중심·퍼짐 변환과 민감도 분석 | `code/evaluation.py` | `results/evaluation.json` |

평가 명세, 표집 규칙, 해석 기준은 [평가 프로토콜](data/records/protocol.md)에 정리되어 있다.

## 기준 결과

AUC는 분류 정확도가 아니라 순위 판별력을 나타낸다. 아래 값은 배포된 기준 결과의 요약이다.

| 평가 조건 | 로지스틱 L | 이웃 G | 결합 S |
|---|---:|---:|---:|
| BotSim 교차검증 | 1.0000 | — | — |
| fox8 확인 집합 | 0.9493 | 0.9885 | 0.9956 |
| fox8 중심 차이 제거 | 0.3792 | 0.9905 | 0.8222 |
| fox8 퍼짐 차이 축소 | 0.9958 | 0.5789 | 0.9176 |

- fox8 확인 집합의 **S − L은 0.0463**, 95% 구간은 **[0.0341, 0.0597]**이다.
- BotSim의 250개 특성 중 147개가 효과크기·유의성 기준을 충족한다. 이 중 분량 매칭에서는 139개, 댓글 한정 분석에서는 140개, politics 한정 분석에서는 137개가 효과 방향·크기 기준을 유지한다.
- 목표 봇 비중 5%에서 평균 결합 AUC는 0.9810이다. 세 번의 하위표집 중 한 번은 S − L의 구간이 0을 포함한다.
- 잔존 자기폭로 유사 문구가 있는 계정을 제외하면 퍼짐 조작의 확인 기준을 충족하지 못한다.

## 데이터와 해석 범위

**BotSim.** 적격 계정은 1,869개다. 학습과 동질성 분석에는 분량을 매칭한 봇·사람 512쌍을 사용한다. Benjamini–Hochberg 보정은 기능어·형태론·품사·리듬별로 적용하며, 세 가지 통제 분석은 각각 독립적으로 수행한다.

**fox8.** 적격 계정은 1,991개이며, 확인 집합은 996개(봇 547개, 사람 449개)다. 특성은 BotSim 학습 분포를 기준으로 변환한다. G는 평가 집합 안에서 열 번째로 가까운 계정까지의 거리에 음수를 취한 점수이며, S는 L과 G의 순위를 같은 가중치로 결합한다. 중심·퍼짐 합성 변환, 봇 비중 하위표집, 사람 자료원별 부분집합, 절단문 처리, 잔존 문구 제외 조건을 평가한다.

개발·확인 분할이 고정되기 전에 fox8 전체 표본을 이용한 분석이 있었다. 따라서 확인 집합은 이전 분석에 전혀 사용되지 않은 독립 시험 집합이 아니다. 부트스트랩 구간은 점수와 이웃 구조를 고정한 상태에서 해당 평가 표본에 조건부로 산출한다. 합성 변환만으로 문체적 퍼짐의 인과적 원인을 식별할 수는 없다.

**OpenRouter.** 다섯 모델의 생성 응답 기록, 계정별 측정값, 사람 대조군, 모방 예시, 분할 정보를 보충 자료로 제공한다. 주 실행 경로는 이 실험을 재생성하거나 평가하지 않는다. 측정값의 키와 CSV 열 이름은 원래 스키마를 유지한다.

## 원문에서 실행

기준 재현 경로는 위의 특성표 기반 실행이다. 원문 전체에서 특성을 다시 추출하는 모드는 별도로 제공한다. 전량 재추출 모드의 종단 간 결과 일치는 확인되지 않았으며, 부분 파싱만으로 전량 재현을 보장하지 않는다.

```bash
.venv/bin/python -m pip install -r code/requirements-full.txt
bash run.sh smoke
bash run.sh full
```

| 명령 | 실행 범위 |
|---|---|
| `bash run.sh` 또는 `bash run.sh fast` | 제공된 특성표로 분석·학습·평가 |
| `bash run.sh smoke` | 코퍼스별 앞부분 최대 3개 계정의 특성을 재추출하고 제공된 특성표와 대조 |
| `bash run.sh full` | 전체 특성 재추출 후 분석·학습·평가 및 기준 결과 대조 |
| `bash run.sh data` | 실험 실행 없이 원자료와 파서 모델 준비 |
| `bash run.sh verify` | 기존 산출물과 기준 결과 대조 |

모든 명령은 단위검사를 먼저 실행한다. 전량 파싱에는 수 시간이 걸릴 수 있다. 어떤 실행 모드도 생성 모델 API를 호출하지 않는다.

### 원자료 준비

원문 코퍼스와 Stanza 모델은 소스 코드 압축파일에 포함되지 않는다. 원본 GitHub 저장소의 `full`, `smoke`, `data` 모드는 필요한 입력이 없으면 고정 릴리스 `repro-final-20260927`에서 약 354 MB를 내려받는다. `code/prepare_data.py`가 릴리스 체크섬을 확인하고 `data/raw/`에 입력 파일을 준비한다.

**익명 미러에서는 원본 GitHub의 릴리스 첨부파일을 제공하지 않는다.** 익명 배포본에서 `full`, `smoke`, `data`를 실행하려면 별도 배포된 준비 완료 원자료를 `data/raw/`에 넣어야 한다. 기본 `fast` 모드는 추가 자료 없이 실행할 수 있다. 필요한 파일명과 체크섬은 `data/manifest.json`에 있다.

준비 완료 데이터 압축파일은 저장소 루트에서 풀어 파일이 `data/raw/`에 놓이도록 한다. 반드시 해당 배포본의 매니페스트와 일치하는 데이터를 사용해야 한다. 원본 릴리스 압축파일과 준비 완료 데이터 압축파일은 내부 구조와 체크섬이 다르다.

## 디렉터리 구성

| 경로 | 내용 |
|---|---|
| `code/` | 특성 추출, 통계 분석, 학습, 평가, 단위검사 |
| `data/features/` | 압축된 계정별 특성표 5개 |
| `data/records/` | 특성 스키마, 분할, 평가 프로토콜, 출처 |
| `data/raw/` | 원문 코퍼스와 파서 모델. 별도 배포 |
| `expected/` | 대조용 기준 결과. 학습이나 점수 산출에는 사용하지 않음 |
| `results/` | 실행 결과와 중간 파일. 버전 관리에서 제외 |

## 출처와 이용 조건

- [BotSim](https://github.com/QQQQQQBY/BotSim), 사용 리비전 `5c3558f`
- [AIBot_fox8](https://github.com/osome-iu/AIBot_fox8), 사용 리비전 `4f6bf49`; [fox8 데이터셋](https://doi.org/10.5281/zenodo.8035289)
- [UD English-EWT](https://github.com/UniversalDependencies/UD_English-EWT)
- [Stanza](https://stanfordnlp.github.io/stanza/)

배포 입력의 체크섬은 `data/manifest.json`, 원본 단계 자료의 체크섬과 평가 이력은 `data/records/provenance.json`에 있다. fox8 원본 라이선스와 출처 문서는 `data/records/`에 보존되어 있다.

데이터에는 소셜미디어 원문과 계정 식별자가 포함되어 있다. 데이터 접근과 재사용에는 원 제공자의 이용 조건이 적용되며, 이 배포본은 제3자 자료에 대한 포괄적 이용 허락을 추가로 부여하지 않는다.

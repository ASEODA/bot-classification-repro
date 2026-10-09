# 계정 간 문체 유사성을 이용한 LLM 봇 판별

BotSim-24와 fox8-23으로 수행한 봇 판별 실험의 코드와 자료다. 계정별 문체 특성으로 학습한 로지스틱 분류기 L, 평가 집합 안의 최근접 이웃 거리 점수 G, 두 점수의 순위를 같은 가중치로 합친 결합 점수 S를 비교한다. L, G, S는 논문의 개별 문체 점수 S_ind, 동질성 점수 S_hom, 결합 점수 S(λ = 0.5)다.

특성은 기능어(F) 172개, 형태자질과 품사(M) 75개, 문장 길이와 구두점(R) 3개를 합한 250개다. 분석·학습·평가에는 BotSim과 fox8을 쓰고, OpenRouter 생성 실험은 보충 자료로만 둔다.

## 실행 방법

저장소 루트에서 실행한다. Python 3.13을 권장하며 패키지 버전은 `requirements.txt`에 고정되어 있다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash run.sh
```

기본 실행은 제공된 계정별 특성표로 통계 분석, 모델 학습, 평가를 수행한 뒤 `expected/`의 기준 결과와 대조한다. 원자료 내려받기나 생성 모델 API 호출은 하지 않는다.

- 결과 요약: `results/summary.md`
- 세부 결과: `results/analysis.json`, `results/training.json`, `results/evaluation.json`
- 기준 결과 대조: `results/verification.json`

기준 결과는 Apple Silicon(arm64)에서 만들었다. 합성 변환 W2·W3는 잔차를 복원 추출하므로 같은 벡터가 생기고, 그 사이의 동점이 CPU에 따라 다르게 갈려 x86_64에서는 일부 값이 10⁻⁴ 수준에서 달라질 수 있다. 대조 단계는 W2·W3 값에만 10⁻³ 허용오차를 두고, 이 허용오차로 통과한 값은 `results/verification.json`에 따로 적는다.

## 실험 구성

| 실험 | 구현 | 산출물 |
|---|---|---|
| 원문에서 FMR 특성 250개 추출 | `code/features.py`, `code/common.py` | `results/features/*.csv`, `results/raw_check.json` |
| 봇·사람 간 차이와 세 가지 독립 통제 분석 | `code/analysis.py` | `results/analysis.json` |
| F·M·R 블록별 집단 내 동질성 | `code/analysis.py` | `results/analysis.json` |
| BotSim 매칭 512쌍의 로지스틱 분류 | `code/train.py` | `results/training.json`, `results/model.joblib` |
| fox8에서 L·G·S 비교 | `code/evaluation.py` | `results/evaluation.json` |
| 중심·밀집도 합성 변환과 민감도 분석 | `code/evaluation.py` | `results/evaluation.json` |

평가 명세, 표집 규칙, 판정 기준은 [평가 프로토콜](data/records/protocol.md)에 있다.

## 기준 결과

| 평가 조건 | L (S_ind) | G (S_hom) | S |
|---|---:|---:|---:|
| BotSim 교차검증 | 1.0000 | - | - |
| fox8 확인 집합 | 0.9493 | 0.9885 | 0.9956 |
| fox8 중심 차이 제거 | 0.3792 | 0.9905 | 0.8222 |
| fox8 밀집도 차이 축소 | 0.9958 | 0.5789 | 0.9176 |

값은 AUC다.

- fox8 확인 집합에서 S − L은 0.0463, 95% 부트스트랩 구간은 [0.0341, 0.0597]이다.
- BotSim의 250개 특성 중 147개가 효과크기·유의성 기준을 충족한다. 분량 매칭에서는 이 중 139개, 댓글 한정 분석에서는 140개, politics 한정 분석에서는 137개가 효과 방향과 크기를 유지한다.
- 목표 봇 비중 5%에서 평균 결합 AUC는 0.9810이다. 세 번의 하위표집 중 한 번은 S − L의 구간이 0을 포함한다.

## 데이터와 해석 범위

**BotSim.** 적격 계정은 1,869개다. 학습과 동질성 분석에는 분량을 매칭한 봇·사람 512쌍을 쓴다. Benjamini-Hochberg 보정은 기능어·형태자질·품사·리듬별로 적용하며, 세 가지 통제 분석은 각각 독립적으로 수행한다.

**fox8.** 적격 계정은 1,991개다. 봇은 무작위로, 사람은 자료원별로 층화하여 개발 집합 995개와 확인 집합 996개(봇 547개, 사람 449개)로 나눈다. 방법은 개발 집합에서 정하고, 평가 명세를 고정한 뒤 확인 집합에서 평가한다. 특성은 BotSim 학습 분포를 기준으로 변환한다. G는 평가 집합 안에서 열 번째로 가까운 계정까지의 거리에 음수를 취한 점수이고, S는 L과 G의 순위를 같은 가중치로 합친 점수다. 이 밖에 중심·밀집도 합성 변환, 봇 비중 하위표집, 사람 자료원별 부분집합, 절단문 처리, 잔존 문구 계정 제외 조건을 평가한다.

부트스트랩 구간은 점수와 이웃 구조를 고정한 채 평가 계정을 다시 뽑아 구한다.

**OpenRouter.** 다섯 모델로 계정 글을 생성한 보충 실험이다. 이 저장소에는 분할 정보(`data/records/openrouter-split.json`)와 설명(`data/records/openrouter.md`)만 두고, 생성 응답 기록과 측정값은 원자료에 속해 넣지 않았다. 주 실행 경로는 이 자료를 쓰지 않는다.

## 원문에서 실행

기준 재현은 위의 특성표 기반 실행으로 한다. 원문에서 특성을 다시 추출하려면 아래 모드를 쓴다. `smoke` 모드는 코퍼스별로 일부 계정을 다시 추출해 제공된 특성표와 같은지 대조한다.

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
| `bash run.sh data` | 실험 없이 원자료와 파서 모델만 준비 |
| `bash run.sh verify` | 기존 산출물과 기준 결과 대조 |

모든 명령은 단위검사를 먼저 실행한다. 전량 파싱에는 수 시간이 걸릴 수 있으며, 어떤 모드도 생성 모델 API를 호출하지 않는다.

### 원자료 준비

원문 코퍼스와 Stanza 모델은 저장소에 넣지 않았다. `full`, `smoke`, `data` 모드는 `data/raw/`에 원자료가 있어야 하며, 필요한 파일명과 체크섬은 `data/manifest.json`에 있다. `code/prepare_data.py`는 원자료가 없으면 고정 릴리스에서 약 354 MB를 내려받아 체크섬을 확인한 뒤 `data/raw/`에 준비한다. 심사용 익명 배포본에서는 릴리스 내려받기를 지원하지 않으므로 기본 `fast` 모드로 재현한다. BotSim, fox8, UD English-EWT, Stanza 원자료는 아래 출처에서 공개되어 있다.

## 디렉터리 구성

| 경로 | 내용 |
|---|---|
| `code/` | 특성 추출, 통계 분석, 학습, 평가, 단위검사 |
| `data/features/` | 압축된 계정별 특성표 5개 |
| `data/records/` | 특성 스키마, 분할, 평가 프로토콜, 출처 |
| `data/raw/` | 원문 코퍼스와 파서 모델 (저장소에 포함하지 않음) |
| `expected/` | 대조용 기준 결과. 학습이나 점수 산출에는 쓰지 않음 |
| `results/` | 실행 결과와 중간 파일. 버전 관리에서 제외 |

## 출처와 이용 조건

- [BotSim](https://github.com/QQQQQQBY/BotSim), 사용 리비전 `5c3558f`
- [AIBot_fox8](https://github.com/osome-iu/AIBot_fox8), 사용 리비전 `4f6bf49`; [fox8 데이터셋](https://doi.org/10.5281/zenodo.8035289)
- [UD English-EWT](https://github.com/UniversalDependencies/UD_English-EWT)
- [Stanza](https://stanfordnlp.github.io/stanza/)

배포 입력의 체크섬은 `data/manifest.json`에, 원본 단계 자료의 체크섬은 `data/records/provenance.json`에 있다. fox8 원본 라이선스와 출처 문서는 `data/records/`에 함께 두었다.

특성표에는 원 자료의 계정 식별자가 들어 있다. 원 자료의 접근과 재사용에는 각 제공처의 이용 조건이 적용된다.

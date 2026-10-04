# bot-classification

BotSim-24와 fox8-23을 이용한 문체지문 기반 봇 판별 실험의 코드와 자료를 제공한다.
실험은 문체지문(FMR) 구성, 집단 간 차이·통제·동질성 분석, 로지스틱 학습, 이웃 거리 결합, fox8 평가 순서로 진행한다.

## 실험 구성

**개별 계정의 문체 특성에 계정 간 문체 유사성을 더하면 봇 판별에 도움이 되는가?**
BotSim에서 학습한 로지스틱 점수(L), 함께 평가하는 계정들 사이의 이웃 거리 점수(G), 두 점수의 결합을 비교한다. 아래 핵심 실험의 계산에는 OpenRouter 자료를 사용하지 않는다.

| 실험 | 담당 코드 | 실행 후 결과 |
|---|---|---|
| 원문에서 FMR 250개 특성 측정 | `code/features.py`, `code/common.py` | `results/features/*.csv`, `results/raw_check.json` (`full` 실행) |
| 봇·사람 차이와 세 통제 분석 | `code/analysis.py` | `results/analysis.json` |
| F·M·R별 집단 내부 동질성 비교 | `code/analysis.py` | `results/analysis.json` |
| BotSim 512쌍으로 로지스틱 학습·교차검증 | `code/train.py` | `results/training.json`, `results/model.joblib` |
| fox8에서 L·G·결합 점수 비교 | `code/evaluation.py` | `results/evaluation.json` |
| 중심·퍼짐 합성 자료, 봇 비중·사람 자료원 등 민감도 평가 | `code/evaluation.py` | `results/evaluation.json` |

각 코드를 따로 실행할 필요 없이 아래의 `bash run.sh`가 분석·학습·평가를 순서대로 수행한다. 결과 요약은 `results/summary.md`에 모인다.

## 주요 결과

AUC는 봇에 사람보다 높은 점수를 주는 능력이다. 0.5는 무작위 수준, 1은 완전한 순위 구분이며, 정확도와는 다르다.

| 평가 자료 | 로지스틱 L | 이웃 거리 G | 결합 |
|---|---:|---:|---:|
| BotSim 교차검증 | 1.0000 | — | — |
| fox8 확인 집합 | 0.9493 | 0.9885 | 0.9956 |
| fox8 중심 차이 제거 합성 자료 | 0.3792 | 0.9905 | 0.8222 |
| fox8 퍼짐 차이 축소 합성 자료 | 0.9958 | 0.5789 | 0.9176 |

- fox8 확인 집합에서 **결합 − L = 0.0463**이며, 95% 구간은 [0.0341, 0.0597]이다.
- BotSim의 주목 특성은 **147/250개**이며, 기존 주목 특성 중 분량 매칭에서 **139개**, 댓글 한정에서 **140개**, politics 한정에서 **137개**가 효과의 방향·크기 기준을 유지했다.
- 봇 비중 5% 조건의 평균 결합 AUC는 **0.9810**이다. 세 번의 표집 중 한 번은 추가 효과의 95% 구간이 0을 포함했다.
- 자기폭로 유사 문구가 남은 계정을 추가 제외한 조건에서는 퍼짐 조작 검증 기준을 충족하지 못했다.

위 값은 저장된 기준 결과의 요약이다. 재실행하면 새로 계산한 값을 기준 결과와 대조한다. fox8에는 개발 이력이 있으며, 부트스트랩 구간은 점수·이웃 구조를 고정한 해당 평가 집합 내부의 불확실성이다.

## 실행

GitHub의 **Code → Download ZIP** 또는 익명 저장소의 **Download ZIP**으로 내려받아 압축을 풀고, 그 폴더에서 실행한다.
Python 3.13 권장. 처음 한 번 환경을 준비한다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
bash run.sh
```

저장된 계정별 측정값으로 통계 분석·모형 학습·평가를 다시 수행하고, 기준 결과와의 일치 여부를 검사한다.
결과 요약은 **`results/summary.md`**, 검증 결과는 `results/verification.json`에 저장된다.

**익명 저장소의 실행 범위:** 기본 실행에는 원자료 다운로드가 필요 없다. 대용량 원자료는 익명 저장소에 포함되지 않고 다운로드 주소도 익명 처리되므로, `full`·`smoke`·`data` 실행에는 원자료와 Stanza 모델을 별도로 받아 `data/raw/`에 넣어야 한다.

**원문부터 재현하려면** 아래를 실행한다. 원본 GitHub 저장소에서는 원자료·Stanza 모델이 없을 때 고정된 Release에서 자동으로 내려받는다(약 354 MB, 최초 1회). 생성형 AI API는 호출하지 않으며, 전량 파싱에는 수 시간이 걸릴 수 있다.

```bash
.venv/bin/python -m pip install -r code/requirements-full.txt
bash run.sh full
```

`bash run.sh smoke`는 코퍼스별 앞 3계정의 원문 파싱 및 저장 측정값 일치를 점검한다. `bash run.sh data`는 원자료만 준비하고, `bash run.sh verify`는 기존 실행 결과만 다시 대조한다.

## 폴더

| 경로 | 용도 |
|---|---|
| `code/` | 원문 처리·통계·학습·최종 평가 코드 |
| `data/raw/` | BotSim·fox8 원자료, UD, Stanza 모델, OpenRouter 기존 데이터 |
| `data/features/` | 빠른 재현을 위한 계정별 측정값 5개 표 |
| `data/records/` | 고정 자질·평가 분할·당시 사전선언·출처 |
| `expected/` | 이전 실행에서 추출한 검증용 기준값. 학습·채점에는 사용하지 않음 |
| `results/` | 실행하면 만들어지는 결과. 파싱 중간 저장은 그 안의 `.work/` |

## 범위와 데이터

- **BotSim:** 전체 1,869계정이며, 분량을 맞춘 512쌍을 학습과 동질성 비교에 사용한다. 문체 특성은 250개이고, BH 보정은 F·형태자질·품사·R의 네 묶음에 각각 적용한다. 세 통제 분석은 서로 독립적으로 수행한다.
- **fox8:** 전체 1,991계정 중 확인 집합은 996계정(봇 547·사람 449)이다. BotSim 학습 자료의 백분위 기준으로 변환한 뒤, 10번째 이웃 거리 점수와 로지스틱 점수를 1:1로 순위 결합한다. 중심·퍼짐 합성 자료, 봇 비중 50/25/10/5%, 사람 자료원, 절단 꼬리, 잔여 자기폭로 문구 조건을 비교한다.
- **OpenRouter 보조 자료:** 5개 모델의 생성 실험 기록, 계정별 측정값, 사람 대조 자료, 예시 글과 데이터 분할 정보를 포함한다. BotSim·fox8 주 실험과는 별개의 참고 자료다.
- fox8 전체를 이전 방식으로 살펴본 후 개발/확인 집합을 나눴다. 완전히 처음 보는 독립 시험으로 간주하지 않는다. 부트스트랩은 점수·이웃 구조를 고정한 평가 집합 내부 구간이다.

출처: [BotSim](https://github.com/QQQQQQBY/BotSim) (`5c3558f`), [fox8](https://github.com/osome-iu/AIBot_fox8) (`4f6bf49`), [fox8 원자료](https://doi.org/10.5281/zenodo.8035289), [UD English-EWT](https://github.com/UniversalDependencies/UD_English-EWT), [Stanza](https://stanfordnlp.github.io/stanza/).
입력 해시는 `data/manifest.json`으로 검사한다. SNS 원문·계정 식별자가 포함되어 있다. 공개 저장소이지만 출처별 권리는 원 제공 조건을 따르며, 임의의 새 공개 라이선스를 부여하지 않았다.

### 원자료 위치

코드·측정값·검증 기준값은 이 저장소에 있고, 대용량 원자료는 [고정 Release](https://github.com/ASEODA/bot-classification-repro/releases/tag/repro-final-20260927)의 `data-final-20260927.tar.gz`와 `models-20260927.tar.gz`에 있다. `code/prepare_data.py`가 두 파일의 해시를 확인하고 필요한 자료를 `data/raw/`에 준비한다.
빠른 재현에는 별도 원자료 다운로드가 필요 없다. OpenRouter 데이터도 `bash run.sh data`로 함께 받을 수 있다.

**검증 상태(2026-10-04):** 단위검사 8개, 분석·학습·평가 결과 대조, 원자료에서 DB 재구성, 코퍼스별 부분 파싱 대조를 통과했다. 원문부터 전 계정을 다시 파싱하는 전량 재현은 미검증 상태다.

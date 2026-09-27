# bot-classification

**소셜미디어 계정의 문체로 LLM 봇과 사람을 구분하는 연구**

손제홍 · 김송 · 김정훈 / UNIST · 비공개 연구자료

기능어(F), 문법·품사(M), 문장 길이·구두점(R)을 계정별로 측정합니다. 문체 차이와 집단 동질성을 살핀 뒤, 로지스틱 점수와 이웃 밀도를 결합해 봇 여부를 판별합니다.

## 1. 데이터와 코드 받기

**BotSim·fox8 원자료와 OpenRouter 생성 댓글이 모두 포함되어 있습니다.**
대용량 데이터·파싱 모델은 [Release에 보관](https://github.com/ASEODA/bot-classification-repro/releases/tag/data-20260927)하며, 아래 실행 명령이 자동으로 내려받습니다. **Code → Download ZIP만 받으면 데이터는 아직 없는 상태입니다.**

저장소 초대를 수락하고 `uv`와 `gh`를 설치한 뒤, 터미널에서 실행합니다. [처음 설치하는 경우](docs/RUN.md#처음-준비하기)

```bash
gh auth login
gh repo clone ASEODA/bot-classification-repro
cd bot-classification-repro
```

ZIP으로 코드를 받았다면 압축을 풀고 그 폴더에서 아래 명령을 실행하면 됩니다. 비공개 데이터 다운로드를 위해 `gh auth login`은 필요합니다.

## 2. 실험 실행하기

```bash
bash run.sh
```

**환경 설치 → 데이터 다운로드 → 동질성 분석 → 판별기 재학습 → fox8·OpenRouter 평가 → 기준 수치 대조**까지 실행합니다. 제공된 측정값부터 시작하므로 전체 글을 다시 파싱하지 않습니다. OpenRouter API 호출이나 과금은 없습니다.

원문 정제와 FMR 측정·통제까지 처음부터 다시 하려면 `bash run.sh full`을 사용합니다. 여러 시간이 걸릴 수 있습니다. [실행 범위·중단 후 재개 안내](docs/RUN.md)

## 3. 결과 확인하기

- 마지막에 **`PASS numerical result comparison`**이 출력되면 대조 대상 수치가 기준 결과와 일치한 것입니다.
- 확인 파일: `work/validation/result-comparison.json` (`passed: true`). 전체 재실행은 `work-full/`에 저장됩니다.
- [연구 결과 요약 보기](docs/RESULTS.md) · [실험 순서와 코드 보기](docs/PIPELINE.md)

새 다운로드·새 환경에서 핵심 분석의 수치 재현을 확인했습니다. 전체 원문 전량 재파싱의 연속 실행은 아직 검증 완료가 아닙니다. [검증 범위](docs/VALIDATION.md)

<details>
<summary>데이터 설명·코드 위치·상세 자료</summary>

- [데이터 원본·구성·출처](docs/DATA.md)
- [실제 연구 코드](source/research/단계별%20진행경과/): 기존 연구 코드의 계산 내용과 내부 경로를 유지했습니다.
- `run.sh`: 처음 사용하는 사람이 실행할 시작 파일
- `scripts/`: 다운로드·실행·수치 대조 도구. `manifests/`는 이 안의 관리용 자료입니다.
- `docs/`: 설명 문서와 검증 기록
- [공유 범위와 제3자 자료 안내](NOTICE.md)

원문·배포 코드는 그대로 두고 작업폴더에서 실행합니다. 과거 코드 일부는 비교용 의존 파일이며 현재 결과와 구분합니다. OpenRouter의 새 생성 및 오래 걸리는 보조 민감도 분석은 기본 실행에 포함하지 않습니다.

</details>

# bot-classification

**소셜미디어 계정의 문체로 LLM 봇과 사람을 구분하는 연구**

손제홍 연구 검토용 · UNIST · 비공개 연구자료

기능어(F), 문법·품사(M), 문장 길이·구두점(R)을 측정하고, 로지스틱 점수와 이웃 밀도를 결합합니다. **최종 연구의 재현에 필요한 자료만 담았습니다. 과거 실행분 보관 폴더는 필요하지 않습니다.**

## 1. 내려받기

저장소 초대를 수락하고 `uv`와 `gh`를 설치한 뒤 실행합니다. [처음 설치하는 방법](docs/RUN.md)

```bash
gh auth login
gh repo clone ASEODA/bot-classification-repro
cd bot-classification-repro
```

GitHub의 **Code → Download ZIP**으로 받아도 됩니다. 대용량 자료는 비공개 [Release](https://github.com/ASEODA/bot-classification-repro/releases/latest)에 있으며, 아래 명령이 자동으로 다운로드합니다. ZIP만 받은 상태에는 데이터가 아직 없습니다.

## 2. 실행하기

```bash
bash run.sh
```

제공된 측정값부터 **문체 차이 → 세 통제 → 동질성 → 판별기 재학습 → fox8·OpenRouter 평가 → 기준 결과 대조**를 실행합니다.

BotSim·fox8의 **원문부터 다시 측정**하려면:

```bash
bash run.sh full
```

전량 파싱에는 수 시간이 걸릴 수 있습니다. 중단하면 **같은 명령으로 재개**합니다. OpenRouter는 저장된 생성 데이터·측정값을 사용하며, 새 생성이나 API 과금은 없습니다.

## 3. 확인하기

마지막 두 검사가 모두 `PASS`여야 합니다.

- `numerical result comparison`: 핵심 결과 수치 대조
- `detailed artifact comparisons`: 계정별 측정값·자질별 결과·분할·개별 점수·계수 대조

결과는 `work/validation/`에, 전량 실행은 `work-full/validation/`에 저장됩니다.

**[연구 결과 요약](docs/RESULTS.md)** · [실험 순서와 코드](docs/PIPELINE.md) · [검증 상태](docs/VALIDATION.md)

<details>
<summary>무엇이 포함되어 있나?</summary>

- BotSim 원문·라벨, fox8 원본 압축 데이터
- OpenRouter에서 이미 생성한 댓글과 분석 입력
- UD 기능어 목록 생성 자료와 고정 Stanza 모델
- 최종 측정·통제·동질성·분류 코드와 기준 결과 검사

`run.sh`만 실행하면 됩니다. 원래 Obsidian 연구 폴더나 개인 Python 환경은 참조하지 않습니다. 실패한 옛 판별기·모델·중복 실행분·생성 API 코드는 배포하지 않습니다.

[데이터 출처·구성](docs/DATA.md) · [상세 실행 안내](docs/RUN.md) · [공유 범위](NOTICE.md)
</details>

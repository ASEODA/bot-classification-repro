#!/usr/bin/env bash
# One entry point; the original research programs remain unchanged.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

mode="${1:-analysis}"
if [[ "$#" -gt 1 ]]; then
    echo '사용법: bash run.sh [analysis|full|help]' >&2
    exit 2
fi
case "$mode" in
    analysis) work=work ;;
    full) work=work-full ;;
    help|--help|-h)
        echo 'bash run.sh       : 환경 설치 + 데이터 다운로드 + 측정값 이후 핵심 분석 재실행'
        echo 'bash run.sh full  : 환경 설치 + 데이터 다운로드 + 원문부터 재파싱 (여러 시간)'
        echo '자세한 안내: docs/RUN.md'
        exit 0 ;;
    *) echo '사용법: bash run.sh [analysis|full|help]' >&2; exit 2 ;;
esac

if [[ "$mode" == full && -e "$work" ]]; then
    echo 'work-full이 이미 있습니다. 이전 실행을 덮어쓰지 않습니다.' >&2
    echo '중단한 단계의 재개 방법: docs/RUN.md. 처음부터 다시 하려면 새 폴더에 내려받으세요.' >&2
    exit 1
fi
for tool in uv gh; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "$tool 설치가 필요합니다. docs/RUN.md의 처음 준비하기를 확인하세요." >&2
        exit 1
    fi
done

echo '[1/3] Python 3.13.7 실행 환경 준비'
if [[ ! -x .venv/bin/python ]]; then
    uv venv --python 3.13.7 .venv
fi
uv pip install --python .venv/bin/python -r requirements.txt
if [[ "$mode" == full ]]; then
    if [[ ! -x .venv-botsim/bin/python ]]; then
        uv venv --python 3.13.7 .venv-botsim
    fi
    uv pip install --python .venv-botsim/bin/python -r requirements-botsim.txt
fi

echo '[2/3] 데이터·파싱 모델 준비 (첫 실행에서 다운로드)'
if [[ ! -e "$work" ]]; then
    .venv/bin/python scripts/reproduce.py prepare --work "$work" --download
elif [[ ! -f "$work/validation/initial-integrity.json" ]] || ! .venv/bin/python -c \
    'import json,sys; sys.exit(not json.load(open(sys.argv[1]))["passed"])' "$work/validation/initial-integrity.json"; then
    echo '작업폴더의 준비 완료 기록이 없습니다. docs/RUN.md의 중단 시 안내를 확인하세요.' >&2
    exit 1
fi

echo '[3/3] 실험 실행 및 기존 결과와 비교 — OpenRouter API 호출 없음'
if [[ "$mode" == full ]]; then
    .venv/bin/python scripts/reproduce.py raw --work "$work" --botsim-python .venv-botsim/bin/python
else
    .venv/bin/python scripts/reproduce.py analysis --work "$work"
fi
echo "완료. 수치 대조 결과: $work/validation/result-comparison.json"
echo "실험별 결과 파일: $work/research/단계별 진행경과/"

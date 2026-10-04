#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ -n "${PYTHON:-}" ]]; then
  py="$PYTHON"
elif [[ -x .venv/bin/python ]]; then
  py=.venv/bin/python
else
  py=python3
fi
export PYTHONDONTWRITEBYTECODE=1
"$py" -c 'import numpy, scipy, sklearn, joblib' || {
  echo '먼저 README의 환경 설치 명령을 실행하세요.' >&2
  exit 1
}
"$py" code/test_core.py
exec "$py" code/run.py "${1:-fast}"

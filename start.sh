#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=========================================================="
echo "⚡ AI YouTube Shorts Automated Factory"
echo "=========================================================="

if [ ! -f ".venv/bin/python" ]; then
    echo "[안내] 가상환경이 없습니다. 초기 환경 설정을 시작합니다..."
    if command -v uv &> /dev/null; then
        uv venv .venv
        uv pip install -r requirements.txt
    elif command -v python3 &> /dev/null; then
        python3 -m venv .venv
        ./.venv/bin/pip install -r requirements.txt
    else
        echo "[오류] 파이썬(python3)이 설치되어 있지 않습니다."
        exit 1
    fi
    echo "[완료] 초기 환경 설정이 완료되었습니다."
fi

./.venv/bin/python run.py

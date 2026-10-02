@echo off
chcp 65001 > nul
title AI YouTube Shorts Automated Factory
echo ==========================================================
echo ⚡ AI 기반 유튜브 쇼츠 자동 제작 공장 시스템
echo ==========================================================
cd /d "%~dp0"

set PATH=%USERPROFILE%\.local\bin;%PATH%

REM 1. 가상환경(.venv) 존재 여부 확인
if not exist ".venv\Scripts\python.exe" (
    echo [안내] 가상환경이 없습니다. 초기 환경 설정을 자동으로 시작합니다...
    
    REM uv가 있는지 확인
    where uv >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        echo [1/2] uv를 사용하여 초고속 파이썬 환경을 구성합니다...
        uv venv .venv --python 3.11 2>nul || uv venv .venv
        uv pip install -r requirements.txt
    ) else (
        REM 시스템 python 확인
        where python >nul 2>nul
        if %ERRORLEVEL% equ 0 (
            echo [1/2] 시스템 파이썬으로 가상환경을 생성합니다...
            python -m venv .venv
            .\.venv\Scripts\python.exe -m pip install --upgrade pip
            .\.venv\Scripts\python.exe -m pip install -r requirements.txt
        ) else (
            echo [오류] 파이썬(Python)이 설치되어 있지 않습니다.
            echo https://www.python.org 에서 파이썬을 설치한 후 다시 실행해주세요.
            echo (설치 시 'Add python.exe to PATH' 체크 필수)
            pause
            exit /b 1
        )
    )
    echo [2/2] 환경 설정이 완료되었습니다!
    echo ==========================================================
)

echo [실행] AI Shorts Factory 서버를 가동합니다...
.\.venv\Scripts\python.exe run.py
pause

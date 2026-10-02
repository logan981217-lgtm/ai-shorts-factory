# ⚡ AI 기반 유튜브 쇼츠 자동 제작 공장 (AI YouTube Shorts Automated Factory)

> **PRD(제품 요구사항 정의서) 기반 엔터프라이즈급 쇼츠 완전 자동화 SaaS 솔루션**  
> 사용자가 입력한 키워드, 주제, 이미지를 바탕으로 **LLM 대본 기획 ➔ TTS 음성 합성 ➔ ASS 자막 생성 ➔ FFmpeg 9:16 비디오 렌더링 ➔ AI 썸네일 ➔ YPP 수익화 검수 ➔ 유튜브 예약 발행**까지 완전 자동 또는 반자동으로 처리합니다.

---

## 🚀 주요 기능 및 특징 (Key Features)

1. **Zero-Touch 원클릭 자동화 파이프라인:**
   - 주제/키워드 입력 시 15초~60초 맞춤형 훅(Hook)-본문(Body)-CTA 스토리라인 자동 생성.
   - 고품질 자연스러운 신경망 음성(Microsoft Neural Voice) 및 밀리초 단위 자막 싱크 동기화.
   - 100% 로열티 프리 분위기별 BGM (활기찬 비트, 로파이, 미스터리, 사이버 신스 등) 자동 합성 및 음량 더킹.

2. **쇼츠 최적화 9:16 비디오 렌더링 엔진 (FFmpeg):**
   - 1080x1920 세로 쇼츠 규격, 30fps 고화질 렌더링.
   - 역동적인 줌인/줌아웃(Ken Burns Effect) 및 상단 실시간 프로그레스 바.
   - 쇼츠 Safe Zone(중앙 하단) 맞춤형 자막 (모던 옐로우, 네온 시안, 볼드 화이트, 자막 박스 등 ASS 스타일 지원).

3. **YPP(유튜브 파트너 프로그램) 수익화 정책 준수 검수기:**
   - 단순 재가공(Reused Content) 필터링 방지 독창적 서사 평가.
   - 유해/금지어 자동 필터링 및 오리지널리티 스코어링 ($\ge 85\%$).
   - AI 합성 미디어 투명성 공개 태그 지원.

4. **AI 썸네일 & 유튜브 SEO 키트:**
   - 1080x1920 고대비 타이포그래피 AI 썸네일 자동 생성.
   - 클릭률(CTR) 극대화 제목, 상세 설명문, 타겟 해시태그(#Shorts #쇼츠) 원클릭 복사.

5. **자동 예약 발행 & 오토파일럿(Auto-Pilot) 모드:**
   - 유튜브 황금 시간대(오후 6시~8시) 맞춤 자동 예약 등록.
   - 1일 1영상 무인 자동 발행 시뮬레이션 및 관리.

---

## 🛠️ 기술 스택 (Tech Stack)

- **Backend:** Python 3.11, FastAPI, Uvicorn, SQLite
- **AI & LLM:** Google Gemini 2.5 Flash (`google-genai`), 크리에이티브 스마트 프롬프트 템플릿 엔진
- **TTS & Audio:** `edge-tts` (Microsoft Neural Voices), procedural BGM synthesizer
- **Video Engine:** `FFmpeg 7.1`, `Pillow (PIL)`, `imageio-ffmpeg`
- **Frontend:** HTML5, CSS3 (YouTube Studio 테마 Glassmorphism), Vanilla JavaScript SPA

---

## ⚡ 빠른 실행 방법 (Quick Start)

### 1. Windows 원클릭 실행
폴더 내의 **`start.bat`** 파일을 더블 클릭하면 서버가 시작되고 웹 브라우저(`http://127.0.0.1:8000`)가 자동으로 열립니다.

### 2. 터미널 명령어로 실행
```powershell
# 가상환경 활성화 후 실행
.\.venv\Scripts\python.exe run.py
```
브라우저에서 `http://127.0.0.1:8000` 접속.

---

## 📂 프로젝트 구조 (Directory Structure)

```text
ai-youtube-shorts-factory/
├── app/
│   ├── config.py             # 시스템 환경 설정, 경로, FFmpeg 경로
│   ├── database.py           # SQLite DB 모델 및 통계
│   ├── main.py               # FastAPI 서버 및 REST API 라우트
│   ├── services/
│   │   ├── script_engine.py  # Gemini API 및 스마트 대본 엔진
│   │   ├── tts_engine.py     # edge-tts 음성 및 SRT 자막 생성
│   │   ├── bgm_engine.py     # 저작권 프리 BGM 합성 및 믹싱
│   │   ├── thumbnail_engine.py # 1080x1920 AI 썸네일 생성기
│   │   ├── video_engine.py   # FFmpeg 9:16 세로 비디오 합성 파이프라인
│   │   ├── ypp_compliance.py # YPP 수익화 정책 준수 검수기
│   │   └── publisher.py      # 유튜브 예약 발행 및 스케줄러
│   └── static/
│       ├── index.html        # 모던 웹 대시보드 UI
│       ├── css/style.css     # 다크 테마 Glassmorphism 스타일
│       └── js/app.js         # 실시간 렌더링 모니터링 및 대시보드 로직
├── output/                   # 생성된 결과물 (비디오, 썸네일, 음성, 자막)
│   ├── videos/
│   ├── thumbnails/
│   ├── audio/
│   └── subtitles/
├── run.py                    # 실행 스크립트
├── start.bat                 # 윈도우 원클릭 배치 파일
└── README.md                 # 제품 문서
```

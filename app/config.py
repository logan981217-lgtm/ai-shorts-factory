import os
from pathlib import Path
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"

IS_VERCEL = bool(os.environ.get("VERCEL")) or not os.access(str(BASE_DIR), os.W_OK)

if IS_VERCEL:
    DATA_DIR = Path("/tmp")
else:
    DATA_DIR = BASE_DIR

OUTPUT_DIR = DATA_DIR / "output"
TEMP_DIR = DATA_DIR / "temp"
DB_PATH = DATA_DIR / "ai_shorts_factory.db"

VIDEOS_DIR = OUTPUT_DIR / "videos"
THUMBNAILS_DIR = OUTPUT_DIR / "thumbnails"
AUDIO_DIR = OUTPUT_DIR / "audio"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"

for d in [OUTPUT_DIR, TEMP_DIR, VIDEOS_DIR, THUMBNAILS_DIR, AUDIO_DIR, SUBTITLES_DIR]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

# FFmpeg binary
try:
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = "ffmpeg"

# Fonts for subtitle and thumbnail rendering
FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgunbd.ttf",
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/gulim.ttc",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
DEFAULT_FONT_PATH = None
for f in FONT_CANDIDATES:
    if os.path.exists(f):
        DEFAULT_FONT_PATH = f
        break

# Default Server Settings
HOST = "127.0.0.1"
PORT = 8000

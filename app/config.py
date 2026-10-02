import os
from pathlib import Path
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

VIDEOS_DIR = OUTPUT_DIR / "videos"
THUMBNAILS_DIR = OUTPUT_DIR / "thumbnails"
AUDIO_DIR = OUTPUT_DIR / "audio"
SUBTITLES_DIR = OUTPUT_DIR / "subtitles"

for d in [OUTPUT_DIR, TEMP_DIR, VIDEOS_DIR, THUMBNAILS_DIR, AUDIO_DIR, SUBTITLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "ai_shorts_factory.db"

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
]
DEFAULT_FONT_PATH = "C:/Windows/Fonts/malgunbd.ttf"
for f in FONT_CANDIDATES:
    if os.path.exists(f):
        DEFAULT_FONT_PATH = f
        break

# Default Server Settings
HOST = "127.0.0.1"
PORT = 8000

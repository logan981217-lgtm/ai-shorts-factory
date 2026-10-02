import uvicorn
import os
import sys
import webbrowser
from threading import Timer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from app.config import HOST, PORT

def open_browser():
    try:
        webbrowser.open(f"http://{HOST}:{PORT}")
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print("⚡ AI YouTube Shorts Automated Factory (쇼츠 자동 제작 공장)")
    print(f"🚀 Server running on: http://{HOST}:{PORT}")
    print("=" * 60)
    
    # Automatically open browser after 1.5 seconds
    Timer(1.5, open_browser).start()
    
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)

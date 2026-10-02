import os
import sys
from pathlib import Path

# Add project root to sys.path so 'app' can be found
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.main import app
from starlette.types import ASGIApp, Scope, Receive, Send

class VercelPathMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            matched_path = headers.get(b"x-matched-path")
            if matched_path:
                scope["path"] = matched_path.decode("utf-8")
        await self.app(scope, receive, send)

app.add_middleware(VercelPathMiddleware)

handler = app

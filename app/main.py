import os
import sys
import uuid
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import (
    APP_DIR, OUTPUT_DIR, VIDEOS_DIR, THUMBNAILS_DIR, AUDIO_DIR, SUBTITLES_DIR, TEMP_DIR
)
from app.database import (
    init_db, get_stats, list_projects, get_project, create_project,
    update_project, delete_project, get_all_settings, save_setting
)
from app.services.script_engine import ScriptEngine
from app.services.tts_engine import TTSEngine, AVAILABLE_VOICES
from app.services.bgm_engine import BGMEngine, BGM_PRESETS
from app.services.thumbnail_engine import ThumbnailEngine
from app.services.video_engine import VideoEngine, SUBTITLE_STYLES
from app.services.ypp_compliance import YPPComplianceEngine
from app.services.publisher import YouTubePublisher

# Initialize Database
init_db()

# Initialize Engines
script_engine = ScriptEngine()
tts_engine = TTSEngine()
bgm_engine = BGMEngine()
thumbnail_engine = ThumbnailEngine()
video_engine = VideoEngine()
ypp_engine = YPPComplianceEngine()
publisher = YouTubePublisher()

app = FastAPI(
    title="AI Shorts Factory API",
    description="Enterprise-grade AI YouTube Shorts Automated Factory",
    version="1.0.0"
)
handler = app

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static and Output files
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
except Exception as e:
    print(f"Warning: could not mount /output: {e}")

# Background rendering pipeline worker
async def run_project_generation_task(project_id: str, custom_image_path: Optional[str] = None):
    try:
        proj = get_project(project_id)
        if not proj:
            return

        topic = proj["topic"]
        duration_target = proj.get("duration_target", 30)
        voice_id = proj.get("voice_id", "ko-KR-SunHiNeural")
        subtitle_style = proj.get("subtitle_style", "modern_yellow")
        bgm_style = proj.get("bgm_style", "energetic")

        # 1. Script Generation (if not already provided)
        update_project(project_id, {"status": "scripting", "progress": 15})
        if not proj.get("script_hook") or not proj.get("script_body"):
            script_data = script_engine.generate_script(topic, duration=duration_target)
            hook = script_data["hook"]
            body = script_data["body"]
            cta = script_data["cta"]
            yt_title = script_data["yt_title"]
            yt_desc = script_data["yt_description"]
            yt_tags = ", ".join(script_data["yt_tags"]) if isinstance(script_data["yt_tags"], list) else script_data["yt_tags"]
            full_script = f"{hook} {body} {cta}"
            update_project(project_id, {
                "title": yt_title,
                "script_hook": hook,
                "script_body": body,
                "script_cta": cta,
                "full_script": full_script,
                "yt_title": yt_title,
                "yt_description": yt_desc,
                "yt_tags": yt_tags,
                "progress": 30
            })
        else:
            hook = proj["script_hook"]
            body = proj["script_body"]
            cta = proj["script_cta"]
            yt_title = proj.get("yt_title", proj.get("title", topic))
            full_script = proj.get("full_script") or f"{hook} {body} {cta}"

        # 2. YPP Compliance Check
        script_dict = {"hook": hook, "body": body, "cta": cta}
        ypp_res = ypp_engine.evaluate_compliance(topic, script_dict, bgm_style=bgm_style)
        update_project(project_id, {
            "ypp_score": ypp_res["score"],
            "ypp_analysis": json.dumps(ypp_res, ensure_ascii=False),
            "progress": 40
        })

        # 3. TTS Speech and Subtitles
        update_project(project_id, {"status": "tts_generating", "progress": 50})
        tts_res = await tts_engine.generate_speech_and_subtitles(
            project_id=project_id,
            script_text=full_script,
            voice_id=voice_id
        )
        audio_path = tts_res["audio_path"]
        srt_path = tts_res["srt_path"]
        duration_actual = tts_res["duration"]

        update_project(project_id, {
            "audio_path": audio_path,
            "srt_path": srt_path,
            "duration_actual": duration_actual,
            "progress": 65
        })

        # 4. Thumbnail Generation
        thumb_path = thumbnail_engine.generate_thumbnail(project_id, topic, yt_title)
        update_project(project_id, {
            "thumbnail_path": thumb_path,
            "progress": 75,
            "status": "rendering"
        })

        # 5. 9:16 Video Rendering Pipeline
        def progress_cb(pct: int, msg: str):
            update_project(project_id, {"progress": 75 + int(pct * 0.24)})

        video_path = video_engine.render_shorts_video(
            project_id=project_id,
            topic=topic,
            title=yt_title,
            audio_path=audio_path,
            srt_path=srt_path,
            duration=duration_actual,
            subtitle_style=subtitle_style,
            bgm_style=bgm_style,
            source_image_path=custom_image_path,
            progress_callback=progress_cb
        )

        update_project(project_id, {
            "video_path": video_path,
            "status": "completed",
            "progress": 100,
            "error_message": None
        })

    except Exception as e:
        print(f"[Worker] Pipeline failed for {project_id}: {e}")
        update_project(project_id, {
            "status": "failed",
            "error_message": str(e)
        })

# --- Pydantic Request Models ---
class ProjectCreateRequest(BaseModel):
    topic: str
    duration_target: Optional[int] = 30
    voice_id: Optional[str] = "ko-KR-SunHiNeural"
    subtitle_style: Optional[str] = "modern_yellow"
    bgm_style: Optional[str] = "energetic"
    custom_script: Optional[Dict[str, str]] = None

class ScriptPreviewRequest(BaseModel):
    topic: str
    duration: Optional[int] = 30
    niche: Optional[str] = "일반"

class ProjectScheduleRequest(BaseModel):
    channel_name: Optional[str] = "AI Shorts Studio"
    target_time: Optional[str] = None

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    channel_name: Optional[str] = None
    default_voice: Optional[str] = None
    default_duration: Optional[str] = None
    auto_pilot_enabled: Optional[str] = None
    daily_publish_time: Optional[str] = None

# --- API Routes ---

@app.get("/")
def serve_index():
    return FileResponse(APP_DIR / "static" / "index.html")

@app.get("/api/stats")
def api_get_stats():
    return get_stats()

@app.get("/api/projects")
def api_list_projects():
    projects = list_projects(50)
    for p in projects:
        p_id = p["id"]
        # Add accessible web URLs for assets
        p["video_url"] = f"/output/videos/{p_id}.mp4" if p.get("video_path") and os.path.exists(p["video_path"]) else None
        p["thumbnail_url"] = f"/output/thumbnails/{p_id}.jpg" if p.get("thumbnail_path") and os.path.exists(p["thumbnail_path"]) else None
        p["audio_url"] = f"/output/audio/{p_id}.mp3" if p.get("audio_path") and os.path.exists(p["audio_path"]) else None
        p["srt_url"] = f"/output/subtitles/{p_id}.srt" if p.get("srt_path") and os.path.exists(p["srt_path"]) else None
    return projects

@app.get("/api/projects/{project_id}")
def api_get_project(project_id: str):
    p = get_project(project_id)
    if not p:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    p["video_url"] = f"/output/videos/{project_id}.mp4" if p.get("video_path") and os.path.exists(p["video_path"]) else None
    p["thumbnail_url"] = f"/output/thumbnails/{project_id}.jpg" if p.get("thumbnail_path") and os.path.exists(p["thumbnail_path"]) else None
    p["audio_url"] = f"/output/audio/{project_id}.mp3" if p.get("audio_path") and os.path.exists(p["audio_path"]) else None
    p["srt_url"] = f"/output/subtitles/{project_id}.srt" if p.get("srt_path") and os.path.exists(p["srt_path"]) else None
    return p

@app.post("/api/projects/preview-script")
def api_preview_script(req: ScriptPreviewRequest):
    """Instant AI script generation preview without running video render"""
    res = script_engine.generate_script(req.topic, duration=req.duration or 30, niche=req.niche or "일반")
    return res

@app.post("/api/projects/create")
async def api_create_project(
    req: ProjectCreateRequest,
    background_tasks: BackgroundTasks
):
    project_id = str(uuid.uuid4())[:8]
    data = {
        "id": project_id,
        "title": req.topic,
        "topic": req.topic,
        "duration_target": req.duration_target or 30,
        "voice_id": req.voice_id or "ko-KR-SunHiNeural",
        "subtitle_style": req.subtitle_style or "modern_yellow",
        "bgm_style": req.bgm_style or "energetic",
        "status": "pending",
        "progress": 5
    }
    
    if req.custom_script:
        data["script_hook"] = req.custom_script.get("hook", "")
        data["script_body"] = req.custom_script.get("body", "")
        data["script_cta"] = req.custom_script.get("cta", "")
        data["full_script"] = f"{data['script_hook']} {data['script_body']} {data['script_cta']}"
        if req.custom_script.get("title"):
            data["title"] = req.custom_script.get("title")
            data["yt_title"] = req.custom_script.get("title")

    create_project(data)
    
    # Launch background async render task
    background_tasks.add_task(run_project_generation_task, project_id)

    return {"project_id": project_id, "status": "started", "message": "쇼츠 자동 제작이 시작되었습니다!"}

@app.post("/api/projects/create-with-image")
async def api_create_with_image(
    background_tasks: BackgroundTasks,
    topic: str = Form(...),
    duration_target: int = Form(30),
    voice_id: str = Form("ko-KR-SunHiNeural"),
    subtitle_style: str = Form("modern_yellow"),
    bgm_style: str = Form("energetic"),
    image: Optional[UploadFile] = File(None)
):
    project_id = str(uuid.uuid4())[:8]
    custom_img_path = None
    
    if image:
        upload_ext = Path(image.filename).suffix or ".jpg"
        custom_img_path = str(TEMP_DIR / f"upload_{project_id}{upload_ext}")
        with open(custom_img_path, "wb") as f:
            content = await image.read()
            f.write(content)

    data = {
        "id": project_id,
        "title": topic,
        "topic": topic,
        "duration_target": duration_target,
        "voice_id": voice_id,
        "subtitle_style": subtitle_style,
        "bgm_style": bgm_style,
        "status": "pending",
        "progress": 5
    }
    create_project(data)
    background_tasks.add_task(run_project_generation_task, project_id, custom_img_path)

    return {"project_id": project_id, "status": "started"}

@app.delete("/api/projects/{project_id}")
def api_delete_project(project_id: str):
    delete_project(project_id)
    return {"success": True, "message": "프로젝트가 삭제되었습니다."}

@app.post("/api/projects/{project_id}/schedule")
def api_schedule_project(project_id: str, req: ProjectScheduleRequest):
    res = publisher.schedule_project(project_id, req.channel_name or "AI Shorts Studio", req.target_time)
    return res

@app.post("/api/projects/{project_id}/publish-now")
def api_publish_now(project_id: str):
    res = publisher.simulate_or_publish_now(project_id)
    return res

@app.get("/api/schedules")
def api_list_schedules():
    return publisher.list_schedules()

@app.get("/api/options")
def api_get_options():
    return {
        "voices": AVAILABLE_VOICES,
        "subtitle_styles": [
            {"id": k, "name": v["name"]} for k, v in SUBTITLE_STYLES.items()
        ],
        "bgm_presets": BGM_PRESETS
    }

@app.get("/api/settings")
def api_get_settings():
    return get_all_settings()

@app.post("/api/settings")
def api_update_settings(req: SettingsUpdateRequest):
    if req.gemini_api_key is not None:
        save_setting("gemini_api_key", req.gemini_api_key)
    if req.channel_name is not None:
        save_setting("channel_name", req.channel_name)
    if req.default_voice is not None:
        save_setting("default_voice", req.default_voice)
    if req.default_duration is not None:
        save_setting("default_duration", req.default_duration)
    if req.auto_pilot_enabled is not None:
        save_setting("auto_pilot_enabled", req.auto_pilot_enabled)
    if req.daily_publish_time is not None:
        save_setting("daily_publish_time", req.daily_publish_time)
    return {"success": True, "settings": get_all_settings()}

@app.post("/api/auto-pilot/trigger")
async def api_trigger_autopilot(background_tasks: BackgroundTasks):
    """
    Auto-Pilot: Automatically generates a trending Shorts video and schedules it!
    """
    import random
    trending_topics = [
        "2026년 상위 1%가 실천하는 아침 10분 돈 버는 습관",
        "인공지능 AI 시대에 살아남는 필수 직무 역량",
        "역사상 가장 미스터리한 실종 사건의 소름 돋는 진실",
        "직장인 스트레스 90%를 날려버리는 마인드셋 3가지",
        "스마트폰 배터리 수명을 2배 늘리는 숨겨진 비밀 설정",
        "부자들이 절대 사지 않는 3가지 낭비 습관"
    ]
    chosen_topic = random.choice(trending_topics)
    project_id = str(uuid.uuid4())[:8]

    data = {
        "id": project_id,
        "title": f"[Auto-Pilot] {chosen_topic}",
        "topic": chosen_topic,
        "duration_target": 30,
        "voice_id": "ko-KR-SunHiNeural",
        "subtitle_style": "modern_yellow",
        "bgm_style": "energetic",
        "status": "pending",
        "progress": 5
    }
    create_project(data)
    background_tasks.add_task(run_project_generation_task, project_id)

    return {
        "success": True,
        "project_id": project_id,
        "topic": chosen_topic,
        "message": f"오토파일럿 가동: '{chosen_topic}' 자동 제작이 시작되었습니다!"
    }

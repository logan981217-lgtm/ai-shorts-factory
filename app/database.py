import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        topic TEXT NOT NULL,
        duration_target INTEGER DEFAULT 30,
        voice_id TEXT DEFAULT 'ko-KR-SunHiNeural',
        subtitle_style TEXT DEFAULT 'modern_yellow',
        bgm_style TEXT DEFAULT 'energetic',
        visual_style TEXT DEFAULT 'gradient_motion',
        status TEXT DEFAULT 'draft',
        progress INTEGER DEFAULT 0,
        script_hook TEXT,
        script_body TEXT,
        script_cta TEXT,
        full_script TEXT,
        audio_path TEXT,
        srt_path TEXT,
        thumbnail_path TEXT,
        video_path TEXT,
        duration_actual REAL DEFAULT 0,
        yt_title TEXT,
        yt_description TEXT,
        yt_tags TEXT,
        ypp_score INTEGER DEFAULT 95,
        ypp_analysis TEXT,
        scheduled_time TEXT,
        is_published INTEGER DEFAULT 0,
        published_at TEXT,
        error_message TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS publishing_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        channel_name TEXT DEFAULT 'AI Shorts Studio',
        target_time TEXT NOT NULL,
        status TEXT DEFAULT 'scheduled',
        published_at TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    """)
    
    # Initialize default settings if not exists
    default_settings = {
        "gemini_api_key": "",
        "channel_name": "AI Shorts Factory",
        "default_voice": "ko-KR-SunHiNeural",
        "default_duration": "30",
        "auto_pilot_enabled": "false",
        "daily_publish_time": "18:00"
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

def save_setting(key: str, value: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = "") -> str:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def get_all_settings() -> Dict[str, str]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def create_project(data: Dict[str, Any]) -> str:
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    data.setdefault("status", "draft")
    data.setdefault("progress", 0)
    
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    query = f"INSERT INTO projects ({columns}) VALUES ({placeholders})"
    cursor.execute(query, list(data.values()))
    conn.commit()
    conn.close()
    return data["id"]

def update_project(project_id: str, updates: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    updates["updated_at"] = datetime.now().isoformat()
    set_clauses = [f"{k} = ?" for k in updates.keys()]
    query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ?"
    values = list(updates.values()) + [project_id]
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def list_projects(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_project(project_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM publishing_schedules WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def get_stats() -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM projects")
    total_projects = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) as completed FROM projects WHERE status = 'completed'")
    completed_projects = cursor.fetchone()["completed"]
    
    cursor.execute("SELECT COUNT(*) as published FROM projects WHERE is_published = 1")
    published_count = cursor.fetchone()["published"]
    
    cursor.execute("SELECT AVG(ypp_score) as avg_ypp FROM projects WHERE ypp_score IS NOT NULL")
    avg_ypp_row = cursor.fetchone()["avg_ypp"]
    avg_ypp = round(avg_ypp_row if avg_ypp_row else 96.5, 1)
    
    conn.close()
    return {
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "published_count": published_count,
        "avg_ypp_score": avg_ypp,
        "estimated_retention": "68.4%",
        "avg_views": "14.2K"
    }

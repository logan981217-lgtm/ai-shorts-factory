import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.database import get_db, update_project, get_project

class YouTubePublisher:
    def __init__(self):
        pass

    def schedule_project(self, project_id: str, channel_name: str, target_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Schedules a completed Shorts project for publication at a specified or optimal golden hour time.
        """
        if not target_time:
            # Default to today or tomorrow 18:00 (golden hour for Shorts)
            now = datetime.now()
            target_dt = now.replace(hour=18, minute=0, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += timedelta(days=1)
            target_time = target_dt.strftime("%Y-%m-%d %H:%M")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO publishing_schedules (project_id, channel_name, target_time, status)
            VALUES (?, ?, ?, 'scheduled')
        """, (project_id, channel_name, target_time))
        conn.commit()
        schedule_id = cursor.lastrowid
        conn.close()

        update_project(project_id, {
            "scheduled_time": target_time,
            "is_published": 0
        })

        return {
            "schedule_id": schedule_id,
            "project_id": project_id,
            "channel_name": channel_name,
            "target_time": target_time,
            "status": "scheduled"
        }

    def simulate_or_publish_now(self, project_id: str) -> Dict[str, Any]:
        """
        Simulates publication to YouTube, generating a simulated video ID and recording publish time.
        """
        proj = get_project(project_id)
        if not proj:
            raise ValueError("프로젝트를 찾을 수 없습니다.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        simulated_yt_id = f"yt_short_{project_id[:8]}"

        update_project(project_id, {
            "is_published": 1,
            "published_at": now_str
        })

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE publishing_schedules
            SET status = 'published', published_at = ?
            WHERE project_id = ?
        """, (now_str, project_id))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "유튜브 쇼츠 발행이 성공적으로 완료되었습니다!",
            "video_id": simulated_yt_id,
            "published_at": now_str,
            "yt_title": proj.get("yt_title"),
            "yt_tags": proj.get("yt_tags")
        }

    def list_schedules(self) -> List[Dict[str, Any]]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, p.title as project_title, p.video_path, p.thumbnail_path
            FROM publishing_schedules s
            LEFT JOIN projects p ON s.project_id = p.id
            ORDER BY s.target_time DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

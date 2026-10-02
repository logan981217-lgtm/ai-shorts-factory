import os
import shutil
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from PIL import Image, ImageDraw, ImageFont
from app.config import (
    FFMPEG_EXE, VIDEOS_DIR, TEMP_DIR, DEFAULT_FONT_PATH
)
from app.services.bgm_engine import BGMEngine

SUBTITLE_STYLES = {
    "modern_yellow": {
        "name": "모던 옐로우 (추천)",
        "font_size": 62,
        "primary_color": "&H0000FFFF",  # Yellow in BBGGRR
        "outline_color": "&H00000000",  # Black
        "back_color": "&H80000000",
        "border_style": 1,
        "outline": 4,
        "shadow": 2
    },
    "neon_cyan": {
        "name": "네온 시안",
        "font_size": 62,
        "primary_color": "&H00FFFF00",  # Cyan in BBGGRR
        "outline_color": "&H00000000",  # Black
        "back_color": "&H80000000",
        "border_style": 1,
        "outline": 4,
        "shadow": 2
    },
    "clean_white": {
        "name": "볼드 화이트",
        "font_size": 64,
        "primary_color": "&H00FFFFFF",  # White
        "outline_color": "&H00000000",  # Black
        "back_color": "&H80000000",
        "border_style": 1,
        "outline": 4,
        "shadow": 2
    },
    "box_black": {
        "name": "자막 박스 배경",
        "font_size": 58,
        "primary_color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&HB0000000",     # Dark Box
        "border_style": 3,
        "outline": 1,
        "shadow": 0
    }
}

class VideoEngine:
    def __init__(self):
        self.bgm_engine = BGMEngine()

    def srt_to_ass(self, srt_path: str, ass_path: str, style_name: str = "modern_yellow") -> str:
        """Converts SRT subtitles to highly-styled YouTube Shorts ASS format"""
        style = SUBTITLE_STYLES.get(style_name, SUBTITLE_STYLES["modern_yellow"])
        
        ass_header = f"""[Script Info]
Title: AI YouTube Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Malgun Gothic,{style['font_size']},{style['primary_color']},&H000000FF,{style['outline_color']},{style['back_color']},-1,0,0,0,100,100,0,0,{style['border_style']},{style['outline']},{style['shadow']},2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        # Parse SRT
        dialogues = []
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = re.compile(
            r'(\d+)\s*\n'
            r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n'
            r'([\s\S]*?)(?=\n\s*\d+\s*\n|\Z)',
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            _, start_str, end_str, text_str = match.groups()
            text_clean = text_str.strip().replace("\n", " ")
            if not text_clean:
                continue
            
            # Format timestamp for ASS: H:MM:SS.cs
            start_ass = self._format_ass_time(start_str)
            end_ass = self._format_ass_time(end_str)
            
            dialogues.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text_clean}")

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_header + "\n".join(dialogues) + "\n")

        return ass_path

    def _format_ass_time(self, srt_time: str) -> str:
        # 00:00:01,850 -> 0:00:01.85
        t = srt_time.replace(",", ".")
        parts = t.split(":")
        hours = int(parts[0])
        minutes = parts[1]
        seconds_and_ms = parts[2]
        secs = float(seconds_and_ms)
        return f"{hours}:{minutes}:{secs:05.2f}"

    def create_backdrop_image(self, topic: str, title: str, output_path: str) -> str:
        """
        Creates a crisp 1080x1920 base backdrop with branding header and dynamic ambiance
        """
        w, h = 1080, 1920
        img = Image.new("RGB", (w, h), (18, 22, 34))
        draw = ImageDraw.Draw(img)

        # Smooth vertical dark gradient
        for y in range(h):
            ratio = y / h
            r = int(14 * (1 - ratio) + 26 * ratio)
            g = int(18 * (1 - ratio) + 20 * ratio)
            b = int(32 * (1 - ratio) + 48 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        # Ambient radiant glow at center
        from PIL import ImageFilter
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        center_y = int(h * 0.42)
        
        # Color accent based on topic
        if any(k in topic for k in ["돈", "재테크", "주식"]):
            glow_color = (255, 215, 0, 45)
            badge_icon = "💰 2026 재테크 핵심"
        elif any(k in topic for k in ["역사", "미스터리", "비밀"]):
            glow_color = (255, 60, 60, 45)
            badge_icon = "🕵️ 아무도 모르는 진실"
        elif any(k in topic for k in ["AI", "테크", "기술"]):
            glow_color = (0, 220, 255, 45)
            badge_icon = "⚡ 2026 AI 테크 리포트"
        else:
            glow_color = (120, 90, 255, 45)
            badge_icon = "💡 30초 순삭 핵심 꿀팁"

        gdraw.ellipse([(w//2 - 380, center_y - 380), (w//2 + 380, center_y + 380)], fill=glow_color)
        glow = glow.filter(ImageFilter.GaussianBlur(90))
        img.paste(glow, (0, 0), glow)
        draw = ImageDraw.Draw(img)

        # Top Header Safe Zone Badge (Y=180)
        try:
            badge_font = ImageFont.truetype(DEFAULT_FONT_PATH, 40)
            topic_font = ImageFont.truetype(DEFAULT_FONT_PATH, 52)
        except Exception:
            badge_font = ImageFont.load_default()
            topic_font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), badge_icon, font=badge_font)
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bx = (w - bw) // 2
        by = 220

        draw.rounded_rectangle(
            [(bx - 30, by - 14), (bx + bw + 30, by + bh + 14)],
            radius=20,
            fill=(30, 36, 52),
            outline=(255, 255, 255, 60),
            width=2
        )
        draw.text((bx, by), badge_icon, font=badge_font, fill=(255, 255, 255))

        # Clean short topic header under badge
        short_topic = topic[:20] + ("..." if len(topic) > 20 else "")
        tbox = draw.textbbox((0, 0), short_topic, font=topic_font)
        tw = tbox[2] - tbox[0]
        draw.text(((w - tw) // 2, by + bh + 45), short_topic, font=topic_font, fill=(200, 220, 255))

        img.save(output_path, "JPEG", quality=95)
        return output_path

    def render_shorts_video(
        self,
        project_id: str,
        topic: str,
        title: str,
        audio_path: str,
        srt_path: str,
        duration: float,
        subtitle_style: str = "modern_yellow",
        bgm_style: str = "energetic",
        source_image_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        Renders complete 9:16 (1080x1920) YouTube Shorts MP4 with:
        - Dynamic background motion (Ken Burns zoom / pan)
        - Narration TTS audio
        - BGM audio with volume ducking
        - Styled ASS Subtitles in Safe Zone
        - Progress bar animation
        """
        if progress_callback:
            progress_callback(10, "비디오 배경 및 스타일 에셋 구성 중...")

        # Create unique temp render dir
        render_dir = TEMP_DIR / project_id
        render_dir.mkdir(parents=True, exist_ok=True)

        backdrop_filename = "backdrop.jpg"
        backdrop_path = str(render_dir / backdrop_filename)
        
        if source_image_path and os.path.exists(source_image_path):
            # Use user uploaded image cropped to 1080x1920
            self._crop_image_to_shorts(source_image_path, backdrop_path)
        else:
            self.create_backdrop_image(topic, title, backdrop_path)

        if progress_callback:
            progress_callback(30, "자막 스타일 및 타임스탬프 변환 중...")

        ass_filename = "subtitles.ass"
        ass_path = str(render_dir / ass_filename)
        self.srt_to_ass(srt_path, ass_path, subtitle_style)

        if progress_callback:
            progress_callback(50, "BGM 음원 매칭 및 오디오 믹싱 준비 중...")

        bgm_path = self.bgm_engine.get_bgm_path(bgm_style)

        # Output video file
        out_filename = f"{project_id}.mp4"
        final_video_path = str(VIDEOS_DIR / out_filename)

        if progress_callback:
            progress_callback(70, "FFmpeg 9:16 고화질 쇼츠 렌더링 중...")

        # Build FFmpeg command with relative file names inside render_dir
        # Zoompan filter creates gentle dynamic zoom effect (Ken Burns effect)
        # Top progress bar indicates video timeline
        fps = 30
        total_frames = int(duration * fps) + 1
        
        # Audio filter: Mix voice and looped low-volume BGM
        if bgm_path and os.path.exists(bgm_path):
            shutil.copy2(bgm_path, str(render_dir / "bgm.wav"))
            shutil.copy2(audio_path, str(render_dir / "voice.mp3"))

            # Filter complex:
            # [0:v] zoompan (gentle zoom in), draw animated red progress bar at top, overlay ASS subtitles
            # [1:a] voice
            # [2:a] bgm with volume 0.12 and loop
            filter_complex = (
                f"[0:v]zoompan=z='min(zoom+0.0005,1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
                f"drawbox=y=0:x=0:w='1080*(t/{duration})':h=8:color=red@0.9:t=fill,"
                f"ass={ass_filename}[v];"
                f"[2:a]aloop=loop=-1:size=2e+09,volume=0.12[bgm];"
                f"[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]"
            )

            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", backdrop_filename,
                "-i", "voice.mp3",
                "-i", "bgm.wav",
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                out_filename
            ]
        else:
            shutil.copy2(audio_path, str(render_dir / "voice.mp3"))
            filter_complex = (
                f"[0:v]zoompan=z='min(zoom+0.0005,1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},"
                f"drawbox=y=0:x=0:w='1080*(t/{duration})':h=8:color=red@0.9:t=fill,"
                f"ass={ass_filename}[v]"
            )
            cmd = [
                FFMPEG_EXE, "-y",
                "-loop", "1", "-i", backdrop_filename,
                "-i", "voice.mp3",
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "1:a",
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                out_filename
            ]

        # Execute FFmpeg inside render_dir
        res = subprocess.run(
            cmd,
            cwd=str(render_dir),
            capture_output=True,
            text=True,
            errors="ignore"
        )

        if res.returncode != 0:
            print(f"[VideoEngine] FFmpeg render failed:\n{res.stderr[-1000:]}")
            raise RuntimeError(f"FFmpeg error: {res.stderr[-400:]}")

        rendered_temp_mp4 = render_dir / out_filename
        if rendered_temp_mp4.exists():
            shutil.move(str(rendered_temp_mp4), final_video_path)

        # Cleanup temp directory
        try:
            shutil.rmtree(str(render_dir), ignore_errors=True)
        except Exception:
            pass

        if progress_callback:
            progress_callback(100, "쇼츠 렌더링 완료!")

        return final_video_path

    def _crop_image_to_shorts(self, input_img: str, output_img: str):
        """Crops or resizes image to exact 1080x1920 9:16 aspect ratio"""
        with Image.open(input_img) as im:
            im = im.convert("RGB")
            target_ratio = 1080 / 1920
            cur_ratio = im.width / im.height
            if cur_ratio > target_ratio:
                # Wider: crop width
                new_w = int(im.height * target_ratio)
                left = (im.width - new_w) // 2
                im = im.crop((left, 0, left + new_w, im.height))
            else:
                # Taller: crop height
                new_h = int(im.width / target_ratio)
                top = (im.height - new_h) // 2
                im = im.crop((0, top, im.width, top + new_h))
            im = im.resize((1080, 1920), Image.Resampling.LANCZOS)
            im.save(output_img, "JPEG", quality=95)

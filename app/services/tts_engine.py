import os
import asyncio
import edge_tts
from typing import Dict, Any, List, Tuple
from app.config import AUDIO_DIR, SUBTITLES_DIR

AVAILABLE_VOICES = [
    {"id": "ko-KR-SunHiNeural", "name": "선희 (한국어 여성 - 밝고 스마트한 톤)", "lang": "ko"},
    {"id": "ko-KR-InJoonNeural", "name": "인준 (한국어 남성 - 신뢰감 있는 톤)", "lang": "ko"},
    {"id": "ko-KR-HyunsuNeural", "name": "현수 (한국어 남성 - 친근하고 빠른 톤)", "lang": "ko"},
    {"id": "en-US-ChristopherNeural", "name": "Christopher (영어 남성 - 내레이션)", "lang": "en"},
    {"id": "en-US-JennyNeural", "name": "Jenny (영어 여성 - 감성적/자연스러움)", "lang": "en"}
]

class TTSEngine:
    def __init__(self):
        pass

    async def generate_speech_and_subtitles(
        self,
        project_id: str,
        script_text: str,
        voice_id: str = "ko-KR-SunHiNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> Dict[str, Any]:
        """
        Synthesizes script into MP3 and generates synchronized SRT subtitles and word cues.
        """
        audio_filename = f"{project_id}.mp3"
        srt_filename = f"{project_id}.srt"
        
        audio_path = str(AUDIO_DIR / audio_filename)
        srt_path = str(SUBTITLES_DIR / srt_filename)

        communicate = edge_tts.Communicate(
            text=script_text,
            voice=voice_id,
            rate=rate,
            pitch=pitch
        )
        sub_maker = edge_tts.SubMaker()

        with open(audio_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    sub_maker.feed(chunk)

        # Generate SRT string
        srt_content = sub_maker.get_srt()
        
        # If edge-tts produced empty SRT cues, generate sentence-based timestamps fallback
        if not srt_content.strip():
            srt_content = self._generate_fallback_srt(script_text, audio_path)

        with open(srt_path, "w", encoding="utf-8") as srt_file:
            srt_file.write(srt_content)

        # Calculate exact audio duration using mutagen or ffmpeg probe
        duration = self._get_audio_duration(audio_path)

        return {
            "audio_path": audio_path,
            "srt_path": srt_path,
            "duration": duration,
            "srt_content": srt_content
        }

    def _get_audio_duration(self, audio_path: str) -> float:
        import subprocess
        from app.config import FFMPEG_EXE
        try:
            # Run ffprobe / ffmpeg to get duration
            cmd = [
                FFMPEG_EXE,
                "-i", audio_path,
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, errors="ignore")
            # Parse Duration: 00:00:15.34
            import re
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
            if m:
                hours, minutes, seconds = map(float, m.groups())
                return hours * 3600 + minutes * 60 + seconds
        except Exception as e:
            print(f"[TTSEngine] Error getting duration: {e}")
        return 30.0

    def _generate_fallback_srt(self, text: str, audio_path: str) -> str:
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        duration = self._get_audio_duration(audio_path)
        if not sentences:
            sentences = [text]
        
        time_per_sentence = duration / len(sentences)
        srt_lines = []
        for i, s in enumerate(sentences):
            start = i * time_per_sentence
            end = (i + 1) * time_per_sentence
            start_str = self._format_srt_timestamp(start)
            end_str = self._format_srt_timestamp(end)
            srt_lines.append(f"{i + 1}\n{start_str} --> {end_str}\n{s}.\n")
        return "\n".join(srt_lines)

    def _format_srt_timestamp(self, seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

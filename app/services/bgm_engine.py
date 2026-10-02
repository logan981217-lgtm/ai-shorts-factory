import os
import math
import wave
import struct
import numpy as np
from pathlib import Path
from typing import Dict, Any
from app.config import APP_DIR

BGM_DIR = APP_DIR / "static" / "assets" / "bgm"
BGM_DIR.mkdir(parents=True, exist_ok=True)

BGM_PRESETS = [
    {"id": "energetic", "name": "🔥 활기찬 텐션 비트 (Energetic Beat)", "desc": "트렌드, 꿀팁, 동기부여 영상에 적합"},
    {"id": "calm_lofi", "name": "☕ 차분한 로파이 (Chill Lo-Fi)", "desc": "직장인 힐링, 심리, 서정적 스토리에 적합"},
    {"id": "mysterious", "name": "🕵️ 미스터리 긴장감 (Mystery Ambient)", "desc": "충격 실화, 역사 비밀, 괴담에 적합"},
    {"id": "cyberpunk", "name": "⚡ 미래 테크 & 사이버 (Cyber Synth)", "desc": "AI, 과학, 신기술, 암호화폐에 적합"},
    {"id": "none", "name": "🔇 BGM 없음 (나레이션만)", "desc": "음성 전달력만을 극대화"}
]

class BGMEngine:
    def __init__(self):
        self._ensure_default_bgm_files()

    def get_bgm_path(self, style: str) -> str:
        if style == "none":
            return ""
        filepath = BGM_DIR / f"{style}.wav"
        if not filepath.exists():
            self._generate_preset_bgm(style, str(filepath))
        return str(filepath)

    def _ensure_default_bgm_files(self):
        for preset in BGM_PRESETS:
            pid = preset["id"]
            if pid != "none":
                path = BGM_DIR / f"{pid}.wav"
                if not path.exists():
                    self._generate_preset_bgm(pid, str(path))

    def _generate_preset_bgm(self, style: str, output_path: str, duration: int = 65):
        """Synthesize pleasant royalty-free ambient chord progression loop"""
        sample_rate = 44100
        n_samples = sample_rate * duration
        t = np.linspace(0, duration, n_samples, endpoint=False)
        
        # Audio buffer (stereo)
        left = np.zeros(n_samples, dtype=np.float32)
        right = np.zeros(n_samples, dtype=np.float32)

        if style == "energetic":
            # Upbeat chord progression (C - G - Am - F) with rhythmic pulse
            bpm = 120
            beat_duration = 60.0 / bpm
            chords = [
                [261.63, 329.63, 392.00],  # C
                [196.00, 246.94, 293.66],  # G
                [220.00, 261.63, 329.63],  # Am
                [174.61, 220.00, 261.63]   # F
            ]
            for i, chord in enumerate(chords):
                chord_start = i * (beat_duration * 4)
                chord_end = (i + 1) * (beat_duration * 4)
                # Loop across duration
                for cycle in range(int(duration / (beat_duration * 16)) + 2):
                    t_start = cycle * (beat_duration * 16) + chord_start
                    t_end = cycle * (beat_duration * 16) + chord_end
                    mask = (t >= t_start) & (t < t_end) & (t < duration)
                    if np.any(mask):
                        sub_t = t[mask]
                        # Pulse envelope
                        pulse = 0.5 + 0.5 * np.sin(2 * np.pi * (sub_t / (beat_duration / 2)))
                        sig = np.zeros(np.sum(mask))
                        for freq in chord:
                            sig += np.sin(2 * np.pi * freq * sub_t) * 0.15
                            # Add overtone
                            sig += np.sin(2 * np.pi * (freq * 2) * sub_t) * 0.05
                        left[mask] += sig * pulse * 0.6
                        right[mask] += sig * np.roll(pulse, 500) * 0.6

            # Add subtle soft kick rhythm
            kick_pulse = np.exp(-((t % beat_duration) * 15)) * np.sin(2 * np.pi * 55 * t) * 0.25
            left += kick_pulse
            right += kick_pulse

        elif style == "calm_lofi":
            # Warm lo-fi Rhodes style chords (Dm9 - G13 - Cmaj7 - A7)
            chords = [
                [146.83, 220.00, 261.63, 329.63],
                [196.00, 246.94, 329.63, 392.00],
                [130.81, 196.00, 246.94, 329.63],
                [220.00, 277.18, 329.63, 392.00]
            ]
            cycle_time = 8.0 # 2 seconds per chord
            for i, chord in enumerate(chords):
                c_start = i * 2.0
                c_end = (i + 1) * 2.0
                for cycle in range(int(duration / cycle_time) + 2):
                    t_s = cycle * cycle_time + c_start
                    t_e = cycle * cycle_time + c_end
                    mask = (t >= t_s) & (t < t_e) & (t < duration)
                    if np.any(mask):
                        sub_t = t[mask]
                        # Gentle envelope
                        env = np.sin(np.pi * (sub_t - t_s) / 2.0) ** 0.5
                        sig = np.zeros(np.sum(mask))
                        for freq in chord:
                            sig += np.sin(2 * np.pi * freq * sub_t) * 0.12
                            sig += np.sin(2 * np.pi * (freq * 0.5) * sub_t) * 0.08
                        left[mask] += sig * env * 0.7
                        right[mask] += sig * env * 0.7

        elif style == "mysterious":
            # Dark atmospheric drone with slow frequency modulation
            drone1 = np.sin(2 * np.pi * 55.0 * t + 0.3 * np.sin(2 * np.pi * 0.1 * t)) * 0.2
            drone2 = np.sin(2 * np.pi * 82.4 * t + 0.2 * np.cos(2 * np.pi * 0.15 * t)) * 0.15
            shimmer = np.sin(2 * np.pi * 440.0 * t) * (0.04 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)))
            left += (drone1 + shimmer) * 0.6
            right += (drone2 + shimmer) * 0.6

        elif style == "cyberpunk":
            # Driving arpeggiated bass synth with sawtooth harmonics
            bpm = 128
            sixteenth = 60.0 / (bpm * 4)
            notes = [110.0, 130.81, 146.83, 164.81, 110.0, 220.0, 146.83, 196.00]
            for step in range(int(duration / sixteenth)):
                t_s = step * sixteenth
                t_e = (step + 1) * sixteenth
                mask = (t >= t_s) & (t < t_e) & (t < duration)
                if np.any(mask):
                    sub_t = t[mask]
                    freq = notes[step % len(notes)]
                    env = np.exp(-(sub_t - t_s) * 20)
                    sig = (np.sin(2 * np.pi * freq * sub_t) + 0.5 * np.sin(2 * np.pi * freq * 2 * sub_t)) * env * 0.2
                    left[mask] += sig
                    right[mask] += sig

        # Normalize and prevent clipping
        max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 0.001)
        left = (left / max_val) * 0.75
        right = (right / max_val) * 0.75

        # Convert to 16-bit PCM WAV
        left_int = (left * 32767).astype(np.int16)
        right_int = (right * 32767).astype(np.int16)
        interleaved = np.empty((n_samples * 2,), dtype=np.int16)
        interleaved[0::2] = left_int
        interleaved[1::2] = right_int

        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(interleaved.tobytes())

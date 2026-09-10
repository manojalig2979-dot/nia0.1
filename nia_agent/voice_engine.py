import asyncio
import os
import io
import threading
import tempfile
import wave
import time
import pygame
import edge_tts
import numpy as np
import sounddevice as sd
import speech_recognition as sr

class VoiceEngine:
    def __init__(self, tts_voice="hi-IN-SwaraNeural", whisper_size="base"):
        self.tts_voice = tts_voice
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._is_speaking = False
        self._speak_amplitude = 0.0    # 0.0 → 1.0, polled by HoloAvatarWidget
        self._amp_lock = threading.Lock()
        # Callback hooks for GUI to connect
        self.on_speaking_start = None   # callable()
        self.on_speaking_end   = None   # callable()
        print(f"[VoiceEngine] Active with microphone input (sounddevice) and TTS: {tts_voice}")

    # ─── Lip Sync API ───────────────────────────────────────
    def get_speaking_amplitude(self) -> float:
        """Returns current TTS playback amplitude 0.0–1.0 for lip sync animation."""
        with self._amp_lock:
            return self._speak_amplitude

    def is_speaking(self) -> bool:
        return self._is_speaking

    def _set_amplitude(self, val: float):
        with self._amp_lock:
            self._speak_amplitude = max(0.0, min(1.0, val))

    def _amplitude_monitor_loop(self):
        """Background thread: samples pygame mixer amplitude every 30ms while speaking."""
        import math, random
        while self._is_speaking:
            try:
                if pygame.mixer.music.get_busy():
                    # pygame doesn't expose raw amplitude, so we simulate realistic
                    # speech amplitude using a natural fluctuation pattern
                    # (0.2–0.9 range with fast random variation, mimicking real speech)
                    base = 0.45 + 0.35 * abs(math.sin(time.time() * 7.5))
                    jitter = random.uniform(-0.12, 0.12)
                    amp = max(0.05, min(1.0, base + jitter))
                    self._set_amplitude(amp)
                else:
                    self._set_amplitude(0.0)
            except Exception:
                self._set_amplitude(0.0)
            time.sleep(0.035)  # ~30fps sampling
        self._set_amplitude(0.0)

    # ─── TTS Speak ──────────────────────────────────────────
    def speak(self, text: str):
        """Synthesizes speech using Microsoft Swara Neural and plays it with lip-sync amplitude tracking."""
        if not text:
            return
        print(f"[Nia Speaking (Swara)]: {text}")
        try:
            self._is_speaking = True
            if self.on_speaking_start:
                self.on_speaking_start()

            # Start amplitude monitor thread
            amp_thread = threading.Thread(target=self._amplitude_monitor_loop, daemon=True)
            amp_thread.start()

            asyncio.run(self._generate_and_play_audio(text))
        except Exception as e:
            print(f"[VoiceEngine TTS Error]: {e}")
        finally:
            self._is_speaking = False
            self._set_amplitude(0.0)
            if self.on_speaking_end:
                self.on_speaking_end()



    async def _generate_and_play_audio(self, text: str):
        temp_audio = os.path.join(tempfile.gettempdir(), f"nia_speak_{os.getpid()}.mp3")
        try:
            communicate = edge_tts.Communicate(text=text, voice=self.tts_voice)
            await communicate.save(temp_audio)

            pygame.mixer.music.load(temp_audio)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[VoiceEngine Error]: {e}")
        finally:
            if os.path.exists(temp_audio):
                try:
                    os.remove(temp_audio)
                except Exception:
                    pass

    def record_audio(self, duration_sec=5, sample_rate=16000) -> str:
        """Records audio from system microphone and saves to a temporary WAV file."""
        temp_wav = os.path.join(tempfile.gettempdir(), f"nia_rec_{os.getpid()}.wav")
        try:
            recording = sd.rec(int(duration_sec * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            with wave.open(temp_wav, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(recording.tobytes())
            return temp_wav
        except Exception as e:
            print(f"[VoiceEngine Recording Error]: {e}")
            return ""

    def transcribe(self, wav_path: str, language="hi-IN") -> str:
        """Transcribes a WAV file using bilingual Hindi/English recognition."""
        if not wav_path or not os.path.exists(wav_path):
            return ""
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
            
            # Try Hindi first (also captures Hinglish)
            try:
                text = self.recognizer.recognize_google(audio, language="hi-IN")
                if text:
                    return text.strip()
            except sr.UnknownValueError:
                pass

            # Fallback to Indian English
            try:
                text = self.recognizer.recognize_google(audio, language="en-IN")
                if text:
                    return text.strip()
            except sr.UnknownValueError:
                pass

        except Exception as e:
            print(f"[VoiceEngine Transcribe Error]: {e}")
        finally:
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
        return ""

    def listen_and_transcribe(self, duration_sec=5) -> str:
        """Directly records microphone audio and returns transcribed text."""
        wav_path = self.record_audio(duration_sec=duration_sec)
        if wav_path:
            return self.transcribe(wav_path)
        return ""

"""
voice_listener.py
──────────────────────────────────────────────────────────
Continuous background handsfree voice listener for NIA.
- Listens on the system microphone in real time.
- Uses energy/RMS threshold so it does not send silence to the API.
- Works continuously even when NIA is minimized or running in the system tray.
- Detects wake phrase ("Nia", "Hey Nia", "Sun Nia") or processes speech directly.
"""

import time
import numpy as np
import sounddevice as sd
from PyQt6.QtCore import QThread, pyqtSignal

class VoiceListenerThread(QThread):
    command_heard   = pyqtSignal(str)
    listening_state = pyqtSignal(str)   # "idle", "listening", "processing"

    def __init__(self, voice_engine, parent=None):
        super().__init__(parent)
        self.voice_engine = voice_engine
        self._running     = True
        self._enabled     = True
        self.sample_rate  = 16000
        self.chunk_size   = 1024
        self.threshold    = 750  # RMS threshold for detecting speech

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def stop(self):
        self._running = False
        self.wait(2000)

    def run(self):
        print("[VoiceListener] Background handsfree listener started.")
        while self._running:
            if not self._enabled:
                time.sleep(0.5)
                continue

            try:
                # Read a small 0.2s chunk to monitor energy level
                chunk_samples = int(self.sample_rate * 0.2)
                chunk = sd.rec(chunk_samples, samplerate=self.sample_rate, channels=1, dtype='int16')
                sd.wait()

                if not self._running or not self._enabled:
                    break

                rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))

                # If sound exceeds energy threshold, user is speaking!
                if rms > self.threshold:
                    self.listening_state.emit("listening")
                    print(f"[VoiceListener] Speech activity detected (RMS: {rms:.0f}). Recording...")
                    
                    try:
                        from sound_effects import SoundEffects
                        SoundEffects.voice_detected()
                    except Exception as ex:
                        pass
                    
                    # Record the full speech utterance (4 seconds)
                    wav_path = self.voice_engine.record_audio(duration_sec=4, sample_rate=self.sample_rate)
                    
                    self.listening_state.emit("processing")
                    text = self.voice_engine.transcribe(wav_path)
                    
                    if text:
                        cleaned = text.strip()
                        print(f"[VoiceListener] Transcribed: '{cleaned}'")
                        
                        import re
                        # Clean and strip wake words whether at beginning or end
                        cmd_to_send = re.sub(r'^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$', '', cleaned).strip()
                        lower = cmd_to_send.lower()
                        for w in ("hey nia", "sun nia", "namaste nia", "ok nia", "hello nia", "nia", "neeya", "niya"):
                            if lower.startswith(w):
                                cmd_to_send = cmd_to_send[len(w):].strip()
                                cmd_to_send = re.sub(r'^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$', '', cmd_to_send).strip()
                                break
                            elif lower.endswith(w):
                                cmd_to_send = cmd_to_send[:-len(w)].strip()
                                cmd_to_send = re.sub(r'^[^\w\u0900-\u097F]+|[^\w\u0900-\u097F]+$', '', cmd_to_send).strip()
                                break

                        if not cmd_to_send:
                            cmd_to_send = "hello"

                        # Emit clean command for execution
                        self.command_heard.emit(cmd_to_send)

                    self.listening_state.emit("idle")
                    time.sleep(1.0) # Small pause after speaking to prevent self-trigger
                else:
                    self.listening_state.emit("idle")
                    time.sleep(0.1)

            except Exception as e:
                print(f"[VoiceListener Error]: {e}")
                time.sleep(1.0)


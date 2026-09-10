import numpy as np
import threading

_pygame_ready = False
_Sound = None

def _ensure_pygame():
    global _pygame_ready, _Sound
    if _pygame_ready:
        return True
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        _Sound = pygame.mixer.Sound
        _pygame_ready = True
        return True
    except Exception as e:
        print(f"pygame not available: {e}")
        return False

def _make_tone(freq_hz, duration_ms, volume=0.6, attack_ms=8, decay_ms=60, sample_rate=44100):
    n = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n, endpoint=False)
    wave = np.sin(2 * np.pi * freq_hz * t)
    attack  = int(sample_rate * attack_ms  / 1000)
    decay_s = int(sample_rate * decay_ms   / 1000)
    release = int(sample_rate * 40         / 1000)
    env = np.ones(n)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    if decay_s > 0 and n > attack + decay_s:
        env[attack:attack + decay_s] = np.linspace(1, 0.85, decay_s)
    if release > 0 and n >= release:
        env[-release:] = np.linspace(env[-release], 0, release)
    return (wave * env * volume * 32767).astype(np.int16)

def _make_sound(waves):
    if not _ensure_pygame(): return None
    try:
        combined = np.concatenate(waves)
        stereo = np.column_stack([combined, combined])
        return _Sound(stereo)
    except Exception as e:
        return None

def _play_async(fn):
    threading.Thread(target=fn, daemon=True).start()

class SoundEffects:
    _muted = False

    @classmethod
    def set_muted(cls, muted: bool):
        cls._muted = bool(muted)

    @classmethod
    def is_muted(cls):
        return cls._muted

    @staticmethod
    def voice_detected():
        if SoundEffects._muted: return
        def _do():
            try:
                if not _ensure_pygame(): return
                n1 = _make_tone(660, 120, volume=0.45, attack_ms=5, decay_ms=40)
                g  = np.zeros(int(44100 * 0.04), dtype=np.int16)
                n2 = _make_tone(880, 160, volume=0.55, attack_ms=5, decay_ms=70)
                snd = _make_sound([n1, g, n2])
                if snd:
                    snd.play()
                    import time; time.sleep(0.35)
            except Exception: pass
        _play_async(_do)

    @staticmethod
    def whatsapp_received():
        if SoundEffects._muted: return
        def _do():
            try:
                if not _ensure_pygame(): return
                n = _make_tone(740, 220, volume=0.5, attack_ms=3, decay_ms=120)
                snd = _make_sound([n])
                if snd:
                    snd.play()
                    import time; time.sleep(0.25)
            except Exception: pass
        _play_async(_do)

    @staticmethod
    def action_done():
        if SoundEffects._muted: return
        def _do():
            try:
                if not _ensure_pygame(): return
                n1 = _make_tone(880, 110, volume=0.35, attack_ms=5, decay_ms=50)
                g  = np.zeros(int(44100 * 0.03), dtype=np.int16)
                n2 = _make_tone(660, 150, volume=0.30, attack_ms=5, decay_ms=80)
                snd = _make_sound([n1, g, n2])
                if snd:
                    snd.play()
                    import time; time.sleep(0.3)
            except Exception: pass
        _play_async(_do)

    @staticmethod
    def startup_chime():
        SoundEffects.action_done()

    @staticmethod
    def error_tone():
        if SoundEffects._muted: return
        def _do():
            try:
                if not _ensure_pygame(): return
                n = _make_tone(280, 250, volume=0.35, attack_ms=10, decay_ms=100)
                snd = _make_sound([n])
                if snd:
                    snd.play()
                    import time; time.sleep(0.28)
            except Exception: pass
        _play_async(_do)

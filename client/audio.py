"""
Module: client/audio.py
Purpose: Client-Side Voice Clip Recorder, Player, & Base64 WAV Serializer
Mapped Requirements:
  - B4 (Voice Message Bonus): Records short push-to-talk / voice message clips as `.wav` audio,
    encodes them into Base64 strings (`audio_b64`) for transmission inside `MSG_VOICE_MSG` over TCP,
    and decodes/plays incoming Base64 `.wav` voice messages in the chat room UI.
"""

# ==============================================================================
# TODO 1: Define Audio Recording Constants
# ==============================================================================
# - SAMPLE_RATE = 16000        # 16 kHz mono is ideal for clear voice with compact TCP payload size
# - CHANNELS = 1               # Mono channel
# - SAMPLE_WIDTH = 2           # 16-bit PCM (2 bytes per sample)
# - MAX_RECORD_SECONDS = 15    # Cap voice clip duration so Base64 JSON packets stay responsive

# ==============================================================================
# TODO 2: Implement Voice Recorder Class (`VoiceRecorder`)
# ==============================================================================
# - Class `VoiceRecorder`:
#     1. Track `self.is_recording: bool = False` and `self.frames: list[bytes] = []`.
#     2. `start_recording() -> bool`:
#          Begin capturing microphone PCM frames in a background thread (using `pyaudio` / `sounddevice`
#          or Windows `winmm` / standard `wave` buffer).
#     3. `stop_recording() -> tuple[str, float] | None`:
#          Stop capturing, write collected PCM frames into an in-memory `io.BytesIO` WAV container
#          using Python's built-in `wave` module, calculate `duration` in seconds, encode the WAV bytes
#          via `base64.b64encode(wav_bytes).decode("ascii")`, and return `(audio_b64, duration)`.

# ==============================================================================
# TODO 3: Implement Base64 WAV Playback Helper (`play_voice_b64`)
# ==============================================================================
# - Function `play_voice_b64(audio_b64: str) -> None`:
#     1. Decode `wav_bytes = base64.b64decode(audio_b64)`.
#     2. Play the WAV audio asynchronously on a background thread so the Tkinter GUI never freezes:
#        - On Windows: can use built-in `winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)`
#          (or write to a temporary `.wav` file and play via `winsound.SND_FILENAME | winsound.SND_ASYNC`).
#        - On cross-platform setups: use `sounddevice` / `pyaudio` or system audio player fallback.

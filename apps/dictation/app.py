"""Dictation app runtime: hotkey → record → STT → insert text."""

from __future__ import annotations

import argparse
import asyncio
import sys
import threading
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stt_lab.config import ensure_dirs  # noqa: E402
from stt_lab.db import SessionLocal, init_db  # noqa: E402
from stt_lab.history import append_dictation  # noqa: E402
from stt_lab.pipeline import run_dictate  # noqa: E402
from stt_lab.profiles import (  # noqa: E402
    RunnableProfile,
    apply_stt_mode,
    list_profiles,
    load_profile,
)

from .audio_capture import PushToTalkRecorder  # noqa: E402
from .insert_text import insert_text  # noqa: E402

ModeToggle = Literal["local", "cloud"]


class DictationApp:
    def __init__(
        self,
        profile: RunnableProfile,
        *,
        mode: ModeToggle | None = None,
        hotkey: str = "<ctrl>+<alt>+<space>",
        toggle_local: str = "<ctrl>+<alt>+l",
        toggle_cloud: str = "<ctrl>+<alt>+c",
        keep_audio: bool = False,
    ):
        self.base_profile = profile
        self.mode: ModeToggle = mode or (
            "cloud" if profile.stt.location == "cloud" else "local"
        )
        self.hotkey = hotkey
        self.toggle_local = toggle_local
        self.toggle_cloud = toggle_cloud
        self.keep_audio = keep_audio
        self.recorder = PushToTalkRecorder()
        self._busy = threading.Lock()

    def active_profile(self) -> RunnableProfile:
        return apply_stt_mode(self.base_profile, self.mode)

    def privacy_banner(self) -> str:
        p = self.active_profile()
        if p.stt.location == "cloud":
            endpoint = p.cloud.stt_base_url or p.stt.provider
            return f"[CLOUD] audio will leave device → {endpoint}"
        return "[LOCAL] audio stays on device"

    def set_mode(self, mode: ModeToggle) -> None:
        self.mode = mode
        print(f"\nMode → {mode.upper()}  {self.privacy_banner()}", flush=True)

    def _process(self, wav_path: Path) -> None:
        if not self._busy.acquire(blocking=False):
            print("Busy — skip overlapping dictate", flush=True)
            return
        try:
            profile = self.active_profile()
            print(f"\nTranscribing ({self.privacy_banner()})…", flush=True)
            db = SessionLocal()
            try:
                text, trace = asyncio.run(run_dictate(db, profile, wav_path))
            finally:
                db.close()

            print(f"→ {text!r}", flush=True)
            print(
                f"   privacy: audio_left={trace.audio_left_device} "
                f"stt={trace.stt_location} mode={trace.mode}",
                flush=True,
            )
            insert_text(text)
            append_dictation(
                text=text,
                profile_id=profile.id,
                trace=trace,
                policy=profile.policy,
                audio_path=str(wav_path) if self.keep_audio else None,
            )
        except Exception as exc:
            print(f"ERROR: {exc}", flush=True)
        finally:
            if not self.keep_audio:
                try:
                    wav_path.unlink(missing_ok=True)
                except Exception:
                    pass
            self._busy.release()

    def on_press(self) -> None:
        if self.recorder.recording:
            return
        print("\n● Recording… (release hotkey to stop)", flush=True)
        try:
            self.recorder.start()
        except Exception as exc:
            print(f"Mic error: {exc}", flush=True)

    def on_release(self) -> None:
        if not self.recorder.recording:
            return
        wav = self.recorder.stop()
        if not wav:
            print("No audio captured", flush=True)
            return
        threading.Thread(target=self._process, args=(wav,), daemon=True).start()

    def run(self) -> None:
        from pynput import keyboard

        ensure_dirs()
        init_db()
        print("STT Lab Dictation", flush=True)
        print(f"Profile: {self.base_profile.id} ({self.base_profile.name})", flush=True)
        print(self.privacy_banner(), flush=True)
        print(f"Hold {self.hotkey} to dictate", flush=True)
        print(f"Toggle local:  {self.toggle_local}", flush=True)
        print(f"Toggle cloud:  {self.toggle_cloud}", flush=True)
        print("Ctrl+C to quit\n", flush=True)
        print(
            "macOS: grant Accessibility + Microphone to your terminal/Python.",
            flush=True,
        )

        ptt_keys = set(keyboard.HotKey.parse(self.hotkey))
        current: set = set()
        ptt_held = False

        def normalize(key):
            return key

        def on_press(key):
            nonlocal ptt_held
            current.add(normalize(key))
            if ptt_keys.issubset(current) and not ptt_held:
                ptt_held = True
                self.on_press()

        def on_release(key):
            nonlocal ptt_held
            current.discard(normalize(key))
            if ptt_held and not ptt_keys.issubset(current):
                ptt_held = False
                self.on_release()

        toggles = keyboard.GlobalHotKeys(
            {
                self.toggle_local: lambda: self.set_mode("local"),
                self.toggle_cloud: lambda: self.set_mode("cloud"),
            }
        )
        toggles.start()
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="STT Lab local dictation app")
    p.add_argument(
        "--profile",
        default="demo-local",
        help="Profile id under data/profiles/ (default: demo-local)",
    )
    p.add_argument(
        "--mode",
        choices=["local", "cloud"],
        default=None,
        help="Override STT location (local/cloud toggle)",
    )
    p.add_argument(
        "--hotkey",
        default="<ctrl>+<alt>+<space>",
        help="Push-to-talk hotkey (pynput syntax)",
    )
    p.add_argument("--list-profiles", action="store_true")
    p.add_argument(
        "--keep-audio",
        action="store_true",
        help="Retain temp wav paths in history when policy allows",
    )
    p.add_argument(
        "--once",
        metavar="WAV",
        help="Transcribe a wav once (no hotkey loop; still inserts text)",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    ensure_dirs()
    init_db()

    if args.list_profiles:
        rows = list_profiles()
        if not rows:
            print("No profiles in data/profiles/")
            return
        for pr in rows:
            print(f"{pr.id:24} mode={pr.mode:16} stt={pr.stt.provider}")
        return

    try:
        profile = load_profile(args.profile)
    except FileNotFoundError:
        raise SystemExit(
            f"Profile not found: {args.profile}. "
            "Export one from the notebook (h.export_profile) or use demo-local."
        )

    app = DictationApp(
        profile,
        mode=args.mode,
        hotkey=args.hotkey,
        keep_audio=args.keep_audio,
    )

    if args.once:
        wav = Path(args.once).expanduser().resolve()
        if not wav.exists():
            raise SystemExit(f"Audio not found: {wav}")
        print(app.privacy_banner())
        # Skip insert in CI-friendly path when STT_LAB_DICTATE_NO_INSERT=1
        import os

        if os.environ.get("STT_LAB_DICTATE_NO_INSERT") == "1":
            profile = app.active_profile()
            db = SessionLocal()
            try:
                text, trace = asyncio.run(run_dictate(db, profile, wav))
            finally:
                db.close()
            print(text)
            print(trace.model_dump())
            return
        app._process(wav)
        return

    app.run()


if __name__ == "__main__":
    main()

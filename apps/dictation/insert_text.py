"""Insert text into the currently focused application."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time


def copy_to_clipboard(text: str) -> None:
    data = text.encode("utf-8")
    if sys.platform == "darwin" and shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=data, check=True)
        return
    if shutil.which("xclip"):
        subprocess.run(
            ["xclip", "-selection", "clipboard"], input=data, check=True
        )
        return
    if shutil.which("xsel"):
        subprocess.run(
            ["xsel", "--clipboard", "--input"], input=data, check=True
        )
        return
    if sys.platform == "win32":
        # clip.exe expects UTF-16LE on modern Windows consoles for Unicode.
        subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
        return
    raise RuntimeError("No clipboard tool found (pbcopy/xclip/xsel/clip)")


def paste_from_clipboard() -> None:
    if sys.platform == "darwin":
        subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to keystroke "v" using command down',
            ],
            check=True,
        )
        return
    if sys.platform == "win32":
        try:
            from pynput.keyboard import Controller, Key
        except ImportError as exc:
            raise RuntimeError("pynput required for paste on Windows") from exc
        kb = Controller()
        with kb.pressed(Key.ctrl):
            kb.press("v")
            kb.release("v")
        return
    # Linux: Ctrl+V via pynput
    try:
        from pynput.keyboard import Controller, Key
    except ImportError as exc:
        raise RuntimeError("pynput required for paste on Linux") from exc
    kb = Controller()
    with kb.pressed(Key.ctrl):
        kb.press("v")
        kb.release("v")


def insert_text(text: str, *, settle_ms: int = 80) -> None:
    """Copy transcript and paste into the focused field."""
    if not text:
        return
    copy_to_clipboard(text)
    time.sleep(settle_ms / 1000.0)
    paste_from_clipboard()

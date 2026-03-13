# actions/send_message.py
# Universal messaging — WhatsApp & others
# macOS-compatible: uses Spotlight (Cmd+Space) to open apps instead of Windows search

import time
import platform
import subprocess
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.08

_OS = platform.system()


def _open_app_macos(app_name: str) -> bool:
    """Open an app on macOS using 'open -a' or Spotlight."""
    try:
        result = subprocess.run(["open", "-a", app_name], capture_output=True, timeout=8)
        if result.returncode == 0:
            time.sleep(2.0)
            return True
    except Exception:
        pass

    # Fallback: Spotlight
    try:
        pyautogui.hotkey("command", "space")
        time.sleep(0.5)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)
        pyautogui.press("enter")
        time.sleep(2.0)
        return True
    except Exception as e:
        print(f"[SendMessage] Spotlight fallback failed: {e}")
        return False


def _open_app_windows(app_name: str) -> bool:
    """Open an app on Windows via Start menu search."""
    try:
        pyautogui.press("win")
        time.sleep(0.4)
        pyautogui.write(app_name, interval=0.04)
        time.sleep(0.5)
        pyautogui.press("enter")
        time.sleep(2.0)
        return True
    except Exception as e:
        print(f"[SendMessage] Could not open {app_name}: {e}")
        return False


def _open_app(app_name: str) -> bool:
    if _OS == "Darwin":
        return _open_app_macos(app_name)
    return _open_app_windows(app_name)


def _search_contact(contact: str):
    """Search for a contact inside the messaging app (cross-platform shortcut)."""
    time.sleep(0.5)
    if _OS == "Darwin":
        pyautogui.hotkey("command", "f")
    else:
        pyautogui.hotkey("ctrl", "f")
    time.sleep(0.4)
    if _OS == "Darwin":
        pyautogui.hotkey("command", "a")
    else:
        pyautogui.hotkey("ctrl", "a")
    pyautogui.write(contact, interval=0.04)
    time.sleep(0.8)
    pyautogui.press("enter")
    time.sleep(0.6)


def _type_and_send(message: str):
    """Types message and sends it."""
    pyautogui.press("tab")
    time.sleep(0.2)
    if _OS == "Darwin":
        pyautogui.hotkey("command", "a")
    else:
        pyautogui.hotkey("ctrl", "a")
    pyautogui.write(message, interval=0.03)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.3)


def _send_whatsapp(receiver: str, message: str) -> str:
    try:
        if not _open_app("WhatsApp"):
            return "Could not open WhatsApp."
        time.sleep(1.5)
        _search_contact(receiver, "whatsapp")
        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via WhatsApp."
    except Exception as e:
        return f"WhatsApp error: {e}"


def _send_instagram(receiver: str, message: str) -> str:
    try:
        import webbrowser
        webbrowser.open("https://www.instagram.com/direct/new/")
        time.sleep(3.5)
        pyautogui.write(receiver, interval=0.05)
        time.sleep(1.5)
        pyautogui.press("down")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.5)
        for _ in range(3):
            pyautogui.press("tab")
            time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(1.5)
        pyautogui.write(message, interval=0.04)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via Instagram."
    except Exception as e:
        return f"Instagram error: {e}"


def _send_telegram(receiver: str, message: str) -> str:
    try:
        if not _open_app("Telegram"):
            return "Could not open Telegram."
        time.sleep(1.5)
        _search_contact(receiver, "telegram")
        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via Telegram."
    except Exception as e:
        return f"Telegram error: {e}"


def _send_generic(platform_name: str, receiver: str, message: str) -> str:
    try:
        if not _open_app(platform_name):
            return f"Could not open {platform_name}."
        time.sleep(1.5)
        _search_contact(receiver, platform_name)
        pyautogui.write(message, interval=0.03)
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Message sent to {receiver} via {platform_name}."
    except Exception as e:
        return f"{platform_name} error: {e}"


def send_message(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None
) -> str:
    params       = parameters or {}
    receiver     = params.get("receiver", "").strip()
    message_text = params.get("message_text", "").strip()
    platform_name = params.get("platform", "whatsapp").strip().lower()

    if not receiver:
        return "Please specify who to send the message to, sir."
    if not message_text:
        return "Please specify what message to send, sir."

    print(f"[SendMessage] 📨 {platform_name} → {receiver}: {message_text[:40]}")
    if player:
        player.write_log(f"[msg] Sending to {receiver} via {platform_name}...")

    if "whatsapp" in platform_name or "wp" in platform_name:
        result = _send_whatsapp(receiver, message_text)
    elif "instagram" in platform_name or "ig" in platform_name:
        result = _send_instagram(receiver, message_text)
    elif "telegram" in platform_name or "tg" in platform_name:
        result = _send_telegram(receiver, message_text)
    else:
        result = _send_generic(platform_name, receiver, message_text)

    print(f"[SendMessage] ✅ {result}")
    if player:
        player.write_log(f"[msg] {result}")
    return result

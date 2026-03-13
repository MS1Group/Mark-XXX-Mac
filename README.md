# Mark-XXX — macOS Port

This is the macOS-compatible build of [Mark-XXX](https://github.com/FatihMakes/Mark-XXX).

---

## What Changed

| File | Change |
|------|--------|
| `actions/reminder.py` | Uses `launchd` plist + `osascript` notifications instead of Windows Task Scheduler + win10toast |
| `actions/send_message.py` | `open -a AppName` instead of Windows Start menu search; `Cmd` instead of `Ctrl` |
| `actions/computer_control.py` | `cv2.CAP_AVFOUNDATION` for camera; AppleScript for window focus |
| `actions/desktop.py` | Removed `ctypes`/`winreg`; wallpaper via `osascript`; macOS-aware Gemini prompt |
| `actions/cmd_control.py` | macOS command shortcuts (`df -h`, `system_profiler`, etc.); Terminal via `osascript` |
| `actions/screen_processor.py` | `cv2.CAP_AVFOUNDATION` on macOS, `cv2.CAP_V4L2` on Linux |
| `actions/youtube_video.py` | `open -a "Google Chrome"` instead of Win key; `mss` for screenshots |
| `agent/executor.py` | Removed `winreg` Desktop path fallback |
| `main.py` | Updated tool descriptions |
| `requirements.txt` | Removed `comtypes`, `pycaw`, `win10toast` |

---

## Setup

### 1. Prerequisites

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Audio (required for pyaudio)
brew install portaudio

# Python tkinter (if using the UI)
brew install python-tk@3.11  # match your Python version
```

### 2. Install dependencies

```bash
cd Mark-XXX-Mac
pip install -r requirements.txt
pip install playwright
playwright install chromium
```

### 3. Permissions (macOS requires these)

Go to **System Settings → Privacy & Security** and enable:

- **Accessibility** → allow your Terminal / Python
- **Screen Recording** → allow your Terminal / Python (needed for screenshot features)
- **Microphone** → allow your Terminal / Python (needed for voice input)


### 4. Run

```bash
python main.py
```

---

## Known Limitations

- **Reminders**: Uses `launchd` — reminders persist across reboots but require the Python script to be reachable at the same path.
- **WhatsApp / Instagram messaging**: Requires the web app open in Chrome. Works the same as Windows via `pyautogui`.
- **YouTube thumbnail detection**: Uses `mss` for screen capture instead of `PIL.ImageGrab`.
- **Volume control**: Uses `osascript` — works system-wide.

---

## Tested On

- macOS Ventura 13+ / Sonoma 14+
- Python 3.11+

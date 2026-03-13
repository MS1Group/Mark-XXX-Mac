# actions/cmd_control.py
# macOS-compatible terminal command runner
# Removed Windows-specific command map and cmd.exe logic

import subprocess
import sys
import json
import re
import platform
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _get_platform() -> str:
    if sys.platform == "win32":  return "windows"
    if sys.platform == "darwin": return "macos"
    return "linux"


# macOS/Linux equivalent command shortcuts
MAC_COMMAND_MAP = [
    (["disk space", "disk usage", "storage", "free space"],
     "df -h", False),
    (["running processes", "list processes", "show processes", "active processes"],
     "ps aux | head -30", False),
    (["ip address", "my ip", "network info"],
     "ifconfig | grep inet", False),
    (["ping", "internet connection", "connected to internet"],
     "ping -c 4 google.com", False),
    (["open ports", "listening ports", "netstat"],
     "lsof -i -P -n | grep LISTEN | head -20", False),
    (["wifi networks", "available wifi", "wireless networks"],
     "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s", False),
    (["system info", "computer info", "hardware info", "specs"],
     "system_profiler SPHardwareDataType", False),
    (["cpu usage", "processor usage"],
     "top -l 1 | grep -E 'CPU|Processes'", False),
    (["memory usage", "ram usage"],
     "vm_stat | head -10", False),
    (["macos version", "os version"],
     "sw_vers", False),
    (["installed apps", "installed software"],
     "ls /Applications", False),
    (["battery", "battery level", "power status"],
     "pmset -g batt", False),
    (["current time", "what time", "system time"],
     "date +%H:%M", False),
    (["current date", "what date", "system date"],
     "date +%Y-%m-%d", False),
    (["desktop files", "files on desktop"],
     f'ls -la "{Path.home() / "Desktop"}"', False),
    (["downloads", "files in downloads"],
     f'ls -la "{Path.home() / "Downloads"}"', False),
    (["large files", "biggest files", "largest files"],
     f'find {Path.home()} -type f -exec du -sh {{}} + 2>/dev/null | sort -rh | head -10', False),
]


def _find_hardcoded(task: str) -> str | None:
    task_lower = task.lower()

    pip_match = re.search(r"install\s+([\w\-]+)", task_lower)
    if pip_match:
        package = pip_match.group(1)
        return f"pip install {package}"

    for keywords, command, _ in MAC_COMMAND_MAP:
        if any(kw in task_lower for kw in keywords):
            return command

    return None


BLOCKED_PATTERNS = [
    r"\brm\s+-rf\b", r"\brmdir\b",
    r"\bformat\b", r"\bfdisk\b",
    r"\bshutdown\b", r"\breboot\b",
    r"\bkill\s+-9\b",
    r"\beval\b", r"\b__import__\b",
    r"\bsudo\s+rm\b",
]
_BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)


def _is_safe(command: str) -> tuple[bool, str]:
    match = _BLOCKED_RE.search(command)
    if match:
        return False, f"Blocked pattern: '{match.group()}'"
    return True, "OK"


def _ask_gemini(task: str) -> str:
    plat = _get_platform()
    shell_name = "zsh (macOS)" if plat == "macos" else "bash (Linux)"
    try:
        import google.generativeai as genai
        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = (
            f"Convert this request to a single {shell_name} terminal command.\n"
            f"Output ONLY the command. No explanation, no markdown, no backticks.\n"
            f"If unsafe or impossible, output: UNSAFE\n\n"
            f"Request: {task}\n\nCommand:"
        )
        response = model.generate_content(prompt)
        command  = response.text.strip().strip("`").strip()
        if command.startswith("```"):
            lines   = command.split("\n")
            command = "\n".join(lines[1:-1]).strip()
        return command
    except Exception as e:
        return f"ERROR: {e}"


def _run_silent(command: str, timeout: int = 20) -> str:
    try:
        plat = _get_platform()
        if plat == "windows":
            is_ps = command.strip().lower().startswith("powershell")
            if is_ps:
                cmd_inner = re.sub(r'^powershell\s+"?', '', command, flags=re.IGNORECASE).rstrip('"')
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd_inner],
                    capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=timeout
                )
            else:
                result = subprocess.run(
                    ["cmd", "/c", command],
                    capture_output=True, text=True,
                    encoding="cp1252", errors="replace",
                    timeout=timeout, cwd=str(Path.home())
                )
        else:
            shell = "/bin/zsh" if plat == "macos" else "/bin/bash"
            result = subprocess.run(
                command, shell=True, executable=shell,
                capture_output=True, text=True,
                errors="replace", timeout=timeout,
                cwd=str(Path.home())
            )

        output = result.stdout.strip()
        error  = result.stderr.strip()
        if output: return output[:2000]
        if error:  return f"[stderr]: {error[:500]}"
        return "Command executed with no output."

    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s."
    except Exception as e:
        return f"Execution error: {e}"


def _run_visible(command: str) -> None:
    """Open a visible terminal window with the command."""
    try:
        plat = _get_platform()
        if plat == "windows":
            subprocess.Popen(f'cmd /k "{command}"', creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif plat == "macos":
            # Escape quotes in command for AppleScript
            escaped = command.replace('\\', '\\\\').replace('"', '\\"')
            subprocess.Popen([
                "osascript", "-e",
                f'tell application "Terminal" to do script "{escaped}"'
            ])
        else:
            for term in ["gnome-terminal", "xterm", "konsole"]:
                try:
                    subprocess.Popen([term, "--", "bash", "-c", f"{command}; exec bash"])
                    break
                except FileNotFoundError:
                    continue
    except Exception as e:
        print(f"[CMD] ⚠️ Terminal open failed: {e}")


def cmd_control(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None
) -> str:
    task    = (parameters or {}).get("task", "").strip()
    command = (parameters or {}).get("command", "").strip()
    visible = (parameters or {}).get("visible", True)

    if not task and not command:
        return "Please describe what you want to do, sir."

    if not command:
        command = _find_hardcoded(task)
        if command:
            print(f"[CMD] ⚡ Hardcoded: {command[:80]}")
        else:
            print(f"[CMD] 🤖 Gemini fallback for: {task}")
            command = _ask_gemini(task)
            print(f"[CMD] ✅ Generated: {command[:80]}")
            if command == "UNSAFE":
                return "I cannot generate a safe command for that request, sir."
            if command.startswith("ERROR:"):
                return f"Could not generate command: {command}"

    safe, reason = _is_safe(command)
    if not safe:
        return f"Blocked for safety: {reason}"

    if player:
        player.write_log(f"[CMD] {command[:60]}")

    # macOS: open apps directly
    plat = _get_platform()
    if plat == "macos" and command.strip().startswith("open "):
        subprocess.Popen(command, shell=True)
        return f"Opened: {command}"
    elif plat == "windows" and any(x in command.lower() for x in ["notepad", "explorer", "start "]):
        subprocess.Popen(command, shell=True)
        return f"Opened: {command}"

    if visible:
        _run_visible(command)
        output = _run_silent(command)
        return f"Terminal opened.\n\nOutput:\n{output}"
    else:
        return _run_silent(command)

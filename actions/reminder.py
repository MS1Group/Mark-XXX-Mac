# actions/reminder.py
# macOS-compatible reminder using launchd (plist)

import subprocess
import os
import sys
import platform
from datetime import datetime
from pathlib import Path


def reminder(
    parameters: dict,
    response: str | None = None,
    player=None,
    session_memory=None
) -> str:
    """
    Sets a timed reminder.
    - macOS: uses launchd (plist scheduling) + osascript notification
    - Linux: uses 'at' command
    """

    date_str = parameters.get("date")
    time_str = parameters.get("time")
    message  = parameters.get("message", "Reminder")

    if not date_str or not time_str:
        return "I need both a date and a time to set a reminder."

    try:
        target_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        if target_dt <= datetime.now():
            return "That time is already in the past."

        safe_message = message.replace('"', '').replace("'", "").strip()[:200]
        system = platform.system()

        if system == "Darwin":
            return _set_reminder_macos(target_dt, safe_message, player)
        else:
            return _set_reminder_linux(target_dt, safe_message, player)

    except ValueError:
        return "I couldn't understand that date or time format."
    except Exception as e:
        return f"Something went wrong while scheduling the reminder: {str(e)[:80]}"


def _set_reminder_macos(target_dt: datetime, message: str, player) -> str:
    """
    Schedule a reminder on macOS using launchd.
    Creates a plist in ~/Library/LaunchAgents/ that fires once at the target time.
    """
    task_name   = f"com.jarvis.reminder.{target_dt.strftime('%Y%m%d%H%M%S')}"
    plist_dir   = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path  = plist_dir / f"{task_name}.plist"

    python_exe  = sys.executable
    script_dir  = Path.home() / ".jarvis_reminders"
    script_dir.mkdir(exist_ok=True)
    script_path = script_dir / f"{task_name}.py"

    script_code = f'''import subprocess, os
subprocess.run([
    "osascript", "-e",
    'display notification "{message}" with title "JARVIS Reminder" sound name "Ping"'
])
try:
    import os
    os.remove(__file__)
except Exception:
    pass
try:
    import subprocess
    subprocess.run(["launchctl", "unload", "{plist_path}"])
    import pathlib
    pathlib.Path("{plist_path}").unlink(missing_ok=True)
except Exception:
    pass
'''

    script_path.write_text(script_code, encoding="utf-8")

    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{task_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Year</key>  <integer>{target_dt.year}</integer>
        <key>Month</key> <integer>{target_dt.month}</integer>
        <key>Day</key>   <integer>{target_dt.day}</integer>
        <key>Hour</key>  <integer>{target_dt.hour}</integer>
        <key>Minute</key><integer>{target_dt.minute}</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
'''

    plist_path.write_text(plist_content, encoding="utf-8")

    result = subprocess.run(
        ["launchctl", "load", str(plist_path)],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip()
        plist_path.unlink(missing_ok=True)
        script_path.unlink(missing_ok=True)
        return f"Could not schedule the reminder: {err}"

    if player:
        player.write_log(f"[reminder] set for {target_dt.strftime('%Y-%m-%d %H:%M')}")

    return f"Reminder set for {target_dt.strftime('%B %d at %I:%M %p')}."


def _set_reminder_linux(target_dt: datetime, message: str, player) -> str:
    """Schedule a reminder on Linux using the 'at' command."""
    at_time = target_dt.strftime("%H:%M %Y-%m-%d")
    cmd = f'echo "notify-send \'JARVIS Reminder\' \'{message}\'" | at {at_time}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        return f"Could not schedule reminder: {result.stderr.strip()}"

    if player:
        player.write_log(f"[reminder] set for {at_time}")

    return f"Reminder set for {target_dt.strftime('%B %d at %I:%M %p')}."

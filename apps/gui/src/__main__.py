import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)


def _log_crash(exctype, value, tb):
    """Log crash to a hardcoded path since Qt might not be ready."""
    home = Path.home()
    if sys.platform == "darwin":
        log_dir = home / "Library" / "Application Support" / "LexiShift" / "LexiShift"
    elif sys.platform.startswith("win"):
        log_dir = home / "AppData" / "Roaming" / "LexiShift" / "LexiShift"
    else:
        log_dir = home / ".local" / "share" / "LexiShift" / "LexiShift"
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        crash_log = log_dir / "crash.log"
        with open(crash_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] Startup Crash:\n")
            traceback.print_exception(exctype, value, tb, file=f)
            f.write("\n")
    except Exception:
        traceback.print_exception(exctype, value, tb)


if __name__ == "__main__":
    try:
        from main import main
        main()
    except Exception:
        _log_crash(*sys.exc_info())
        sys.exit(1)

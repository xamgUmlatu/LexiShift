from __future__ import annotations

from datetime import datetime
from importlib import import_module
from os import environ, getpid, path
from pathlib import Path
from subprocess import Popen
from threading import Thread
from traceback import format_exc

from PySide6.QtCore import QCoreApplication, QLocale, QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from lexishift_core.helper.paths import build_helper_paths
from lexishift_core.helper.status import load_status
from helper_daemon import DaemonConfig, run_daemon
from i18n import set_locale, t
from utils_paths import resource_path, reveal_path

MAIN_APP_BUNDLE_NAME = "LexiShift.app"
SYS = import_module("sys")


def _tray_icon() -> QIcon:
    if SYS.platform == "darwin":
        candidate = resource_path("ttbn.icns")
        if path.exists(candidate):
            return QIcon(candidate)
        # Fallback: look in bundle resources if running from .app
        try:
            bundle_res = Path(SYS.executable).parent.parent / "Resources" / "ttbn.icns"
            if bundle_res.exists():
                return QIcon(str(bundle_res))
        except Exception:
            pass
    else:
        candidate = resource_path("ttbn.ico")
        if path.exists(candidate):
            return QIcon(candidate)
    return QApplication.windowIcon()


def _debug_icon() -> QIcon:
    pixmap = QPixmap(22, 22)
    pixmap.fill()
    painter = QPainter(pixmap)
    painter.fillRect(0, 0, 22, 22, "#2E6BD6")
    painter.setPen("#FFFFFF")
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "L")
    painter.end()
    return QIcon(pixmap)


def _tray_icon_for_statusbar() -> QIcon:
    if environ.get("LEXISHIFT_TRAY_DEBUG"):
        return _debug_icon()
    base = _tray_icon()
    pixmap = base.pixmap(18, 18)
    if pixmap.isNull():
        return _debug_icon()
    return QIcon(pixmap)


def _log_line(paths, message: str) -> None:
    try:
        log_path = paths.data_root / "helper_tray.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")
    except Exception:  # noqa: BLE001
        pass


def _open_main_app() -> None:
    paths = build_helper_paths()

    env = dict(environ)
    cmd = []

    if getattr(SYS, "frozen", False):
        # On macOS helper builds, open the main app bundle directly.
        if SYS.platform == "darwin":
            exe_path = Path(SYS.executable)
            if exe_path.parent.name == "MacOS" and exe_path.parent.parent.name == "Contents":
                current_bundle = exe_path.parent.parent.parent
                main_bundle = current_bundle.with_name(MAIN_APP_BUNDLE_NAME)
                if not main_bundle.exists():
                    _log_line(paths, f"[{datetime.now()}] Main app bundle not found: {main_bundle}")
                    return
                cmd = ["open", str(main_bundle)]
                try:
                    _log_line(paths, f"[{datetime.now()}] Tray launching via open: {cmd}")
                    Popen(cmd, close_fds=True)
                    return
                except Exception as e:
                    _log_line(paths, f"[{datetime.now()}] Tray failed to launch via open: {e}")
                    return

        # Clean up environment to prevent PyInstaller one-file conflicts
        for key in ["_MEIPASS2", "DYLD_LIBRARY_PATH", "LD_LIBRARY_PATH"]:
            env.pop(key, None)
        cmd = [SYS.executable]
    else:
        entry = Path(__file__).resolve().parent / "main.py"
        cmd = [SYS.executable, str(entry)]

    try:
        _log_line(paths, f"[{datetime.now()}] Tray launching: {cmd}")
        Popen(cmd, close_fds=True, env=env)
    except Exception as e:
        _log_line(paths, f"[{datetime.now()}] Tray failed to launch app: {e}")


class HelperTrayController:
    def __init__(self) -> None:
        self.paths = build_helper_paths()
        _log_line(self.paths, "Helper tray starting.")
        _log_line(
            self.paths,
            f"Frozen: {getattr(sys, 'frozen', False)}, OneFile: {hasattr(sys, '_MEIPASS')}",
        )
        _log_line(self.paths, f"System tray available: {QSystemTrayIcon.isSystemTrayAvailable()}")
        self.status_action = QAction(t("helper_tray.status_starting"))
        self.status_action.setEnabled(False)

        self.open_app_action = QAction(t("helper_tray.action_open_app"))
        self.open_app_action.triggered.connect(_open_main_app)

        self.open_data_action = QAction(t("helper_tray.action_open_data"))
        self.open_data_action.triggered.connect(lambda: reveal_path(str(self.paths.data_root)))

        self.open_status_action = QAction(t("helper_tray.action_open_status"))
        self.open_status_action.triggered.connect(
            lambda: reveal_path(str(self.paths.srs_status_path))
        )

        self.notify_action = QAction(t("helper_tray.action_show_notification"))
        self.notify_action.triggered.connect(self._show_notification)

        self.quit_action = QAction(t("helper_tray.action_quit"))
        self.quit_action.triggered.connect(QApplication.quit)

        self.menu = QMenu()
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()
        self.menu.addAction(self.open_app_action)
        self.menu.addAction(self.open_data_action)
        self.menu.addAction(self.open_status_action)
        self.menu.addAction(self.notify_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        icon = _tray_icon_for_statusbar()
        sizes = icon.availableSizes()
        _log_line(self.paths, f"Tray icon null: {icon.isNull()}, sizes: {sizes}")
        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip(t("helper_tray.tooltip"))
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self.tray.setVisible(True)
        _log_line(self.paths, f"Tray visible: {self.tray.isVisible()}")

        self._start_daemon()
        self._start_status_timer()

    def _start_daemon(self) -> None:
        config = DaemonConfig()
        thread = Thread(target=run_daemon, args=(config,), daemon=True)
        thread.start()

    def _start_status_timer(self) -> None:
        self._timer = QTimer()
        self._timer.setInterval(15_000)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start()
        self._refresh_status()

    def _refresh_status(self) -> None:
        status = load_status(self.paths.srs_status_path)
        label = t("helper_tray.status_running")
        if status.last_error:
            label = t("helper_tray.status_error", error=status.last_error)
        elif status.last_run_at:
            label = t("helper_tray.status_last_run", value=status.last_run_at)
        self.status_action.setText(label)

    def _show_notification(self) -> None:
        self.tray.showMessage(
            t("helper_tray.notification_title"),
            t("helper_tray.notification_message"),
        )


def run_helper_tray() -> None:
    paths = build_helper_paths()
    _log_line(paths, f"[{datetime.now()}] Helper tray process started (PID: {getpid()})")
    try:
        # Match main app identity so QSettings resolves the same locale preference.
        QCoreApplication.setOrganizationName("LexiShift")
        QCoreApplication.setApplicationName("LexiShift")
        app = QApplication(SYS.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setWindowIcon(_tray_icon_for_statusbar())
        ui_settings = QSettings()
        locale_pref = ui_settings.value("appearance/locale", "system")
        if locale_pref == "system":
            locale_pref = QLocale.system().name()
        set_locale(str(locale_pref))
        controller = HelperTrayController()
        QTimer.singleShot(1500, controller._show_notification)
        ret = app.exec()
        _log_line(paths, f"[{datetime.now()}] Helper tray process exited cleanly (Code: {ret})")
        SYS.exit(ret)
    except Exception:
        _log_line(paths, f"[{datetime.now()}] Helper tray process crashed:\n{format_exc()}")
        SYS.exit(1)

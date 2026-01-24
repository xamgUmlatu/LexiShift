from __future__ import annotations

import webbrowser

INTEGRATION_LINKS = {
    "app_download": "https://lexishift.app/download",
    "chrome_extension": "https://lexishift.app/extension",
    "betterdiscord_plugin": "https://lexishift.app/betterdiscord",
}


def open_integration_link(key: str) -> None:
    url = INTEGRATION_LINKS.get(key)
    if not url:
        return
    webbrowser.open(url)

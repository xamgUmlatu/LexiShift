from __future__ import annotations

import webbrowser

INTEGRATION_LINKS = {
    "chrome_extension": "https://lexishift.app/extension",
    "betterdiscord_plugin": "https://lexishift.app/betterdiscord",
    "website": "https://lexishift.app",
}


def open_integration_link(key: str) -> None:
    url = INTEGRATION_LINKS.get(key)
    if not url:
        return
    webbrowser.open(url)

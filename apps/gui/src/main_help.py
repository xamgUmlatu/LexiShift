from __future__ import annotations

import webbrowser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Single source for "open instructions" actions (Help menu + empty-state affordances).
# Prefer the GitHub Pages manual, but fall back to the repository README until Pages is enabled.
SETUP_GUIDE_URLS: tuple[str, ...] = (
    "https://xamgUmlatu.github.io/LexiShift/getting-started/",
    "https://github.com/xamgUmlatu/LexiShift/blob/main/docs/getting-started/README.md",
)


def _url_is_reachable(url: str, timeout: float = 1.0) -> bool:
    request = Request(url, method="HEAD", headers={"User-Agent": "LexiShift-GUI"})
    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = int(getattr(response, "status", 200))
            return 200 <= status_code < 400
    except HTTPError as exc:
        # 401/403/405 still indicate the endpoint is up; avoid treating only 404/410 as hard misses.
        return exc.code < 500 and exc.code not in {404, 410}
    except URLError:
        return False
    except Exception:  # noqa: BLE001
        return False


def open_setup_guide() -> None:
    for url in SETUP_GUIDE_URLS:
        if _url_is_reachable(url):
            webbrowser.open(url)
            return
    # Final fallback: still attempt to open the preferred URL.
    webbrowser.open(SETUP_GUIDE_URLS[0])

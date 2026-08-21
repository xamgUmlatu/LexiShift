(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const PROMPT_ID = "lexishift-manual-source-prompt";
  const DISMISS_PREFIX = "lexishift.manualSourcePrompt.dismissed.";

  const ENTRIES = Object.freeze([
    Object.freeze({
      packId: "lookup-dictionary-directory",
      mode: "dictionary-directory",
      name: "Yomitan popup dictionaries",
      source: "community-maintained directory",
      pageMatches: [
        Object.freeze({
          hostname: "github.com",
          pathname: "/MarvNC/yomitan-dictionaries"
        })
      ]
    }),
    Object.freeze({
      packId: "freq-ja-bccwj",
      mode: "manual-download",
      pair: "en-ja",
      name: "BCCWJ Japanese Frequency (SUW)",
      source: "NINJAL",
      expectedFilename: "BCCWJ_frequencylist_suw_ver1_0.zip",
      licenseUrl: "https://clrd.ninjal.ac.jp/bccwj/en/freq-list.html#freq-list",
      downloadUrl: "https://repository.ninjal.ac.jp/record/3234/files/BCCWJ_frequencylist_suw_ver1_0.zip",
      pageMatches: [
        Object.freeze({
          hostname: "clrd.ninjal.ac.jp",
          pathname: "/bccwj/en/freq-list.html"
        })
      ]
    })
  ]);

  function safeUrl(value) {
    try {
      return new URL(String(value || ""));
    } catch (_error) {
      return null;
    }
  }

  function normalizePathname(pathname) {
    const value = String(pathname || "").trim();
    if (!value || value === "/") {
      return "/";
    }
    return value.replace(/\/+$/, "");
  }

  function matchesPage(url, matcher) {
    if (!url || !matcher) {
      return false;
    }
    const hostname = String(matcher.hostname || "").trim().toLowerCase();
    const pathname = normalizePathname(matcher.pathname);
    return (
      url.hostname.toLowerCase() === hostname
      && normalizePathname(url.pathname) === pathname
    );
  }

  function findEntryForUrl(href) {
    const url = safeUrl(href);
    if (!url) {
      return null;
    }
    return ENTRIES.find((entry) => (
      Array.isArray(entry.pageMatches)
      && entry.pageMatches.some((matcher) => matchesPage(url, matcher))
    )) || null;
  }

  function fallbackFormat(message, substitutions) {
    const values = Array.isArray(substitutions) ? substitutions : [];
    return String(message || "").replace(/\$(\d+)/g, (_match, index) => {
      const value = values[Number(index) - 1];
      return value === undefined ? "" : String(value);
    });
  }

  function t(key, substitutions, fallback) {
    const values = Array.isArray(substitutions)
      ? substitutions.map((value) => String(value))
      : [];
    try {
      if (globalThis.chrome && chrome.i18n && typeof chrome.i18n.getMessage === "function") {
        const message = chrome.i18n.getMessage(key, values);
        if (message) {
          return message;
        }
      }
    } catch (_error) {
      // Fall back below when extension i18n is unavailable in tests or unusual pages.
    }
    return fallbackFormat(fallback, values);
  }

  function isTopFrame() {
    try {
      return globalThis.window && window.top === window;
    } catch (_error) {
      return false;
    }
  }

  function dismissedKey(entry) {
    return `${DISMISS_PREFIX}${entry.packId}`;
  }

  function isDismissed(entry) {
    try {
      return sessionStorage.getItem(dismissedKey(entry)) === "1";
    } catch (_error) {
      return false;
    }
  }

  function dismiss(entry, host) {
    try {
      sessionStorage.setItem(dismissedKey(entry), "1");
    } catch (_error) {
      // Dismiss visually even if page storage is unavailable.
    }
    if (host && host.parentNode) {
      host.parentNode.removeChild(host);
    }
  }

  function createButton(label, variant) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute("data-variant", variant || "secondary");
    return button;
  }

  function openUrl(url) {
    window.open(url, "_blank", "noopener,noreferrer");
  }

  function renderManualSourcePrompt(entry) {
    if (!entry || typeof document === "undefined" || !document.body) {
      return false;
    }
    if (document.getElementById(PROMPT_ID) || isDismissed(entry)) {
      return false;
    }

    const host = document.createElement("aside");
    host.id = PROMPT_ID;
    host.setAttribute("aria-label", "LexiShift source download");
    const shadow = host.attachShadow({ mode: "open" });

    const style = document.createElement("style");
    style.textContent = `
:host {
  all: initial;
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 2147483647;
  color-scheme: light;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.card {
  box-sizing: border-box;
  width: min(360px, calc(100vw - 28px));
  border: 1px solid rgba(134, 117, 93, 0.34);
  border-radius: 10px;
  background: rgba(255, 252, 247, 0.98);
  color: #241f1a;
  box-shadow: 0 18px 48px rgba(30, 24, 18, 0.24);
  padding: 14px;
}
.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.title {
  margin: 0;
  font-size: 14px;
  line-height: 1.28;
  font-weight: 750;
}
.body,
.file,
.after {
  margin: 8px 0 0;
  font-size: 12px;
  line-height: 1.45;
}
.file,
.after {
  color: #5d5146;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
button {
  appearance: none;
  border: 1px solid rgba(116, 98, 78, 0.42);
  border-radius: 7px;
  background: #fffaf3;
  color: #2b241e;
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 650;
  line-height: 1.2;
  padding: 8px 10px;
}
button:hover,
button:focus-visible {
  background: #f1e4d3;
  outline: none;
}
button[data-variant="primary"] {
  background: #2f2f2f;
  border-color: #2f2f2f;
  color: white;
}
button[data-variant="primary"]:hover,
button[data-variant="primary"]:focus-visible {
  background: #202020;
}
.close {
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 50%;
  font-size: 16px;
  line-height: 1;
}
`;

    const card = document.createElement("section");
    card.className = "card";

    const header = document.createElement("div");
    header.className = "header";
    const title = document.createElement("h2");
    title.className = "title";
    const isDictionaryDirectory = entry.mode === "dictionary-directory";
    title.textContent = isDictionaryDirectory
      ? t(
        "dictionary_source_prompt_title",
        [],
        "LexiShift popup dictionaries"
      )
      : t(
        "manual_source_prompt_title",
        [],
        "LexiShift data source"
      );
    const closeButton = createButton(
      t("manual_source_prompt_dismiss", [], "Dismiss"),
      "secondary"
    );
    closeButton.className = "close";
    closeButton.setAttribute("aria-label", t("manual_source_prompt_dismiss", [], "Dismiss"));
    closeButton.textContent = "x";
    closeButton.addEventListener("click", () => dismiss(entry, host));
    header.append(title, closeButton);

    const body = document.createElement("p");
    body.className = "body";
    if (isDictionaryDirectory) {
      body.textContent = t(
        "dictionary_source_prompt_body",
        [],
        "LexiShift can import compatible Yomitan format-3 term dictionary ZIPs from this community-maintained directory. Review each dictionary's license or terms before obtaining it."
      );
      const after = document.createElement("p");
      after.className = "after";
      after.textContent = t(
        "dictionary_source_prompt_after_download",
        [],
        "After downloading an eligible ZIP, return to LexiShift. The desktop app will validate it and offer to import it locally."
      );
      card.append(header, body, after);
      shadow.append(style, card);
      document.body.append(host);
      return true;
    }
    body.textContent = t(
      "manual_source_prompt_body",
      [entry.name, entry.pair],
      "This page hosts $1 for $2. Review the provider terms, then download the required source file."
    );

    const file = document.createElement("p");
    file.className = "file";
    file.textContent = t(
      "manual_source_prompt_file",
      [entry.expectedFilename],
      "Expected file: $1"
    );

    const actions = document.createElement("div");
    actions.className = "actions";
    const termsButton = createButton(
      t("manual_source_prompt_terms", [], "Review terms on this page"),
      "secondary"
    );
    termsButton.addEventListener("click", () => {
      window.location.href = entry.licenseUrl;
    });
    const downloadButton = createButton(
      t("manual_source_prompt_download", [], "Download source file"),
      "primary"
    );
    const after = document.createElement("p");
    after.className = "after";
    after.textContent = t(
      "manual_source_prompt_after_download",
      [],
      "After it downloads, return to LexiShift and import the file."
    );
    downloadButton.addEventListener("click", () => {
      openUrl(entry.downloadUrl);
      after.textContent = t(
        "manual_source_prompt_download_opened",
        [],
        "Download opened. Return to LexiShift when it finishes."
      );
    });
    actions.append(termsButton, downloadButton);
    card.append(header, body, file, actions, after);
    shadow.append(style, card);
    document.body.append(host);
    return true;
  }

  function init() {
    if (!isTopFrame() || typeof window === "undefined") {
      return false;
    }
    const entry = findEntryForUrl(window.location && window.location.href);
    if (!entry) {
      return false;
    }
    return renderManualSourcePrompt(entry);
  }

  root.manualSourcePrompt = {
    entries: ENTRIES,
    findEntryForUrl,
    renderManualSourcePrompt,
    init
  };

  if (typeof document === "undefined" || typeof window === "undefined") {
    return;
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();

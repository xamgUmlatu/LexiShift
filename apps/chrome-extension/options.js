const DEFAULT_SETTINGS = {
  enabled: true,
  rules: [],
  highlightEnabled: true,
  highlightColor: "#9AA0A6",
  debugEnabled: false,
  debugFocusWord: "",
  rulesSource: "editor",
  rulesFileName: ""
};

const enabledInput = document.getElementById("enabled");
const highlightEnabledInput = document.getElementById("highlight-enabled");
const highlightColorInput = document.getElementById("highlight-color");
const highlightColorText = document.getElementById("highlight-color-text");
const debugEnabledInput = document.getElementById("debug-enabled");
const debugFocusInput = document.getElementById("debug-focus-word");
const rulesInput = document.getElementById("rules");
const saveButton = document.getElementById("save");
const status = document.getElementById("status");
const rulesSourceInputs = Array.from(document.querySelectorAll("input[name='rules-source']"));
const rulesFileInput = document.getElementById("rules-file");
const importFileButton = document.getElementById("import-file");
const exportFileButton = document.getElementById("export-file");
const fileStatus = document.getElementById("file-status");
const shareCodeInput = document.getElementById("share-code");
const shareCodeCjk = document.getElementById("share-code-cjk");
const generateCodeButton = document.getElementById("generate-code");
const importCodeButton = document.getElementById("import-code");
const copyCodeButton = document.getElementById("copy-code");

let currentRules = [];

function extractRules(input) {
  if (Array.isArray(input)) return input;
  if (input && typeof input === "object" && Array.isArray(input.rules)) return input.rules;
  throw new Error("Expected a JSON array or an object with a rules array.");
}

function setStatus(message, color) {
  status.textContent = message;
  status.style.color = color || "#6c675f";
  if (message) {
    setTimeout(() => {
      if (status.textContent === message) {
        status.textContent = "";
      }
    }, 2000);
  }
}

function updateRulesSourceUI(source) {
  rulesSourceInputs.forEach((input) => {
    input.checked = input.value === source;
  });
  const isFile = source === "file";
  rulesInput.disabled = isFile;
  saveButton.disabled = isFile;
}

function saveDisplaySettings() {
  const highlightEnabled = highlightEnabledInput.checked;
  const highlightColor = highlightColorInput.value || DEFAULT_SETTINGS.highlightColor;
  const debugEnabled = debugEnabledInput.checked;
  const debugFocusWord = debugFocusInput.value.trim();
  chrome.storage.local.set({ highlightEnabled, highlightColor, debugEnabled, debugFocusWord }, () => {
    setStatus("Display settings saved.", "#3c5a2a");
  });
}

function parseRulesFromEditor() {
  const parsed = JSON.parse(rulesInput.value || "[]");
  return extractRules(parsed);
}

function saveRules() {
  if (rulesInput.disabled) {
    setStatus("Switch to Edit JSON to save changes.", "#b42318");
    return;
  }
  let rules;
  try {
    rules = parseRulesFromEditor();
  } catch (err) {
    setStatus(err.message, "#b42318");
    return;
  }
  currentRules = rules;
  chrome.storage.local.set({ rules, rulesSource: "editor" }, () => {
    updateRulesSourceUI("editor");
    setStatus("Rules saved.", "#3c5a2a");
  });
}

function importFromFile() {
  const file = rulesFileInput.files && rulesFileInput.files[0];
  if (!file) {
    setStatus("Choose a JSON file first.", "#b42318");
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(reader.result);
      const rules = extractRules(parsed);
      currentRules = rules;
      rulesInput.value = JSON.stringify(rules, null, 2);
      chrome.storage.local.set(
        { rules, rulesSource: "file", rulesFileName: file.name },
        () => {
          updateRulesSourceUI("file");
          fileStatus.textContent = `Last imported: ${file.name}`;
          setStatus(`Imported ${rules.length} rules.`, "#3c5a2a");
        }
      );
    } catch (err) {
      setStatus(err.message || "Invalid JSON file.", "#b42318");
    }
  };
  reader.onerror = () => {
    setStatus("Failed to read file.", "#b42318");
  };
  reader.readAsText(file);
}

function exportToFile() {
  const payload = JSON.stringify(currentRules || [], null, 2);
  const blob = new Blob([payload], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "lexishift-rules.json";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  setStatus("Exported rules.", "#3c5a2a");
}

function getActiveRulesForCode() {
  if (!rulesInput.disabled) {
    return parseRulesFromEditor();
  }
  return currentRules || [];
}

function generateShareCode() {
  try {
    const rules = getActiveRulesForCode();
    const useCjk = shareCodeCjk.checked;
    shareCodeInput.value = encodeRulesCode(rules, useCjk);
    if (!shareCodeInput.value) {
      throw new Error("Generated code is empty.");
    }
    setStatus(`Code generated (${shareCodeInput.value.length} chars).`, "#3c5a2a");
  } catch (err) {
    setStatus(err.message || "Failed to generate code.", "#b42318");
  }
}

function importShareCode() {
  try {
    const decodedRules = decodeRulesCode(shareCodeInput.value || "", shareCodeCjk.checked);
    if (!Array.isArray(decodedRules)) {
      throw new Error("Decoded rules are not a list.");
    }
    if (!decodedRules.length) {
      throw new Error("Decoded rules are empty.");
    }
    currentRules = decodedRules;
    rulesInput.value = JSON.stringify(decodedRules, null, 2);
    chrome.storage.local.set({ rules: decodedRules, rulesSource: "editor" }, () => {
      updateRulesSourceUI("editor");
      setStatus("Code imported.", "#3c5a2a");
    });
  } catch (err) {
    setStatus(err.message || "Invalid code.", "#b42318");
  }
}

function copyShareCode() {
  if (!shareCodeInput.value) {
    return;
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(shareCodeInput.value).then(() => {
      setStatus("Copied.", "#3c5a2a");
    });
    return;
  }
  shareCodeInput.select();
  document.execCommand("copy");
  setStatus("Copied.", "#3c5a2a");
}

function load() {
  chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
    enabledInput.checked = items.enabled;
    highlightEnabledInput.checked = items.highlightEnabled !== false;
    highlightColorInput.value = items.highlightColor || DEFAULT_SETTINGS.highlightColor;
    highlightColorText.value = highlightColorInput.value;
    highlightColorInput.disabled = !highlightEnabledInput.checked;
    highlightColorText.disabled = !highlightEnabledInput.checked;
    debugEnabledInput.checked = items.debugEnabled === true;
    debugFocusInput.value = items.debugFocusWord || "";
    debugFocusInput.disabled = !debugEnabledInput.checked;
    currentRules = items.rules || [];
    rulesInput.value = JSON.stringify(currentRules, null, 2);
    updateRulesSourceUI(items.rulesSource || "editor");
    fileStatus.textContent = items.rulesFileName
      ? `Last imported: ${items.rulesFileName}`
      : "No file imported yet. Re-import after changes.";
  });
}

saveButton.addEventListener("click", saveRules);
importFileButton.addEventListener("click", importFromFile);
exportFileButton.addEventListener("click", exportToFile);

rulesSourceInputs.forEach((input) => {
  input.addEventListener("change", () => {
    const selected = rulesSourceInputs.find((item) => item.checked);
    const value = selected ? selected.value : "editor";
    chrome.storage.local.set({ rulesSource: value }, () => {
      updateRulesSourceUI(value);
      setStatus("Rules source updated.", "#3c5a2a");
    });
  });
});

highlightEnabledInput.addEventListener("change", () => {
  highlightColorInput.disabled = !highlightEnabledInput.checked;
  highlightColorText.disabled = !highlightEnabledInput.checked;
  saveDisplaySettings();
});

highlightColorInput.addEventListener("change", () => {
  highlightColorText.value = highlightColorInput.value;
  saveDisplaySettings();
});

highlightColorText.addEventListener("change", () => {
  const value = highlightColorText.value.trim();
  if (value) {
    highlightColorInput.value = value;
    saveDisplaySettings();
  }
});

debugEnabledInput.addEventListener("change", () => {
  debugFocusInput.disabled = !debugEnabledInput.checked;
  saveDisplaySettings();
});

debugFocusInput.addEventListener("change", () => {
  saveDisplaySettings();
});

enabledInput.addEventListener("change", () => {
  chrome.storage.local.set({ enabled: enabledInput.checked }, () => {
    setStatus("Extension updated.", "#3c5a2a");
  });
});

generateCodeButton.addEventListener("click", generateShareCode);
importCodeButton.addEventListener("click", importShareCode);
copyCodeButton.addEventListener("click", copyShareCode);

load();

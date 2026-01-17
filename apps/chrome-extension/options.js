const DEFAULT_SETTINGS = {
  enabled: true,
  rules: []
};

const enabledInput = document.getElementById("enabled");
const rulesInput = document.getElementById("rules");
const saveButton = document.getElementById("save");
const status = document.getElementById("status");

function load() {
  chrome.storage.local.get(DEFAULT_SETTINGS, (items) => {
    enabledInput.checked = items.enabled;
    rulesInput.value = JSON.stringify(items.rules, null, 2);
  });
}

function save() {
  let rules;
  try {
    rules = JSON.parse(rulesInput.value || "[]");
    if (!Array.isArray(rules)) {
      throw new Error("Rules must be a JSON array.");
    }
  } catch (err) {
    status.textContent = err.message;
    status.style.color = "#b42318";
    return;
  }
  chrome.storage.local.set({ enabled: enabledInput.checked, rules }, () => {
    status.textContent = "Saved.";
    status.style.color = "#3c5a2a";
    setTimeout(() => (status.textContent = ""), 1500);
  });
}

saveButton.addEventListener("click", save);
load();

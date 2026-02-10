class RulesManager {
  constructor(settingsManager, i18n) {
    this.settingsManager = settingsManager;
    this.i18n = i18n;
  }

  extractRules(input) {
    if (Array.isArray(input)) return input;
    if (input && typeof input === "object" && Array.isArray(input.rules)) return input.rules;
    throw new Error(
      this.i18n.t(
        "error_rules_expected_array",
        null,
        "Expected a JSON array or an object with a rules array."
      )
    );
  }

  parseFromEditor(jsonString) {
    const parsed = JSON.parse(jsonString || "[]");
    return this.extractRules(parsed);
  }

  async saveFromEditor(jsonString) {
    const rules = this.parseFromEditor(jsonString);
    this.settingsManager.currentRules = rules;
    const updatedAt = new Date().toISOString();
    return new Promise((resolve) => {
      chrome.storage.local.set({ rules, rulesSource: "editor", rulesUpdatedAt: updatedAt }, () => {
        resolve({ rules, updatedAt });
      });
    });
  }

  async importFromFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const parsed = JSON.parse(reader.result);
          const rules = this.extractRules(parsed);
          this.settingsManager.currentRules = rules;
          const updatedAt = new Date().toISOString();
          chrome.storage.local.set(
            { rules, rulesSource: "file", rulesFileName: file.name, rulesUpdatedAt: updatedAt },
            () => {
              resolve({ rules, updatedAt, fileName: file.name });
            }
          );
        } catch (err) {
          reject(err);
        }
      };
      reader.onerror = () => {
        reject(new Error(this.i18n.t("status_read_failed", null, "Failed to read file.")));
      };
      reader.readAsText(file);
    });
  }

  exportToFile() {
    const payload = JSON.stringify(this.settingsManager.currentRules || [], null, 2);
    const blob = new Blob([payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "lexishift-rules.json";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  generateShareCode(useCjk, editorValue, isEditorDisabled) {
    let rules;
    if (!isEditorDisabled) {
      rules = this.parseFromEditor(editorValue);
    } else {
      rules = this.settingsManager.currentRules || [];
    }
    const code = encodeRulesCode(rules, useCjk);
    if (!code) {
      throw new Error(this.i18n.t("error_generated_code_empty", null, "Generated code is empty."));
    }
    return code;
  }

  async importShareCode(code, useCjk) {
    const decodedRules = decodeRulesCode(code || "", useCjk);
    if (!Array.isArray(decodedRules)) {
      throw new Error(this.i18n.t("error_decoded_not_list", null, "Decoded rules are not a list."));
    }
    if (!decodedRules.length) {
      throw new Error(this.i18n.t("error_decoded_empty", null, "Decoded rules are empty."));
    }
    this.settingsManager.currentRules = decodedRules;
    const updatedAt = new Date().toISOString();
    return new Promise((resolve) => {
      chrome.storage.local.set({ rules: decodedRules, rulesSource: "editor", rulesUpdatedAt: updatedAt }, () => {
        resolve({ rules: decodedRules, updatedAt });
      });
    });
  }
}
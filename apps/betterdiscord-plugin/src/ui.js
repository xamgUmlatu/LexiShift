function buildSettingsPanel(plugin) {
	const panel = document.createElement("div");
	panel.style.padding = "10px";

	const description = document.createElement("div");
	description.textContent = "Paste a rules JSON array or a full dataset JSON with a rules field.";
	description.style.marginBottom = "8px";
	panel.appendChild(description);

	const textarea = document.createElement("textarea");
	textarea.style.width = "100%";
	textarea.style.minHeight = "180px";
	textarea.value = JSON.stringify(rules, null, 2);
	panel.appendChild(textarea);

	const buttonRow = document.createElement("div");
	buttonRow.style.marginTop = "10px";
	buttonRow.style.display = "flex";
	buttonRow.style.gap = "10px";

	const saveButton = document.createElement("button");
	saveButton.textContent = "Save";
	saveButton.className = BDFDB.disCN.button;
	buttonRow.appendChild(saveButton);

	const status = document.createElement("div");
	status.style.alignSelf = "center";
	panel.appendChild(buttonRow);
	panel.appendChild(status);

	const codeLabel = document.createElement("div");
	codeLabel.textContent = "Share code (compressed):";
	codeLabel.style.marginTop = "16px";
	panel.appendChild(codeLabel);

	const codeInput = document.createElement("textarea");
	codeInput.style.width = "100%";
	codeInput.style.minHeight = "80px";
	codeInput.style.color = "var(--text-normal)";
	codeInput.style.background = "var(--background-secondary)";
	codeInput.style.fontFamily = "Noto Sans CJK JP, Hiragino Sans, Apple SD Gothic Neo, sans-serif";
	codeInput.placeholder = "Generate or paste a code string here";
	panel.appendChild(codeInput);

	const codeModeRow = document.createElement("div");
	codeModeRow.style.marginTop = "6px";
	codeModeRow.style.display = "flex";
	codeModeRow.style.alignItems = "center";
	panel.appendChild(codeModeRow);

	const codeModeLabel = document.createElement("label");
	codeModeLabel.style.display = "flex";
	codeModeLabel.style.alignItems = "center";
	codeModeLabel.style.gap = "6px";
	codeModeLabel.style.cursor = "pointer";
	codeModeRow.appendChild(codeModeLabel);

	const codeModeCheckbox = document.createElement("input");
	codeModeCheckbox.type = "checkbox";
	codeModeCheckbox.checked = true;
	codeModeLabel.appendChild(codeModeCheckbox);

	const codeModeText = document.createElement("span");
	codeModeText.textContent = "Short code (CJK)";
	codeModeLabel.appendChild(codeModeText);

	const codeButtons = document.createElement("div");
	codeButtons.style.marginTop = "8px";
	codeButtons.style.display = "flex";
	codeButtons.style.gap = "10px";
	panel.appendChild(codeButtons);

	const generateButton = document.createElement("button");
	generateButton.textContent = "Generate Code";
	generateButton.className = BDFDB.disCN.button;
	codeButtons.appendChild(generateButton);

	const importButton = document.createElement("button");
	importButton.textContent = "Import Code";
	importButton.className = BDFDB.disCN.button;
	codeButtons.appendChild(importButton);

	const copyButton = document.createElement("button");
	copyButton.textContent = "Copy";
	copyButton.className = BDFDB.disCN.button;
	codeButtons.appendChild(copyButton);

	saveButton.onclick = _ => {
		try {
			const parsed = JSON.parse(textarea.value || "[]");
			rules = extractRules(parsed);
			BDFDB.DataUtils.save(rules, plugin, "rules");
			trie = buildTrie(normalizeRules(rules));
			oldMessages = {};
			plugin.requestRefresh();
			status.textContent = "Saved.";
			status.style.color = "var(--text-positive)";
		}
		catch (error) {
			status.textContent = error.message || "Invalid JSON.";
			status.style.color = "var(--text-danger)";
		}
	};

	generateButton.onclick = _ => {
		try {
			const useCjk = codeModeCheckbox.checked;
			codeInput.value = encodeRulesCode(rules, useCjk);
			if (!codeInput.value) throw new Error("Generated code is empty.");
			let detail = "";
			if (useCjk) {
				const firstCode = codeInput.value.charCodeAt(0);
				if (Number.isFinite(firstCode)) {
					const hex = firstCode.toString(16).toUpperCase().padStart(4, "0");
					detail = ` First: U+${hex}.`;
				}
			}
			status.textContent = `Code generated (${codeInput.value.length} chars).${detail}`;
			status.style.color = "var(--text-positive)";
		}
		catch (error) {
			let fallback = "";
			let fallbackDetail = "";
			if (codeModeCheckbox.checked) {
				try {
					fallback = encodeRulesCodeSafe(rules);
					fallbackDetail = ` Fallback safe code (${fallback.length} chars).`;
				}
				catch (fallbackError) {
					fallbackDetail = "";
				}
			}
			codeInput.value = fallback;
			status.textContent = `${error.message || "Could not generate code."}${fallbackDetail}`;
			status.style.color = "var(--text-danger)";
		}
	};

	importButton.onclick = _ => {
		try {
			const decodedRules = decodeRulesCode(codeInput.value || "", codeModeCheckbox.checked);
			if (!Array.isArray(decodedRules)) throw new Error("Decoded rules are not a list.");
			if (!decodedRules.length) throw new Error("Decoded rules are empty.");
			rules = decodedRules;
			textarea.value = JSON.stringify(rules, null, 2);
			BDFDB.DataUtils.save(rules, plugin, "rules");
			trie = buildTrie(normalizeRules(rules));
			oldMessages = {};
			plugin.requestRefresh();
			status.textContent = "Code imported.";
			status.style.color = "var(--text-positive)";
		}
		catch (error) {
			status.textContent = error.message || "Invalid code.";
			status.style.color = "var(--text-danger)";
		}
	};

	copyButton.onclick = _ => {
		if (!codeInput.value) return;
		if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
			navigator.clipboard.writeText(codeInput.value);
		}
		else {
			codeInput.focus();
			codeInput.select();
			document.execCommand("copy");
		}
		status.textContent = "Copied.";
		status.style.color = "var(--text-positive)";
	};

	return panel;
}

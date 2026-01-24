function buildSettingsPanel(plugin) {
	const panel = document.createElement("div");
	panel.style.padding = "10px";
	panel.style.minWidth = "520px";
	panel.style.minHeight = "520px";

	const description = document.createElement("div");
	description.textContent = "Choose a rules source: paste JSON or load a local file.";
	description.style.marginBottom = "8px";
	panel.appendChild(description);

	const integrationsTitle = document.createElement("div");
	integrationsTitle.textContent = "Integrations";
	integrationsTitle.style.marginTop = "6px";
	integrationsTitle.style.marginBottom = "6px";
	integrationsTitle.style.fontWeight = "600";
	panel.appendChild(integrationsTitle);

	const integrationsRow = document.createElement("div");
	integrationsRow.style.display = "flex";
	integrationsRow.style.gap = "10px";
	integrationsRow.style.marginBottom = "12px";

	const appButton = document.createElement("button");
	appButton.textContent = "Get Desktop App";
	appButton.className = BDFDB.disCN.button;
	appButton.onclick = _ => window.open("https://lexishift.app/download", "_blank", "noopener");
	integrationsRow.appendChild(appButton);

	const extButton = document.createElement("button");
	extButton.textContent = "Get Chrome Extension";
	extButton.className = BDFDB.disCN.button;
	extButton.onclick = _ => window.open("https://lexishift.app/extension", "_blank", "noopener");
	integrationsRow.appendChild(extButton);

	panel.appendChild(integrationsRow);

	const sourceRow = document.createElement("label");
	sourceRow.style.display = "flex";
	sourceRow.style.alignItems = "center";
	sourceRow.style.gap = "8px";
	sourceRow.style.marginBottom = "8px";
	sourceRow.style.cursor = "pointer";
	const sourceCheckbox = document.createElement("input");
	sourceCheckbox.type = "checkbox";
	sourceCheckbox.checked = plugin.getUseFileRules();
	const sourceText = document.createElement("span");
	sourceText.textContent = "Load rules from file (read-only)";
	sourceRow.appendChild(sourceCheckbox);
	sourceRow.appendChild(sourceText);
	panel.appendChild(sourceRow);

	const fileRow = document.createElement("div");
	fileRow.style.display = "flex";
	fileRow.style.alignItems = "center";
	fileRow.style.gap = "8px";
	fileRow.style.marginBottom = "12px";

	const hasOpenDialog = BdApi && typeof BdApi.openDialog === "function";

	const filePathInput = document.createElement("input");
	filePathInput.type = "text";
	filePathInput.readOnly = false;
	filePathInput.placeholder = hasOpenDialog ? "No rules file selected" : "Paste a rules file path";
	filePathInput.value = plugin.getRulesFilePath();
	filePathInput.style.flex = "1";
	fileRow.appendChild(filePathInput);

	const browseButton = document.createElement("button");
	browseButton.textContent = "Choose File";
	browseButton.className = BDFDB.disCN.button;
	browseButton.disabled = !hasOpenDialog;
	fileRow.appendChild(browseButton);

	const reloadButton = document.createElement("button");
	reloadButton.textContent = "Load";
	reloadButton.className = BDFDB.disCN.button;
	fileRow.appendChild(reloadButton);

	panel.appendChild(fileRow);

	const highlightRow = document.createElement("label");
	highlightRow.style.display = "flex";
	highlightRow.style.alignItems = "center";
	highlightRow.style.gap = "8px";
	highlightRow.style.marginBottom = "12px";
	highlightRow.style.cursor = "pointer";
	const highlightCheckbox = document.createElement("input");
	highlightCheckbox.type = "checkbox";
	highlightCheckbox.checked = plugin.getHighlightReplacements();
	const highlightText = document.createElement("span");
	highlightText.textContent = "Highlight replaced words (click to toggle original)";
	highlightRow.appendChild(highlightCheckbox);
	highlightRow.appendChild(highlightText);
	panel.appendChild(highlightRow);

	const colorRow = document.createElement("div");
	colorRow.style.display = "flex";
	colorRow.style.alignItems = "center";
	colorRow.style.gap = "8px";
	colorRow.style.marginBottom = "12px";

	const colorLabel = document.createElement("span");
	colorLabel.textContent = "Highlight color";
	colorRow.appendChild(colorLabel);

	const colorInput = document.createElement("input");
	colorInput.type = "color";
	colorInput.value = plugin.getHighlightColor();
	colorRow.appendChild(colorInput);

	const colorValue = document.createElement("input");
	colorValue.type = "text";
	colorValue.value = plugin.getHighlightColor();
	colorValue.style.width = "90px";
	colorRow.appendChild(colorValue);

	panel.appendChild(colorRow);

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
		if (sourceCheckbox.checked) {
			status.textContent = "Disable file mode to edit JSON.";
			status.style.color = "var(--text-danger)";
			return;
		}
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
		if (sourceCheckbox.checked) {
			status.textContent = "Disable file mode to import a code.";
			status.style.color = "var(--text-danger)";
			return;
		}
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

	highlightCheckbox.onchange = _ => {
		plugin.setHighlightReplacements(highlightCheckbox.checked);
		colorInput.disabled = !highlightCheckbox.checked;
		colorValue.disabled = !highlightCheckbox.checked;
		status.textContent = "Display preference saved.";
		status.style.color = "var(--text-positive)";
	};

	colorInput.onchange = _ => {
		colorValue.value = colorInput.value;
		plugin.setHighlightColor(colorInput.value);
		status.textContent = "Highlight color saved.";
		status.style.color = "var(--text-positive)";
	};

	colorValue.onchange = _ => {
		colorInput.value = colorValue.value;
		plugin.setHighlightColor(colorValue.value);
		status.textContent = "Highlight color saved.";
		status.style.color = "var(--text-positive)";
	};

	colorInput.disabled = !highlightCheckbox.checked;
	colorValue.disabled = !highlightCheckbox.checked;

	const setStatus = (message, color) => {
		status.textContent = message;
		status.style.color = color;
	};

	const applySourceState = () => {
		const fileMode = sourceCheckbox.checked;
		textarea.disabled = fileMode;
		saveButton.disabled = fileMode;
		reloadButton.textContent = fileMode ? "Reload" : "Load";
		reloadButton.disabled = !filePathInput.value;
	};

	const loadFromFile = path => {
		if (!path) return;
		plugin.setRulesFilePath(path);
		if (!sourceCheckbox.checked) {
			sourceCheckbox.checked = true;
			plugin.setUseFileRules(true, true);
		}
		const result = plugin.loadRulesFromFile(path);
		if (result && result.ok) {
			textarea.value = JSON.stringify(rules, null, 2);
			setStatus(`Loaded ${rules.length} rules from file.`, "var(--text-positive)");
		}
		else {
			const message = result && result.error ? result.error.message : "Failed to load file.";
			setStatus(message, "var(--text-danger)");
		}
		applySourceState();
	};

	const selectFile = () => {
		if (!BdApi || typeof BdApi.openDialog !== "function") {
			setStatus("File picker is not available. Paste a path and click Load.", "var(--text-danger)");
			return;
		}
		const dialogResult = BdApi.openDialog({
			title: "Select LexiShift rules JSON",
			filters: [{name: "JSON", extensions: ["json"]}],
			properties: ["openFile"]
		});
		const handlePaths = paths => {
			if (!paths || !paths.length) return;
			const path = paths[0];
			filePathInput.value = path;
			loadFromFile(path);
		};
		if (dialogResult && typeof dialogResult.then === "function") {
			dialogResult.then(handlePaths);
		}
		else {
			handlePaths(dialogResult);
		}
	};

	sourceCheckbox.onchange = _ => {
		plugin.setUseFileRules(sourceCheckbox.checked);
		if (sourceCheckbox.checked && filePathInput.value) {
			loadFromFile(filePathInput.value);
		}
		else {
			setStatus("Rules source updated.", "var(--text-positive)");
		}
		applySourceState();
	};

	browseButton.onclick = _ => {
		selectFile();
	};

	reloadButton.onclick = _ => {
		if (!filePathInput.value) return;
		loadFromFile(filePathInput.value);
	};

	filePathInput.oninput = _ => {
		plugin.setRulesFilePath(filePathInput.value.trim());
		applySourceState();
	};

	applySourceState();

	return panel;
}

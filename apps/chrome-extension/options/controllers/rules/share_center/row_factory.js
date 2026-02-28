(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createDynamicLeafRow(targetMeta, optionsArg) {
    const rowOptions = optionsArg && typeof optionsArg === "object" ? optionsArg : {};
    const label = document.createElement("label");
    label.className = "share-center-target";
    if (rowOptions.isPending) {
      label.classList.add("is-pending");
    }
    if (rowOptions.isDisabled) {
      label.classList.add("is-disabled");
    }

    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "share-center-target";
    input.value = targetMeta.id;
    if (rowOptions.checked === true) {
      input.checked = true;
    }
    if (rowOptions.isDisabled === true) {
      input.disabled = true;
    }

    const body = document.createElement("span");
    body.className = "share-center-target-body";

    const title = document.createElement("span");
    title.className = "share-center-target-title";
    title.textContent = targetMeta.label;

    const hint = document.createElement("span");
    hint.className = "share-center-target-hint";
    hint.textContent = String(rowOptions.hint || "").trim() || " ";

    body.appendChild(title);
    body.appendChild(hint);
    label.appendChild(input);
    label.appendChild(body);

    if (rowOptions.badge) {
      const badge = document.createElement("span");
      badge.className = "share-center-badge";
      badge.textContent = String(rowOptions.badge);
      label.appendChild(badge);
    }

    return { label, input };
  }

  root.optionsShareCenterRowFactory = {
    createDynamicLeafRow
  };
})();

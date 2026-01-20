function encodeMarkerPayload(text) {
	try {
		return btoa(unescape(encodeURIComponent(text)));
	}
	catch (error) {
		return "";
	}
}

function decodeMarkerPayload(text) {
	try {
		return decodeURIComponent(escape(atob(text)));
	}
	catch (error) {
		return "";
	}
}

function wrapReplacement(replacement, original) {
	const payload = encodeMarkerPayload(original);
	return `${MARKER_START}${payload}${MARKER_MID}${replacement}${MARKER_END}`;
}

function createReplacementElement(replacement, original, plugin) {
	const React = BdApi.React;
	const highlight = plugin && plugin.getHighlightReplacements && plugin.getHighlightReplacements();
	const className = highlight ? "ls-replaced ls-highlight" : "ls-replaced";
	const style = highlight && plugin && plugin.getHighlightColor ? {color: plugin.getHighlightColor()} : null;
	const onEnter = event => {
		event.currentTarget.classList.add("ls-hover");
	};
	const onLeave = event => {
		event.currentTarget.classList.remove("ls-hover");
	};
	const onClick = event => {
		event.currentTarget.classList.toggle("ls-show-original");
	};
	return React.createElement(
		"span",
		{
			className,
			style,
			"data-original": original,
			onMouseEnter: onEnter,
			onMouseLeave: onLeave,
			onClick
		},
		React.createElement("span", {className: "ls-replacement"}, replacement),
		React.createElement("span", {className: "ls-original"}, original)
	);
}

function splitMarkers(text, plugin) {
	if (text.indexOf(MARKER_START) === -1) return text;
	const parts = [];
	let cursor = 0;
	while (cursor < text.length) {
		const start = text.indexOf(MARKER_START, cursor);
		if (start === -1) break;
		const mid = text.indexOf(MARKER_MID, start + MARKER_START.length);
		const end = text.indexOf(MARKER_END, mid + MARKER_MID.length);
		if (mid === -1 || end === -1) break;
		if (start > cursor) parts.push(text.slice(cursor, start));
		const payload = text.slice(start + MARKER_START.length, mid);
		const original = decodeMarkerPayload(payload);
		const replacement = text.slice(mid + MARKER_MID.length, end);
		parts.push(createReplacementElement(replacement, original, plugin));
		cursor = end + MARKER_END.length;
	}
	if (cursor < text.length) parts.push(text.slice(cursor));
	return parts;
}

function replaceMarkersInTree(node, plugin) {
	const React = BdApi.React;
	if (node == null || typeof node === "boolean") return node;
	if (typeof node === "string") return splitMarkers(node, plugin);
	if (Array.isArray(node)) {
		const mapped = [];
		for (const child of node) {
			const replaced = replaceMarkersInTree(child, plugin);
			if (Array.isArray(replaced)) mapped.push(...replaced);
			else mapped.push(replaced);
		}
		return mapped;
	}
	if (React.isValidElement(node) && node.props && node.props.children) {
		const replacedChildren = replaceMarkersInTree(node.props.children, plugin);
		if (replacedChildren !== node.props.children) {
			return React.cloneElement(node, Object.assign({}, node.props), replacedChildren);
		}
	}
	return node;
}

function createReplacementNode(replacement, original, plugin) {
	const span = document.createElement("span");
	span.className = plugin && plugin.getHighlightReplacements && plugin.getHighlightReplacements()
		? "ls-replaced ls-highlight"
		: "ls-replaced";
	if (plugin && plugin.getHighlightReplacements && plugin.getHighlightReplacements() && plugin.getHighlightColor) {
		span.style.color = plugin.getHighlightColor();
	}
	span.dataset.original = original;
	const replacementSpan = document.createElement("span");
	replacementSpan.className = "ls-replacement";
	replacementSpan.textContent = replacement;
	const originalSpan = document.createElement("span");
	originalSpan.className = "ls-original";
	originalSpan.textContent = original;
	span.appendChild(replacementSpan);
	span.appendChild(originalSpan);
	span.addEventListener("mouseenter", event => {
		event.currentTarget.classList.add("ls-hover");
	});
	span.addEventListener("mouseleave", event => {
		event.currentTarget.classList.remove("ls-hover");
	});
	span.addEventListener("click", event => {
		event.currentTarget.classList.toggle("ls-show-original");
	});
	return span;
}

function splitMarkersToNodes(text, plugin) {
	if (text.indexOf(MARKER_START) === -1) return null;
	const parts = [];
	let cursor = 0;
	while (cursor < text.length) {
		const start = text.indexOf(MARKER_START, cursor);
		if (start === -1) break;
		const mid = text.indexOf(MARKER_MID, start + MARKER_START.length);
		const end = text.indexOf(MARKER_END, mid + MARKER_MID.length);
		if (mid === -1 || end === -1) break;
		if (start > cursor) parts.push(text.slice(cursor, start));
		const payload = text.slice(start + MARKER_START.length, mid);
		const original = decodeMarkerPayload(payload);
		const replacement = text.slice(mid + MARKER_MID.length, end);
		parts.push(createReplacementNode(replacement, original, plugin));
		cursor = end + MARKER_END.length;
	}
	if (cursor < text.length) parts.push(text.slice(cursor));
	return parts;
}

function replaceMarkersInElement(element, plugin) {
	if (!element || !element.querySelectorAll) return;
	const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
	const nodes = [];
	let node = walker.nextNode();
	while (node) {
		if (node.nodeValue && node.nodeValue.indexOf(MARKER_START) !== -1) {
			nodes.push(node);
		}
		node = walker.nextNode();
	}
	for (const textNode of nodes) {
		const parts = splitMarkersToNodes(textNode.nodeValue || "", plugin);
		if (!parts) continue;
		const fragment = document.createDocumentFragment();
		for (const part of parts) {
			if (typeof part === "string") fragment.appendChild(document.createTextNode(part));
			else fragment.appendChild(part);
		}
		if (textNode.parentNode) {
			textNode.parentNode.replaceChild(fragment, textNode);
		}
	}
}

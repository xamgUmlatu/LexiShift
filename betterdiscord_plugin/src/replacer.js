function normalizeRules(rules) {
	return (rules || []).map(rule => ({
		source_phrase: String(rule.source_phrase || ""),
		replacement: String(rule.replacement || ""),
		priority: Number.isFinite(rule.priority) ? rule.priority : 0,
		case_policy: rule.case_policy || "match",
		enabled: rule.enabled !== false
	}));
}

function extractRules(input) {
	if (Array.isArray(input)) return input;
	if (input && typeof input === "object") {
		if (Array.isArray(input.rules)) return input.rules;
	}
	throw new Error("Expected a JSON array or an object with a rules array.");
}

function buildTrie(rules) {
	const root = {children: Object.create(null), bestRule: null};
	for (const rule of rules) {
		if (!rule.enabled) continue;
		const words = tokenize(rule.source_phrase).filter(t => t.kind === "word");
		if (!words.length) continue;
		let node = root;
		for (const word of words) {
			const key = normalize(word.text);
			node.children[key] = node.children[key] || {children: Object.create(null), bestRule: null};
			node = node.children[key];
		}
		if (!node.bestRule || rule.priority > node.bestRule.priority) {
			node.bestRule = rule;
		}
	}
	return root;
}

function tokenize(text) {
	const tokens = [];
	const matches = text.matchAll(TOKEN_RE);
	for (const match of matches) {
		const chunk = match[0];
		let kind = "punct";
		if (WORD_RE.test(chunk)) kind = "word";
		else if (/^\s+$/.test(chunk)) kind = "space";
		tokens.push({text: chunk, kind});
	}
	return tokens;
}

function normalize(word) {
	return word.toLowerCase();
}

function computeGapOk(tokens, wordPositions) {
	const gapOk = [];
	for (let i = 0; i < wordPositions.length - 1; i += 1) {
		const start = wordPositions[i] + 1;
		const end = wordPositions[i + 1];
		let ok = true;
		for (let j = start; j < end; j += 1) {
			if (tokens[j].kind !== "space") {
				ok = false;
				break;
			}
		}
		gapOk.push(ok);
	}
	return gapOk;
}

function applyCase(replacement, sourceWords, policy) {
	if (policy === "as-is") return replacement;
	if (policy === "lower") return replacement.toLowerCase();
	if (policy === "upper") return replacement.toUpperCase();
	if (policy === "title") return replacement.replace(/\b\w/g, m => m.toUpperCase());
	if (policy === "match") {
		const sourceText = sourceWords.join(" ");
		if (sourceText === sourceText.toUpperCase()) return replacement.toUpperCase();
		if (sourceWords.length && sourceWords[0][0] && sourceWords[0][0] === sourceWords[0][0].toUpperCase()) {
			return replacement.replace(/\b\w/g, m => m.toUpperCase());
		}
	}
	return replacement;
}

function findLongestMatch(trie, words, gapOk, startIndex) {
	let node = trie;
	let bestRule = null;
	let bestEnd = null;
	let bestPriority = -1;

	for (let idx = startIndex; idx < words.length; idx += 1) {
		if (idx > startIndex && !gapOk[idx - 1]) break;
		const normalized = normalize(words[idx]);
		node = node.children[normalized];
		if (!node) break;
		if (node.bestRule && node.bestRule.priority >= bestPriority) {
			if (node.bestRule.priority > bestPriority || bestEnd === null || idx > bestEnd) {
				bestRule = node.bestRule;
				bestEnd = idx;
				bestPriority = node.bestRule.priority;
			}
		}
	}

	if (!bestRule || bestEnd === null) return null;
	return {startWordIndex: startIndex, endWordIndex: bestEnd, rule: bestRule};
}

function replaceText(text, trie) {
	if (!trie) return text;
	const tokens = tokenize(text);
	const wordPositions = [];
	const wordTexts = [];
	tokens.forEach((token, idx) => {
		if (token.kind === "word") {
			wordPositions.push(idx);
			wordTexts.push(token.text);
		}
	});
	if (!wordPositions.length) return text;
	const gapOk = computeGapOk(tokens, wordPositions);
	const matches = [];
	let wordIndex = 0;
	while (wordIndex < wordTexts.length) {
		const match = findLongestMatch(trie, wordTexts, gapOk, wordIndex);
		if (match) {
			matches.push(match);
			wordIndex = match.endWordIndex + 1;
		}
		else wordIndex += 1;
	}

	let output = "";
	let tokenCursor = 0;
	for (const match of matches) {
		const startTokenIdx = wordPositions[match.startWordIndex];
		const endTokenIdx = wordPositions[match.endWordIndex];
		for (let i = tokenCursor; i < startTokenIdx; i += 1) {
			output += tokens[i].text;
		}
		const sourceWords = wordTexts.slice(match.startWordIndex, match.endWordIndex + 1);
		output += applyCase(match.rule.replacement, sourceWords, match.rule.case_policy || "match");
		tokenCursor = endTokenIdx + 1;
	}
	for (let i = tokenCursor; i < tokens.length; i += 1) {
		output += tokens[i].text;
	}
	return output;
}

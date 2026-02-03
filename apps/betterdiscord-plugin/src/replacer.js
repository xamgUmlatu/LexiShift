const root = (globalThis.LexiShift = globalThis.LexiShift || {});
const { tokenize, computeGapOk } = root.tokenizer || {};
const { buildTrie, findLongestMatch, applyCase, normalizeRules } = root.matcher || {};

if (!tokenize || !computeGapOk || !buildTrie || !findLongestMatch || !applyCase || !normalizeRules) {
	throw new Error("[LexiShift] Shared tokenizer/matcher not loaded. Rebuild the plugin.");
}

function extractRules(input) {
	if (Array.isArray(input)) return input;
	if (input && typeof input === "object") {
		if (Array.isArray(input.rules)) return input.rules;
	}
	throw new Error("Expected a JSON array or an object with a rules array.");
}

function replaceText(text, trie, options = {}) {
	if (!trie) return text;
	const annotate = options.annotate === true;
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
		const replacement = applyCase(match.rule.replacement, sourceWords, match.rule.case_policy || "match");
		if (annotate) {
			const original = sourceWords.join(" ");
			output += wrapReplacement(replacement, original);
		}
		else {
			output += replacement;
		}
		tokenCursor = endTokenIdx + 1;
	}
	for (let i = tokenCursor; i < tokens.length; i += 1) {
		output += tokens[i].text;
	}
	return output;
}

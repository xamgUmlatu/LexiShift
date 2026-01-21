if (typeof CJK_BASE_START === "undefined") {
	var CJK_BASE_START = 0x4E00;
}
if (typeof CJK_BASE === "undefined") {
	var CJK_BASE = 16384;
}

function isCjkCode(text) {
	let sawChar = false;
	for (let i = 0; i < text.length; i += 1) {
		const code = text.charCodeAt(i);
		if (code <= 32) continue;
		sawChar = true;
		if (code < CJK_BASE_START || code >= CJK_BASE_START + CJK_BASE) return false;
	}
	return sawChar;
}

function stringToBytes(text) {
	const bytes = new Uint8Array(text.length * 2);
	for (let i = 0; i < text.length; i += 1) {
		const code = text.charCodeAt(i);
		bytes[i * 2] = code >>> 8;
		bytes[i * 2 + 1] = code & 0xff;
	}
	return bytes;
}

function bytesToString(bytes) {
	if (bytes.length % 2 !== 0) throw new Error("Invalid byte length.");
	const chars = new Array(bytes.length / 2);
	for (let i = 0; i < bytes.length; i += 2) {
		chars[i / 2] = String.fromCharCode((bytes[i] << 8) | bytes[i + 1]);
	}
	return chars.join("");
}

function encodeBase16384(bytes) {
	const base = Number(CJK_BASE);
	const start = Number(CJK_BASE_START);
	if (!Number.isFinite(base) || base <= 0) throw new Error("CJK base not initialized.");
	if (!Number.isFinite(start)) throw new Error("CJK base start not initialized.");
	if (!bytes || bytes.length === 0) return "";
	const digits = [0];
	for (let i = 0; i < bytes.length; i += 1) {
		let carry = bytes[i];
		for (let j = 0; j < digits.length; j += 1) {
			carry += digits[j] * 256;
			digits[j] = carry % base;
			carry = Math.floor(carry / base);
		}
		while (carry > 0) {
			digits.push(carry % base);
			carry = Math.floor(carry / base);
		}
	}
	let zeros = 0;
	while (zeros < bytes.length && bytes[zeros] === 0) zeros += 1;
	let output = "";
	for (let i = 0; i < zeros; i += 1) {
		output += String.fromCharCode(start);
	}
	for (let i = digits.length - 1; i >= 0; i -= 1) {
		output += String.fromCharCode(start + digits[i]);
	}
	return output;
}

function decodeBase16384(text) {
	const base = Number(CJK_BASE);
	const start = Number(CJK_BASE_START);
	if (!Number.isFinite(base) || base <= 0) throw new Error("CJK base not initialized.");
	if (!Number.isFinite(start)) throw new Error("CJK base start not initialized.");
	const cleaned = String(text || "").replace(/\s+/g, "");
	if (!cleaned) throw new Error("Code is empty.");
	const bytes = [0];
	for (let i = 0; i < cleaned.length; i += 1) {
		const value = cleaned.charCodeAt(i) - start;
		if (value < 0 || value >= base) throw new Error("Invalid CJK code.");
		let carry = value;
		for (let j = 0; j < bytes.length; j += 1) {
			carry += bytes[j] * base;
			bytes[j] = carry & 0xff;
			carry = Math.floor(carry / 256);
		}
		while (carry > 0) {
			bytes.push(carry & 0xff);
			carry = Math.floor(carry / 256);
		}
	}
	let zeros = 0;
	while (zeros < cleaned.length && cleaned.charCodeAt(zeros) === start) zeros += 1;
	const output = new Uint8Array(zeros + bytes.length);
	for (let i = 0; i < zeros; i += 1) output[i] = 0;
	for (let i = 0; i < bytes.length; i += 1) {
		output[zeros + i] = bytes[bytes.length - 1 - i];
	}
	return output;
}

function encodeRulesCodeSafe(rules) {
	const json = JSON.stringify(rules || []);
	const encoded = getLZString().compressToEncodedURIComponent(json);
	if (!encoded) throw new Error("Compression failed.");
	return encoded;
}

function decodeRulesCodeSafe(code) {
	const cleaned = String(code || "").trim();
	if (!cleaned) throw new Error("Code is empty.");
	const json = getLZString().decompressFromEncodedURIComponent(cleaned);
	if (!json) throw new Error("Invalid or corrupted code.");
	const parsed = JSON.parse(json);
	return extractRules(parsed);
}

function encodeRulesCodeCjk(rules) {
	const json = JSON.stringify(rules || []);
	const compressed = getLZString().compress(json);
	if (!compressed) throw new Error("Compression failed.");
	const bytes = stringToBytes(compressed);
	const encoded = encodeBase16384(bytes);
	if (!encoded) throw new Error("Compression failed.");
	if (!isCjkCode(encoded)) throw new Error("CJK encoding produced invalid characters.");
	return encoded;
}

function decodeRulesCodeCjk(code) {
	const bytes = decodeBase16384(code);
	const compressed = bytesToString(bytes);
	const json = getLZString().decompress(compressed);
	if (!json) throw new Error("Invalid or corrupted code.");
	const parsed = JSON.parse(json);
	return extractRules(parsed);
}

function encodeRulesCode(rules, useCjk) {
	return useCjk ? encodeRulesCodeCjk(rules) : encodeRulesCodeSafe(rules);
}

function decodeRulesCode(code, preferCjk) {
	const cleaned = String(code || "").trim();
	if (!cleaned) throw new Error("Code is empty.");
	if (preferCjk) {
		try {
			return decodeRulesCodeCjk(cleaned);
		}
		catch (error) {
			return decodeRulesCodeSafe(cleaned);
		}
	}
	if (isCjkCode(cleaned)) return decodeRulesCodeCjk(cleaned);
	try {
		return decodeRulesCodeSafe(cleaned);
	}
	catch (error) {
		return decodeRulesCodeCjk(cleaned);
	}
}

/**
 * @name LexiShift
 * @author myuurin
 * @version 0.1.0
 * @description Replace message text using vocab rules.
 */

module.exports = (_ => {
	const changeLog = {};

	return !window.BDFDB_Global || (!window.BDFDB_Global.loaded && !window.BDFDB_Global.started) ? class {
		constructor (meta) {for (let key in meta) this[key] = meta[key];}
		getName () {return this.name;}
		getAuthor () {return this.author;}
		getVersion () {return this.version;}
		getDescription () {return `The Library Plugin needed for ${this.name} is missing. Open the Plugin Settings to download it. \n\n${this.description}`;}

		downloadLibrary () {
			BdApi.Net.fetch("https://mwittrien.github.io/BetterDiscordAddons/Library/0BDFDB.plugin.js").then(r => {
				if (!r || r.status != 200) throw new Error();
				else return r.text();
			}).then(b => {
				if (!b) throw new Error();
				else return require("fs").writeFile(require("path").join(BdApi.Plugins.folder, "0BDFDB.plugin.js"), b, _ => BdApi.UI.showToast("Finished downloading BDFDB Library", {type: "success"}));
			}).catch(error => {
				BdApi.UI.alert("Error", "Could not download BDFDB Library Plugin. Try again later or download it manually from GitHub: https://mwittrien.github.io/downloader/?library");
			});
		}

		load () {
			if (!window.BDFDB_Global || !Array.isArray(window.BDFDB_Global.pluginQueue)) window.BDFDB_Global = Object.assign({}, window.BDFDB_Global, {pluginQueue: []});
			if (!window.BDFDB_Global.downloadModal) {
				window.BDFDB_Global.downloadModal = true;
				BdApi.UI.showConfirmationModal("Library Missing", `The Library Plugin needed for ${this.name} is missing. Please click "Download Now" to install it.`, {
					confirmText: "Download Now",
					cancelText: "Cancel",
					onCancel: _ => {delete window.BDFDB_Global.downloadModal;},
					onConfirm: _ => {
						delete window.BDFDB_Global.downloadModal;
						this.downloadLibrary();
					}
				});
			}
			if (!window.BDFDB_Global.pluginQueue.includes(this.name)) window.BDFDB_Global.pluginQueue.push(this.name);
		}
		start () {this.load();}
		stop () {}
		getSettingsPanel () {
			let template = document.createElement("template");
			template.innerHTML = `<div style="color: var(--text-primary); font-size: 16px; font-weight: 300; white-space: pre; line-height: 22px;">The Library Plugin needed for ${this.name} is missing.\nPlease click <a style="font-weight: 500;">Download Now</a> to install it.</div>`;
			template.content.firstElementChild.querySelector("a").addEventListener("click", this.downloadLibrary);
			return template.content.firstElementChild;
		}
	} : (([Plugin, BDFDB]) => {

const TOKEN_RE = /[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*|\s+|[^\w\s]+/g;
const WORD_RE = /^[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*$/;

var CJK_BASE_START = 0x4E00;
var CJK_BASE = 16384;

const MARKER_START = "\uE000LS:";
const MARKER_MID = "\uE001";
const MARKER_END = "\uE002";
const STYLE_ID = "lexishift-replacements";
const STYLE_RULES = `
.ls-replaced {
	cursor: pointer;
}
.ls-replaced.ls-highlight {
	color: var(--text-muted);
	transition: color 120ms ease;
}
.ls-replaced .ls-original {
	display: none;
}
.ls-replaced.ls-show-original .ls-replacement {
	display: none;
}
.ls-replaced.ls-show-original .ls-original {
	display: inline;
	color: var(--text-normal);
}
`;

let rules = [];
let trie = null;
let oldMessages = {};

var lzString;

function getLZString () {
	if (!lzString) {
		lzString = (function () {
			const f = String.fromCharCode;
			const keyStrUriSafe = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-$";
			const baseReverseDic = {};

			function getBaseValue(alphabet, character) {
				if (!baseReverseDic[alphabet]) {
					baseReverseDic[alphabet] = {};
					for (let i = 0; i < alphabet.length; i += 1) {
						baseReverseDic[alphabet][alphabet.charAt(i)] = i;
					}
				}
				return baseReverseDic[alphabet][character];
			}

			function compressToEncodedURIComponent(input) {
				if (input == null) return "";
				return _compress(input, 6, function (a) { return keyStrUriSafe.charAt(a); });
			}

			function decompressFromEncodedURIComponent(input) {
				if (input == null) return "";
				if (input === "") return null;
				input = input.replace(/ /g, "+");
				return _decompress(input.length, 32, function (index) {
					return getBaseValue(keyStrUriSafe, input.charAt(index));
				});
			}

			function _compress(uncompressed, bitsPerChar, getCharFromInt) {
				if (uncompressed == null) return "";
				let i;
				let value;
				const context_dictionary = {};
				const context_dictionaryToCreate = {};
				let context_c = "";
				let context_wc = "";
				let context_w = "";
				let context_enlargeIn = 2;
				let context_dictSize = 3;
				let context_numBits = 2;
				let context_data = [];
				let context_data_val = 0;
				let context_data_position = 0;

				for (let ii = 0; ii < uncompressed.length; ii += 1) {
					context_c = uncompressed.charAt(ii);
					if (!Object.prototype.hasOwnProperty.call(context_dictionary, context_c)) {
						context_dictionary[context_c] = context_dictSize++;
						context_dictionaryToCreate[context_c] = true;
					}

					context_wc = context_w + context_c;
					if (Object.prototype.hasOwnProperty.call(context_dictionary, context_wc)) {
						context_w = context_wc;
					}
					else {
						if (Object.prototype.hasOwnProperty.call(context_dictionaryToCreate, context_w)) {
							if (context_w.charCodeAt(0) < 256) {
								for (i = 0; i < context_numBits; i += 1) {
									context_data_val = (context_data_val << 1);
									if (context_data_position === bitsPerChar - 1) {
										context_data_position = 0;
										context_data.push(getCharFromInt(context_data_val));
										context_data_val = 0;
									}
									else {
										context_data_position += 1;
									}
								}
								value = context_w.charCodeAt(0);
								for (i = 0; i < 8; i += 1) {
									context_data_val = (context_data_val << 1) | (value & 1);
									if (context_data_position === bitsPerChar - 1) {
										context_data_position = 0;
										context_data.push(getCharFromInt(context_data_val));
										context_data_val = 0;
									}
									else {
										context_data_position += 1;
									}
									value = value >> 1;
								}
							}
							else {
								value = 1;
								for (i = 0; i < context_numBits; i += 1) {
									context_data_val = (context_data_val << 1) | value;
									if (context_data_position === bitsPerChar - 1) {
										context_data_position = 0;
										context_data.push(getCharFromInt(context_data_val));
										context_data_val = 0;
									}
									else {
										context_data_position += 1;
									}
									value = 0;
								}
								value = context_w.charCodeAt(0);
								for (i = 0; i < 16; i += 1) {
									context_data_val = (context_data_val << 1) | (value & 1);
									if (context_data_position === bitsPerChar - 1) {
										context_data_position = 0;
										context_data.push(getCharFromInt(context_data_val));
										context_data_val = 0;
									}
									else {
										context_data_position += 1;
									}
									value = value >> 1;
								}
							}
							context_enlargeIn -= 1;
							if (context_enlargeIn === 0) {
								context_enlargeIn = Math.pow(2, context_numBits);
								context_numBits += 1;
							}
							delete context_dictionaryToCreate[context_w];
						}
						else {
							value = context_dictionary[context_w];
							for (i = 0; i < context_numBits; i += 1) {
								context_data_val = (context_data_val << 1) | (value & 1);
								if (context_data_position === bitsPerChar - 1) {
									context_data_position = 0;
									context_data.push(getCharFromInt(context_data_val));
									context_data_val = 0;
								}
								else {
									context_data_position += 1;
								}
								value = value >> 1;
							}
						}
						context_enlargeIn -= 1;
						if (context_enlargeIn === 0) {
							context_enlargeIn = Math.pow(2, context_numBits);
							context_numBits += 1;
						}
						context_dictionary[context_wc] = context_dictSize++;
						context_w = String(context_c);
					}
				}

				if (context_w !== "") {
					if (Object.prototype.hasOwnProperty.call(context_dictionaryToCreate, context_w)) {
						if (context_w.charCodeAt(0) < 256) {
							for (i = 0; i < context_numBits; i += 1) {
								context_data_val = (context_data_val << 1);
								if (context_data_position === bitsPerChar - 1) {
									context_data_position = 0;
									context_data.push(getCharFromInt(context_data_val));
									context_data_val = 0;
								}
								else {
									context_data_position += 1;
								}
							}
							value = context_w.charCodeAt(0);
							for (i = 0; i < 8; i += 1) {
								context_data_val = (context_data_val << 1) | (value & 1);
								if (context_data_position === bitsPerChar - 1) {
									context_data_position = 0;
									context_data.push(getCharFromInt(context_data_val));
									context_data_val = 0;
								}
								else {
									context_data_position += 1;
								}
								value = value >> 1;
							}
						}
						else {
							value = 1;
							for (i = 0; i < context_numBits; i += 1) {
								context_data_val = (context_data_val << 1) | value;
								if (context_data_position === bitsPerChar - 1) {
									context_data_position = 0;
									context_data.push(getCharFromInt(context_data_val));
									context_data_val = 0;
								}
								else {
									context_data_position += 1;
								}
								value = 0;
							}
							value = context_w.charCodeAt(0);
							for (i = 0; i < 16; i += 1) {
								context_data_val = (context_data_val << 1) | (value & 1);
								if (context_data_position === bitsPerChar - 1) {
									context_data_position = 0;
									context_data.push(getCharFromInt(context_data_val));
									context_data_val = 0;
								}
								else {
									context_data_position += 1;
								}
								value = value >> 1;
							}
						}
						context_enlargeIn -= 1;
						if (context_enlargeIn === 0) {
							context_enlargeIn = Math.pow(2, context_numBits);
							context_numBits += 1;
						}
						delete context_dictionaryToCreate[context_w];
					}
					else {
						value = context_dictionary[context_w];
						for (i = 0; i < context_numBits; i += 1) {
							context_data_val = (context_data_val << 1) | (value & 1);
							if (context_data_position === bitsPerChar - 1) {
								context_data_position = 0;
								context_data.push(getCharFromInt(context_data_val));
								context_data_val = 0;
							}
							else {
								context_data_position += 1;
							}
							value = value >> 1;
						}
					}
					context_enlargeIn -= 1;
					if (context_enlargeIn === 0) {
						context_enlargeIn = Math.pow(2, context_numBits);
						context_numBits += 1;
					}
				}

				value = 2;
				for (i = 0; i < context_numBits; i += 1) {
					context_data_val = (context_data_val << 1) | (value & 1);
					if (context_data_position === bitsPerChar - 1) {
						context_data_position = 0;
						context_data.push(getCharFromInt(context_data_val));
						context_data_val = 0;
					}
					else {
						context_data_position += 1;
					}
					value = value >> 1;
				}

				while (true) {
					context_data_val = (context_data_val << 1);
					if (context_data_position === bitsPerChar - 1) {
						context_data.push(getCharFromInt(context_data_val));
						break;
					}
					else context_data_position += 1;
				}

				return context_data.join("");
			}

			function _decompress(length, resetValue, getNextValue) {
				const dictionary = [];
				let next;
				let enlargeIn = 4;
				let dictSize = 4;
				let numBits = 3;
				let entry = "";
				let result = [];
				let i;
				let w;
				let bits;
				let resb;
				let maxpower;
				let power;
				let c;

				const data = {val: getNextValue(0), position: resetValue, index: 1};

				for (i = 0; i < 3; i += 1) {
					dictionary[i] = i;
				}

				bits = 0;
				maxpower = Math.pow(2, 2);
				power = 1;
				while (power !== maxpower) {
					resb = data.val & data.position;
					data.position >>= 1;
					if (data.position === 0) {
						data.position = resetValue;
						data.val = getNextValue(data.index++);
					}
					bits |= (resb > 0 ? 1 : 0) * power;
					power <<= 1;
				}

				switch (next = bits) {
					case 0:
						bits = 0;
						maxpower = Math.pow(2, 8);
						power = 1;
						while (power !== maxpower) {
							resb = data.val & data.position;
							data.position >>= 1;
							if (data.position === 0) {
								data.position = resetValue;
								data.val = getNextValue(data.index++);
							}
							bits |= (resb > 0 ? 1 : 0) * power;
							power <<= 1;
						}
						c = f(bits);
						break;
					case 1:
						bits = 0;
						maxpower = Math.pow(2, 16);
						power = 1;
						while (power !== maxpower) {
							resb = data.val & data.position;
							data.position >>= 1;
							if (data.position === 0) {
								data.position = resetValue;
								data.val = getNextValue(data.index++);
							}
							bits |= (resb > 0 ? 1 : 0) * power;
							power <<= 1;
						}
						c = f(bits);
						break;
					case 2:
						return "";
				}
				dictionary[3] = c;
				w = c;
				result.push(c);

				while (true) {
					if (data.index > length) {
						return "";
					}

					bits = 0;
					maxpower = Math.pow(2, numBits);
					power = 1;
					while (power !== maxpower) {
						resb = data.val & data.position;
						data.position >>= 1;
						if (data.position === 0) {
							data.position = resetValue;
							data.val = getNextValue(data.index++);
						}
						bits |= (resb > 0 ? 1 : 0) * power;
						power <<= 1;
					}

					switch (c = bits) {
						case 0:
							bits = 0;
							maxpower = Math.pow(2, 8);
							power = 1;
							while (power !== maxpower) {
								resb = data.val & data.position;
								data.position >>= 1;
								if (data.position === 0) {
									data.position = resetValue;
									data.val = getNextValue(data.index++);
								}
								bits |= (resb > 0 ? 1 : 0) * power;
								power <<= 1;
							}
							dictionary[dictSize++] = f(bits);
							c = dictSize - 1;
							enlargeIn -= 1;
							break;
						case 1:
							bits = 0;
							maxpower = Math.pow(2, 16);
							power = 1;
							while (power !== maxpower) {
								resb = data.val & data.position;
								data.position >>= 1;
								if (data.position === 0) {
									data.position = resetValue;
									data.val = getNextValue(data.index++);
								}
								bits |= (resb > 0 ? 1 : 0) * power;
								power <<= 1;
							}
							dictionary[dictSize++] = f(bits);
							c = dictSize - 1;
							enlargeIn -= 1;
							break;
						case 2:
							return result.join("");
					}

					if (enlargeIn === 0) {
						enlargeIn = Math.pow(2, numBits);
						numBits += 1;
					}

					if (dictionary[c]) {
						entry = dictionary[c];
					}
					else {
						if (c === dictSize) {
							entry = w + w.charAt(0);
						}
						else {
							return null;
						}
					}
					result.push(entry);

					dictionary[dictSize++] = w + entry.charAt(0);
					enlargeIn -= 1;

					w = entry;

					if (enlargeIn === 0) {
						enlargeIn = Math.pow(2, numBits);
						numBits += 1;
					}
				}
			}

			function compress(uncompressed) {
				return _compress(uncompressed, 16, function (a) { return f(a); });
			}

			function decompress(compressed) {
				if (compressed == null) return "";
				if (compressed === "") return null;
				return _decompress(compressed.length, 32768, function (index) {
					return compressed.charCodeAt(index);
				});
			}

			return {
				compress,
				decompress,
				compressToEncodedURIComponent,
				decompressFromEncodedURIComponent
			};
		})();
	}
	return lzString;
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

function buildSettingsPanel(plugin) {
	const panel = document.createElement("div");
	panel.style.padding = "10px";
	panel.style.minWidth = "520px";
	panel.style.minHeight = "520px";

	const description = document.createElement("div");
	description.textContent = "Choose a rules source: paste JSON or load a local file.";
	description.style.marginBottom = "8px";
	panel.appendChild(description);

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

		return class LexiShift extends Plugin {
			onLoad () {
				this.defaults = {
					general: {
						targetMessages: {value: true, description: "Replace words in messages"}
					}
				};

				this.modulePatches = {
					before: ["Messages", "Message"],
					after: ["MessageContent"]
				};
			}

			onStart () {
				this._loadPreferences();
				if (this._useFileRules && this._rulesFilePath) {
					const loaded = this._loadRulesFromFile(this._rulesFilePath);
					if (!loaded.ok) {
						rules = BDFDB.DataUtils.load(this, "rules");
						if (!Array.isArray(rules)) rules = [];
						trie = buildTrie(normalizeRules(rules));
						oldMessages = {};
					}
				}
				else {
					rules = BDFDB.DataUtils.load(this, "rules");
					if (!Array.isArray(rules)) rules = [];
					trie = buildTrie(normalizeRules(rules));
					oldMessages = {};
				}
				this._installStyle();
				this._startMarkerObserver();
				this.requestRefresh();
			}

			onStop () {
				this._removeStyle();
				this._stopMarkerObserver();
				this.requestRefresh();
			}

			getSettingsPanel () {
				return buildSettingsPanel(this);
			}

			requestRefresh () {
				if (typeof this.forceUpdateAll === "function") {
					this.forceUpdateAll();
					return;
				}
				if (BDFDB && BDFDB.PluginUtils && typeof BDFDB.PluginUtils.forceUpdateAll === "function") {
					BDFDB.PluginUtils.forceUpdateAll(this);
				}
			}

			processMessages (e) {
				if (!this.settings.general.targetMessages) return;
				e.instance.props.channelStream = [].concat(e.instance.props.channelStream);
				for (let i in e.instance.props.channelStream) {
					let message = e.instance.props.channelStream[i].content;
					if (message) {
						if (BDFDB.ArrayUtils.is(message.attachments)) this.checkMessage(e.instance.props.channelStream[i], message);
						else if (BDFDB.ArrayUtils.is(message)) for (let j in message) {
							let childMessage = message[j].content;
							if (childMessage && BDFDB.ArrayUtils.is(childMessage.attachments)) this.checkMessage(message[j], childMessage);
						}
					}
				}
			}

			processMessage (e) {
				if (!this.settings.general.targetMessages) return;
				let repliedMessage = e.instance.props.childrenRepliedMessage;
				if (repliedMessage && repliedMessage.props && repliedMessage.props.children && repliedMessage.props.children.props && repliedMessage.props.children.props.referencedMessage && repliedMessage.props.children.props.referencedMessage.message) {
					let message = repliedMessage.props.children.props.referencedMessage.message;
					if (oldMessages[message.id]) {
						let {content, embeds} = this.parseMessage(message);
						repliedMessage.props.children.props.referencedMessage.message = new BDFDB.DiscordObjects.Message(Object.assign({}, message, {content, embeds}));
					}
				}
			}

			processMessageContent (e) {
				if (!this.settings.general.targetMessages) return;
				if (!e || !e.returnvalue) return;
				const replaced = replaceMarkersInTree(e.returnvalue, this);
				if (Array.isArray(replaced)) {
					e.returnvalue = BdApi.React.createElement(BdApi.React.Fragment, null, ...replaced);
				}
				else {
					e.returnvalue = replaced;
				}
			}

			checkMessage (stream, message) {
				let {changed, content, embeds} = this.parseMessage(message);
				if (changed) {
					if (!oldMessages[message.id]) oldMessages[message.id] = new BDFDB.DiscordObjects.Message(message);
					stream.content.content = content;
					stream.content.embeds = embeds;
				}
				else if (oldMessages[message.id]) {
					stream.content.content = oldMessages[message.id].content;
					stream.content.embeds = oldMessages[message.id].embeds;
					delete oldMessages[message.id];
				}
			}

			parseMessage (message) {
				let content = message.content;
				let embeds = [].concat(message.embeds || []);
				let changed = false;
				if (content && typeof content == "string") {
					let replaced = replaceText(content, trie, {annotate: true});
					if (replaced !== content) {
						content = replaced;
						changed = true;
					}
				}
				if (embeds.length) {
					embeds = embeds.map(embed => {
						let raw = embed.rawDescription || embed.description;
						if (!raw || typeof raw !== "string") return embed;
						let replaced = replaceText(raw, trie, {annotate: false});
						if (replaced === raw) return embed;
						changed = true;
						return Object.assign({}, embed, {rawDescription: replaced, description: replaced});
					});
				}
				return {changed, content, embeds};
			}

			_loadPreferences () {
				const prefs = BDFDB.DataUtils.load(this, "prefs") || {};
				this._highlightReplacements = prefs.highlightReplacements !== false;
				this._highlightColor = prefs.highlightColor || "#9AA0A6";
				this._useFileRules = prefs.useFileRules === true;
				this._rulesFilePath = prefs.rulesFilePath || "";
			}

			_savePreferences () {
				BDFDB.DataUtils.save(
					{
						highlightReplacements: this._highlightReplacements,
						highlightColor: this._highlightColor,
						useFileRules: this._useFileRules,
						rulesFilePath: this._rulesFilePath
					},
					this,
					"prefs"
				);
			}

			getHighlightReplacements () {
				return this._highlightReplacements !== false;
			}

			setHighlightReplacements (value) {
				this._highlightReplacements = Boolean(value);
				this._savePreferences();
				this._applyHighlightToDom();
				this.requestRefresh();
			}

			getHighlightColor () {
				return this._highlightColor || "#9AA0A6";
			}

			setHighlightColor (value) {
				this._highlightColor = value || "#9AA0A6";
				this._savePreferences();
				this._applyHighlightToDom();
				this.requestRefresh();
			}

			getUseFileRules () {
				return this._useFileRules === true;
			}

			setUseFileRules (value, skipLoad) {
				this._useFileRules = Boolean(value);
				this._savePreferences();
				if (!skipLoad && this._useFileRules && this._rulesFilePath) {
					this._loadRulesFromFile(this._rulesFilePath);
				}
				this.requestRefresh();
			}

			getRulesFilePath () {
				return this._rulesFilePath || "";
			}

			setRulesFilePath (path) {
				this._rulesFilePath = String(path || "");
				this._savePreferences();
			}

			loadRulesFromFile (path) {
				return this._loadRulesFromFile(path);
			}

			_loadRulesFromFile (path) {
				try {
					const fs = require("fs");
					const payload = fs.readFileSync(path, "utf8");
					const parsed = JSON.parse(payload);
					rules = extractRules(parsed);
					BDFDB.DataUtils.save(rules, this, "rules");
					trie = buildTrie(normalizeRules(rules));
					oldMessages = {};
					return {ok: true};
				}
				catch (error) {
					return {ok: false, error};
				}
			}

			_installStyle () {
				if (BdApi.DOM && typeof BdApi.DOM.addStyle === "function") {
					BdApi.DOM.addStyle(STYLE_ID, STYLE_RULES);
				}
			}

			_removeStyle () {
				if (BdApi.DOM && typeof BdApi.DOM.removeStyle === "function") {
					BdApi.DOM.removeStyle(STYLE_ID);
				}
			}

			_startMarkerObserver () {
				if (this._markerObserver || !document || !document.body) return;
				this._markerObserver = new MutationObserver(mutations => {
					if (this._markerReplacing) return;
					this._markerReplacing = true;
					try {
						for (const mutation of mutations) {
							for (const node of mutation.addedNodes) {
								if (node && node.nodeType === Node.ELEMENT_NODE) {
									replaceMarkersInElement(node, this);
								}
								else if (node && node.nodeType === Node.TEXT_NODE && node.nodeValue) {
									if (node.nodeValue.indexOf(MARKER_START) !== -1 && node.parentNode) {
										replaceMarkersInElement(node.parentNode, this);
									}
								}
							}
						}
					}
					finally {
						this._markerReplacing = false;
					}
				});
				this._markerObserver.observe(document.body, {childList: true, subtree: true});
				replaceMarkersInElement(document.body, this);
			}

			_stopMarkerObserver () {
				if (!this._markerObserver) return;
				this._markerObserver.disconnect();
				this._markerObserver = null;
			}

			_applyHighlightToDom () {
				if (!document) return;
				const highlight = this.getHighlightReplacements();
				const color = this.getHighlightColor();
				for (const node of document.querySelectorAll(".ls-replaced")) {
					if (highlight) {
						node.classList.add("ls-highlight");
						node.style.color = color;
					}
					else {
						node.classList.remove("ls-highlight");
						node.style.color = "";
					}
				}
			}
		};

	})(window.BDFDB_Global.PluginUtils.buildPlugin(changeLog));
})();

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

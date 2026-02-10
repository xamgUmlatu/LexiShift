(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  const TOKEN_RE = /[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*|\s+|[^\w\s]+/g;
  const WORD_RE = /^[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*$/;

  function tokenize(text) {
    const tokens = [];
    const matches = text.matchAll(TOKEN_RE);
    for (const match of matches) {
      const chunk = match[0];
      let kind = "punct";
      if (WORD_RE.test(chunk)) {
        kind = "word";
      } else if (/^\s+$/.test(chunk)) {
        kind = "space";
      }
      tokens.push({ text: chunk, kind });
    }
    return tokens;
  }

  function normalize(word) {
    return word.toLowerCase();
  }

  function textHasToken(text, token) {
    if (!text || !token) {
      return false;
    }
    const tokens = tokenize(text);
    return tokens.some((item) => item.kind === "word" && item.text.toLowerCase() === token);
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

  root.tokenizer = { TOKEN_RE, WORD_RE, tokenize, normalize, textHasToken, computeGapOk };
})();

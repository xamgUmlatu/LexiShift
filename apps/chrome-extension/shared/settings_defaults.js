(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  root.defaults = {
    enabled: true,
    rules: [],
    highlightEnabled: true,
    highlightColor: "#9AA0A6",
    maxOnePerTextBlock: false,
    allowAdjacentReplacements: true,
    debugEnabled: false,
    debugFocusWord: "",
    rulesSource: "editor",
    rulesFileName: "",
    rulesUpdatedAt: ""
  };
})();

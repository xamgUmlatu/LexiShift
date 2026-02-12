class HelperManager {
  constructor(i18n, logger) {
    this.i18n = i18n;
    this.logger = logger || console.log;
  }
}

(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const installers = [
    ["installHelperBaseMethods", root.installHelperBaseMethods],
    ["installHelperDiagnosticsMethods", root.installHelperDiagnosticsMethods],
    ["installHelperSrsSetMethods", root.installHelperSrsSetMethods]
  ];
  for (const [name, install] of installers) {
    if (typeof install !== "function") {
      throw new Error(`[LexiShift][Options] Missing HelperManager installer: ${name}`);
    }
    install(HelperManager.prototype);
  }
})();

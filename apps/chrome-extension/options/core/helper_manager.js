class HelperManager {
  constructor(i18n, logger) {
    this.i18n = i18n;
    this.logger = logger || console.log;
  }
}

(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});
  const installers = [
    root.installHelperBaseMethods,
    root.installHelperDiagnosticsMethods,
    root.installHelperSrsSetMethods
  ];
  for (const install of installers) {
    if (typeof install === "function") {
      install(HelperManager.prototype);
    }
  }
})();

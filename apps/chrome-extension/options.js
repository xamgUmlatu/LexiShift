const settingsManager = new SettingsManager();

const i18n = new LocalizationService();
const t = (k, s, f) => i18n.t(k, s, f);
const rulesManager = new RulesManager(settingsManager, i18n);
const ui = new UIManager(i18n);

function logOptions(...args) {
  console.log("[LexiShift][Options]", ...args);
}
const helperManager = new HelperManager(i18n, logOptions);

function errorMessage(err, fallbackKey, fallbackText) {
  if (err instanceof SyntaxError) {
    return t(fallbackKey, null, fallbackText);
  }
  if (err && err.message) {
    return err.message;
  }
  return t(fallbackKey, null, fallbackText);
}

i18n.apply();

const uiBridgeFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsUiBridge
  && typeof globalThis.LexiShift.optionsUiBridge.createUiBridge === "function"
  ? globalThis.LexiShift.optionsUiBridge.createUiBridge
  : null;
if (!uiBridgeFactory) {
  throw new Error("[LexiShift][Options] Missing required bootstrap module: optionsUiBridge");
}
const uiBridge = uiBridgeFactory({ ui });

const controllerFactoryResolverFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsControllerFactoryResolver
  && typeof globalThis.LexiShift.optionsControllerFactoryResolver.createResolver === "function"
  ? globalThis.LexiShift.optionsControllerFactoryResolver.createResolver
  : null;
if (!controllerFactoryResolverFactory) {
  throw new Error("[LexiShift][Options] Missing required bootstrap module: optionsControllerFactoryResolver");
}
const controllerFactoryResolver = controllerFactoryResolverFactory();
const requireControllerFactory = controllerFactoryResolver.requireControllerFactory;

const domAliasesFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsDomAliases
  && typeof globalThis.LexiShift.optionsDomAliases.createDomAliases === "function"
  ? globalThis.LexiShift.optionsDomAliases.createDomAliases
  : null;
if (!domAliasesFactory) {
  throw new Error("[LexiShift][Options] Missing required bootstrap module: optionsDomAliases");
}
const dom = domAliasesFactory(ui.dom);

const controllerGraphFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsControllerGraph
  && typeof globalThis.LexiShift.optionsControllerGraph.createControllerGraph === "function"
  ? globalThis.LexiShift.optionsControllerGraph.createControllerGraph
  : null;
if (!controllerGraphFactory) {
  throw new Error("[LexiShift][Options] Missing required bootstrap module: optionsControllerGraph");
}

const languagePrefsAdapterFactory = globalThis.LexiShift
  && globalThis.LexiShift.optionsLanguagePrefsAdapter
  && typeof globalThis.LexiShift.optionsLanguagePrefsAdapter.createAdapter === "function"
  ? globalThis.LexiShift.optionsLanguagePrefsAdapter.createAdapter
  : null;

const app = controllerGraphFactory({
  settingsManager,
  i18n,
  t,
  rulesManager,
  ui,
  helperManager,
  uiBridge,
  requireControllerFactory,
  languagePrefsAdapterFactory,
  errorMessage,
  logOptions,
  dom
});

app.eventWiringController.bind();
app.pageInitController.load();

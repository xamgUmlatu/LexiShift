(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createController(options) {
    const opts = options && typeof options === "object" ? options : {};
    const output = opts.output || null;
    const translate = root.optionsTranslateResolver.resolveTranslate(opts.t);
    let state = opts.initialState && typeof opts.initialState === "object"
      ? { ...opts.initialState }
      : {
          mode: "i18n",
          key: "hint_profile_loading",
          substitutions: null,
          fallback: "Loading profiles…"
        };

    function render() {
      if (!output) {
        return;
      }
      if (state && state.mode === "message") {
        output.textContent = String(state.message || "");
        return;
      }
      const resolved = state && typeof state === "object"
        ? state
        : { key: "hint_profile_loading", substitutions: null, fallback: "Loading profiles…" };
      output.textContent = translate(
        resolved.key || "hint_profile_loading",
        resolved.substitutions || null,
        resolved.fallback || "Loading profiles…"
      );
    }

    function setLocalized(key, substitutions, fallback) {
      state = {
        mode: "i18n",
        key: String(key || "").trim() || "hint_profile_loading",
        substitutions: substitutions === undefined ? null : substitutions,
        fallback: String(fallback || "Loading profiles…")
      };
      render();
    }

    function setMessage(message) {
      state = {
        mode: "message",
        message: String(message || "")
      };
      render();
    }

    function getState() {
      return state && typeof state === "object" ? { ...state } : state;
    }

    return {
      render,
      setLocalized,
      setMessage,
      getState
    };
  }

  root.optionsProfileStatus = {
    createController
  };
})();

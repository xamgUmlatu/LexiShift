(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createManager(options) {
    const opts = options && typeof options === "object" ? options : {};
    const documentRef = opts.documentRef && opts.documentRef.body
      ? opts.documentRef
      : document;
    const normalizeBackdropColor = typeof opts.normalizeBackdropColor === "function"
      ? opts.normalizeBackdropColor
      : (value) => String(value || "").trim();
    const clampOpacity = typeof opts.clampOpacity === "function"
      ? opts.clampOpacity
      : (value) => Number(value);
    const hexColorToRgb = typeof opts.hexColorToRgb === "function"
      ? opts.hexColorToRgb
      : (_value) => ({ r: 251, g: 247, b: 240 });
    const urlApi = opts.urlApi && typeof opts.urlApi.createObjectURL === "function"
      && typeof opts.urlApi.revokeObjectURL === "function"
      ? opts.urlApi
      : URL;
    let appliedObjectUrl = "";

    function revokeAppliedUrl() {
      if (!appliedObjectUrl) {
        return;
      }
      urlApi.revokeObjectURL(appliedObjectUrl);
      appliedObjectUrl = "";
    }

    function clearBackgroundImageLayer() {
      revokeAppliedUrl();
      documentRef.body.style.removeProperty("background-image");
      documentRef.body.style.removeProperty("background-size");
      documentRef.body.style.removeProperty("background-position");
      documentRef.body.style.removeProperty("background-attachment");
    }

    function clearBackground() {
      clearBackgroundImageLayer();
      documentRef.body.style.removeProperty("background-color");
    }

    function applyBackdropColor(backdropColor) {
      documentRef.body.style.backgroundColor = normalizeBackdropColor(backdropColor);
    }

    function applyBackdropOnly(backdropColor) {
      clearBackgroundImageLayer();
      applyBackdropColor(backdropColor);
      // Override CSS default radial gradient when only a solid backdrop is desired.
      documentRef.body.style.backgroundImage = "none";
    }

    function applyBackgroundFromBlob(blob, opacity, backdropColor) {
      if (!(blob instanceof Blob)) {
        clearBackground();
        return;
      }
      revokeAppliedUrl();
      appliedObjectUrl = urlApi.createObjectURL(blob);
      const clamped = clampOpacity(opacity);
      const color = normalizeBackdropColor(backdropColor);
      const rgb = hexColorToRgb(color);
      const wash = Math.max(0, Math.min(1, 1 - clamped));
      documentRef.body.style.backgroundColor = color;
      documentRef.body.style.backgroundImage = `linear-gradient(rgba(${rgb.r},${rgb.g},${rgb.b},${wash}), rgba(${rgb.r},${rgb.g},${rgb.b},${wash})), url("${appliedObjectUrl}")`;
      documentRef.body.style.backgroundSize = "cover";
      documentRef.body.style.backgroundPosition = "center center";
      documentRef.body.style.backgroundAttachment = "fixed";
    }

    function dispose() {
      revokeAppliedUrl();
    }

    return {
      applyBackdropOnly,
      applyBackgroundFromBlob,
      clearBackground,
      dispose
    };
  }

  root.optionsProfileBackgroundPageBackgroundManager = {
    createManager
  };
})();

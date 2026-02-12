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
    const clampPositionPercent = typeof opts.clampPositionPercent === "function"
      ? opts.clampPositionPercent
      : (value, fallback) => {
          const parsed = Number.parseFloat(value);
          const fallbackValue = Number.isFinite(Number(fallback)) ? Number(fallback) : 50;
          const base = Number.isFinite(parsed) ? parsed : fallbackValue;
          return Math.min(100, Math.max(0, base));
        };
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

    function normalizePosition(positionX, positionY) {
      return {
        x: clampPositionPercent(positionX, 50),
        y: clampPositionPercent(positionY, 50)
      };
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

    function applyBackgroundFromBlob(blob, opacity, backdropColor, positionX, positionY) {
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
      const position = normalizePosition(positionX, positionY);
      documentRef.body.style.backgroundColor = color;
      documentRef.body.style.backgroundImage = `linear-gradient(rgba(${rgb.r},${rgb.g},${rgb.b},${wash}), rgba(${rgb.r},${rgb.g},${rgb.b},${wash})), url("${appliedObjectUrl}")`;
      documentRef.body.style.backgroundSize = "cover";
      documentRef.body.style.backgroundPosition = `${position.x}% ${position.y}%`;
      documentRef.body.style.backgroundAttachment = "fixed";
    }

    function setBackgroundPosition(positionX, positionY) {
      const position = normalizePosition(positionX, positionY);
      documentRef.body.style.backgroundPosition = `${position.x}% ${position.y}%`;
      return position;
    }

    function dispose() {
      revokeAppliedUrl();
    }

    return {
      applyBackdropOnly,
      applyBackgroundFromBlob,
      setBackgroundPosition,
      clearBackground,
      dispose
    };
  }

  root.optionsProfileBackgroundPageBackgroundManager = {
    createManager
  };
})();

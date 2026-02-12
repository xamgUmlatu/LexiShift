(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createManager(options) {
    const opts = options && typeof options === "object" ? options : {};
    const previewImage = opts.previewImage || null;
    const previewWrap = opts.previewWrap || null;
    const previewMarker = opts.previewMarker || null;
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
    let previewObjectUrl = "";
    let position = { x: 50, y: 50 };
    let dragState = {
      active: false,
      pointerId: null
    };
    let onPositionInput = () => {};
    let onPositionCommit = () => {};

    function normalizePosition(nextX, nextY) {
      return {
        x: clampPositionPercent(nextX, position.x),
        y: clampPositionPercent(nextY, position.y)
      };
    }

    function hasPreviewContent() {
      return Boolean(previewImage && previewImage.getAttribute("src"));
    }

    function applyPreviewPosition() {
      if (previewImage) {
        previewImage.style.objectPosition = `${position.x}% ${position.y}%`;
      }
      if (previewMarker) {
        previewMarker.style.left = `${position.x}%`;
        previewMarker.style.top = `${position.y}%`;
        if (hasPreviewContent()) {
          previewMarker.classList.remove("hidden");
        } else {
          previewMarker.classList.add("hidden");
        }
      }
    }

    function updatePositionFromPointer(event) {
      if (!previewWrap || !previewImage || !hasPreviewContent()) {
        return position;
      }
      const rect = previewWrap.getBoundingClientRect();
      if (!(rect.width > 0) || !(rect.height > 0)) {
        return position;
      }
      const ratioX = (event.clientX - rect.left) / rect.width;
      const ratioY = (event.clientY - rect.top) / rect.height;
      return setPreviewPosition(ratioX * 100, ratioY * 100);
    }

    function revokePreviewUrl() {
      if (!previewObjectUrl) {
        return;
      }
      urlApi.revokeObjectURL(previewObjectUrl);
      previewObjectUrl = "";
    }

    function clearPreview() {
      revokePreviewUrl();
      if (previewImage) {
        previewImage.removeAttribute("src");
      }
      if (previewMarker) {
        previewMarker.classList.add("hidden");
      }
      if (previewWrap) {
        previewWrap.classList.remove("is-dragging");
        previewWrap.classList.add("hidden");
      }
    }

    function setPreviewFromBlob(blob) {
      if (!(blob instanceof Blob) || !previewImage || !previewWrap) {
        clearPreview();
        return;
      }
      revokePreviewUrl();
      previewObjectUrl = urlApi.createObjectURL(blob);
      previewImage.src = previewObjectUrl;
      previewWrap.classList.remove("hidden");
      applyPreviewPosition();
    }

    function setPreviewPosition(nextX, nextY) {
      position = normalizePosition(nextX, nextY);
      applyPreviewPosition();
      return {
        x: position.x,
        y: position.y
      };
    }

    function getPreviewPosition() {
      return {
        x: position.x,
        y: position.y
      };
    }

    function bindPositionInteractions(handlers) {
      const localHandlers = handlers && typeof handlers === "object" ? handlers : {};
      onPositionInput = typeof localHandlers.onInput === "function" ? localHandlers.onInput : (() => {});
      onPositionCommit = typeof localHandlers.onCommit === "function" ? localHandlers.onCommit : (() => {});
    }

    function beginDrag(event) {
      if (!previewWrap || !previewImage || !hasPreviewContent()) {
        return;
      }
      if (event.button !== 0) {
        return;
      }
      dragState.active = true;
      dragState.pointerId = event.pointerId;
      if (typeof previewWrap.setPointerCapture === "function") {
        try {
          previewWrap.setPointerCapture(event.pointerId);
        } catch (_err) {}
      }
      previewWrap.classList.add("is-dragging");
      const next = updatePositionFromPointer(event);
      onPositionInput(next);
      event.preventDefault();
    }

    function continueDrag(event) {
      if (!dragState.active || event.pointerId !== dragState.pointerId) {
        return;
      }
      const next = updatePositionFromPointer(event);
      onPositionInput(next);
      event.preventDefault();
    }

    function endDrag(event) {
      if (!dragState.active || event.pointerId !== dragState.pointerId) {
        return;
      }
      const next = updatePositionFromPointer(event);
      if (previewWrap) {
        previewWrap.classList.remove("is-dragging");
        if (typeof previewWrap.releasePointerCapture === "function") {
          try {
            previewWrap.releasePointerCapture(event.pointerId);
          } catch (_err) {}
        }
      }
      dragState.active = false;
      dragState.pointerId = null;
      onPositionCommit(next);
      event.preventDefault();
    }

    if (previewWrap) {
      previewWrap.addEventListener("pointerdown", beginDrag);
      previewWrap.addEventListener("pointermove", continueDrag);
      previewWrap.addEventListener("pointerup", endDrag);
      previewWrap.addEventListener("pointercancel", endDrag);
    }

    function dispose() {
      revokePreviewUrl();
      if (previewWrap) {
        previewWrap.removeEventListener("pointerdown", beginDrag);
        previewWrap.removeEventListener("pointermove", continueDrag);
        previewWrap.removeEventListener("pointerup", endDrag);
        previewWrap.removeEventListener("pointercancel", endDrag);
      }
    }

    return {
      clearPreview,
      setPreviewFromBlob,
      setPreviewPosition,
      getPreviewPosition,
      bindPositionInteractions,
      dispose
    };
  }

  root.optionsProfileBackgroundPreviewManager = {
    createManager
  };
})();

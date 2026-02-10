(() => {
  const root = (globalThis.LexiShift = globalThis.LexiShift || {});

  function createManager(options) {
    const opts = options && typeof options === "object" ? options : {};
    const previewImage = opts.previewImage || null;
    const previewWrap = opts.previewWrap || null;
    const urlApi = opts.urlApi && typeof opts.urlApi.createObjectURL === "function"
      && typeof opts.urlApi.revokeObjectURL === "function"
      ? opts.urlApi
      : URL;
    let previewObjectUrl = "";

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
      if (previewWrap) {
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
    }

    function dispose() {
      revokePreviewUrl();
    }

    return {
      clearPreview,
      setPreviewFromBlob,
      dispose
    };
  }

  root.optionsProfileBackgroundPreviewManager = {
    createManager
  };
})();

# Chrome Web Store promotional artwork

Upload-ready artwork lives in `final/`; its reproducible ImageMagick renderer
lives in `source/`.

`small-promo-440x280.png` is a 24-bit RGB PNG without transparency at the
required 440 x 280 pixel size. The composition uses the shipping extension
icon, a compact LexiShift wordmark, and abstract replacement highlights so it
still reads clearly at half size without depending on a particular language
pair.

Regenerate it from the repository root with:

```bash
bash release-assets/chrome-web-store/promo/source/render_small_promo.sh
```

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
NODE_FILTERS_JS = PROJECT_ROOT / "apps/chrome-extension/content/runtime/dom_scan/node_filters.js"
FEEDBACK_POPUP_CONTROLLER_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/ui/feedback_popup_controller.js"
)
POPUP_LAYOUT_MEASUREMENT_JS = (
    PROJECT_ROOT / "apps/chrome-extension/content/ui/popup_layout_measurement.js"
)


def _run_node(script: str) -> None:
    result = subprocess.run(
        ["node"],
        input=script,
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "Node extension scan-skip contract test failed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestExtensionScanSkipContract(unittest.TestCase):
    def test_feedback_popup_placement_flips_and_bounds_tall_module_stacks(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const measurementPath = {json.dumps(str(POPUP_LAYOUT_MEASUREMENT_JS))};
const modulePath = {json.dumps(str(FEEDBACK_POPUP_CONTROLLER_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(measurementPath, "utf8"), context, {{ filename: measurementPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const measureNaturalHeight = context.LexiShift.uiPopupLayoutMeasurement.measureNaturalHeight;
const place = context.LexiShift.uiFeedbackPopupController.computePopupPlacement;
assert.equal(typeof measureNaturalHeight, "function");
assert.equal(typeof place, "function");

const naturalHeight = measureNaturalHeight(
  {{ getBoundingClientRect: () => ({{ height: 220 }}) }},
  {{ scrollHeight: 420, getBoundingClientRect: () => ({{ height: 140 }}) }}
);
assert.equal(naturalHeight, 500);

const below = place({{
  targetRect: {{ top: 200, bottom: 220, left: 300, right: 340, width: 40, height: 20 }},
  popupWidth: 240,
  popupHeight: 180,
  viewportWidth: 800,
  viewportHeight: 600,
  anchorPoint: {{ clientX: 320, clientY: 210 }}
}});
assert.equal(below.vertical, "below");
assert.equal(below.horizontal, "right");
assert.equal(below.top, 228);
assert.equal(below.left, 328);
assert.equal(below.maxHeight, 180);

const above = place({{
  targetRect: {{ top: 520, bottom: 540, left: 300, right: 340, width: 40, height: 20 }},
  popupWidth: 240,
  popupHeight: 180,
  viewportWidth: 800,
  viewportHeight: 600,
  anchorPoint: {{ clientX: 320, clientY: 530 }}
}});
assert.equal(above.vertical, "above");
assert.equal(above.top, 332);

const grownAbove = place({{
  targetRect: {{ top: 520, bottom: 540, left: 300, right: 340, width: 40, height: 20 }},
  popupWidth: 240,
  popupHeight: naturalHeight,
  viewportWidth: 800,
  viewportHeight: 600,
  anchorPoint: {{ clientX: 320, clientY: 530 }}
}});
assert.equal(grownAbove.vertical, "above");
assert.equal(grownAbove.top, 12);

const clampedToViewport = place({{
  targetRect: {{ top: 336, bottom: 350, left: 300, right: 340, width: 40, height: 14 }},
  popupWidth: 240,
  popupHeight: naturalHeight,
  viewportWidth: 800,
  viewportHeight: 600,
  anchorPoint: {{ clientX: 320, clientY: 343 }}
}});
assert.equal(clampedToViewport.vertical, "viewport");
assert.equal(clampedToViewport.top, 92);
assert.equal(clampedToViewport.maxHeight, 500);

const tall = place({{
  targetRect: {{ top: 280, bottom: 300, left: 300, right: 340, width: 40, height: 20 }},
  popupWidth: 240,
  popupHeight: 900,
  viewportWidth: 800,
  viewportHeight: 600,
  anchorPoint: {{ clientX: 320, clientY: 290 }}
}});
assert.equal(tall.vertical, "viewport");
assert.equal(tall.top, 8);
assert.equal(tall.maxHeight, 584);

const leftFlip = place({{
  targetRect: {{ top: 200, bottom: 220, left: 740, right: 780, width: 40, height: 20 }},
  popupWidth: 220,
  popupHeight: 180,
  viewportWidth: 800,
  viewportHeight: 600,
  anchorPoint: {{ clientX: 760, clientY: 210 }}
}});
assert.equal(leftFlip.horizontal, "left");
assert.equal(leftFlip.left, 532);

const narrow = place({{
  targetRect: {{ top: 200, bottom: 220, left: 180, right: 220, width: 40, height: 20 }},
  popupWidth: 1000,
  popupHeight: 180,
  viewportWidth: 400,
  viewportHeight: 600,
  anchorPoint: {{ clientX: 200, clientY: 210 }}
}});
assert.equal(narrow.left, 8);
assert.ok(narrow.maxHeight <= 584);
"""
        _run_node(script)

    def test_dom_scan_filter_skips_nested_non_rendered_subtrees(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(NODE_FILTERS_JS))};
const context = vm.createContext({{
  console,
  getComputedStyle(element) {{
    return element.computedStyle || {{
      display: "block",
      visibility: "visible",
      contentVisibility: "visible"
    }};
  }}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

function element(tagName, options = {{}}) {{
  return {{
    tagName,
    hidden: options.hidden === true,
    computedStyle: {{
      display: options.display || "block",
      visibility: options.visibility || "visible",
      contentVisibility: options.contentVisibility || "visible"
    }},
    parentElement: options.parentElement || null
  }};
}}

function text(parentElement) {{
  return {{ parentElement }};
}}

const filters = context.LexiShift.contentDomScanNodeFilters.createNodeFilters();
const visibleRoot = element("DIV");
const visibleParent = element("SPAN", {{ parentElement: visibleRoot }});
assert.equal(filters.isExcluded(text(visibleParent)), false);

const hiddenRoot = element("SECTION", {{ hidden: true }});
const hiddenChild = element("SPAN", {{ parentElement: hiddenRoot }});
assert.equal(filters.isExcluded(text(hiddenChild)), true);

const displayNoneRoot = element("DIV", {{ display: "none" }});
const displayNoneChild = element("SPAN", {{ parentElement: displayNoneRoot }});
assert.equal(filters.isExcluded(text(displayNoneChild)), true);

const contentHiddenRoot = element("DIV", {{ contentVisibility: "hidden" }});
const contentHiddenChild = element("SPAN", {{ parentElement: contentHiddenRoot }});
assert.equal(filters.isExcluded(text(contentHiddenChild)), true);

const visibilityHiddenParent = element("SPAN", {{ visibility: "hidden" }});
assert.equal(filters.isExcluded(text(visibilityHiddenParent)), true);

const templateRoot = element("TEMPLATE");
const templateChild = element("SPAN", {{ parentElement: templateRoot }});
assert.equal(filters.isExcluded(text(templateChild)), true);
"""
        _run_node(script)

    def test_dom_scan_filter_skips_shared_lexishift_scan_skip_marker(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const modulePath = {json.dumps(str(NODE_FILTERS_JS))};
const context = vm.createContext({{ console }});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const filters = context.LexiShift.contentDomScanNodeFilters.createNodeFilters();
let seenSelector = "";
const skippedNode = {{
  parentElement: {{
    closest(selector) {{
      seenSelector = selector;
      return selector.includes('[data-lexishift-scan-skip="true"]') ? {{}} : null;
    }}
  }}
}};
const normalNode = {{
  parentElement: {{
    closest() {{
      return null;
    }}
  }}
}};

assert.equal(filters.isLexiShiftNode(skippedNode), true);
assert.equal(seenSelector.includes(".lexishift-replacement"), true);
assert.equal(seenSelector.includes('[data-lexishift-scan-skip="true"]'), true);
assert.equal(filters.isLexiShiftNode(normalNode), false);
"""
        _run_node(script)

    def test_feedback_popup_root_carries_shared_scan_skip_marker(self) -> None:
        script = f"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const measurementPath = {json.dumps(str(POPUP_LAYOUT_MEASUREMENT_JS))};
const modulePath = {json.dumps(str(FEEDBACK_POPUP_CONTROLLER_JS))};

function createClassList(element) {{
  return {{
    add(...classes) {{
      const current = new Set(String(element.className || "").split(/\\s+/).filter(Boolean));
      classes.forEach((value) => current.add(value));
      element.className = Array.from(current).join(" ");
    }},
    remove(...classes) {{
      const removals = new Set(classes);
      element.className = String(element.className || "")
        .split(/\\s+/)
        .filter((value) => value && !removals.has(value))
        .join(" ");
    }},
    contains(className) {{
      return String(element.className || "").split(/\\s+/).includes(className);
    }}
  }};
}}

function createElement(tagName) {{
  const element = {{
    tagName: String(tagName || "").toUpperCase(),
    className: "",
    dataset: {{}},
    style: {{}},
    attributes: {{}},
    childNodes: [],
    children: [],
    childElementCount: 0,
    textContent: "",
    setAttribute(name, value) {{
      this.attributes[name] = String(value);
    }},
    appendChild(child) {{
      this.childNodes.push(child);
      this.children.push(child);
      this.childElementCount = this.children.length;
      child.parentElement = this;
      return child;
    }},
    addEventListener(type, handler) {{
      this.listeners = this.listeners || {{}};
      this.listeners[type] = handler;
    }},
    getBoundingClientRect() {{
      return {{ top: 0, bottom: 48, left: 0, right: 180, width: 180, height: 48 }};
    }},
    querySelector() {{
      return null;
    }}
  }};
  element.classList = createClassList(element);
  return element;
}}

let contextMenuHandler = null;
let appendedPopup = null;
const context = vm.createContext({{
  console,
  requestAnimationFrame(callback) {{
    callback();
  }},
  document: {{
    createElement,
    body: {{
      appendChild(node) {{
        appendedPopup = node;
        return node;
      }}
    }},
    documentElement: {{ clientWidth: 1024 }},
    addEventListener(type, handler) {{
      if (type === "contextmenu") {{
        contextMenuHandler = handler;
      }}
    }},
    removeEventListener() {{}}
  }},
  window: {{
    scrollY: 0,
    scrollX: 0,
    innerHeight: 768,
    addEventListener() {{}},
    removeEventListener() {{}}
  }},
  Node: function Node() {{}}
}});
context.globalThis = context;
context.LexiShift = {{}};
vm.runInContext(fs.readFileSync(measurementPath, "utf8"), context, {{ filename: measurementPath }});
vm.runInContext(fs.readFileSync(modulePath, "utf8"), context, {{ filename: modulePath }});

const controller = context.LexiShift.uiFeedbackPopupController.createController({{}});
controller.attachFeedbackListener(() => {{}});
assert.equal(typeof contextMenuHandler, "function");

const replacementTarget = {{
  dataset: {{
    origin: "srs",
    languagePair: "en-ja",
    displayReplacement: "犬",
    replacement: "犬"
  }},
  getBoundingClientRect() {{
    return {{ top: 80, bottom: 104, left: 120, right: 160, width: 40, height: 24 }};
  }}
}};
let prevented = false;
contextMenuHandler({{
  target: {{
    closest(selector) {{
      assert.equal(selector, ".lexishift-replacement");
      return replacementTarget;
    }}
  }},
  preventDefault() {{
    prevented = true;
  }}
}});

assert.equal(prevented, true);
assert.ok(appendedPopup);
assert.equal(appendedPopup.className.includes("lexishift-feedback-popup"), true);
assert.equal(appendedPopup.dataset.lexishiftScanSkip, "true");
assert.equal(appendedPopup.attributes.role, "dialog");
"""
        _run_node(script)


if __name__ == "__main__":
    unittest.main()

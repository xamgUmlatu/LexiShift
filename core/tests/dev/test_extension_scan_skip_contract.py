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

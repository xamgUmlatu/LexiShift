import {
  NODE_SEQUENCE,
  getAvailableFields,
  getNode,
  getPhaseLabel,
  extractStableNodeKey,
} from "./veto_e2e_state.mjs";

const stage = document.getElementById("diagram");
const jumpList = document.getElementById("node-jump-list");
const inspectorKey = document.getElementById("inspector-key");
const inspectorTitle = document.getElementById("inspector-title");
const inspectorPhase = document.getElementById("inspector-phase");
const inspectorSummary = document.getElementById("inspector-summary");
const inspectorDomId = document.getElementById("inspector-dom-id");
const introducedList = document.getElementById("introduced-fields");
const availableList = document.getElementById("available-fields");
const snapshotBlock = document.getElementById("state-snapshot");

let selectedNodeKey = "O0";
let selectedRawId = null;
let currentSvg = null;

function createJumpList() {
  const fragment = document.createDocumentFragment();

  for (const nodeKey of NODE_SEQUENCE) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "node-jump-button";
    button.dataset.nodeKey = nodeKey;
    button.textContent = nodeKey;
    button.addEventListener("click", () => selectNode(nodeKey, null));
    fragment.appendChild(button);
  }

  jumpList.innerHTML = "";
  jumpList.appendChild(fragment);
}

function renderFieldCards(target, items) {
  if (!items.length) {
    target.innerHTML = `<p class="empty-state">No fields recorded here.</p>`;
    return;
  }

  const fragment = document.createDocumentFragment();

  for (const item of items) {
    const article = document.createElement("article");
    article.className = "field-card";
    article.innerHTML = `
      <div class="field-name-row">
        <code class="field-name">${item.name}</code>
        ${item.introducedAt ? `<span class="field-origin">from ${item.introducedAt}</span>` : ""}
      </div>
      <p>${item.description}</p>
      <pre class="field-example"><code>${item.example}</code></pre>
    `;
    fragment.appendChild(article);
  }

  target.innerHTML = "";
  target.appendChild(fragment);
}

function renderAvailableFields(nodeKey) {
  const fields = getAvailableFields(nodeKey);
  if (!fields.length) {
    availableList.innerHTML = `<p class="empty-state">No fields available yet.</p>`;
    return;
  }

  const rows = fields
    .map(
      (item) => `
        <tr>
          <td><code>${item.name}</code></td>
          <td><code>${item.introducedAt}</code></td>
          <td>${item.description}</td>
        </tr>
      `,
    )
    .join("");

  availableList.innerHTML = `
    <table class="field-table">
      <thead>
        <tr>
          <th>Field</th>
          <th>Introduced</th>
          <th>Meaning</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function highlightSelectedNode(nodeKey) {
  if (!currentSvg) {
    return;
  }

  for (const node of currentSvg.querySelectorAll(".node")) {
    node.classList.toggle("is-selected", node.dataset.nodeKey === nodeKey);
  }

  for (const button of jumpList.querySelectorAll(".node-jump-button")) {
    button.classList.toggle("is-active", button.dataset.nodeKey === nodeKey);
  }
}

function selectNode(nodeKey, rawId) {
  const node = getNode(nodeKey);
  if (!node) {
    return;
  }

  selectedNodeKey = nodeKey;
  selectedRawId = rawId ?? null;

  inspectorKey.textContent = nodeKey;
  inspectorTitle.textContent = node.title;
  inspectorPhase.textContent = getPhaseLabel(node.phase);
  inspectorSummary.textContent = node.summary;
  inspectorDomId.textContent =
    selectedRawId ??
    `stable key ${nodeKey}; rendered Mermaid ids normalize to this key (for example: semantic-routing-veto-e2e-flowchart-${nodeKey}-N)`;

  renderFieldCards(introducedList, node.introduced);
  renderAvailableFields(nodeKey);
  snapshotBlock.textContent = JSON.stringify(node.exampleState, null, 2);
  highlightSelectedNode(nodeKey);
}

function attachSvgInteractivity(svgRoot) {
  currentSvg = svgRoot;
  stage.classList.add("diagram-stage-ready");

  for (const nodeGroup of svgRoot.querySelectorAll(".node[id]")) {
    const nodeKey = extractStableNodeKey(nodeGroup.id);
    if (!nodeKey || !getNode(nodeKey)) {
      continue;
    }

    nodeGroup.dataset.nodeKey = nodeKey;
    nodeGroup.setAttribute("tabindex", "0");
    nodeGroup.setAttribute("role", "button");
    nodeGroup.setAttribute("aria-label", `Inspect ${nodeKey}`);

    const activate = (event) => {
      event.preventDefault();
      event.stopPropagation();
      selectNode(nodeKey, nodeGroup.id);
    };

    nodeGroup.addEventListener("click", activate);
    nodeGroup.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        activate(event);
      }
    });
  }

  highlightSelectedNode(selectedNodeKey);
}

async function render() {
  try {
    const [{ default: mermaid }, diagramResponse] = await Promise.all([
      import("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"),
      fetch("../rulegen/semantic_routing_veto_e2e_diagram.mmd"),
    ]);

    if (!diagramResponse.ok) {
      throw new Error(`Diagram fetch failed: ${diagramResponse.status}`);
    }

    const source = await diagramResponse.text();
    globalThis.diagramNodeClick = (nodeKey) => selectNode(nodeKey, null);

    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: "base",
      flowchart: { useMaxWidth: true, curve: "basis" },
      themeVariables: {
        background: "#fffaf4",
        primaryTextColor: "#0f172a",
        lineColor: "#475569",
        fontFamily: "IBM Plex Sans, Avenir Next, Segoe UI, sans-serif",
      },
    });

    const { svg } = await mermaid.render("semantic-routing-veto-e2e", source);
    stage.innerHTML = svg;
    attachSvgInteractivity(stage.querySelector("svg"));
    selectNode(selectedNodeKey, null);
  } catch (error) {
    stage.innerHTML =
      `<p><strong>Diagram render failed.</strong></p><p>${String(error)}</p>`;
  }
}

createJumpList();
render();

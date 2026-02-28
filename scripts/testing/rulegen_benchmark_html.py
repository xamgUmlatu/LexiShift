from __future__ import annotations

import html
import json
from typing import Iterable, Mapping, Sequence

def _escape_html(value: object) -> str:
    return html.escape(str(value), quote=True)


def _format_percent(value: float) -> str:
    return f"{float(value) * 100.0:.1f}%"


def _format_optional_float(value: object, *, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def render_html_report(
    *,
    report_payload: Mapping[str, object],
    pair_runs: Mapping[str, Sequence[object]],
    cases_by_pair: Mapping[str, Sequence[object]],
    top_n: int,
) -> str:
    generated_at = _escape_html(report_payload.get("generated_at", ""))
    profile_id = _escape_html(report_payload.get("profile_id", ""))
    data_root = _escape_html(report_payload.get("data_root", ""))
    dataset_path = _escape_html(report_payload.get("dataset_path", ""))
    sweep_payload = report_payload.get("sweep")
    configuration_count = "-"
    if isinstance(sweep_payload, Mapping):
        configuration_count = _escape_html(sweep_payload.get("configuration_count", "-"))

    pair_sections: list[str] = []
    for pair, runs in sorted(pair_runs.items()):
        if not runs:
            continue
        pair_html = _escape_html(pair)
        pair_cases = tuple(cases_by_pair.get(pair, ()))
        pair_case_by_id = {case.case_id: case for case in pair_cases}
        pair_case_by_target = {case.target: case for case in pair_cases}
        best_run = runs[0]
        best_summary = best_run.summary

        top_rows: list[str] = []
        for rank, run in enumerate(runs[:max(1, int(top_n))], start=1):
            summary = run.summary
            top_rows.append(
                "<tr>"
                f"<td>{rank}</td>"
                f"<td>{summary.objective_score:.3f}</td>"
                f"<td>{_format_percent(summary.top1_accuracy)}</td>"
                f"<td>{_format_percent(summary.top3_recall)}</td>"
                f"<td>{_format_percent(summary.forbidden_top1_rate)}</td>"
                f"<td>{_format_percent(summary.forbidden_any_rate)}</td>"
                f"<td>{summary.avg_rules_per_target:.2f}</td>"
                f"<td><code>{_escape_html(run.config.label())}</code></td>"
                "</tr>"
            )

        case_rows: list[str] = []
        for case_result in best_run.case_results:
            target_raw = str(case_result.get("target", "") or "").strip()
            target_html = _escape_html(target_raw)
            case_id_raw = str(case_result.get("case_id", "") or "").strip()
            case_id_html = _escape_html(case_id_raw)
            case_def = pair_case_by_id.get(case_id_raw) or pair_case_by_target.get(target_raw)
            known_green: set[str] = set()
            known_black: set[str] = set()
            if case_def is not None:
                known_green.update(case_def.expected_any)
                known_green.update(case_def.expected_top1_any)
                known_black.update(case_def.forbidden_top1)
                known_black.update(case_def.forbidden_any)

            all_sources_raw = case_result.get("all_sources")
            all_sources: list[str] = []
            if isinstance(all_sources_raw, Sequence) and not isinstance(all_sources_raw, (str, bytes)):
                all_sources = _dedupe_preserve_order(
                    str(item or "").strip()
                    for item in all_sources_raw
                )

            source_chips: list[str] = []
            for source in all_sources:
                source_html = _escape_html(source)
                if source in known_black:
                    base_label = "black"
                    chip_class = "chip-black"
                elif source in known_green:
                    base_label = "green"
                    chip_class = "chip-green"
                else:
                    base_label = "neutral"
                    chip_class = "chip-neutral"
                source_chips.append(
                    "<button type=\"button\" class=\"source-chip "
                    f"{chip_class}\" "
                    f"data-pair=\"{pair_html}\" "
                    f"data-case-id=\"{case_id_html}\" "
                    f"data-target=\"{target_html}\" "
                    f"data-phrase=\"{source_html}\" "
                    f"data-base-label=\"{base_label}\" "
                    f"data-current-label=\"{base_label}\" "
                    "title=\"Right-click to label\">"
                    f"{source_html}</button>"
                )
            all_sources_html = "".join(source_chips) if source_chips else "<span class=\"text-muted\">-</span>"
            label_hint = _escape_html(f"G:{len(known_green)} / B:{len(known_black)}")

            top1_source = _escape_html(case_result.get("top1_source", "-") or "-")
            top1_conf = _format_optional_float(case_result.get("top1_confidence"), digits=4)
            top3_sources_raw = case_result.get("top3_sources")
            if isinstance(top3_sources_raw, Sequence) and not isinstance(top3_sources_raw, (str, bytes)):
                top3_sources = ", ".join(_escape_html(item) for item in top3_sources_raw) or "-"
            else:
                top3_sources = "-"

            top1_correct = bool(case_result.get("top1_correct", False))
            top3_contains = bool(case_result.get("top3_contains_expected", False))
            top1_forbidden = bool(case_result.get("top1_forbidden", False))
            forbidden_any = bool(case_result.get("forbidden_any_present", False))
            variant_count = int(case_result.get("variant_rule_count", 0) or 0)
            rule_count = int(case_result.get("rule_count", 0) or 0)
            if top1_correct and not top1_forbidden and not forbidden_any:
                status_class = "status-ok"
                status_text = "PASS"
            elif top3_contains and not top1_forbidden:
                status_class = "status-warn"
                status_text = "REVIEW"
            else:
                status_class = "status-bad"
                status_text = "FAIL"
            case_rows.append(
                "<tr>"
                f"<td><span class=\"status-pill {status_class}\">{status_text}</span></td>"
                f"<td><code>{case_id_html}</code></td>"
                f"<td>{target_html}</td>"
                f"<td>{top1_source}</td>"
                f"<td>{top1_conf}</td>"
                f"<td>{top3_sources}</td>"
                f"<td class=\"source-cell\">{all_sources_html}</td>"
                f"<td><span class=\"label-hint\">{label_hint}</span></td>"
                f"<td>{'yes' if top1_correct else 'no'}</td>"
                f"<td>{'yes' if top3_contains else 'no'}</td>"
                f"<td>{'yes' if top1_forbidden else 'no'}</td>"
                f"<td>{'yes' if forbidden_any else 'no'}</td>"
                f"<td>{rule_count}</td>"
                f"<td>{variant_count}</td>"
                "</tr>"
            )

        pair_sections.append(
            f"<section class=\"pair-section\" data-pair=\"{pair_html}\">"
            f"<div class=\"pair-head\"><h2>{pair_html}</h2>"
            f"<p>best objective <strong>{best_summary.objective_score:.3f}</strong> "
            f"| top1 {_format_percent(best_summary.top1_accuracy)} "
            f"| top3 {_format_percent(best_summary.top3_recall)}</p></div>"
            "<div class=\"metric-grid\">"
            f"<article class=\"metric-card\"><h3>Top1</h3><p>{_format_percent(best_summary.top1_accuracy)}</p></article>"
            f"<article class=\"metric-card\"><h3>Top3</h3><p>{_format_percent(best_summary.top3_recall)}</p></article>"
            f"<article class=\"metric-card\"><h3>Forbidden Top1</h3><p>{_format_percent(best_summary.forbidden_top1_rate)}</p></article>"
            f"<article class=\"metric-card\"><h3>Forbidden Any</h3><p>{_format_percent(best_summary.forbidden_any_rate)}</p></article>"
            f"<article class=\"metric-card\"><h3>Avg Rules</h3><p>{best_summary.avg_rules_per_target:.2f}</p></article>"
            f"<article class=\"metric-card\"><h3>Variant Top1</h3><p>{_format_percent(best_summary.variant_top1_rate)}</p></article>"
            "</div>"
            "<details open>"
            "<summary>Leaderboard</summary>"
            "<div class=\"table-wrap\"><table><thead><tr>"
            "<th>Rank</th><th>Objective</th><th>Top1</th><th>Top3</th><th>Forbidden Top1</th>"
            "<th>Forbidden Any</th><th>Avg Rules</th><th>Config</th>"
            "</tr></thead><tbody>"
            + "".join(top_rows)
            + "</tbody></table></div>"
            "</details>"
            "<details>"
            "<summary>Best Run Case Diagnostics + Labeling</summary>"
            "<div class=\"table-wrap\"><table><thead><tr>"
            "<th>Status</th><th>Case</th><th>Target</th><th>Top1 Source</th><th>Top1 Conf</th><th>Top3 Sources</th>"
            "<th>All Sources (right-click chips)</th><th>Known Labels</th>"
            "<th>Top1 Correct</th><th>Top3 Hit</th><th>Top1 Forbidden</th><th>Forbidden Any</th>"
            "<th>Rules</th><th>Variants</th>"
            "</tr></thead><tbody>"
            + "".join(case_rows)
            + "</tbody></table></div>"
            "</details>"
            "</section>"
        )

    label_script = """
<script>
const DATASET_PATH = __DATASET_PATH__;
const REPORT_GENERATED_AT = __REPORT_GENERATED_AT__;
const STORAGE_KEY = 'lexishift_rulegen_label_workbench_v1';
const WORKFLOW_STORAGE_KEY = 'lexishift_rulegen_lp_workflow_v1';

const chips = Array.from(document.querySelectorAll('.source-chip'));
const pairSections = Array.from(document.querySelectorAll('.pair-section[data-pair]'));
const pairOrder = pairSections
  .map((section) => section.dataset.pair || '')
  .filter((pair, index, arr) => pair && arr.indexOf(pair) === index);

const menu = document.getElementById('label-menu');
const labelCountEl = document.getElementById('label-count');
const downloadBtn = document.getElementById('download-labels');
const copyBtn = document.getElementById('copy-labels');
const clearBtn = document.getElementById('clear-labels');

const pairStateEl = document.getElementById('pair-workflow-state');
const pairNavListEl = document.getElementById('pair-nav-list');
const prevPairBtn = document.getElementById('prev-pair');
const nextPairBtn = document.getElementById('next-pair');
const markDoneBtn = document.getElementById('mark-pair-done');
const skipPairBtn = document.getElementById('skip-pair');
const resetPairStatusBtn = document.getElementById('reset-pair-status');
const showAllPairsToggle = document.getElementById('show-all-pairs');

let activeChip = null;

function emptyState() {
  return { cases: {} };
}

function normalizeLabel(value) {
  if (value === 'green' || value === 'black' || value === 'neutral') {
    return value;
  }
  return 'neutral';
}

function caseKey(pair, caseId, target) {
  return [pair || '', caseId || '', target || ''].join('|||');
}

function loadState() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyState();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || !parsed.cases || typeof parsed.cases !== 'object') {
      return emptyState();
    }
    return parsed;
  } catch (error) {
    return emptyState();
  }
}

function emptyWorkflowState() {
  return {
    current_pair: pairOrder[0] || '',
    statuses: {},
    show_all_pairs: false,
  };
}

function normalizePairStatus(value) {
  if (value === 'done' || value === 'skipped') return value;
  return 'todo';
}

function loadWorkflowState() {
  try {
    const raw = window.localStorage.getItem(WORKFLOW_STORAGE_KEY);
    if (!raw) return emptyWorkflowState();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return emptyWorkflowState();
    const statuses = parsed.statuses && typeof parsed.statuses === 'object' ? parsed.statuses : {};
    return {
      current_pair: typeof parsed.current_pair === 'string' ? parsed.current_pair : (pairOrder[0] || ''),
      statuses,
      show_all_pairs: Boolean(parsed.show_all_pairs),
    };
  } catch (error) {
    return emptyWorkflowState();
  }
}

let state = loadState();
let workflowState = loadWorkflowState();
if (!pairOrder.includes(workflowState.current_pair)) {
  workflowState.current_pair = pairOrder[0] || '';
}

function saveState() {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function saveWorkflowState() {
  window.localStorage.setItem(WORKFLOW_STORAGE_KEY, JSON.stringify(workflowState));
}

function ensureCaseBucket(pair, caseId, target) {
  const key = caseKey(pair, caseId, target);
  if (!state.cases[key]) {
    state.cases[key] = {
      pair: pair || '',
      case_id: caseId || '',
      target: target || '',
      decisions: {},
    };
  }
  return state.cases[key];
}

function getDecision(pair, caseId, target, phrase) {
  const key = caseKey(pair, caseId, target);
  const bucket = state.cases[key];
  if (!bucket || !bucket.decisions || typeof bucket.decisions !== 'object') return null;
  if (!(phrase in bucket.decisions)) return null;
  return normalizeLabel(bucket.decisions[phrase]);
}

function getPairStatus(pair) {
  if (!pair || !workflowState.statuses || typeof workflowState.statuses !== 'object') {
    return 'todo';
  }
  return normalizePairStatus(workflowState.statuses[pair]);
}

function setPairStatus(pair, status) {
  if (!pair) return;
  const normalized = normalizePairStatus(status);
  if (!workflowState.statuses || typeof workflowState.statuses !== 'object') {
    workflowState.statuses = {};
  }
  if (normalized === 'todo') {
    delete workflowState.statuses[pair];
  } else {
    workflowState.statuses[pair] = normalized;
  }
  saveWorkflowState();
}

function setCurrentPair(pair, options = {}) {
  if (!pairOrder.includes(pair)) return;
  workflowState.current_pair = pair;
  saveWorkflowState();
  applyPairVisibility(options);
  renderPairWorkflow();
}

function applyChipClasses(chip, label, isManual) {
  chip.classList.remove('chip-green', 'chip-black', 'chip-neutral', 'chip-manual');
  if (label === 'green') chip.classList.add('chip-green');
  else if (label === 'black') chip.classList.add('chip-black');
  else chip.classList.add('chip-neutral');
  if (isManual) chip.classList.add('chip-manual');
  chip.dataset.currentLabel = label;
  chip.title = `Right-click to label (${label})`;
}

function applyChipLabel(chip) {
  const pair = chip.dataset.pair || '';
  const caseId = chip.dataset.caseId || '';
  const target = chip.dataset.target || '';
  const phrase = chip.dataset.phrase || '';
  const baseLabel = normalizeLabel(chip.dataset.baseLabel || 'neutral');
  const decision = getDecision(pair, caseId, target, phrase);
  const resolved = decision || baseLabel;
  applyChipClasses(chip, resolved, Boolean(decision && decision !== baseLabel));
}

function refreshDecisionCount() {
  const buckets = Object.values(state.cases || {});
  let decisionCount = 0;
  let caseCount = 0;
  for (const bucket of buckets) {
    if (!bucket || !bucket.decisions || typeof bucket.decisions !== 'object') continue;
    const size = Object.keys(bucket.decisions).length;
    if (size > 0) caseCount += 1;
    decisionCount += size;
  }
  if (labelCountEl) {
    labelCountEl.textContent = `${decisionCount} decisions across ${caseCount} cases`;
  }
}

function applyPairVisibility(options = {}) {
  const showAll = Boolean(workflowState.show_all_pairs);
  pairSections.forEach((section) => {
    const pair = section.dataset.pair || '';
    section.hidden = !showAll && pair !== workflowState.current_pair;
  });
  const shouldScroll = options.scroll !== false;
  if (!showAll && shouldScroll) {
    const active = pairSections.find((section) => (section.dataset.pair || '') === workflowState.current_pair);
    if (active) {
      active.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

function renderPairWorkflow() {
  if (!pairOrder.length) {
    if (pairStateEl) pairStateEl.textContent = 'No LP sections in this report';
    return;
  }

  if (!pairOrder.includes(workflowState.current_pair)) {
    workflowState.current_pair = pairOrder[0];
    saveWorkflowState();
  }

  const currentIndex = pairOrder.indexOf(workflowState.current_pair);
  const doneCount = pairOrder.filter((pair) => getPairStatus(pair) === 'done').length;
  const skippedCount = pairOrder.filter((pair) => getPairStatus(pair) === 'skipped').length;
  const todoCount = pairOrder.length - doneCount - skippedCount;

  if (pairStateEl) {
    pairStateEl.textContent = `LP ${currentIndex + 1}/${pairOrder.length}: ${workflowState.current_pair} | todo ${todoCount} done ${doneCount} skipped ${skippedCount}`;
  }

  if (pairNavListEl) {
    pairNavListEl.innerHTML = '';
    pairOrder.forEach((pair) => {
      const status = getPairStatus(pair);
      const button = document.createElement('button');
      button.type = 'button';
      button.className = `pair-chip status-${status}${pair === workflowState.current_pair ? ' active' : ''}`;
      button.textContent = `${pair} (${status})`;
      button.addEventListener('click', () => {
        setCurrentPair(pair);
      });
      pairNavListEl.appendChild(button);
    });
  }

  if (prevPairBtn) prevPairBtn.disabled = currentIndex <= 0;
  if (nextPairBtn) nextPairBtn.disabled = currentIndex >= (pairOrder.length - 1);
  if (markDoneBtn) markDoneBtn.disabled = !workflowState.current_pair;
  if (skipPairBtn) skipPairBtn.disabled = !workflowState.current_pair;
  if (resetPairStatusBtn) resetPairStatusBtn.disabled = !workflowState.current_pair;
}

function moveRelativePair(offset) {
  if (!pairOrder.length) return;
  const index = pairOrder.indexOf(workflowState.current_pair);
  if (index < 0) return;
  const targetIndex = index + offset;
  if (targetIndex < 0 || targetIndex >= pairOrder.length) return;
  setCurrentPair(pairOrder[targetIndex]);
}

function findNextTodoIndex(afterIndex) {
  for (let i = afterIndex + 1; i < pairOrder.length; i += 1) {
    if (getPairStatus(pairOrder[i]) === 'todo') return i;
  }
  for (let i = 0; i < pairOrder.length; i += 1) {
    if (getPairStatus(pairOrder[i]) === 'todo') return i;
  }
  return -1;
}

function markCurrentPairAndAdvance(status) {
  if (!workflowState.current_pair) return;
  const currentIndex = pairOrder.indexOf(workflowState.current_pair);
  setPairStatus(workflowState.current_pair, status);
  const nextTodo = findNextTodoIndex(currentIndex);
  if (nextTodo >= 0) {
    setCurrentPair(pairOrder[nextTodo]);
    return;
  }
  if (currentIndex >= 0 && currentIndex < pairOrder.length - 1) {
    setCurrentPair(pairOrder[currentIndex + 1]);
    return;
  }
  renderPairWorkflow();
  applyPairVisibility({ scroll: false });
}

function setLabelForChip(chip, label) {
  const pair = chip.dataset.pair || '';
  const caseId = chip.dataset.caseId || '';
  const target = chip.dataset.target || '';
  const phrase = chip.dataset.phrase || '';
  const baseLabel = normalizeLabel(chip.dataset.baseLabel || 'neutral');
  const normalizedLabel = normalizeLabel(label);
  const key = caseKey(pair, caseId, target);
  const bucket = ensureCaseBucket(pair, caseId, target);
  if (normalizedLabel === baseLabel) {
    delete bucket.decisions[phrase];
  } else {
    bucket.decisions[phrase] = normalizedLabel;
  }
  if (Object.keys(bucket.decisions).length === 0) {
    delete state.cases[key];
  }
  applyChipLabel(chip);
  saveState();
  refreshDecisionCount();
}

function hideMenu() {
  if (!menu) return;
  menu.hidden = true;
  activeChip = null;
}

function openMenuForChip(event) {
  if (!menu) return;
  event.preventDefault();
  activeChip = event.currentTarget;
  menu.hidden = false;
  const x = Math.min(event.pageX, window.scrollX + window.innerWidth - 190);
  const y = Math.min(event.pageY, window.scrollY + window.innerHeight - 160);
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
}

function sortedDecisionCases() {
  const entries = Object.values(state.cases || {}).filter((entry) => {
    return entry && entry.decisions && Object.keys(entry.decisions).length > 0;
  });
  entries.sort((a, b) => {
    const left = `${a.pair || ''}::${a.case_id || ''}::${a.target || ''}`;
    const right = `${b.pair || ''}::${b.case_id || ''}::${b.target || ''}`;
    return left.localeCompare(right);
  });
  return entries.map((entry) => {
    const ordered = {};
    Object.keys(entry.decisions || {}).sort().forEach((phrase) => {
      ordered[phrase] = normalizeLabel(entry.decisions[phrase]);
    });
    return {
      pair: entry.pair || '',
      case_id: entry.case_id || '',
      target: entry.target || '',
      decisions: ordered,
    };
  });
}

function exportPayloadText() {
  const payload = {
    labels_version: 1,
    generated_at: new Date().toISOString(),
    source_report_generated_at: REPORT_GENERATED_AT,
    dataset_path: DATASET_PATH,
    cases: sortedDecisionCases(),
  };
  return JSON.stringify(payload, null, 2);
}

function downloadDecisions() {
  const payloadText = exportPayloadText();
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `rulegen_label_overrides_${timestamp}.json`;
  const blob = new Blob([payloadText], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1500);
}

async function copyDecisions() {
  if (!copyBtn) return;
  const original = copyBtn.textContent;
  try {
    await navigator.clipboard.writeText(exportPayloadText());
    copyBtn.textContent = 'Copied';
  } catch (error) {
    copyBtn.textContent = 'Copy failed';
  }
  window.setTimeout(() => {
    copyBtn.textContent = original;
  }, 1500);
}

function clearDecisions() {
  if (!window.confirm('Clear all local label decisions for this report?')) return;
  state = emptyState();
  saveState();
  chips.forEach((chip) => applyChipLabel(chip));
  refreshDecisionCount();
}

if (menu) {
  menu.querySelectorAll('button[data-action]').forEach((button) => {
    button.addEventListener('click', () => {
      if (activeChip) {
        setLabelForChip(activeChip, button.dataset.action || 'neutral');
      }
      hideMenu();
    });
  });
}

chips.forEach((chip) => {
  chip.addEventListener('contextmenu', openMenuForChip);
  applyChipLabel(chip);
});

document.addEventListener('click', (event) => {
  if (!menu || menu.hidden) return;
  if (!menu.contains(event.target)) hideMenu();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') hideMenu();
});

if (showAllPairsToggle) {
  showAllPairsToggle.checked = Boolean(workflowState.show_all_pairs);
  showAllPairsToggle.addEventListener('change', () => {
    workflowState.show_all_pairs = Boolean(showAllPairsToggle.checked);
    saveWorkflowState();
    applyPairVisibility({ scroll: false });
    renderPairWorkflow();
  });
}

if (prevPairBtn) prevPairBtn.addEventListener('click', () => moveRelativePair(-1));
if (nextPairBtn) nextPairBtn.addEventListener('click', () => moveRelativePair(1));
if (markDoneBtn) markDoneBtn.addEventListener('click', () => markCurrentPairAndAdvance('done'));
if (skipPairBtn) skipPairBtn.addEventListener('click', () => markCurrentPairAndAdvance('skipped'));
if (resetPairStatusBtn) {
  resetPairStatusBtn.addEventListener('click', () => {
    if (!workflowState.current_pair) return;
    setPairStatus(workflowState.current_pair, 'todo');
    renderPairWorkflow();
    applyPairVisibility({ scroll: false });
  });
}

window.addEventListener('scroll', hideMenu, true);
if (downloadBtn) downloadBtn.addEventListener('click', downloadDecisions);
if (copyBtn) copyBtn.addEventListener('click', copyDecisions);
if (clearBtn) clearBtn.addEventListener('click', clearDecisions);

refreshDecisionCount();
renderPairWorkflow();
applyPairVisibility({ scroll: false });
</script>
""".replace("__DATASET_PATH__", json.dumps(str(report_payload.get("dataset_path", "")))).replace(
        "__REPORT_GENERATED_AT__", json.dumps(str(report_payload.get("generated_at", "")))
    )

    return "".join(
        [
            "<!doctype html>",
            "<html lang=\"en\">",
            "<head>",
            "<meta charset=\"utf-8\">",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "<title>LexiShift Rulegen Benchmark</title>",
            "<style>",
            ":root{",
            "--bg:#f7f4ef;--panel:#ffffff;--text:#162022;--muted:#5d6a6d;",
            "--line:#d8dfdc;--accent:#0f766e;--accent-soft:#d1fae5;",
            "--warn:#b45309;--warn-soft:#fef3c7;--bad:#b91c1c;--bad-soft:#fee2e2;",
            "--ok:#166534;--ok-soft:#dcfce7;--radius:16px;--shadow:0 10px 25px rgba(15,23,42,0.08);",
            "}",
            "*{box-sizing:border-box}",
            "body{margin:0;font-family:'IBM Plex Sans','Avenir Next',sans-serif;color:var(--text);",
            "background:radial-gradient(circle at 15% 0%, #fff9ec 0%, var(--bg) 55%),",
            "linear-gradient(180deg,#f6f7f4 0%,#f3f1ec 100%);}",
            "main{max-width:1320px;margin:0 auto;padding:32px 20px 60px}",
            "header{background:linear-gradient(135deg,#fcfffe 0%,#ecfdf5 100%);border:1px solid var(--line);",
            "border-radius:calc(var(--radius) + 6px);box-shadow:var(--shadow);padding:26px 26px 20px;position:relative;overflow:hidden}",
            "header::after{content:'';position:absolute;right:-24px;top:-24px;width:180px;height:180px;border-radius:50%;",
            "background:radial-gradient(circle,rgba(15,118,110,0.14) 0%,rgba(15,118,110,0) 70%)}",
            "h1{margin:0;font-family:'Fraunces','Iowan Old Style',serif;font-size:clamp(1.6rem,2.8vw,2.3rem);letter-spacing:0.01em}",
            ".meta{margin-top:10px;color:var(--muted);font-size:0.94rem;display:flex;gap:14px;flex-wrap:wrap}",
            ".meta code{background:#eef2f3;border:1px solid #d9e0e2;padding:2px 6px;border-radius:8px}",
            ".label-workbench{margin-top:14px;padding:12px;border:1px solid #c8d7d3;background:#f8fffd;border-radius:12px}",
            ".label-workbench p{margin:0 0 10px;color:#33484c;font-size:0.92rem}",
            ".label-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center}",
            ".pair-workflow{margin-top:12px;padding:12px;border:1px dashed #b8ccc9;border-radius:12px;background:#f5fbfa}",
            ".pair-workflow-head{display:flex;gap:10px;flex-wrap:wrap;align-items:center;justify-content:space-between}",
            ".pair-workflow-state{font-size:0.9rem;color:#2c4044;font-weight:700}",
            ".pair-workflow-buttons{display:flex;flex-wrap:wrap;gap:8px;align-items:center}",
            ".pair-nav{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}",
            ".pair-chip{border:1px solid #bfd0ce;background:#fff;border-radius:999px;padding:4px 11px;font-size:0.78rem;font-weight:700;color:#1e3236;cursor:pointer}",
            ".pair-chip:hover{background:#eef8f6}",
            ".pair-chip.active{box-shadow:0 0 0 2px rgba(15,23,42,0.18) inset}",
            ".pair-chip.status-done{background:#e8fff2;border-color:#9ad8b6;color:#12502d}",
            ".pair-chip.status-skipped{background:#f5f7fa;border-color:#ccd7df;color:#34434f}",
            ".pair-chip.status-todo{background:#fffdf6;border-color:#e7dbb2;color:#5f4a0a}",
            ".show-all-wrap{display:inline-flex;align-items:center;gap:6px;color:#2f4649;font-size:0.83rem;font-weight:700}",
            ".btn{background:#0f766e;color:#fff;border:1px solid #0f766e;border-radius:10px;padding:7px 11px;font-weight:700;cursor:pointer}",
            ".btn.btn-secondary{background:#fff;color:#0f766e}",
            ".btn:hover{filter:brightness(0.96)}",
            "#label-count{font-weight:700;color:#30484b;font-size:0.88rem}",
            ".pair-section{margin-top:22px;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow);padding:20px}",
            ".pair-head h2{margin:0;font-family:'Fraunces','Iowan Old Style',serif;font-size:1.45rem}",
            ".pair-head p{margin:8px 0 0;color:var(--muted)}",
            ".metric-grid{margin-top:16px;display:grid;grid-template-columns:repeat(6,minmax(140px,1fr));gap:10px}",
            ".metric-card{background:#f8faf9;border:1px solid var(--line);border-radius:12px;padding:10px 12px}",
            ".metric-card h3{margin:0;color:var(--muted);font-size:0.76rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase}",
            ".metric-card p{margin:8px 0 0;font-size:1.25rem;font-weight:700;color:#0f172a}",
            "details{margin-top:14px;border:1px solid var(--line);border-radius:12px;background:#fcfdfd;overflow:hidden}",
            "summary{cursor:pointer;padding:12px 14px;font-weight:700;background:#f4f8f7}",
            ".table-wrap{overflow:auto}",
            "table{width:100%;border-collapse:collapse;font-size:0.9rem}",
            "th,td{padding:10px 10px;text-align:left;border-bottom:1px solid #ebeff0;vertical-align:top}",
            "th{font-size:0.78rem;text-transform:uppercase;letter-spacing:0.04em;color:#415255;background:#f8fbfa;position:sticky;top:0;z-index:1}",
            "code{font-family:'Source Code Pro','Menlo',monospace;font-size:0.84rem}",
            ".status-pill{display:inline-block;padding:2px 8px;border-radius:999px;font-weight:700;font-size:0.72rem;letter-spacing:0.04em}",
            ".status-ok{background:var(--ok-soft);color:var(--ok)}",
            ".status-warn{background:var(--warn-soft);color:var(--warn)}",
            ".status-bad{background:var(--bad-soft);color:var(--bad)}",
            ".source-cell{min-width:380px;max-width:560px}",
            ".source-chip{border:1px solid #cad4d6;background:#fff;border-radius:999px;padding:3px 10px;margin:2px 4px 2px 0;font-size:0.78rem;cursor:context-menu;line-height:1.4}",
            ".source-chip.chip-green{background:#e8fff2;border-color:#a7f3d0;color:#14532d}",
            ".source-chip.chip-black{background:#ffe8e8;border-color:#fecaca;color:#7f1d1d}",
            ".source-chip.chip-neutral{background:#f8fafb;border-color:#d3dde0;color:#1f2f33}",
            ".source-chip.chip-manual{box-shadow:0 0 0 2px rgba(15,23,42,0.18) inset}",
            ".label-hint{font-weight:700;color:#4a5f63;font-size:0.78rem}",
            ".text-muted{color:#7a8a8d;font-style:italic}",
            ".label-menu{position:absolute;z-index:5000;background:#fff;border:1px solid #bfd0ce;border-radius:10px;box-shadow:0 14px 30px rgba(15,23,42,0.2);padding:6px;width:170px}",
            ".label-menu[hidden]{display:none}",
            ".label-menu button{display:block;width:100%;text-align:left;background:#fff;border:0;border-radius:8px;padding:7px 9px;cursor:pointer;font-weight:600;color:#203235}",
            ".label-menu button:hover{background:#eef8f5}",
            "@media (max-width:1020px){.metric-grid{grid-template-columns:repeat(3,minmax(140px,1fr));}.source-cell{min-width:320px}}",
            "@media (max-width:640px){main{padding:20px 12px 36px}.metric-grid{grid-template-columns:repeat(2,minmax(120px,1fr));}.source-cell{min-width:250px}",
            "th,td{padding:8px 8px;font-size:0.82rem}}",
            "</style>",
            "</head>",
            "<body>",
            "<main>",
            "<header>",
            "<h1>Rulegen Benchmark Dashboard</h1>",
            "<div class=\"meta\">",
            f"<span>generated <code>{generated_at}</code></span>",
            f"<span>pairs <code>{len(pair_runs)}</code></span>",
            f"<span>configs per pair <code>{configuration_count}</code></span>",
            f"<span>profile <code>{profile_id}</code></span>",
            f"<span>data root <code>{data_root}</code></span>",
            "</div>",
            "<section class=\"label-workbench\">",
            "<p>Right-click any source chip to mark greenlist or blacklist. Export the decisions JSON to update benchmark cases.</p>",
            "<div class=\"label-actions\">",
            "<button id=\"download-labels\" class=\"btn\" type=\"button\">Download labels JSON</button>",
            "<button id=\"copy-labels\" class=\"btn btn-secondary\" type=\"button\">Copy labels JSON</button>",
            "<button id=\"clear-labels\" class=\"btn btn-secondary\" type=\"button\">Clear local labels</button>",
            "<span id=\"label-count\">0 decisions across 0 cases</span>",
            f"<span>dataset <code>{dataset_path}</code></span>",
            "</div>",
            "<div class=\"pair-workflow\">",
            "<div class=\"pair-workflow-head\">",
            "<span id=\"pair-workflow-state\" class=\"pair-workflow-state\">LP workflow</span>",
            "<div class=\"pair-workflow-buttons\">",
            "<button id=\"prev-pair\" class=\"btn btn-secondary\" type=\"button\">Prev LP</button>",
            "<button id=\"next-pair\" class=\"btn btn-secondary\" type=\"button\">Next LP</button>",
            "<button id=\"mark-pair-done\" class=\"btn\" type=\"button\">Mark Done + Next</button>",
            "<button id=\"skip-pair\" class=\"btn btn-secondary\" type=\"button\">Skip LP</button>",
            "<button id=\"reset-pair-status\" class=\"btn btn-secondary\" type=\"button\">Reset LP</button>",
            "<label class=\"show-all-wrap\"><input id=\"show-all-pairs\" type=\"checkbox\">Show all LPs</label>",
            "</div>",
            "</div>",
            "<div id=\"pair-nav-list\" class=\"pair-nav\"></div>",
            "</div>",
            "</section>",
            "</header>",
            "".join(pair_sections),
            "</main>",
            "<div id=\"label-menu\" class=\"label-menu\" hidden>",
            "<button type=\"button\" data-action=\"green\">Greenlist</button>",
            "<button type=\"button\" data-action=\"black\">Blacklist</button>",
            "<button type=\"button\" data-action=\"neutral\">Clear label</button>",
            "</div>",
            label_script,
            "</body>",
            "</html>",
        ]
    )



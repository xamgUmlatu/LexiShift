#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


APP_TITLE = "SRS Journey Pedagogical Review"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return payload


def render_html(payload: dict[str, Any], *, title: str = APP_TITLE) -> str:
    scenario = payload.get("scenario") if isinstance(payload.get("scenario"), dict) else {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    phase_count = len(payload.get("phases") or [])
    status = html.escape(str(summary.get("status") or "UNKNOWN"))
    scenario_name = html.escape(str(scenario.get("name") or ""))
    scenario_pair = html.escape(str(scenario.get("pair") or ""))
    scenario_lane = html.escape(str(scenario.get("lane") or ""))
    generated_at = html.escape(str(payload.get("generated_at") or ""))
    title_text = html.escape(str(title or APP_TITLE))
    data_blob = html.escape(json.dumps(payload, ensure_ascii=False), quote=False)
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{title_text}</title>
  <style>
    :root {{
      --paper: #f7f1e3;
      --paper-2: #efe5cf;
      --ink: #1e2328;
      --muted: #59616b;
      --line: #c7b99e;
      --line-strong: #8f7d5b;
      --card: rgba(255, 250, 238, 0.88);
      --ok: #1d6b3b;
      --warn: #9a5a00;
      --fail: #a52a2a;
      --accent: #004f67;
      --accent-soft: #d7eef3;
      --chip: #ece3cf;
      --shadow: 0 14px 34px rgba(36, 28, 16, 0.12);
      --mono: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      --sans: "Avenir Next", "Segoe UI", "Trebuchet MS", Verdana, sans-serif;
      --serif: Charter, "Iowan Old Style", "Palatino Linotype", Georgia, serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--sans);
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(0, 79, 103, 0.08), transparent 28%),
        linear-gradient(180deg, rgba(255,255,255,0.52), rgba(255,255,255,0.18)),
        repeating-linear-gradient(
          0deg,
          transparent 0,
          transparent 27px,
          rgba(143, 125, 91, 0.08) 28px
        ),
        var(--paper);
    }}
    .app {{
      max-width: 1680px;
      margin: 0 auto;
      padding: 24px;
    }}
    .hero {{
      display: grid;
      gap: 16px;
      background: linear-gradient(135deg, rgba(255, 248, 232, 0.95), rgba(232, 244, 247, 0.95));
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 24px;
      box-shadow: var(--shadow);
    }}
    .hero-top {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .eyebrow {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }}
    h1, h2, h3 {{
      font-family: var(--serif);
      margin: 0;
      font-weight: 700;
      line-height: 1.08;
    }}
    h1 {{ font-size: clamp(2rem, 3vw, 3.2rem); }}
    h2 {{ font-size: 1.35rem; margin-bottom: 12px; }}
    h3 {{ font-size: 1rem; margin-bottom: 10px; }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .meta-card, .card {{
      background: var(--card);
      border: 1px solid rgba(143, 125, 91, 0.24);
      border-radius: 18px;
      padding: 16px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.4);
    }}
    .meta-label {{
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .meta-value {{
      font-size: 1rem;
      font-weight: 700;
      word-break: break-word;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid currentColor;
      font-weight: 700;
      font-size: 0.95rem;
      background: rgba(255,255,255,0.72);
    }}
    .status-pass {{ color: var(--ok); }}
    .status-warn {{ color: var(--warn); }}
    .status-fail {{ color: var(--fail); }}
    .controls {{
      margin-top: 18px;
      display: grid;
      gap: 12px;
      background: rgba(255, 252, 244, 0.92);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}
    .controls-top {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }}
    button {{
      appearance: none;
      border: 1px solid var(--line-strong);
      background: linear-gradient(180deg, #fff9ef, #eadfc7);
      color: var(--ink);
      border-radius: 999px;
      padding: 10px 14px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    button[disabled] {{ opacity: 0.45; cursor: default; }}
    .phase-range {{ width: 100%; }}
    .phase-tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .phase-tab {{
      border-radius: 999px;
      padding: 8px 12px;
      background: var(--chip);
      border: 1px solid rgba(143, 125, 91, 0.2);
      cursor: pointer;
      font-size: 0.92rem;
    }}
    .phase-tab.active {{
      background: var(--accent);
      color: white;
      border-color: var(--accent);
    }}
    .layout {{
      margin-top: 18px;
      display: grid;
      grid-template-columns: minmax(0, 1.9fr) minmax(320px, 0.95fr);
      gap: 18px;
      align-items: start;
    }}
    .stack {{ display: grid; gap: 18px; }}
    .sidebar {{ position: sticky; top: 18px; display: grid; gap: 18px; }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px;
    }}
    .count-card {{
      padding: 14px;
      border-radius: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(242, 231, 210, 0.9));
      border: 1px solid rgba(143, 125, 91, 0.18);
    }}
    .count-card .meta-label {{ margin-bottom: 4px; }}
    .count-card .meta-value {{ font-size: 1.5rem; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 9px;
      border-radius: 999px;
      background: var(--chip);
      border: 1px solid rgba(143, 125, 91, 0.18);
      font-size: 0.86rem;
      font-family: var(--mono);
    }}
    .chip.ok {{ background: rgba(29, 107, 59, 0.12); color: var(--ok); }}
    .chip.warn {{ background: rgba(154, 90, 0, 0.12); color: var(--warn); }}
    .chip.fail {{ background: rgba(165, 42, 42, 0.12); color: var(--fail); }}
    .chip.active {{ background: rgba(0, 79, 103, 0.14); color: var(--accent); }}
    .muted {{ color: var(--muted); }}
    .mono {{ font-family: var(--mono); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ text-align: left; vertical-align: top; padding: 10px 8px; border-bottom: 1px solid rgba(143, 125, 91, 0.18); }}
    th {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }}
    .table-wrap {{ overflow-x: auto; }}
    .item-main {{ font-weight: 700; }}
    .item-sub {{ margin-top: 4px; color: var(--muted); font-size: 0.83rem; line-height: 1.35; }}
    details {{ border-top: 1px dashed rgba(143, 125, 91, 0.35); padding-top: 12px; }}
    summary {{ cursor: pointer; font-weight: 700; }}
    pre {{
      margin: 12px 0 0;
      padding: 14px;
      border-radius: 14px;
      background: #1f2328;
      color: #f1f5f8;
      overflow: auto;
      font-size: 0.82rem;
      line-height: 1.5;
    }}
    .timeline-note {{ margin-top: 8px; font-size: 0.88rem; color: var(--muted); }}
    .finding-list {{ display: grid; gap: 10px; }}
    .finding {{
      border-left: 4px solid var(--line-strong);
      padding: 10px 12px;
      border-radius: 0 14px 14px 0;
      background: rgba(255,255,255,0.58);
    }}
    .finding.pass {{ border-color: var(--ok); }}
    .finding.warn {{ border-color: var(--warn); }}
    .finding.fail {{ border-color: var(--fail); }}
    .empty {{ color: var(--muted); font-style: italic; }}
    .sidebar .card {{ max-height: calc(100vh - 48px); overflow: auto; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .phase-kicker {{ font-size: 0.95rem; color: var(--muted); }}
    @media (max-width: 1100px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ position: static; }}
      .sidebar .card {{ max-height: none; }}
    }}
  </style>
</head>
<body>
  <div class=\"app\">
    <section class=\"hero\">
      <div class=\"hero-top\">
        <div>
          <p class=\"eyebrow\">Pedagogical Playback</p>
          <h1>{title_text}</h1>
          <p class=\"phase-kicker\">Scenario <span class=\"mono\">{scenario_name}</span> · Pair <span class=\"mono\">{scenario_pair}</span> · Lane <span class=\"mono\">{scenario_lane}</span></p>
        </div>
        <div class=\"status-pill status-{"pass" if summary.get("status") == "PASS" else "warn" if summary.get("status") == "WARN" else "fail"}\">{status}</div>
      </div>
      <div class=\"meta-grid\">
        <div class=\"meta-card\"><div class=\"meta-label\">Generated</div><div class=\"meta-value mono\">{generated_at}</div></div>
        <div class=\"meta-card\"><div class=\"meta-label\">Phase Count</div><div class=\"meta-value\">{phase_count}</div></div>
        <div class=\"meta-card\"><div class=\"meta-label\">Findings</div><div class=\"meta-value\">pass={int(summary.get("pass_count") or 0)} warn={int(summary.get("warn_count") or 0)} fail={int(summary.get("fail_count") or 0)}</div></div>
        <div class=\"meta-card\"><div class=\"meta-label\">Contract Mode</div><div class=\"meta-value mono\">{html.escape(str(scenario.get("contract_mode") or ""))}</div></div>
      </div>
    </section>

    <section class=\"controls\">
      <div class=\"controls-top\">
        <button id=\"prev-phase\" type=\"button\">Previous</button>
        <button id=\"playback-toggle\" type=\"button\">Play</button>
        <button id=\"next-phase\" type=\"button\">Next</button>
        <span class=\"muted\" id=\"phase-position\"></span>
      </div>
      <input id=\"phase-range\" class=\"phase-range\" type=\"range\" min=\"0\" max=\"0\" value=\"0\" step=\"1\">
      <div id=\"phase-tabs\" class=\"phase-tabs\"></div>
    </section>

    <main class=\"layout\">
      <section class=\"stack\">
        <article class=\"card\">
          <p class=\"eyebrow\">Current Step</p>
          <h2 id=\"phase-title\">Phase</h2>
          <p id=\"phase-subtitle\" class=\"phase-kicker\"></p>
          <div id=\"phase-counts\" class=\"card-grid\"></div>
        </article>

        <article class=\"card\">
          <h2>Sets and Deltas</h2>
          <div id=\"phase-sets\"></div>
        </article>

        <article class=\"card\">
          <h2>Signals and Events</h2>
          <div id=\"phase-events\"></div>
        </article>

        <article class=\"card\">
          <h2>Admission Review</h2>
          <div id=\"phase-admission\"></div>
        </article>

        <article class=\"card\">
          <h2>Findings</h2>
          <div id=\"phase-findings\"></div>
        </article>

        <article class=\"card\">
          <h2>Raw Phase JSON</h2>
          <details open>
            <summary>Open current phase payload</summary>
            <pre id=\"raw-phase\"></pre>
          </details>
        </article>
      </section>

      <aside class=\"sidebar\">
        <article class=\"card\">
          <h2>Profile State</h2>
          <p class=\"phase-kicker\">Item-level scheduler state for the currently selected step.</p>
          <div class=\"legend\">
            <span class=\"chip active\">A = admitted</span>
            <span class=\"chip ok\">D = due</span>
            <span class=\"chip warn\">P = published</span>
          </div>
          <div id=\"profile-state\"></div>
        </article>

        <article class=\"card\">
          <h2>Global Data</h2>
          <div id=\"global-panels\"></div>
          <details>
            <summary>Full report JSON</summary>
            <pre id=\"raw-report\"></pre>
          </details>
        </article>
      </aside>
    </main>
  </div>

  <script id=\"journey-data\" type=\"application/json\">{data_blob}</script>
  <script>
    const payload = JSON.parse(document.getElementById('journey-data').textContent);
    const phases = Array.isArray(payload.phases) ? payload.phases : [];
    let currentIndex = 0;
    let timer = null;

    const els = {{
      prev: document.getElementById('prev-phase'),
      play: document.getElementById('playback-toggle'),
      next: document.getElementById('next-phase'),
      range: document.getElementById('phase-range'),
      tabs: document.getElementById('phase-tabs'),
      position: document.getElementById('phase-position'),
      title: document.getElementById('phase-title'),
      subtitle: document.getElementById('phase-subtitle'),
      counts: document.getElementById('phase-counts'),
      sets: document.getElementById('phase-sets'),
      events: document.getElementById('phase-events'),
      admission: document.getElementById('phase-admission'),
      findings: document.getElementById('phase-findings'),
      profileState: document.getElementById('profile-state'),
      globalPanels: document.getElementById('global-panels'),
      rawPhase: document.getElementById('raw-phase'),
      rawReport: document.getElementById('raw-report'),
    }};

    function fmt(value, digits = 3) {{
      if (value === null || value === undefined || value === '') return '—';
      const number = Number(value);
      if (Number.isNaN(number)) return String(value);
      return number.toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1');
    }}

    function pct(value) {{
      if (value === null || value === undefined) return '—';
      const number = Number(value);
      if (Number.isNaN(number)) return '—';
      return `${{(number * 100).toFixed(1)}}%`;
    }}

    function escapeHtml(value) {{
      const span = document.createElement('span');
      span.textContent = value === null || value === undefined ? '' : String(value);
      return span.innerHTML;
    }}

    function statusClass(level) {{
      const normalized = String(level || '').toUpperCase();
      if (normalized === 'PASS') return 'pass';
      if (normalized === 'WARN') return 'warn';
      return 'fail';
    }}

    function chipList(values, kind = '') {{
      const items = Array.isArray(values) ? values : [];
      if (!items.length) return '<span class=\"empty\">none</span>';
      return `<div class=\"chips\">${{items.map((item) => `<span class=\"chip ${{kind}}\">${{escapeHtml(item)}}</span>`).join('')}}</div>`;
    }}

    function renderPhaseTabs() {{
      els.range.max = String(Math.max(phases.length - 1, 0));
      els.tabs.innerHTML = phases.map((phase, index) => {{
        const active = index === currentIndex ? ' active' : '';
        return `<button type=\"button\" class=\"phase-tab${{active}}\" data-index=\"${{index}}\">${{index + 1}}. ${{escapeHtml(phase.label || 'phase')}}</button>`;
      }}).join('');
      Array.from(els.tabs.querySelectorAll('.phase-tab')).forEach((button) => {{
        button.addEventListener('click', () => renderPhase(Number(button.dataset.index || '0')));
      }});
    }}

    function renderCounts(phase) {{
      const counts = phase && typeof phase.counts === 'object' ? phase.counts : {{}};
      const refreshPayload = phase && phase.refresh && phase.refresh.payload && typeof phase.refresh.payload === 'object'
        ? phase.refresh.payload
        : null;
      const feedbackWindow = refreshPayload && refreshPayload.admission_refresh && typeof refreshPayload.admission_refresh.feedback_window === 'object'
        ? refreshPayload.admission_refresh.feedback_window
        : null;
      const cards = [
        ['Admitted', counts.admitted],
        ['Due', counts.due],
        ['Published', counts.published],
        ['Feedback In Step', phase.events_applied && phase.events_applied.counts ? phase.events_applied.counts.feedback : 0],
        ['Exposure In Step', phase.events_applied && phase.events_applied.counts ? phase.events_applied.counts.exposure : 0],
        ['Retention', feedbackWindow ? pct(feedbackWindow.retention_ratio) : '—'],
      ];
      els.counts.innerHTML = cards.map(([label, value]) => `
        <div class=\"count-card\">
          <div class=\"meta-label\">${{escapeHtml(label)}}</div>
          <div class=\"meta-value\">${{escapeHtml(value)}}</div>
        </div>
      `).join('');
    }}

    function renderSets(phase) {{
      const sets = phase && typeof phase.sets === 'object' ? phase.sets : {{}};
      const deltas = phase && typeof phase.deltas === 'object' ? phase.deltas : {{}};
      const relationships = phase && typeof phase.relationships === 'object' ? phase.relationships : {{}};
      els.sets.innerHTML = `
        <div class=\"card-grid\">
          <div class=\"meta-card\"><div class=\"meta-label\">Admitted</div>${{chipList(sets.admitted)}}</div>
          <div class=\"meta-card\"><div class=\"meta-label\">Due</div>${{chipList(sets.due, 'ok')}}</div>
          <div class=\"meta-card\"><div class=\"meta-label\">Published</div>${{chipList(sets.published, 'warn')}}</div>
        </div>
        <div class=\"card-grid\" style=\"margin-top:12px;\">
          <div class=\"meta-card\"><div class=\"meta-label\">Admitted In / Out</div>${{chipList(deltas.admitted_in, 'active')}}<div style=\"height:8px\"></div>${{chipList(deltas.admitted_out)}}</div>
          <div class=\"meta-card\"><div class=\"meta-label\">Due In / Out</div>${{chipList(deltas.due_in, 'ok')}}<div style=\"height:8px\"></div>${{chipList(deltas.due_out)}}</div>
          <div class=\"meta-card\"><div class=\"meta-label\">Published In / Out</div>${{chipList(deltas.published_in, 'warn')}}<div style=\"height:8px\"></div>${{chipList(deltas.published_out)}}</div>
        </div>
        <div class=\"card-grid\" style=\"margin-top:12px;\">
          <div class=\"meta-card\"><div class=\"meta-label\">Published Not Due</div>${{chipList(relationships.published_not_due, 'warn')}}</div>
          <div class=\"meta-card\"><div class=\"meta-label\">Due Not Published</div>${{chipList(relationships.due_not_published, 'fail')}}</div>
          <div class=\"meta-card\"><div class=\"meta-label\">Published Not Admitted</div>${{chipList(relationships.published_not_admitted, 'fail')}}</div>
        </div>
      `;
    }}

    function renderEventTable(events, kind) {{
      if (!Array.isArray(events) || !events.length) return '<p class=\"empty\">none</p>';
      const ratingHeader = kind === 'feedback' ? '<th>Rating</th>' : '';
      return `
        <div class=\"table-wrap\">
          <table>
            <thead>
              <tr><th>#</th><th>Lemma</th>${{ratingHeader}}<th>Cohort</th><th>Timestamp</th></tr>
            </thead>
            <tbody>
              ${{events.map((event) => `
                <tr>
                  <td class=\"mono\">${{escapeHtml(event.index)}}</td>
                  <td class=\"mono\">${{escapeHtml(event.lemma)}}</td>
                  ${{kind === 'feedback' ? `<td class=\"mono\">${{escapeHtml(event.rating || '—')}}</td>` : ''}}
                  <td>${{escapeHtml(event.cohort || '—')}}</td>
                  <td class=\"mono\">${{escapeHtml(event.ts || '—')}}</td>
                </tr>
              `).join('')}}
            </tbody>
          </table>
        </div>
      `;
    }}

    function renderEvents(phase) {{
      const events = phase && typeof phase.events_applied === 'object' ? phase.events_applied : {{}};
      els.events.innerHTML = `
        <div class=\"card-grid\">
          <div class=\"meta-card\"><div class=\"meta-label\">Feedback</div>${{renderEventTable(events.feedback, 'feedback')}}</div>
          <div class=\"meta-card\"><div class=\"meta-label\">Exposure</div>${{renderEventTable(events.exposure, 'exposure')}}</div>
        </div>
      `;
    }}

    function renderCandidateTable(candidates, selectorMode) {{
      if (!Array.isArray(candidates) || !candidates.length) return '<p class=\"empty\">no candidate audit</p>';
      const selectorHeaders = selectorMode
        ? '<th>Eligible</th><th>Reason</th><th>Score</th><th>Score Share</th>'
        : '';
      const selectorCells = (candidate) => selectorMode
        ? `<td>${{candidate.eligible ? 'yes' : 'no'}}</td><td class=\"mono\">${{escapeHtml(candidate.filtered_reason || '—')}}</td><td class=\"mono\">${{escapeHtml(fmt(candidate.selector_score, 6))}}</td><td class=\"mono\">${{escapeHtml(pct(candidate.selector_score_share))}}</td>`
        : '';
      return `
        <div class=\"table-wrap\">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Lemma</th>
                <th>Cohort</th>
                <th>Selected</th>
                <th>Admit Wt</th>
                <th>Wt Share</th>
                ${{selectorHeaders}}
                <th>Core Rank</th>
                <th>POS</th>
              </tr>
            </thead>
            <tbody>
              ${{candidates.map((candidate) => `
                <tr>
                  <td class=\"mono\">${{escapeHtml(candidate.seed_rank)}}</td>
                  <td>
                    <div class=\"item-main mono\">${{escapeHtml(candidate.lemma)}}</div>
                    <div class=\"item-sub\">${{escapeHtml(candidate.word_package && candidate.word_package.reading ? candidate.word_package.reading : '')}}</div>
                  </td>
                  <td>${{escapeHtml(candidate.cohort || '—')}}</td>
                  <td>${{candidate.selected ? `<span class=\"chip active\">#${{candidate.selected_order}}</span>` : '<span class=\"empty\">no</span>'}}</td>
                  <td class=\"mono\">${{escapeHtml(fmt(candidate.admission_weight, 6))}}</td>
                  <td class=\"mono\">${{escapeHtml(pct(candidate.admission_weight_share))}}</td>
                  ${{selectorCells(candidate)}}
                  <td class=\"mono\">${{escapeHtml(fmt(candidate.core_rank, 2))}}</td>
                  <td class=\"mono\">${{escapeHtml(candidate.pos_bucket || candidate.pos || '—')}}</td>
                </tr>
              `).join('')}}
            </tbody>
          </table>
        </div>
      `;
    }}

    function renderAdmission(phase) {{
      const refresh = phase && typeof phase.refresh === 'object' ? phase.refresh : {{}};
      const payload = refresh && typeof refresh.payload === 'object' ? refresh.payload : null;
      const admission = payload && typeof payload.admission_refresh === 'object'
        ? payload.admission_refresh
        : null;
      const audit = refresh && typeof refresh.audit === 'object' ? refresh.audit : null;
      const bootstrapAudit = payload && payload.bootstrap_audit;
      if (refresh.requested && payload) {{
        els.admission.innerHTML = `
          <div class=\"card-grid\">
            <div class=\"meta-card\"><div class=\"meta-label\">Refresh Applied</div><div class=\"meta-value\">${{payload.applied ? 'yes' : 'no'}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Reason</div><div class=\"meta-value mono\">${{escapeHtml(admission && admission.reason_code ? admission.reason_code : '—')}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Admission Budget</div><div class=\"meta-value\">${{escapeHtml(admission ? admission.admission_budget : '—')}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Selected Lemmas</div>${{chipList(admission && admission.selected_lemmas, 'active')}}</div>
          </div>
          <div class=\"card-grid\" style=\"margin-top:12px;\">
            <div class=\"meta-card\"><div class=\"meta-label\">Due Pressure</div><div class=\"meta-value\">${{escapeHtml(pct(admission && admission.due_pressure))}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Candidate Pool</div><div class=\"meta-value\">${{escapeHtml(admission ? admission.candidate_pool_size : '—')}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Retention</div><div class=\"meta-value\">${{escapeHtml(pct(admission && admission.feedback_window ? admission.feedback_window.retention_ratio : null))}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Strain</div><div class=\"meta-value\">${{escapeHtml(pct(admission && admission.feedback_window ? admission.feedback_window.strain_ratio : null))}}</div></div>
          </div>
          <div style=\"margin-top:12px;\">${{renderCandidateTable(audit && audit.candidates, true)}}</div>
        `;
        return;
      }}
      const bootstrap = payload && typeof payload.bootstrap_audit === 'object' ? payload.bootstrap_audit : null;
      if ((phase.label === 'bootstrap_publish' || phase.label === 'baseline_observe') && payload === null) {{
        const initAudit = payload && payload.bootstrap_audit;
      }}
      const initBootstrap = payload && typeof payload.bootstrap_audit === 'object'
        ? payload.bootstrap_audit
        : null;
      const bootstrapSource = (payload && payload.bootstrap_audit) || (window.__bootstrapAudit || null);
      if ((phase.label === 'bootstrap_publish' || phase.label === 'baseline_observe') && bootstrapSource) {{
        els.admission.innerHTML = `
          <div class=\"card-grid\">
            <div class=\"meta-card\"><div class=\"meta-label\">Bootstrap Candidates</div><div class=\"meta-value\">${{escapeHtml(bootstrapSource.candidate_count || '—')}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Initial Active</div><div class=\"meta-value\">${{escapeHtml(bootstrapSource.admitted_count || '—')}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Admission Weight Sum</div><div class=\"meta-value mono\">${{escapeHtml(fmt(bootstrapSource.admission_weight_sum, 6))}}</div></div>
            <div class=\"meta-card\"><div class=\"meta-label\">Stopwords</div><div class=\"meta-value mono\">${{escapeHtml(bootstrapSource.stopwords_path || 'none')}}</div></div>
          </div>
          <div style=\"margin-top:12px;\">${{renderCandidateTable(bootstrapSource.candidates, false)}}</div>
        `;
        return;
      }}
      els.admission.innerHTML = '<p class=\"empty\">No admission review for this phase.</p>';
    }}

    function renderFindings(phase) {{
      const local = Array.isArray(phase.findings) ? phase.findings : [];
      const globalWarnings = (Array.isArray(payload.findings) ? payload.findings : []).filter((item) => item && item.phase === phase.label);
      const merged = [...local, ...globalWarnings.filter((item) => !local.includes(item))];
      if (!merged.length) {{
        els.findings.innerHTML = '<p class=\"empty\">No findings attached to this phase.</p>';
        return;
      }}
      els.findings.innerHTML = `<div class=\"finding-list\">${{merged.map((item) => `
        <div class=\"finding ${{statusClass(item.level)}}\">
          <div class=\"meta-label\">${{escapeHtml(item.level || 'NOTE')}} · <span class=\"mono\">${{escapeHtml(item.code || 'code')}}</span></div>
          <div><strong>${{escapeHtml(item.message || '')}}</strong></div>
          <div class=\"timeline-note\">${{escapeHtml(item.details || '') || 'No extra details.'}}</div>
        </div>
      `).join('')}}</div>`;
    }}

    function itemBadges(item) {{
      const badges = ['<span class=\"chip active\">A</span>'];
      if (item.in_due) badges.push('<span class=\"chip ok\">D</span>');
      if (item.in_published) badges.push('<span class=\"chip warn\">P</span>');
      return badges.join(' ');
    }}

    function historyText(item) {{
      const history = Array.isArray(item.recent_history) ? item.recent_history : [];
      if (!history.length) return 'no recent reviews';
      return history.map((entry) => `${{entry.rating || '?'}} @ ${{entry.ts || '—'}}`).join(' · ');
    }}

    function renderProfileState(phase) {{
      const items = Array.isArray(phase.items) ? phase.items : [];
      if (!items.length) {{
        els.profileState.innerHTML = '<p class=\"empty\">No item state available.</p>';
        return;
      }}
      els.profileState.innerHTML = `
        <div class=\"table-wrap\">
          <table>
            <thead>
              <tr>
                <th>Lemma</th>
                <th>State</th>
                <th>Confidence</th>
                <th>Stability</th>
                <th>Difficulty</th>
                <th>Exposure</th>
                <th>Next Due</th>
              </tr>
            </thead>
            <tbody>
              ${{items.map((item) => `
                <tr>
                  <td>
                    <div class=\"item-main mono\">${{escapeHtml(item.lemma)}}</div>
                    <div class=\"item-sub\">${{escapeHtml(item.word_package && item.word_package.reading ? item.word_package.reading : '')}}</div>
                    <div class=\"item-sub\">${{escapeHtml(item.word_package && item.word_package.pos_canonical ? item.word_package.pos_canonical : item.source_type || '')}}</div>
                  </td>
                  <td>
                    <div>${{itemBadges(item)}}</div>
                    <div class=\"item-sub\">${{escapeHtml(item.cohort || '—')}} · ${{escapeHtml(item.status || '—')}}</div>
                    <div class=\"item-sub\">due rank: ${{escapeHtml(item.due_rank || '—')}}</div>
                    <div class=\"item-sub\">${{escapeHtml(historyText(item))}}</div>
                  </td>
                  <td class=\"mono\">${{escapeHtml(fmt(item.confidence, 6))}}</td>
                  <td class=\"mono\">${{escapeHtml(fmt(item.stability, 3))}}</td>
                  <td class=\"mono\">${{escapeHtml(fmt(item.difficulty, 3))}}</td>
                  <td class=\"mono\">${{escapeHtml(item.exposures)}}</td>
                  <td class=\"mono\">${{escapeHtml(item.next_due || '—')}}</td>
                </tr>
              `).join('')}}
            </tbody>
          </table>
        </div>
      `;
    }}

    function renderGlobalPanels() {{
      const signalSummary = payload.signal_summary && typeof payload.signal_summary === 'object'
        ? payload.signal_summary
        : null;
      const bootstrapAudit = payload.initialize && typeof payload.initialize.bootstrap_audit === 'object'
        ? payload.initialize.bootstrap_audit
        : null;
      window.__bootstrapAudit = bootstrapAudit;
      els.globalPanels.innerHTML = `
        <div class=\"meta-card\">
          <div class=\"meta-label\">Signal Log</div>
          <div class=\"meta-value\">${{escapeHtml(signalSummary ? signalSummary.event_count : '—')}}</div>
          <div class=\"timeline-note\">feedback=${{escapeHtml(signalSummary && signalSummary.event_types ? signalSummary.event_types.feedback : '0')}} exposure=${{escapeHtml(signalSummary && signalSummary.event_types ? signalSummary.event_types.exposure : '0')}}</div>
        </div>
        <div class=\"meta-card\" style=\"margin-top:12px;\">
          <div class=\"meta-label\">Bootstrap Audit</div>
          <div class=\"meta-value\">${{escapeHtml(bootstrapAudit ? bootstrapAudit.candidate_count : '—')}} candidates</div>
          <div class=\"timeline-note\">Selected at bootstrap: ${{bootstrapAudit && Array.isArray(bootstrapAudit.candidates) ? bootstrapAudit.candidates.filter((item) => item.selected).map((item) => item.lemma).join(', ') : '—'}}</div>
        </div>
      `;
      els.rawReport.textContent = JSON.stringify(payload, null, 2);
    }}

    function stopPlayback() {{
      if (timer) {{
        window.clearInterval(timer);
        timer = null;
      }}
      els.play.textContent = 'Play';
    }}

    function togglePlayback() {{
      if (timer) {{
        stopPlayback();
        return;
      }}
      els.play.textContent = 'Pause';
      timer = window.setInterval(() => {{
        if (currentIndex >= phases.length - 1) {{
          stopPlayback();
          return;
        }}
        renderPhase(currentIndex + 1);
      }}, 1500);
    }}

    function renderPhase(index) {{
      if (!phases.length) return;
      currentIndex = Math.max(0, Math.min(index, phases.length - 1));
      const phase = phases[currentIndex];
      els.range.value = String(currentIndex);
      els.position.textContent = `Step ${{currentIndex + 1}} of ${{phases.length}}`;
      els.title.textContent = `${{currentIndex + 1}}. ${{phase.label || 'phase'}}`;
      els.subtitle.textContent = `${{phase.now || '—'}}`;
      renderPhaseTabs();
      renderCounts(phase);
      renderSets(phase);
      renderEvents(phase);
      renderAdmission(phase);
      renderFindings(phase);
      renderProfileState(phase);
      els.rawPhase.textContent = JSON.stringify(phase, null, 2);
      els.prev.disabled = currentIndex <= 0;
      els.next.disabled = currentIndex >= phases.length - 1;
    }}

    els.prev.addEventListener('click', () => renderPhase(currentIndex - 1));
    els.next.addEventListener('click', () => renderPhase(currentIndex + 1));
    els.play.addEventListener('click', togglePlayback);
    els.range.addEventListener('input', (event) => renderPhase(Number(event.target.value || '0')));

    renderGlobalPanels();
    if (phases.length) {{
      renderPhase(0);
    }} else {{
      els.title.textContent = 'No phases in report';
      els.subtitle.textContent = '';
      els.rawReport.textContent = JSON.stringify(payload, null, 2);
    }}
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render an interactive HTML pedagogical review surface from SRS journey JSON."
    )
    parser.add_argument(
        "--journey-json", type=Path, required=True, help="Path to SRS journey JSON."
    )
    parser.add_argument("--title", default=APP_TITLE, help="HTML title.")
    parser.add_argument("--html-out", type=Path, required=True, help="Path to write HTML output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    html_text = render_html(_load_json(args.journey_json), title=str(args.title))
    args.html_out.parent.mkdir(parents=True, exist_ok=True)
    args.html_out.write_text(html_text, encoding="utf-8")
    print(f"html_out: {args.html_out}")


if __name__ == "__main__":
    main()

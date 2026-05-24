// Model color palette — consistent across all charts.
const MODEL_COLORS = {
  "claude-opus-4-7":               "hsl(280, 70%, 65%)",
  "claude-sonnet-4-6":             "hsl(220, 80%, 65%)",
  "claude-haiku-4-5-20251001":     "hsl(180, 70%, 60%)",
  "llama-3.3-70b-versatile":       "hsl(25, 85%, 60%)",
  "deepseek-r1-distill-llama-70b": "hsl(0, 75%, 60%)",
  "llama-3.1-8b-instant":          "hsl(55, 85%, 60%)",
};

const $ = (sel) => document.querySelector(sel);
let INDEX = null;       // { runs: [{timestamp, finished_at, placeholder, overall_model_means, task_model_means}] }
let CURRENT = null;     // full run JSON for the currently-selected timestamp

function scoreColor(score) {
  if (score == null) return "#2a2f3a";
  const hue = score * 130;
  const sat = 65 - Math.abs(score - 0.5) * 20;
  return `hsl(${hue}, ${sat}%, 50%)`;
}

function costUsd(inputTok, outputTok, model) {
  const inCost = (inputTok / 1_000_000) * model.input_per_mtok;
  const outCost = (outputTok / 1_000_000) * model.output_per_mtok;
  return inCost + outCost;
}

function fmtUsd(n) {
  if (n === 0) return "free";
  if (n < 0.001) return `<$0.001`;
  if (n < 0.01) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(3)}`;
}

function fmtTimestamp(ts) {
  if (!ts) return "—";
  // 20260601T100000Z → 2026-06-01 10:00 UTC
  const m = ts.match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]} ${m[4]}:${m[5]} UTC`;
  return ts;
}

function fmtShortDate(ts) {
  const m = ts.match(/^(\d{4})(\d{2})(\d{2})/);
  return m ? `${m[1]}-${m[2]}` : ts;
}

function renderMeta(data) {
  const placeholder = data.placeholder
    ? `<div class="placeholder-banner">⚠ Showing placeholder data. Real runs will replace this each month — first will fire on the 1st.</div>`
    : "";
  const ts = data.finished_at ? new Date(data.finished_at).toLocaleString() : "—";
  $("#run-meta").innerHTML =
    `${placeholder}This view: <strong>${ts}</strong> · ` +
    `${data.tasks.length} tasks × ${data.models.length} models · ` +
    `${data.tasks.reduce((s, t) => s + t.n_prompts, 0)} prompts/model`;
}

function renderRunPicker(index, selectedTs) {
  const picker = $("#run-picker");
  picker.innerHTML = "";
  const runs = [...(index?.runs || [])].reverse();
  for (const run of runs) {
    const opt = document.createElement("option");
    opt.value = run.timestamp;
    opt.textContent = fmtTimestamp(run.timestamp) + (run.placeholder ? "  (placeholder)" : "");
    if (run.timestamp === selectedTs) opt.selected = true;
    picker.appendChild(opt);
  }
  picker.onchange = async () => {
    const ts = picker.value;
    const r = await fetch(`results/${ts}.json`);
    if (r.ok) {
      CURRENT = await r.json();
      renderEverything();
    } else {
      // Some timestamps might not have a file (e.g., latest.json points to a file
      // with a different name). Fall back to latest.json.
      const r2 = await fetch("results/latest.json");
      CURRENT = await r2.json();
      renderEverything();
    }
  };
}

function renderGrid(data) {
  const grid = $("#grid");
  grid.innerHTML = "";

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headRow.appendChild(document.createElement("th"));
  for (const model of data.models) {
    const th = document.createElement("th");
    th.className = "col-header";
    th.innerHTML = `<span class="dot" style="background:${MODEL_COLORS[model.id] || '#888'}"></span>${model.label}`;
    headRow.appendChild(th);
  }
  thead.appendChild(headRow);
  grid.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const task of data.tasks) {
    const row = document.createElement("tr");
    const nameTd = document.createElement("td");
    nameTd.className = "task-name";
    nameTd.innerHTML = `${task.category}<span class="scorer">${task.scorer_kind}</span>`;
    row.appendChild(nameTd);

    for (const model of data.models) {
      const cell = data.cells?.[task.category]?.[model.id];
      const td = document.createElement("td");
      td.className = "cell";
      if (!cell) {
        td.style.background = "#2a2f3a";
        td.textContent = "—";
      } else {
        const score = cell.mean_score;
        td.style.background = scoreColor(score);
        td.style.color = score > 0.4 ? "#000" : "#fff";
        const cost = costUsd(cell.total_input_tokens || 0, cell.total_output_tokens || 0, model);
        td.innerHTML = `${score.toFixed(2)}<span class="cost">${fmtUsd(cost)}</span>`;
        td.onclick = () => renderDrill(task, model, cell);
      }
      row.appendChild(td);
    }
    tbody.appendChild(row);
  }
  grid.appendChild(tbody);
}

function renderDrift(index, currentTs) {
  const container = $("#drift-table");
  container.innerHTML = "";
  if (!index || index.runs.length < 2) {
    container.innerHTML = `<p class="muted">Drift will appear once two or more runs exist.</p>`;
    return;
  }
  const idx = index.runs.findIndex(r => r.timestamp === currentTs);
  if (idx <= 0) {
    container.innerHTML = `<p class="muted">No earlier run to compare against.</p>`;
    return;
  }
  const cur = index.runs[idx];
  const prev = index.runs[idx - 1];

  const deltas = [];
  for (const [cat, modelMap] of Object.entries(cur.task_model_means)) {
    const prevMap = prev.task_model_means[cat] || {};
    for (const [mid, score] of Object.entries(modelMap)) {
      if (prevMap[mid] == null) continue;
      const delta = score - prevMap[mid];
      deltas.push({ cat, mid, prev: prevMap[mid], cur: score, delta });
    }
  }
  deltas.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  const top = deltas.slice(0, 10);

  const table = document.createElement("table");
  table.className = "drift-table";
  table.innerHTML = `<thead><tr>
    <th>Task</th><th>Model</th><th>Prev (${fmtShortDate(prev.timestamp)})</th>
    <th>Now (${fmtShortDate(cur.timestamp)})</th><th>Δ</th>
  </tr></thead>`;
  const tbody = document.createElement("tbody");
  for (const d of top) {
    const tr = document.createElement("tr");
    const deltaCls = d.delta < -0.05 ? "drop" : d.delta > 0.05 ? "rise" : "neutral";
    const sign = d.delta >= 0 ? "+" : "";
    tr.innerHTML = `
      <td>${d.cat}</td>
      <td><span class="dot" style="background:${MODEL_COLORS[d.mid] || '#888'}"></span>${d.mid}</td>
      <td>${d.prev.toFixed(2)}</td>
      <td>${d.cur.toFixed(2)}</td>
      <td class="delta ${deltaCls}">${sign}${d.delta.toFixed(2)}</td>
    `;
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  container.appendChild(table);
}

function renderTrends(index) {
  const grid = $("#trends-grid");
  grid.innerHTML = "";
  if (!index || index.runs.length === 0) {
    grid.innerHTML = `<p class="muted">No runs yet.</p>`;
    return;
  }
  const categories = Object.keys(index.runs[index.runs.length - 1].task_model_means);
  const modelIds = Object.keys(index.runs[index.runs.length - 1].overall_model_means);
  for (const cat of categories) {
    const card = document.createElement("div");
    card.className = "trend-card";
    card.innerHTML = `<h3>${cat}</h3>`;
    card.appendChild(buildTrendSvg(index.runs, cat, modelIds));
    grid.appendChild(card);
  }
  // Legend
  const legend = $("#trend-legend");
  legend.innerHTML = "";
  for (const mid of modelIds) {
    const span = document.createElement("span");
    span.className = "legend-item";
    span.innerHTML = `<span class="dot" style="background:${MODEL_COLORS[mid] || '#888'}"></span>${mid}`;
    legend.appendChild(span);
  }
}

function buildTrendSvg(runs, category, modelIds) {
  const W = 280, H = 120, padL = 28, padR = 8, padT = 8, padB = 18;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const xs = runs.map((_, i) => padL + (runs.length === 1 ? innerW / 2 : (i * innerW) / (runs.length - 1)));
  const yScale = (s) => padT + (1 - s) * innerH;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("class", "trend-svg");

  // Y axis grid lines at 0, 0.5, 1
  for (const y of [0, 0.5, 1]) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", padL); line.setAttribute("x2", W - padR);
    line.setAttribute("y1", yScale(y)); line.setAttribute("y2", yScale(y));
    line.setAttribute("class", "axis-line");
    svg.appendChild(line);
    const lab = document.createElementNS("http://www.w3.org/2000/svg", "text");
    lab.setAttribute("x", 4); lab.setAttribute("y", yScale(y) + 3);
    lab.setAttribute("class", "axis-label"); lab.textContent = y.toFixed(1);
    svg.appendChild(lab);
  }

  // X axis labels (first, last)
  if (runs.length > 0) {
    const first = document.createElementNS("http://www.w3.org/2000/svg", "text");
    first.setAttribute("x", padL); first.setAttribute("y", H - 4);
    first.setAttribute("class", "axis-label"); first.textContent = fmtShortDate(runs[0].timestamp);
    svg.appendChild(first);
    if (runs.length > 1) {
      const last = document.createElementNS("http://www.w3.org/2000/svg", "text");
      last.setAttribute("x", W - padR); last.setAttribute("y", H - 4);
      last.setAttribute("class", "axis-label"); last.setAttribute("text-anchor", "end");
      last.textContent = fmtShortDate(runs[runs.length - 1].timestamp);
      svg.appendChild(last);
    }
  }

  // Median band
  const medianPts = runs.map((r, i) => {
    const scores = modelIds.map(mid => r.task_model_means?.[category]?.[mid]).filter(v => v != null);
    if (!scores.length) return null;
    scores.sort((a, b) => a - b);
    const median = scores[Math.floor(scores.length / 2)];
    return `${xs[i]},${yScale(median)}`;
  }).filter(Boolean);
  if (medianPts.length > 1) {
    const medianLine = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    medianLine.setAttribute("points", medianPts.join(" "));
    medianLine.setAttribute("class", "median-line");
    svg.appendChild(medianLine);
  }

  // Model lines
  for (const mid of modelIds) {
    const pts = runs.map((r, i) => {
      const v = r.task_model_means?.[category]?.[mid];
      return v == null ? null : `${xs[i]},${yScale(v)}`;
    }).filter(Boolean);
    if (pts.length === 0) continue;
    if (pts.length === 1) {
      const [x, y] = pts[0].split(",");
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", x); circle.setAttribute("cy", y); circle.setAttribute("r", 2.5);
      circle.setAttribute("fill", MODEL_COLORS[mid] || "#888");
      svg.appendChild(circle);
    } else {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      line.setAttribute("points", pts.join(" "));
      line.setAttribute("stroke", MODEL_COLORS[mid] || "#888");
      line.setAttribute("class", "trend-line");
      svg.appendChild(line);
    }
  }
  return svg;
}

function renderDrill(task, model, cell) {
  $("#drill").classList.remove("hidden");
  $("#drill-title").textContent = `${task.category} × ${model.label}`;
  const body = $("#drill-body");
  body.innerHTML = "";
  for (const p of cell.prompts) {
    const card = document.createElement("div");
    card.className = "prompt-card";
    const pill = `<span class="score-pill" style="background:${scoreColor(p.score)}">${p.score?.toFixed(2) ?? "—"}</span>`;
    card.innerHTML = `
      <div class="header">
        <span>${p.prompt_id} <em>(${p.length})</em></span>
        ${pill}
      </div>
      <pre>${(p.response || "").replace(/[<>&]/g, c => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c]))}</pre>
      ${p.judge_reasoning ? `<div class="judge">judge: ${p.judge_reasoning}</div>` : ""}
    `;
    body.appendChild(card);
  }
  $("#drill").scrollIntoView({ behavior: "smooth", block: "start" });
}

function deriveCurrentTimestamp() {
  if (!CURRENT) return null;
  const finished = CURRENT.finished_at || "";
  const core = finished.split(".")[0].split("+")[0];   // "2026-05-01T10:00:00"
  return core.replace(/-/g, "").replace(/:/g, "") + "Z"; // "20260501T100000Z"
}

function renderEverything() {
  renderMeta(CURRENT);
  renderGrid(CURRENT);
  const ts = deriveCurrentTimestamp();
  renderRunPicker(INDEX, ts);
  renderDrift(INDEX, ts);
  renderTrends(INDEX);
}

$("#drill-close").addEventListener("click", () => $("#drill").classList.add("hidden"));

async function boot() {
  try {
    const latestResp = await fetch("results/latest.json");
    CURRENT = await latestResp.json();
  } catch (e) {
    $("#run-meta").innerHTML =
      `<div class="placeholder-banner">No results yet — results/latest.json not found.</div>`;
    return;
  }
  try {
    const idxResp = await fetch("results/index.json");
    if (idxResp.ok) INDEX = await idxResp.json();
  } catch (e) {
    INDEX = null;
  }
  renderEverything();
}

boot();

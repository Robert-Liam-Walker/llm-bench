const RESULTS_URL = "results/latest.json";

const $ = (sel) => document.querySelector(sel);

function scoreColor(score) {
  if (score == null) return "#2a2f3a";
  const hue = score * 130;
  const sat = 65 - Math.abs(score - 0.5) * 20;
  const light = 50;
  return `hsl(${hue}, ${sat}%, ${light}%)`;
}

function costUsd(inputTok, outputTok, model) {
  const inCost = (inputTok / 1_000_000) * model.input_per_mtok;
  const outCost = (outputTok / 1_000_000) * model.output_per_mtok;
  return inCost + outCost;
}

function fmtUsd(n) {
  if (n < 0.001) return `<$0.001`;
  if (n < 0.01) return `$${n.toFixed(4)}`;
  return `$${n.toFixed(3)}`;
}

function renderMeta(data) {
  const placeholder = data.placeholder
    ? `<div class="placeholder-banner">⚠ This page shows seed/placeholder data. No real API calls have been made yet — run <code>python -m bench</code> to populate.</div>`
    : "";
  const ts = data.finished_at ? new Date(data.finished_at).toLocaleString() : "—";
  $("#run-meta").innerHTML =
    `${placeholder}Last run: <strong>${ts}</strong> · ` +
    `${data.tasks.length} tasks × ${data.models.length} models · ` +
    `${data.tasks.reduce((s, t) => s + t.n_prompts, 0)} prompts/model`;
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
    th.textContent = model.label;
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

$("#drill-close").addEventListener("click", () => $("#drill").classList.add("hidden"));

fetch(RESULTS_URL)
  .then(r => r.ok ? r.json() : Promise.reject(r.status))
  .then(data => {
    renderMeta(data);
    renderGrid(data);
  })
  .catch(err => {
    $("#run-meta").innerHTML =
      `<div class="placeholder-banner">No results yet — ${RESULTS_URL} not found. Run the bench locally and reload.</div>`;
  });

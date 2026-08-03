from __future__ import annotations


def workflow_console_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mitra Workflow Console</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      --page:#f4f6f3; --surface:#ffffff; --ink:#17201d; --muted:#64716c;
      --line:#d7dfd9; --green:#18715b; --green-soft:#e0f2eb;
      --blue:#265fc4; --blue-soft:#e7efff; --amber:#9a6200;
      --amber-soft:#fff2ce; --red:#b42318; --red-soft:#fde8e7;
      --dark:#23312d;
    }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:var(--page); }
    button, textarea { font:inherit; }
    button { cursor:pointer; }
    header {
      border-bottom:1px solid var(--line); background:var(--surface);
    }
    .bar {
      max-width:1380px; margin:auto; padding:15px 24px;
      display:flex; align-items:center; justify-content:space-between; gap:18px;
    }
    .brand { display:flex; align-items:center; gap:12px; min-width:0; }
    .mark {
      width:34px; height:34px; display:grid; place-items:center;
      background:var(--dark); color:white; font-weight:850; border-radius:6px;
    }
    .brand strong { display:block; font-size:15px; }
    .brand small { display:block; color:var(--muted); margin-top:2px; }
    .temp {
      color:var(--amber); background:var(--amber-soft); border:1px solid #ecd187;
      padding:6px 9px; border-radius:5px; font-size:11px; font-weight:800;
      text-transform:uppercase;
    }
    main { max-width:1380px; margin:auto; padding:28px 24px 60px; }
    .intro {
      display:flex; justify-content:space-between; align-items:flex-end; gap:24px;
      margin-bottom:18px;
    }
    h1 { margin:0; font-size:30px; line-height:1.15; }
    .intro p { color:var(--muted); line-height:1.55; margin:8px 0 0; max-width:760px; }
    .links { white-space:nowrap; font-size:13px; }
    a { color:var(--blue); font-weight:750; text-decoration:none; }
    a:hover { text-decoration:underline; }
    .workspace {
      display:grid; grid-template-columns:minmax(300px, .72fr) minmax(0, 1.55fr);
      border:1px solid var(--line); background:var(--surface); min-height:640px;
    }
    .composer { padding:22px; border-right:1px solid var(--line); }
    .eyebrow {
      color:var(--green); font-size:11px; font-weight:850; text-transform:uppercase;
      margin-bottom:9px;
    }
    label { display:block; font-size:13px; font-weight:800; margin-bottom:8px; }
    textarea {
      width:100%; min-height:140px; resize:vertical; border:1px solid #aebbb5;
      border-radius:6px; padding:13px; color:var(--ink); background:white;
      line-height:1.5; outline:none;
    }
    textarea:focus { border-color:var(--blue); box-shadow:0 0 0 3px var(--blue-soft); }
    .presets { display:flex; flex-wrap:wrap; gap:7px; margin:10px 0 18px; }
    .preset {
      border:1px solid var(--line); background:#f8faf8; color:#394640;
      border-radius:5px; padding:7px 9px; font-size:12px;
    }
    .preset:hover { border-color:#9ba9a3; background:white; }
    .mode {
      display:flex; align-items:center; justify-content:space-between; gap:12px;
      border-top:1px solid var(--line); border-bottom:1px solid var(--line);
      padding:13px 0; margin-bottom:18px;
    }
    .mode span { font-size:13px; font-weight:800; }
    .mode small { color:var(--muted); }
    .run {
      width:100%; border:0; border-radius:6px; padding:12px 16px;
      background:var(--green); color:white; font-weight:850;
    }
    .run:hover { background:#115c49; }
    .run:disabled { cursor:not-allowed; background:#91a59d; }
    .request-meta {
      margin-top:15px; color:var(--muted); font-size:12px; line-height:1.7;
      word-break:break-word;
    }
    .request-meta code { color:#254e9c; }
    .visual { min-width:0; }
    .visual-head {
      min-height:72px; padding:18px 20px; border-bottom:1px solid var(--line);
      display:flex; align-items:center; justify-content:space-between; gap:16px;
    }
    .visual-head h2 { margin:0 0 3px; font-size:17px; }
    .visual-head small { color:var(--muted); }
    .run-state {
      font-size:12px; font-weight:850; padding:6px 9px; border-radius:5px;
      color:#435049; background:#edf1ee;
    }
    .run-state.running { color:var(--blue); background:var(--blue-soft); }
    .run-state.completed { color:var(--green); background:var(--green-soft); }
    .run-state.failed { color:var(--red); background:var(--red-soft); }
    .stage-rail { display:grid; gap:0; border-bottom:1px solid var(--line); }
    .stage-group { min-width:0; border-bottom:1px solid var(--line); }
    .stage-group:last-child { border-bottom:0; }
    .stage-group-head {
      min-height:54px; padding:10px 14px; display:flex; align-items:center;
      justify-content:space-between; gap:14px; border-bottom:1px solid var(--line);
      background:#f6f8f7;
    }
    .stage-group-title { display:block; font-size:12px; font-weight:900; }
    .stage-group-purpose { color:var(--muted); font-size:11px; }
    .stage-group-flow {
      flex:0 0 auto; color:#456157; font-size:10px; font-weight:850;
      text-transform:uppercase;
    }
    .stage-group.tantra .stage-group-head {
      background:#eef4ff; box-shadow:inset 4px 0 0 var(--blue);
    }
    .stage-group-grid {
      display:grid; grid-template-columns:repeat(5, minmax(120px, 1fr));
    }
    .stage {
      min-height:112px; padding:14px; border:0; border-right:1px solid var(--line);
      background:white; text-align:left; position:relative;
    }
    .stage:last-child { border-right:0; }
    .stage:hover, .stage.selected { background:#f7faf8; }
    .stage.selected { box-shadow:inset 0 -3px 0 var(--blue); }
    .stage-index { color:#89958f; font-size:10px; font-weight:850; }
    .stage-name { display:block; margin:7px 0 5px; font-size:13px; font-weight:850; }
    .stage-owner { color:var(--muted); font-size:11px; }
    .dot {
      position:absolute; top:13px; right:13px; width:9px; height:9px;
      border-radius:50%; background:#c7cfca;
    }
    .stage.running .dot { background:var(--blue); box-shadow:0 0 0 4px var(--blue-soft); }
    .stage.completed .dot { background:var(--green); }
    .stage.failed .dot { background:var(--red); box-shadow:0 0 0 4px var(--red-soft); }
    .stage.skipped .dot { background:var(--amber); }
    .inspector { padding:18px 20px 22px; }
    .inspector-head {
      display:flex; justify-content:space-between; align-items:center; gap:16px;
      margin-bottom:10px;
    }
    .inspector h3 { margin:0; font-size:15px; }
    .stage-status { color:var(--muted); font-size:12px; font-weight:800; }
    pre {
      margin:0; min-height:250px; max-height:430px; overflow:auto;
      border:1px solid #ced7d1; background:#101916; color:#dce9e3;
      padding:15px; border-radius:6px; font:12px/1.55 Consolas, monospace;
      white-space:pre-wrap; overflow-wrap:anywhere;
    }
    .empty { color:#91a19a; }
    .actions { margin-top:11px; display:flex; gap:14px; font-size:12px; }
    @media (max-width:1000px) {
      .workspace { grid-template-columns:1fr; }
      .composer { border-right:0; border-bottom:1px solid var(--line); }
      .stage-group-grid { grid-template-columns:repeat(2, minmax(130px, 1fr)); }
      .stage { border-bottom:1px solid var(--line); }
      .stage:nth-child(2n) { border-right:0; }
      .stage-group-grid .stage:nth-last-child(-n+2) { border-bottom:0; }
    }
    @media (max-width:620px) {
      .bar, main { padding-left:14px; padding-right:14px; }
      .intro { align-items:flex-start; flex-direction:column; }
      .links { white-space:normal; }
      .stage-group-head { align-items:flex-start; flex-direction:column; }
      .stage-group-grid { grid-template-columns:1fr; }
      .stage, .stage:nth-child(2n) {
        border-right:0; border-bottom:1px solid var(--line);
      }
      .stage-group-grid .stage:nth-last-child(-n+2) { border-bottom:1px solid var(--line); }
      .stage-group-grid .stage:last-child { border-bottom:0; }
      .visual-head { align-items:flex-start; flex-direction:column; }
    }
  </style>
</head>
<body>
<header><div class="bar">
  <div class="brand"><div class="mark">M</div><div>
    <strong>Mitra Runtime</strong><small>Natural request workflow console</small>
  </div></div>
  <div class="temp">Temporary operator surface</div>
</div></header>
<main>
  <div class="intro">
    <div><h1>Watch a request move through the ecosystem</h1>
      <p>Submit a natural request. Mitra selects the capability, Raj orchestrates
      the workflow, and TANTRA executes the downstream runtime chain.</p>
    </div>
    <div class="links"><a href="/">Dashboard</a> &nbsp;|&nbsp;
      <a href="/docs">OpenAPI</a></div>
  </div>
  <div class="workspace">
    <section class="composer">
      <div class="eyebrow">Request</div>
      <label for="request">What should Mitra do?</label>
      <textarea id="request" placeholder="Example: Show AAPL stock">Show AAPL stock</textarea>
      <div class="presets" aria-label="Example requests">
        <button class="preset" data-request="Show AAPL stock">AAPL stock</button>
        <button class="preset" data-request="Distance of Earth from Sun">Earth-Sun distance</button>
        <button class="preset" data-request="Show low-stock inventory">Low-stock inventory</button>
      </div>
      <div class="mode"><div><span>Automatic capability selection</span>
        <small>Mitra resolves the attached product from its manifest.</small></div>
      </div>
      <button class="run" id="run">Run workflow</button>
      <div class="request-meta" id="request-meta">
        No execution started. Responses shown here come from the live runtime.
      </div>
    </section>
    <section class="visual">
      <div class="visual-head"><div><h2>Execution path</h2>
        <small id="trace">Waiting for a request</small></div>
        <div class="run-state" id="run-state">IDLE</div>
      </div>
      <div class="stage-rail" id="stage-rail"></div>
      <div class="inspector">
        <div class="inspector-head"><h3 id="inspector-title">Stage response</h3>
          <span class="stage-status" id="stage-status">NOT STARTED</span></div>
        <pre id="response"><span class="empty">Select a stage after starting the workflow.</span></pre>
        <div class="actions" id="actions"></div>
      </div>
    </section>
  </div>
</main>
<script>
const stageDefinitions = [
  ["user-request", "Natural request", "User"],
  ["capability-selection", "Capability selection", "Mitra"],
  ["dependency-preflight", "Dependency preflight", "Mitra"],
  ["raj-execution", "Control-plane execution", "Raj"],
  ["tantra-runtime", "Runtime handoff", "TANTRA"],
  ["universal-capability-runtime", "Capability runtime", "Universal Runtime"],
  ["capability-execution", "Product capability", "Capability"],
  ["bucket-truth", "Artifact storage", "Bucket"],
  ["replay-validation", "Deterministic replay", "Replay"],
  ["insightflow-telemetry", "Telemetry record", "InsightFlow"],
  ["mitra-response", "Companion response", "MITRA"]
];
const workflowDomains = [
  {
    id: "user",
    title: "User",
    purpose: "Submits the natural-language request",
    handoff: "Hands request to MITRA Companion",
    stages: ["user-request"]
  },
  {
    id: "mitra",
    title: "MITRA Companion",
    purpose: "Natural request intake and manifest-driven capability selection",
    handoff: "Hands selected capability to Raj",
    stages: ["capability-selection", "dependency-preflight"]
  },
  {
    id: "raj",
    title: "Raj Control Plane",
    purpose: "Hands the selected execution contract to TANTRA",
    handoff: "Hands execution result to TANTRA",
    stages: ["raj-execution"]
  },
  {
    id: "tantra",
    title: "TANTRA Runtime",
    purpose: "Runs the canonical capability execution path",
    handoff: "Universal Runtime -> Capability -> Bucket -> Replay -> InsightFlow",
    stages: [
      "tantra-runtime", "universal-capability-runtime", "capability-execution",
      "bucket-truth", "replay-validation", "insightflow-telemetry"
    ]
  },
  {
    id: "response",
    title: "MITRA Response",
    purpose: "Returns the verified capability result to the user",
    handoff: "Closes the response-critical execution path",
    stages: ["mitra-response"]
  }
];
let currentExecution = null;
let selectedStage = stageDefinitions[0][0];
let pollTimer = null;
let activeKey = null;
let recoveryInFlight = false;
let lastRecoveryAt = 0;
const RECOVERY_STALE_AFTER_MS = 330000;

const requestInput = document.getElementById("request");
const runButton = document.getElementById("run");
const rail = document.getElementById("stage-rail");
const responseBox = document.getElementById("response");
const stateBox = document.getElementById("run-state");

function safeStatus(value) {
  const status = String(value || "waiting").toLowerCase();
  return ["running", "completed", "failed", "skipped"].includes(status)
    ? status : "waiting";
}

function displayStage(id) {
  const persisted = currentExecution?.stages?.find(item => item.stage_name === id);
  if (persisted) return persisted;
  const execution = currentExecution?.execution;
  if (id === "user-request" && execution) {
    return {
      stage_name: id,
      status: "COMPLETED",
      response: { accepted: true, request: execution.request },
      finished_at: execution.created_at
    };
  }
  if (id === "mitra-response" && execution) {
    const complete = String(execution.status).toUpperCase() === "COMPLETED";
    const failed = String(execution.status).toUpperCase() === "FAILED";
    return {
      stage_name: id,
      status: complete ? "COMPLETED" : (failed ? "FAILED" : "WAITING"),
      response: complete ? {
        execution_id: execution.execution_id,
        trace_id: execution.trace_id,
        status: execution.status
      } : null,
      last_error: failed ? execution.error : null,
      finished_at: complete ? execution.updated_at : null
    };
  }
  return null;
}

function renderStages() {
  const stages = currentExecution?.stages || [];
  rail.innerHTML = stageDefinitions.map(([id, label, owner], index) => {
    const stage = displayStage(id);
    const status = safeStatus(stage?.status);
    return `<button class="stage ${status} ${selectedStage === id ? "selected" : ""}"
      data-stage="${id}">
      <span class="dot" aria-hidden="true"></span>
      <span class="stage-index">${String(index + 1).padStart(2, "0")}</span>
      <span class="stage-name">${label}</span>
      <span class="stage-owner">${owner} · ${status.toUpperCase()}</span>
    </button>`;
  }).join("");
  const stageMarkup = new Map(
    [...rail.querySelectorAll(".stage")].map(button => [
      button.dataset.stage,
      button.outerHTML
    ])
  );
  rail.innerHTML = workflowDomains.map(domain => {
    const domainStages = domain.stages
      .map(stageId => stageMarkup.get(stageId) || "")
      .join("");
    return `<section class="stage-group ${domain.id}" aria-label="${domain.title}">
      <div class="stage-group-head">
        <div><span class="stage-group-title">${domain.title}</span>
          <span class="stage-group-purpose">${domain.purpose}</span></div>
        <span class="stage-group-flow">${domain.handoff}</span>
      </div>
      <div class="stage-group-grid">${domainStages}</div>
    </section>`;
  }).join("");
  rail.querySelectorAll(".stage").forEach(button => {
    button.addEventListener("click", () => {
      selectedStage = button.dataset.stage;
      renderStages();
      renderInspector();
    });
  });
}

function renderInspector() {
  const definition = stageDefinitions.find(item => item[0] === selectedStage);
  const stage = displayStage(selectedStage);
  document.getElementById("inspector-title").textContent =
    definition ? `${definition[1]} response` : "Stage response";
  document.getElementById("stage-status").textContent =
    stage ? String(stage.status).toUpperCase() : "NOT STARTED";
  if (!stage) {
    responseBox.innerHTML = '<span class="empty">This stage has not produced an artifact yet.</span>';
    return;
  }
  const output = {
    stage_name: stage.stage_name,
    status: stage.status,
    attempts: stage.attempts,
    request: stage.request,
    response: stage.response,
    last_error: stage.last_error,
    request_hash: stage.request_hash,
    response_hash: stage.response_hash,
    chain_hash: stage.chain_hash,
    finished_at: stage.finished_at
  };
  responseBox.textContent = JSON.stringify(output, null, 2);
}

function normalizeDetail(data) {
  const root = data.ecosystem || data;
  return {
    execution: root.execution || root,
    stages: root.stages || root.execution?.stages || []
  };
}

function updateExecution(detail) {
  currentExecution = normalizeDetail(detail);
  const execution = currentExecution.execution;
  const status = safeStatus(execution.status);
  stateBox.textContent = String(execution.status || "running").toUpperCase();
  stateBox.className = `run-state ${status}`;
  document.getElementById("trace").textContent =
    `Trace ${execution.trace_id || "pending"}`;
  document.getElementById("request-meta").innerHTML =
    `Execution <code>${execution.execution_id || "pending"}</code><br>` +
    `Current stage: ${execution.current_stage || "initializing"}`;
  const id = execution.execution_id;
  document.getElementById("actions").innerHTML = id
    ? `<a href="/operator/ecosystem/${id}">Operator detail</a>
       <a href="/api/v1/ecosystem/executions/${id}/replay">Replay package</a>`
    : "";
  const active = currentExecution.stages.find(item =>
    ["RUNNING", "FAILED"].includes(String(item.status).toUpperCase())
  );
  if (active) selectedStage = active.stage_name;
  renderStages();
  renderInspector();
  if (["COMPLETED", "FAILED"].includes(String(execution.status).toUpperCase())) {
    runButton.disabled = false;
    clearInterval(pollTimer);
  }
}

async function locateExecution() {
  const result = await fetch("/api/v1/ecosystem/executions?limit=50");
  if (!result.ok) throw new Error(`Execution index returned HTTP ${result.status}`);
  const data = await result.json();
  const rows = data.executions || data.ecosystem?.executions || [];
  return rows.find(item => item.idempotency_key === activeKey);
}

async function pollExecution() {
  try {
    const summary = currentExecution?.execution?.execution_id
      ? currentExecution.execution
      : await locateExecution();
    if (!summary?.execution_id) return;
    const result = await fetch(`/api/v1/ecosystem/executions/${summary.execution_id}`);
    if (!result.ok) throw new Error(`Execution detail returned HTTP ${result.status}`);
    const detail = await result.json();
    updateExecution(detail);
    const normalized = normalizeDetail(detail);
    const execution = normalized.execution;
    const currentStage = normalized.stages.find(
      item => item.stage_name === execution.current_stage
    );
    const progressTimes = [
      execution.updated_at,
      currentStage?.started_at,
      currentStage?.finished_at
    ].map(value => Date.parse(value || "")).filter(Number.isFinite);
    const lastProgressAt = progressTimes.length
      ? Math.max(...progressTimes)
      : Date.now();
    const staleForMs = Date.now() - lastProgressAt;
    const recoveryReady =
      String(execution.status).toUpperCase() === "RUNNING" &&
      staleForMs > RECOVERY_STALE_AFTER_MS &&
      Date.now() - lastRecoveryAt > RECOVERY_STALE_AFTER_MS &&
      !recoveryInFlight;
    if (recoveryReady) {
      recoveryInFlight = true;
      lastRecoveryAt = Date.now();
      document.getElementById("request-meta").innerHTML =
        `Execution <code>${execution.execution_id}</code><br>` +
        `Resuming from checkpoint after hosting timeout`;
      fetch(
        `/api/v1/ecosystem/executions/${execution.execution_id}/recover`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            schema_version: "1.0.0",
            contract_version: "1.0.0"
          })
        }
      ).then(async recovery => {
        if (!recovery.ok) {
          throw new Error(`Recovery returned HTTP ${recovery.status}`);
        }
        updateExecution(await recovery.json());
      }).catch(error => {
        document.getElementById("request-meta").textContent =
          `Recovery connection ended: ${error.message}. Retrying from the persisted checkpoint.`;
      }).finally(() => {
        recoveryInFlight = false;
      });
    }
  } catch (error) {
    document.getElementById("request-meta").textContent =
      `Polling error: ${error.message}. Retrying automatically.`;
  }
}

async function runWorkflow() {
  const message = requestInput.value.trim();
  if (!message) {
    requestInput.focus();
    return;
  }
  activeKey = `temp-console-${Date.now()}-${crypto.randomUUID()}`;
  currentExecution = null;
  recoveryInFlight = false;
  lastRecoveryAt = 0;
  selectedStage = stageDefinitions[0][0];
  runButton.disabled = true;
  stateBox.textContent = "SUBMITTING";
  stateBox.className = "run-state running";
  document.getElementById("trace").textContent = "Creating persisted execution";
  document.getElementById("request-meta").innerHTML =
    `Idempotency key<br><code>${activeKey}</code>`;
  document.getElementById("actions").innerHTML = "";
  renderStages();
  renderInspector();

  const body = {
    schema_version: "1.0.0",
    contract_version: "1.0.0",
    actor_id: "temporary-workflow-console",
    workspace_id: "temporary-workflow-console",
    message,
    idempotency_key: activeKey,
    payload: {
      query: message,
      raj_workflow: {
        action_type: "task",
        title: "Natural request from Mitra workflow console",
        description: message
      }
    },
    metadata: { source: "temporary-workflow-console" }
  };

  fetch("/api/v1/ecosystem/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  }).then(async result => {
    const data = await result.json();
    if (!result.ok) throw new Error(data.error?.message || `HTTP ${result.status}`);
    updateExecution(data);
  }).catch(error => {
    if (!currentExecution) {
      document.getElementById("request-meta").textContent =
        `Submission connection ended: ${error.message}. Checking persisted state.`;
    }
  });

  pollTimer = setInterval(pollExecution, 3000);
  await pollExecution();
}

document.querySelectorAll(".preset").forEach(button => {
  button.addEventListener("click", () => {
    requestInput.value = button.dataset.request;
    requestInput.focus();
  });
});
runButton.addEventListener("click", runWorkflow);
requestInput.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") runWorkflow();
});
renderStages();
</script>
</body>
</html>"""

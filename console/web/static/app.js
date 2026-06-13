const $ = (sel) => document.querySelector(sel);

const log = $("#chat-log");
const form = $("#chat-form");
const input = $("#chat-input");
const sendBtn = $("#send-btn");
const statusEl = $("#status");

let inFlight = false;

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

if (window.marked) {
  marked.setOptions({ breaks: true, gfm: true });
}

function addMsg(role, text) {
  const wrap = el("div", `msg ${role}`);
  const bubble = el("div", "bubble");
  if (text !== undefined) {
    if (role === "assistant" && window.marked) {
      bubble.dataset.raw = text;
      bubble.innerHTML = marked.parse(text);
    } else {
      bubble.textContent = text;
    }
  }
  wrap.appendChild(bubble);
  log.appendChild(wrap);
  log.scrollTop = log.scrollHeight;
  return bubble;
}

function appendTo(bubble, text) {
  if (bubble.classList.contains("bubble") && bubble.parentElement?.classList.contains("assistant") && window.marked) {
    bubble.dataset.raw = (bubble.dataset.raw || "") + text;
    bubble.innerHTML = marked.parse(bubble.dataset.raw);
  } else {
    bubble.textContent += text;
  }
  log.scrollTop = log.scrollHeight;
}

function addBreadcrumb(text) {
  const wrap = el("div", "msg breadcrumb");
  const inner = el("div", "crumb", text);
  wrap.appendChild(inner);
  log.appendChild(wrap);
  log.scrollTop = log.scrollHeight;
}

function summarizeToolCall(toolUse) {
  const name = toolUse.name || "tool";
  const input = toolUse.input || {};
  if (name === "Bash") {
    const cmd = (input.command || "").split("\n")[0].slice(0, 80);
    return `▸ Bash · ${cmd}`;
  }
  if (name === "Read") {
    const p = input.file_path || input.path || "";
    return `▸ Read · ${p.replace(/^.*[\\/]/, "")}`;
  }
  if (name === "Write" || name === "Edit") {
    const p = input.file_path || input.path || "";
    return `▸ ${name} · ${p.replace(/^.*[\\/]/, "")}`;
  }
  if (name === "Glob" || name === "Grep") {
    return `▸ ${name} · ${input.pattern || ""}`;
  }
  return `▸ ${name}`;
}

function renderQuestionCard(toolUse) {
  const card = el("div", "msg assistant");
  const inner = el("div", "question-card");
  const questions = toolUse.input?.questions || [];
  for (const q of questions) {
    const block = el("div", "q-block");
    block.appendChild(el("div", "q-text", q.question || ""));
    const optsWrap = el("div", "q-options");
    for (const opt of (q.options || [])) {
      const btn = el("button", "q-option");
      btn.appendChild(el("div", "q-label", opt.label || ""));
      if (opt.description) btn.appendChild(el("div", "q-desc", opt.description));
      btn.addEventListener("click", () => {
        if (inFlight) return;
        optsWrap.querySelectorAll(".q-option").forEach(b => b.disabled = true);
        btn.classList.add("selected");
        sendPrompt(opt.label);
      });
      optsWrap.appendChild(btn);
    }
    block.appendChild(optsWrap);
    if (q.multiSelect) {
      const note = el("div", "q-note", "（可多選 — 目前每次只送出單一選項，需多選時可用文字輸入）");
      block.appendChild(note);
    }
    inner.appendChild(block);
  }
  card.appendChild(inner);
  log.appendChild(card);
  log.scrollTop = log.scrollHeight;
}

function handleAssistantEvent(event, ctx) {
  const content = event.message?.content;
  if (!Array.isArray(content)) return;
  for (const block of content) {
    if (block.type === "text" && block.text) {
      if (!ctx.assistantBubble) ctx.assistantBubble = addMsg("assistant", "");
      if (ctx.firstText) { ctx.assistantBubble.textContent = ""; ctx.firstText = false; }
      appendTo(ctx.assistantBubble, block.text);
    } else if (block.type === "tool_use") {
      if (block.name === "AskUserQuestion") {
        renderQuestionCard(block);
      } else {
        addBreadcrumb(summarizeToolCall(block));
      }
      // Force next assistant text to start a new bubble
      ctx.assistantBubble = null;
      ctx.firstText = true;
    }
  }
}

function handleUserEvent(event) {
  // user-role events carry tool_result blocks. We don't render their content
  // (too noisy — multi-KB SRD/SKILL excerpts); a quiet "✓ done" is enough.
  const content = event.message?.content;
  if (!Array.isArray(content)) return;
  for (const block of content) {
    if (block.type === "tool_result") {
      if (block.is_error) {
        const err = typeof block.content === "string"
          ? block.content
          : Array.isArray(block.content) ? block.content.map(c => c.text || "").join("") : "";
        // Suppress AskUserQuestion's "Answer questions?" placeholder — that's
        // not an error, it's the CLI's non-interactive fallback. We've already
        // rendered the picker card from the matching tool_use event.
        const trimmed = err.trim();
        if (trimmed === "Answer questions?" || trimmed.startsWith("Answer question")) continue;
        addMsg("error", `Tool 錯誤：${err.slice(0, 400)}`);
      }
    }
  }
}

async function refreshSidebar() {
  try {
    await fetch("/api/health").then(r => r.json());
    statusEl.textContent = "已連線";
    statusEl.className = "badge ok";
    const data = await fetch("/api/campaigns").then(r => r.json());
    const list = $("#campaign-list");
    list.innerHTML = "";
    if (data.campaigns.length === 0) {
      list.innerHTML = '<li class="muted">尚無戰役。<br>對 DM 說「<code>/dnd</code>」開始。</li>';
      return;
    }
    for (const c of data.campaigns) {
      const li = el("li", null, c.name);
      li.title = c.path;
      list.appendChild(li);
    }
  } catch (e) {
    statusEl.textContent = "後端離線";
    statusEl.className = "badge err";
  }
}

async function sendPrompt(prompt) {
  if (inFlight) return;
  inFlight = true;
  sendBtn.disabled = true;

  addMsg("user", prompt);

  const ctx = { assistantBubble: null, firstText: true };

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!res.ok) {
      addMsg("error", `後端錯誤 ${res.status}`);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let frameEnd;
      while ((frameEnd = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, frameEnd);
        buffer = buffer.slice(frameEnd + 2);

        for (const line of frame.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (!payload) continue;
          let event;
          try { event = JSON.parse(payload); } catch { continue; }

          if (event.type === "error") {
            addMsg("error", event.text || "未知錯誤");
          } else if (event.type === "assistant") {
            handleAssistantEvent(event, ctx);
          } else if (event.type === "user") {
            handleUserEvent(event);
          }
          // system / result / done events: ignored in UI
        }
      }
    }
  } catch (e) {
    addMsg("error", `送出失敗：${e.message}`);
  } finally {
    inFlight = false;
    sendBtn.disabled = false;
    input.focus();
    refreshSidebar();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const prompt = input.value.trim();
  if (!prompt) return;
  input.value = "";
  sendPrompt(prompt);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

$("#reset-session").addEventListener("click", async () => {
  if (!confirm("確定要重置對話階段？目前的上下文會清空（戰役資料不受影響）。")) return;
  await fetch("/api/session/reset", { method: "POST" });
  addMsg("system", "Session 已重置 — 下一句訊息會開新的對話階段。");
});

refreshSidebar();
setInterval(refreshSidebar, 10000);

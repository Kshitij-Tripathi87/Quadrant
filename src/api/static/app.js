// Interactive Web Client for Technical Documentation Assistant

let sessionId = localStorage.getItem("rag_session_id") || "sess_" + Math.random().toString(36).substring(2, 10);
localStorage.setItem("rag_session_id", sessionId);

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  loadDocuments();

  const inputEl = document.getElementById("user-input");
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });
});

// Tab Switching
function switchTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach((btn) => btn.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach((pane) => pane.classList.remove("active"));

  document.getElementById(`tab-${tabName}-btn`).classList.add("active");
  document.getElementById(`tab-${tabName}`).classList.add("active");

  if (tabName === "corpus") {
    loadDocuments();
  }
}

// Health Check
async function checkHealth() {
  try {
    const res = await fetch("/api/v1/health");
    if (res.ok) {
      const data = await res.json();
      document.getElementById("health-dot").style.background = "#10b981";
      document.getElementById("health-text").innerText = `${data.llm_provider.toUpperCase()}`;
      document.getElementById("vectors-badge").innerText = `${data.vector_store_count} Chunks`;
    }
  } catch (err) {
    document.getElementById("health-dot").style.background = "#f43f5e";
    document.getElementById("health-text").innerText = "Offline";
  }
}

// Load Documents
async function loadDocuments() {
  const grid = document.getElementById("documents-grid");
  try {
    const res = await fetch("/api/v1/documents");
    if (!res.ok) throw new Error("Failed to fetch documents");
    const data = await res.json();

    if (data.documents.length === 0) {
      grid.innerHTML = `<p style="color: var(--text-dim); grid-column: 1/-1;">No documents indexed yet. Try clicking Ingest Documents.</p>`;
      return;
    }

    grid.innerHTML = data.documents.map((doc) => `
      <div class="doc-card">
        <div class="doc-card-title">📖 ${escapeHtml(doc.title)}</div>
        <div style="font-size: 0.78rem; color: var(--text-dim); margin-bottom: 0.6rem; word-break: break-all;">
          ${escapeHtml(doc.source)}
        </div>
        <div class="doc-card-meta">
          <span>📦 <strong>${doc.chunk_count}</strong> chunks</span>
          <span style="text-transform: capitalize;">${doc.source_type || 'file'}</span>
        </div>
      </div>
    `).join("");

    document.getElementById("vectors-badge").innerText = `${data.total_vectors} Chunks`;
  } catch (err) {
    grid.innerHTML = `<p style="color: var(--accent-rose); grid-column: 1/-1;">Error loading documents: ${err.message}</p>`;
  }
}

// Suggestion chip clicked
function sendSuggestion(text) {
  document.getElementById("user-input").value = text;
  handleSend();
}

// Send Query to Assistant
async function handleSend() {
  const input = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-button");
  const query = input.value.trim();
  if (!query) return;

  // Clear empty state
  const emptyState = document.getElementById("empty-state");
  if (emptyState) emptyState.remove();

  // Append User message
  appendUserMessage(query);
  input.value = "";
  sendBtn.disabled = true;

  // Append loading indicator
  const loadingId = appendLoadingMessage();

  try {
    const res = await fetch("/api/v1/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query, session_id: sessionId })
    });

    removeMessage(loadingId);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Query execution failed");
    }

    const data = await res.json();
    appendAssistantMessage(data);
  } catch (err) {
    removeMessage(loadingId);
    appendErrorMessage(err.message);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

function appendUserMessage(text) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "message-row user-row";
  div.innerHTML = `
    <div class="message-content">
      <div class="bubble user-bubble">${escapeHtml(text)}</div>
    </div>
    <div class="message-avatar user-avatar">👤</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendLoadingMessage() {
  const container = document.getElementById("chat-messages");
  const id = "loading-" + Date.now();
  const div = document.createElement("div");
  div.id = id;
  div.className = "message-row";
  div.innerHTML = `
    <div class="message-avatar bot-avatar">⚡</div>
    <div class="message-content">
      <div class="bubble bot-bubble" style="display: flex; align-items: center; gap: 0.75rem;">
        <span class="spin">⏳</span>
        <span>Running LangGraph Self-Corrective Workflow (Query Analysis ➔ Retrieval ➔ Grading)...</span>
      </div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeMessage(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendErrorMessage(errText) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "message-row";
  div.innerHTML = `
    <div class="message-avatar bot-avatar" style="background: var(--accent-rose);">⚠️</div>
    <div class="message-content">
      <div class="bubble bot-bubble" style="border-color: rgba(244, 63, 94, 0.4);">
        <strong>Execution Error:</strong> ${escapeHtml(errText)}
      </div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendAssistantMessage(data) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "message-row";

  // Build execution steps badge
  const stepsHtml = (data.execution_steps || []).map((step, idx) => `
    <span class="step-node ${idx === data.execution_steps.length - 1 ? 'active' : ''}">${step}</span>
    ${idx < data.execution_steps.length - 1 ? '<span class="step-arrow">➔</span>' : ''}
  `).join("");

  // Build citations
  let citationsHtml = "";
  if (data.sources && data.sources.length > 0) {
    citationsHtml = `
      <div class="citations-wrapper">
        <div class="citations-header">📚 Referenced Sources (${data.sources.length})</div>
        <div class="citation-cards">
          ${data.sources.map((s) => `
            <div class="citation-card">
              <div class="citation-title">${escapeHtml(s.title)} › <span style="color: #c7d2fe;">${escapeHtml(s.header_path)}</span></div>
              <div class="citation-snippet">${escapeHtml(s.snippet)}</div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  // Grounded badge
  const groundedBadge = data.grounded === "grounded" 
    ? `<span style="font-size: 0.72rem; color: #10b981; background: rgba(16, 185, 129, 0.15); padding: 0.15rem 0.4rem; border-radius: 4px;">✓ Self-RAG Grounded</span>`
    : `<span style="font-size: 0.72rem; color: #f59e0b; background: rgba(245, 158, 11, 0.15); padding: 0.15rem 0.4rem; border-radius: 4px;">⚠ Disclaimed / Review</span>`;

  div.innerHTML = `
    <div class="message-avatar bot-avatar">⚡</div>
    <div class="message-content">
      <div class="bubble bot-bubble">
        <div class="pipeline-trail">
          <span style="font-weight: 600;">Graph Trail:</span>
          ${stepsHtml}
          ${data.retries_used > 0 ? `<span style="color: #f59e0b;">(Rewrote ${data.retries_used}x)</span>` : ''}
          ${groundedBadge}
        </div>
        <div class="markdown-body">${formatMarkdown(data.answer)}</div>
        ${citationsHtml}
        <div class="feedback-actions">
          <button class="feedback-btn up" onclick="submitFeedback('${data.query_id}', 'up', this)">👍 Helpful</button>
          <button class="feedback-btn down" onclick="submitFeedback('${data.query_id}', 'down', this)">👎 Inaccurate</button>
        </div>
      </div>
    </div>
  `;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// User Feedback Submission
async function submitFeedback(queryId, rating, btn) {
  try {
    const parent = btn.parentElement;
    parent.querySelectorAll(".feedback-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    await fetch("/api/v1/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_id: queryId, rating: rating })
    });
  } catch (err) {
    console.error("Failed to submit feedback", err);
  }
}

// File Ingestion Handler
async function handleFileUpload(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  const statusBox = document.getElementById("ingest-status-box");
  statusBox.style.display = "block";
  statusBox.style.background = "rgba(99, 102, 241, 0.15)";
  statusBox.style.color = "#a5b4fc";
  statusBox.innerHTML = `Uploading and chunking ${files.length} document(s)...`;

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }

  try {
    const res = await fetch("/api/v1/ingest/upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");

    statusBox.style.background = "rgba(16, 185, 129, 0.15)";
    statusBox.style.color = "#6ee7b7";
    statusBox.innerHTML = `✅ ${data.message}`;
    loadDocuments();
    checkHealth();
  } catch (err) {
    statusBox.style.background = "rgba(244, 63, 94, 0.15)";
    statusBox.style.color = "#fda4af";
    statusBox.innerHTML = `❌ Error: ${err.message}`;
  }
}

// URL Ingestion Handler
async function handleUrlIngest() {
  const urlInput = document.getElementById("url-input");
  const btn = document.getElementById("ingest-url-btn");
  const url = urlInput.value.trim();
  if (!url) return;

  const statusBox = document.getElementById("ingest-status-box");
  statusBox.style.display = "block";
  statusBox.style.background = "rgba(99, 102, 241, 0.15)";
  statusBox.style.color = "#a5b4fc";
  statusBox.innerHTML = `Crawling and indexing ${url}...`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/v1/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urls: [url] }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "URL ingestion failed");

    statusBox.style.background = "rgba(16, 185, 129, 0.15)";
    statusBox.style.color = "#6ee7b7";
    statusBox.innerHTML = `✅ ${data.message}`;
    urlInput.value = "";
    loadDocuments();
    checkHealth();
  } catch (err) {
    statusBox.style.background = "rgba(244, 63, 94, 0.15)";
    statusBox.style.color = "#fda4af";
    statusBox.innerHTML = `❌ Error: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
}

// Lightweight Markdown Formatter
function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/```([a-zA-Z]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    })
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/^### (.*$)/gim, '<h4 style="margin: 0.6rem 0 0.3rem; color: #a5b4fc;">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 style="margin: 0.8rem 0 0.4rem; color: #c7d2fe;">$1</h3>')
    .replace(/^# (.*$)/gim, '<h2 style="margin: 1rem 0 0.5rem; color: #fff;">$1</h2>')
    .replace(/\n\n/g, '<p style="margin-bottom: 0.6rem;"></p>')
    .replace(/\n/g, '<br/>');

  return html;
}

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/* Quantellix.AI Modern Chatbot Page JavaScript */
document.addEventListener("DOMContentLoaded", function () {
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const btnSend = document.getElementById("btnSend");
  const btnRestart = document.getElementById("btnRestart");
  const btnThemeToggle = document.getElementById("btnThemeToggle");

  function scrollToBottom() {
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }
  scrollToBottom();

  // Theme Toggle
  if (btnThemeToggle) {
    const savedTheme = localStorage.getItem("quantellix_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    btnThemeToggle.textContent = savedTheme === "dark" ? "☀️" : "🌙";

    btnThemeToggle.addEventListener("click", function () {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const nextTheme = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      localStorage.setItem("quantellix_theme", nextTheme);
      btnThemeToggle.textContent = nextTheme === "dark" ? "☀️" : "🌙";
    });
  }

  function lockEdaButtons() {
    if (btnViewEDA) {
      btnViewEDA.className = "side-btn-disabled";
      btnViewEDA.title = "Locked until dataset upload and EDA completion";
      btnViewEDA.onclick = null;
      if (badgeViewEDA) {
        badgeViewEDA.textContent = "Locked";
      }
    }
    if (btnExecutiveDashboard) {
      btnExecutiveDashboard.className = "side-btn-disabled";
      btnExecutiveDashboard.title = "Locked until you pick a problem";
      btnExecutiveDashboard.onclick = null;
      if (badgeExecutiveDashboard) {
        badgeExecutiveDashboard.textContent = "Locked";
      }
    }
  }

  // Restart Button
  if (btnRestart) {
    btnRestart.addEventListener("click", async function () {
      if (!confirm("Are you sure you want to restart the chat session?")) return;
      try {
        localStorage.removeItem("quantellix_attached_files");
        localStorage.removeItem("quantellix_files_added");
        localStorage.removeItem("quantellix_eda_ready");
        localStorage.removeItem("quantellix_dashboard_url");
        lockEdaButtons();
        await fetch("/api/chat/restart", { method: "POST" });
        window.location.reload();
      } catch (err) {
        console.error("Failed to restart:", err);
        window.location.reload();
      }
    });
  }

  // Recent Files & Dataset Attachment
  const btnAttachFile = document.getElementById("btnAttachFile");
  const fileAttachInput = document.getElementById("fileAttachInput");
  const recentFilesContainer = document.getElementById("recentFilesContainer");
  const recentFilesBadge = document.getElementById("recentFilesBadge");
  const btnViewEDA = document.getElementById("btnViewEDA");
  const badgeViewEDA = document.getElementById("badgeViewEDA");
  const btnExecutiveDashboard = document.getElementById("btnExecutiveDashboard");
  const badgeExecutiveDashboard = document.getElementById("badgeExecutiveDashboard");

  function unlockEdaButtons(sessionId, viewUrl) {
    if (btnViewEDA) {
      btnViewEDA.className = "side-btn-active";
      btnViewEDA.title = "Download Automated EDA Report as PDF";
      if (badgeViewEDA) {
        badgeViewEDA.textContent = "Ready";
      }
      btnViewEDA.onclick = function (e) {
        if (e) e.preventDefault();
        const sid = sessionId || btnViewEDA.getAttribute("data-session-id") || "";
        if (!sid) return;

        // Visual feedback on badge
        const originalBadge = badgeViewEDA ? badgeViewEDA.textContent : "Ready";
        if (badgeViewEDA) badgeViewEDA.textContent = "Downloading...";

        // Trigger direct file download without opening a separate tab
        const downloadUrl = `/api/eda/download-pdf/${sid}`;
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.setAttribute("download", "Quantellix_EDA_Report.pdf");
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        setTimeout(() => {
          if (badgeViewEDA) badgeViewEDA.textContent = originalBadge;
        }, 1800);
      };
    }
  }

  function unlockExecutiveDashboard(url) {
    if (btnExecutiveDashboard) {
      btnExecutiveDashboard.className = "side-btn-active";
      btnExecutiveDashboard.title = "Open Executive Dashboard";
      if (badgeExecutiveDashboard) {
        badgeExecutiveDashboard.textContent = "Open";
      }
      btnExecutiveDashboard.onclick = function () {
        window.location.href = url;
      };
    }
  }

  // If server already rendered buttons as active on page load
  if (btnViewEDA && btnViewEDA.classList.contains("side-btn-active")) {
    const sessId = btnViewEDA.getAttribute("data-session-id") || "";
    unlockEdaButtons(sessId);
  }

  const savedDashUrl = localStorage.getItem("quantellix_dashboard_url");
  if (savedDashUrl) {
    unlockExecutiveDashboard(savedDashUrl);
  }

  function renderRecentFiles() {
    let files = [];
    try {
      files = JSON.parse(localStorage.getItem("quantellix_attached_files") || "[]");
    } catch (e) {
      files = [];
    }

    if (!files || files.length === 0) {
      if (recentFilesBadge) recentFilesBadge.textContent = "0 Active";
      if (recentFilesContainer) {
        recentFilesContainer.innerHTML = `
          <div class="no-files-notice" id="noFilesNotice">
            No files added
          </div>
        `;
      }
    } else {
      if (recentFilesBadge) recentFilesBadge.textContent = `${files.length} Active`;
      if (recentFilesContainer) {
        recentFilesContainer.innerHTML = files.map(f => `
          <div class="file-item">
            <span class="file-icon">📊</span>
            <div class="file-details">
              <div class="file-name" title="${escapeHtml(f.name)}">${escapeHtml(f.name)}</div>
              <div class="file-meta">${escapeHtml(f.meta || "Ready for analysis")}</div>
            </div>
          </div>
        `).join("");
      }
    }
  }

  renderRecentFiles();

  if (btnAttachFile && fileAttachInput) {
    btnAttachFile.addEventListener("click", function () {
      fileAttachInput.click();
    });

    fileAttachInput.addEventListener("change", async function (e) {
      const file = e.target.files[0];
      if (!file) return;

      const sizeStr = file.size > 1024 * 1024
        ? (file.size / (1024 * 1024)).toFixed(1) + " MB"
        : (file.size / 1024).toFixed(0) + " KB";

      // Show attachment bubble in chat immediately
      appendUserMessage(`📎 Uploading dataset: ${file.name} (${sizeStr})...`);
      showTypingIndicator();

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch("/api/chat/upload", {
          method: "POST",
          body: formData
        });

        removeTypingIndicator();

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Upload failed (status ${response.status})`);
        }

        const data = await response.json();

        // Append bot responses
        if (data && data.messages && data.messages.length > 0) {
          data.messages.forEach(msg => {
            appendBotMessage(msg);
          });
        }

        // Unlock View EDA button
        if (data.eda_ready) {
          unlockEdaButtons(data.session_id, data.eda_view_url);
        }

        // Add to recent files storage
        let files = [];
        try {
          files = JSON.parse(localStorage.getItem("quantellix_attached_files") || "[]");
        } catch (err) {
          files = [];
        }

        files.unshift({
          name: file.name,
          meta: `${data.row_count.toLocaleString()} rows • ${data.col_count} cols • ${sizeStr}`,
          timestamp: Date.now()
        });

        localStorage.setItem("quantellix_files_added", "true");
        localStorage.setItem("quantellix_attached_files", JSON.stringify(files));
        renderRecentFiles();

      } catch (err) {
        removeTypingIndicator();
        console.error("Upload error:", err);
        appendBotMessage({
          sender: "bot",
          type: "text",
          text: `⚠️ **Upload Failed:** ${escapeHtml(err.message)}<br>Please ensure you are uploading a valid CSV or Excel file.`
        });
      } finally {
        fileAttachInput.value = "";
        scrollToBottom();
      }
    });
  }

  // Dashboards Menu Drawer Toggle
  window.toggleDashboardsMenu = function () {
    const drawer = document.getElementById("dashboardsMenuDrawer");
    const backdrop = document.getElementById("dashboardsBackdrop");
    if (!drawer || !backdrop) return;
    const isOpen = drawer.classList.contains("open");
    if (isOpen) {
      drawer.classList.remove("open");
      backdrop.classList.remove("open");
    } else {
      drawer.classList.add("open");
      backdrop.classList.add("open");
    }
  };

  // Close menu drawer with Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      const drawer = document.getElementById("dashboardsMenuDrawer");
      const backdrop = document.getElementById("dashboardsBackdrop");
      if (drawer && drawer.classList.contains("open")) {
        drawer.classList.remove("open");
        backdrop.classList.remove("open");
      }
    }
  });

  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Format Markdown-like text safely
  function formatMessageText(text) {
    if (!text) return "";

    // Normalize any accidental HTML tags to clean markdown/newlines before escaping
    let clean = text.replace(/<br\s*[\/]?>/gi, "\n");
    clean = clean.replace(/<\/?(strong|b)>/gi, "**");
    clean = clean.replace(/<\/?(em|i)>/gi, "*");

    let formatted = escapeHtml(clean);

    // Bold **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Inline code `text`
    formatted = formatted.replace(/`(.*?)`/g, "<code>$1</code>");
    // Unordered lists
    formatted = formatted.replace(/^\s*[-•]\s+(.*)$/gm, "<li>$1</li>");
    formatted = formatted.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");
    // Newlines to <br>
    formatted = formatted.replace(/\n/g, "<br>");
    return formatted;
  }

  // Append user message
  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "msg-row user";
    row.innerHTML = `
      <div class="msg-avatar">👤</div>
      <div class="msg-bubble">
        <p>${escapeHtml(text)}</p>
      </div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
  }

  // Show typing indicator
  function showTypingIndicator() {
    const row = document.createElement("div");
    row.className = "msg-row bot";
    row.id = "typingIndicator";
    row.innerHTML = `
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function removeTypingIndicator() {
    const el = document.getElementById("typingIndicator");
    if (el) el.remove();
  }

  // Render Bot Message
  function appendBotMessage(msg) {
    const row = document.createElement("div");
    row.className = "msg-row bot";

    if (msg.type === "license_card") {
      row.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="license-card">
          <div class="license-header">
            <span class="license-icon">⚡</span>
            <span class="license-title">${escapeHtml(msg.title || "Signed in from your license.")}</span>
          </div>
          <div class="license-plan">${escapeHtml(msg.plan || "")}</div>
          <ul class="license-notices">
            ${msg.used_notice ? `<li>${escapeHtml(msg.used_notice)}</li>` : ""}
            ${msg.credits_notice ? `<li>${escapeHtml(msg.credits_notice)}</li>` : ""}
            ${msg.terms_notice ? `<li>${escapeHtml(msg.terms_notice)}</li>` : ""}
          </ul>
          <div class="license-footer">
            <span>🛡️</span>
            <span>${escapeHtml(msg.validity || "License active")}</span>
          </div>
        </div>
      `;
    } else {
      row.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble">
          <div>${formatMessageText(msg.text || "")}</div>
        </div>
      `;
    }

    chatMessages.appendChild(row);
    scrollToBottom();
  }

  // Send message handler
  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendUserMessage(text);
    chatInput.value = "";
    chatInput.focus();

    btnSend.disabled = true;
    showTypingIndicator();

    try {
      const response = await fetch("/api/chat/interactive", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: text }),
      });

      removeTypingIndicator();

      if (!response.ok) {
        throw new Error("HTTP error " + response.status);
      }

      const data = await response.json();
      if (data && data.messages && data.messages.length > 0) {
        data.messages.forEach((msg) => {
          if (msg.sender === "bot") {
            appendBotMessage(msg);
          }
        });
      }

      if (data && data.dashboard_url) {
        unlockExecutiveDashboard(data.dashboard_url);
        localStorage.setItem("quantellix_dashboard_url", data.dashboard_url);
      }
    } catch (err) {
      removeTypingIndicator();
      console.error("Chat error:", err);
      appendBotMessage({
        sender: "bot",
        type: "text",
        text: "⚠️ An error occurred while communicating with the assistant. Please try again.",
      });
    } finally {
      btnSend.disabled = false;
      scrollToBottom();
    }
  }

  if (chatForm) {
    chatForm.addEventListener("submit", function (e) {
      e.preventDefault();
      sendMessage();
    });
  }

  if (chatInput) {
    chatInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }
});

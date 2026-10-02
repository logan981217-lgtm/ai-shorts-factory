// State
let currentProjectId = null;
let pollInterval = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
  loadStats();
  loadProjects();
  loadSettings();
  loadSchedules();
  startStatusPolling();
});

// Tab Switching
function switchTab(tabName) {
  document.querySelectorAll(".tab-content").forEach(el => el.style.display = "none");
  document.querySelectorAll(".nav-btn").forEach(el => el.classList.remove("active"));
  
  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) targetTab.style.display = "block";
  
  const navBtns = document.querySelectorAll(".nav-btn");
  if (tabName === "dashboard") navBtns[0].classList.add("active");
  if (tabName === "schedules") {
    navBtns[1].classList.add("active");
    loadSchedules();
  }
  if (tabName === "settings") navBtns[2].classList.add("active");
}

// Fetch Stats
async function loadStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("kpi-total").innerText = data.total_projects;
    document.getElementById("kpi-published").innerText = data.published_count;
    document.getElementById("kpi-retention").innerText = data.estimated_retention;
    document.getElementById("kpi-ypp").innerText = `${data.avg_ypp_score}점`;
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

// Fetch Projects
async function loadProjects() {
  try {
    const res = await fetch("/api/projects");
    const projects = await res.json();
    document.getElementById("project-count").innerText = projects.length;
    renderProjects(projects);
    checkActiveGenerations(projects);
  } catch (err) {
    console.error("Failed to load projects:", err);
  }
}

function renderProjects(projects) {
  const container = document.getElementById("projects-grid");
  if (!projects || projects.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted); background: var(--bg-secondary); border-radius: var(--card-radius); border: 1px dashed var(--border-color);">
        <p style="font-size: 16px; margin-bottom: 12px;">생성된 쇼츠 프로젝트가 아직 없습니다.</p>
        <button class="btn-primary" onclick="openCreateModal()" style="margin: 0 auto;">
          <span>+</span> 첫 번째 쇼츠 자동 제작하기
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = projects.map(p => {
    const isCompleted = p.status === "completed";
    const isFailed = p.status === "failed";
    const isGenerating = !isCompleted && !isFailed;
    
    const thumbSrc = p.thumbnail_url || "/static/assets/placeholder.jpg";
    const statusText = {
      "draft": "대기",
      "scripting": "대본 작성 중",
      "tts_generating": "음성/자막 합성 중",
      "rendering": "9:16 비디오 렌더링 중",
      "completed": "제작 완료",
      "failed": "오류 발생"
    }[p.status] || p.status;

    return `
      <div class="project-card">
        <div class="thumb-preview-wrap" onclick="openDetailModal('${p.id}')">
          <img src="${thumbSrc}" alt="Thumbnail" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&q=80'">
          ${isCompleted ? `<div class="play-overlay">▶</div>` : ""}
          <span class="duration-tag">${p.duration_actual ? Math.round(p.duration_actual) + "초" : p.duration_target + "초"}</span>
          <span class="ypp-tag">YPP ${p.ypp_score || 95}점</span>
        </div>

        <div class="card-body">
          <div class="card-topic">📌 ${escapeHtml(p.topic)}</div>
          <div class="card-title" title="${escapeHtml(p.title)}">${escapeHtml(p.title || p.topic)}</div>

          ${isGenerating ? `
            <div style="margin: 8px 0;">
              <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--accent-cyan);">
                <span>${statusText}</span>
                <span>${p.progress}%</span>
              </div>
              <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${p.progress}%;"></div>
              </div>
            </div>
          ` : ""}

          <div class="card-meta">
            <span>${p.voice_id.includes("SunHi") ? "선희(여)" : p.voice_id.includes("InJoon") ? "인준(남)" : "AI 보이스"}</span>
            <span>${p.created_at ? p.created_at.substring(0, 10) : ""}</span>
          </div>

          <div class="card-actions">
            ${isCompleted ? `
              <button class="btn-card" onclick="openDetailModal('${p.id}')">🎬 재생 & 상세</button>
            ` : isGenerating ? `
              <button class="btn-card" disabled style="opacity: 0.6;">⏳ 렌더링 중</button>
            ` : `
              <button class="btn-card" onclick="openDetailModal('${p.id}')">🔍 상태 확인</button>
            `}
            <button class="btn-card btn-card-del" onclick="deleteProject('${p.id}')" title="삭제">🗑️</button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function checkActiveGenerations(projects) {
  const active = projects.find(p => p.status !== "completed" && p.status !== "failed");
  const banner = document.getElementById("active-banner");
  if (active) {
    banner.style.display = "flex";
    document.getElementById("active-banner-title").innerText = `[${active.topic}] 쇼츠 제작 파이프라인 가동 중...`;
    document.getElementById("active-banner-msg").innerText = `진행 단계: ${active.status} (${active.progress}%)`;
    document.getElementById("active-banner-progress").style.width = `${active.progress}%`;
  } else {
    banner.style.display = "none";
  }
}

function startStatusPolling() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(() => {
    loadProjects();
    loadStats();
  }, 2500);
}

// Modal Handlers
function openCreateModal() {
  document.getElementById("modal-create").style.display = "flex";
}

function closeCreateModal() {
  document.getElementById("modal-create").style.display = "none";
}

function setTopic(text) {
  // Remove icon emoji from chip text
  const clean = text.replace(/^[^\w가-힣]+/, "").trim();
  document.getElementById("input-topic").value = clean;
}

// Script preview generator
async function previewScript() {
  const topic = document.getElementById("input-topic").value.trim();
  if (!topic) {
    alert("먼저 주제나 키워드를 입력해주세요.");
    return;
  }
  const duration = parseInt(document.getElementById("select-duration").value);

  const btn = event.target;
  const originalText = btn.innerText;
  btn.innerText = "✨ AI 작성 중...";
  btn.disabled = true;

  try {
    const res = await fetch("/api/projects/preview-script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, duration })
    });
    const data = await res.json();
    document.getElementById("script-hook").value = data.hook || "";
    document.getElementById("script-body").value = data.body || "";
    document.getElementById("script-cta").value = data.cta || "";
  } catch (err) {
    alert("스크립트 생성 중 오류가 발생했습니다: " + err);
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}

// Submit Create Project
async function submitCreateProject() {
  const topic = document.getElementById("input-topic").value.trim();
  if (!topic) {
    alert("주제 및 핵심 키워드를 입력해주세요.");
    return;
  }

  const duration = parseInt(document.getElementById("select-duration").value);
  const voice = document.getElementById("select-voice").value;
  const substyle = document.getElementById("select-substyle").value;
  const bgm = document.getElementById("select-bgm").value;
  const imgInput = document.getElementById("input-bg-image");

  const hook = document.getElementById("script-hook").value.trim();
  const body = document.getElementById("script-body").value.trim();
  const cta = document.getElementById("script-cta").value.trim();

  closeCreateModal();

  if (imgInput.files && imgInput.files.length > 0) {
    const formData = new FormData();
    formData.append("topic", topic);
    formData.append("duration_target", duration);
    formData.append("voice_id", voice);
    formData.append("subtitle_style", substyle);
    formData.append("bgm_style", bgm);
    formData.append("image", imgInput.files[0]);

    await fetch("/api/projects/create-with-image", {
      method: "POST",
      body: formData
    });
  } else {
    const payload = {
      topic: topic,
      duration_target: duration,
      voice_id: voice,
      subtitle_style: substyle,
      bgm_style: bgm
    };
    if (hook && body) {
      payload.custom_script = { hook, body, cta };
    }

    await fetch("/api/projects/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  loadProjects();
  loadStats();
}

// Open Detail Modal
async function openDetailModal(projectId) {
  currentProjectId = projectId;
  try {
    const res = await fetch(`/api/projects/${projectId}`);
    const p = await res.json();

    document.getElementById("detail-title").innerText = p.title || p.topic;
    document.getElementById("detail-badge-ypp").innerText = `🛡️ YPP ${p.ypp_score || 95}점 (수익화 안전)`;
    document.getElementById("detail-badge-duration").innerText = `⏱️ ${p.duration_actual ? Math.round(p.duration_actual) + "초" : p.duration_target + "초"}`;
    document.getElementById("detail-badge-voice").innerText = `🎙️ ${p.voice_id.includes("SunHi") ? "선희" : "인준"}`;

    const videoPlayer = document.getElementById("detail-video-player");
    if (p.video_url) {
      videoPlayer.src = p.video_url;
      videoPlayer.style.display = "block";
      videoPlayer.load();
    } else {
      videoPlayer.style.display = "none";
    }

    // Set Download Links
    const btnDlVid = document.getElementById("btn-dl-video");
    const btnDlThumb = document.getElementById("btn-dl-thumb");
    const btnDlSrt = document.getElementById("btn-dl-srt");

    if (p.video_url) {
      btnDlVid.href = p.video_url;
      btnDlVid.style.display = "inline-flex";
    } else {
      btnDlVid.style.display = "none";
    }

    if (p.thumbnail_url) {
      btnDlThumb.href = p.thumbnail_url;
      btnDlThumb.style.display = "inline-flex";
    } else {
      btnDlThumb.style.display = "none";
    }

    if (p.srt_url) {
      btnDlSrt.href = p.srt_url;
      btnDlSrt.style.display = "inline-flex";
    } else {
      btnDlSrt.style.display = "none";
    }

    // SEO Copy Boxes
    document.getElementById("detail-yt-title").innerText = p.yt_title || p.title || "";
    document.getElementById("detail-yt-tags").innerText = p.yt_tags || "";
    document.getElementById("detail-yt-desc").innerText = p.yt_description || "";

    document.getElementById("modal-detail").style.display = "flex";
  } catch (err) {
    alert("프로젝트 정보를 불러오지 못했습니다: " + err);
  }
}

function closeDetailModal() {
  const videoPlayer = document.getElementById("detail-video-player");
  videoPlayer.pause();
  videoPlayer.src = "";
  document.getElementById("modal-detail").style.display = "none";
}

// Delete Project
async function deleteProject(projectId) {
  if (!confirm("정말 이 프로젝트를 삭제하시겠습니까?")) return;
  try {
    await fetch(`/api/projects/${projectId}`, { method: "DELETE" });
    loadProjects();
    loadStats();
  } catch (err) {
    alert("삭제 실패: " + err);
  }
}

// Copy to clipboard helper
function copyText(elemId) {
  const text = document.getElementById(elemId).innerText;
  navigator.clipboard.writeText(text).then(() => {
    alert("클립보드에 복사되었습니다!");
  }).catch(() => {
    // fallback
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
    alert("클립보드에 복사되었습니다!");
  });
}

// Schedule Project
async function scheduleCurrentProject() {
  if (!currentProjectId) return;
  try {
    const res = await fetch(`/api/projects/${currentProjectId}/schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel_name: "AI Shorts Studio" })
    });
    const data = await res.json();
    alert(`유튜브 예약 발행이 등록되었습니다!\n발행 예정 시간: ${data.target_time}`);
    loadSchedules();
  } catch (err) {
    alert("예약 실패: " + err);
  }
}

// Publish Now
async function publishCurrentProjectNow() {
  if (!currentProjectId) return;
  try {
    const res = await fetch(`/api/projects/${currentProjectId}/publish-now`, {
      method: "POST"
    });
    const data = await res.json();
    alert(`🎉 ${data.message}\n생성된 유튜브 비디오 ID: ${data.video_id}`);
    loadProjects();
    loadStats();
    loadSchedules();
  } catch (err) {
    alert("발행 실패: " + err);
  }
}

// Auto-Pilot Trigger
async function triggerAutoPilot() {
  try {
    const res = await fetch("/api/auto-pilot/trigger", { method: "POST" });
    const data = await res.json();
    alert(`🤖 ${data.message}`);
    loadProjects();
  } catch (err) {
    alert("오토파일럿 실행 실패: " + err);
  }
}

// Schedules
async function loadSchedules() {
  try {
    const res = await fetch("/api/schedules");
    const schedules = await res.json();
    const tbody = document.getElementById("schedules-table-body");
    if (!schedules || schedules.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">예약된 발행 일정이 없습니다.</td></tr>`;
      return;
    }
    tbody.innerHTML = schedules.map(s => `
      <tr>
        <td>#${s.id}</td>
        <td><strong>${escapeHtml(s.project_title || s.project_id)}</strong></td>
        <td>${escapeHtml(s.channel_name)}</td>
        <td>${s.target_time}</td>
        <td>
          <span class="status-badge ${s.status === 'published' ? 'badge-completed' : 'badge-rendering'}">
            ${s.status === 'published' ? '발행 완료' : '예약 대기'}
          </span>
        </td>
        <td>
          ${s.status !== 'published' ? `
            <button class="btn-card" style="padding: 4px 10px; font-size: 11px;" onclick="publishProjectDirectly('${s.project_id}')">
              즉시 발행
            </button>
          ` : `<span style="color: var(--text-muted); font-size: 12px;">완료됨</span>`}
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Failed to load schedules:", err);
  }
}

async function publishProjectDirectly(projectId) {
  try {
    const res = await fetch(`/api/projects/${projectId}/publish-now`, { method: "POST" });
    const data = await res.json();
    alert(`🎉 ${data.message}`);
    loadSchedules();
    loadStats();
  } catch (err) {
    alert("발행 실패: " + err);
  }
}

// Settings
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const s = await res.json();
    if (s.gemini_api_key) document.getElementById("setting-gemini-key").value = s.gemini_api_key;
    if (s.channel_name) document.getElementById("setting-channel-name").value = s.channel_name;
    if (s.default_voice) document.getElementById("setting-default-voice").value = s.default_voice;
    if (s.default_duration) document.getElementById("setting-default-duration").value = s.default_duration;
    if (s.daily_publish_time) document.getElementById("setting-daily-time").value = s.daily_publish_time;
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

async function saveSettings() {
  const gemini_api_key = document.getElementById("setting-gemini-key").value;
  const channel_name = document.getElementById("setting-channel-name").value;
  const default_voice = document.getElementById("setting-default-voice").value;
  const default_duration = document.getElementById("setting-default-duration").value;
  const daily_publish_time = document.getElementById("setting-daily-time").value;

  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gemini_api_key,
        channel_name,
        default_voice,
        default_duration,
        daily_publish_time
      })
    });
    alert("설정이 성공적으로 저장되었습니다!");
  } catch (err) {
    alert("설정 저장 실패: " + err);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

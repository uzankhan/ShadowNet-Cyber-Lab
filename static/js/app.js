// ShadowNet Cyber Labs — client-side glue
// Made by Uzan Khan | ID 468675
//
// NOTE (hardcoded secret — intentional vulnerability #14):
// This key should never have shipped to the browser. It grants access to
// /api/admin/panel via the X-Api-Key header. TODO remove before prod.
const ADMIN_API_KEY = "sk_live_sh4d0wn3t_4dm1n_9f81c2";

// ---------------- Matrix rain background ----------------
(function initMatrix() {
  const canvas = document.getElementById("matrix-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let w, h, cols, drops;
  const chars = "01ｱｲｳｴｵｶｷｸｹｺ$#@%&";

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    cols = Math.floor(w / 16);
    drops = new Array(cols).fill(1);
  }
  window.addEventListener("resize", resize);
  resize();

  function draw() {
    ctx.fillStyle = "rgba(10,10,10,0.08)";
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#ff2b2b";
    ctx.font = "14px monospace";
    for (let i = 0; i < drops.length; i++) {
      const text = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(text, i * 16, drops[i] * 16);
      if (drops[i] * 16 > h && Math.random() > 0.975) drops[i] = 0;
      drops[i]++;
    }
  }
  setInterval(draw, 50);
})();

// ---------------- Victory popup ----------------
function showVictoryPopup(challengeName) {
  let overlay = document.getElementById("victory-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "victory-overlay";
    overlay.className = "popup-overlay";
    overlay.innerHTML = `
      <div class="popup-box">
        <h2>🎉 CONGRATULATIONS, HACKER!</h2>
        <div class="flag-name" id="victory-challenge-name"></div>
        <div class="flag-motivation">Every master was once a beginner. Keep breaking, keep learning!</div>
        <div class="countdown"><span id="victory-countdown">10</span>s</div>
      </div>`;
    document.body.appendChild(overlay);
  }
  document.getElementById("victory-challenge-name").textContent = challengeName;
  overlay.classList.add("show");

  let seconds = 10;
  const counterEl = document.getElementById("victory-countdown");
  counterEl.textContent = seconds;
  const interval = setInterval(() => {
    seconds -= 1;
    counterEl.textContent = seconds;
    if (seconds <= 0) {
      clearInterval(interval);
      overlay.classList.remove("show");
    }
  }, 1000);
}

// ---------------- Flag submission bar ----------------
async function submitFlagValue(value) {
  const res = await fetch("/api/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ flag: value }),
  });
  return res.json();
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("flag-submit-form");
  if (!form) return;
  const input = document.getElementById("flag-input");
  const flash = document.getElementById("flag-flash");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const value = input.value.trim();
    if (!value) return;
    const data = await submitFlagValue(value);
    if (data.correct) {
      input.value = "";
      flash.textContent = data.already_captured ? "Already captured." : "";
      showVictoryPopup(data.challenge);
      updateProgressPill(data.total_captured, data.total);
      const card = document.querySelector(`[data-flag-name="${data.challenge}"]`);
    } else {
      flash.textContent = "Not a valid flag.";
      setTimeout(() => (flash.textContent = ""), 2000);
    }
  });
});

function updateProgressPill(captured, total) {
  const pill = document.getElementById("progress-pill");
  if (pill) pill.textContent = `${captured} / ${total} FLAGS`;
}

async function loadHint(flagId, targetId) {
  const res = await fetch(`/api/hint/${flagId}`);
  const data = await res.json();
  const el = document.getElementById(targetId);
  if (el) {
    el.textContent = data.hint;
    el.style.display = "block";
  }
}

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="SA-UDP Cross-Layer Engine",
    page_icon="📡",
    layout="wide"
)

st.title("📡 SA-UDP: Cross-Layer Adaptive Protocol Simulator")
st.caption("Dynamic Telemetry Adaptation, Wireless Loss Isolation & High-Capacity Turbo Mode")

animation_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #0b1120; color: #f8fafc; margin: 0; padding: 12px; }
  
  .controls-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    background: #1e293b;
    padding: 14px;
    border-radius: 8px;
    margin-bottom: 12px;
    border: 1px solid #334155;
  }
  
  .control-group label {
    display: block;
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 6px;
    font-weight: 600;
  }
  
  .control-group input[type="range"] {
    width: 100%;
    accent-color: #38bdf8;
  }
  
  .btn-action {
    background: #0284c7;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
    transition: 0.2s;
  }
  .btn-action:hover { background: #0369a1; }
  
  .badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
  }
  .tag-low { background: #7f1d1d; color: #fecaca; }
  .tag-mid { background: #1e3a8a; color: #bfdbfe; }
  .tag-high { background: #14532d; color: #bbf7d0; }

  canvas {
    background: #020617;
    border-radius: 8px;
    width: 100%;
    height: 380px;
    border: 1px solid #334155;
    display: block;
  }
  
  .logger-terminal {
    background: #020617;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px;
    margin-top: 12px;
    height: 140px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 12px;
    color: #38bdf8;
  }
  .log-entry { margin-bottom: 4px; line-height: 1.4; }
  .log-warn { color: #f59e0b; }
  .log-err { color: #ef4444; }
  .log-success { color: #10b981; }
  .log-telemetry { color: #c084fc; }
</style>
</head>
<body>

<div class="controls-panel">
  <div class="control-group">
    <label>Channel SNR: <span id="snrVal">20.0</span> dB <span id="snrTag" class="badge tag-mid">Standard Mode</span></label>
    <input type="range" id="snrSlider" min="5" max="30" step="0.5" value="20">
  </div>

  <div class="control-group">
    <label>CWND: <span id="cwndVal" style="color:#38bdf8; font-size:14px;">4.00</span> pkts | RTO: <span id="rtoVal">0.200</span>s</label>
    <label style="color: #64748b; font-weight: normal;">Status: <span id="strategyVal" style="color: #38bdf8;">Normal Transmission</span></label>
  </div>

  <div class="control-group" style="display: flex; gap: 8px; align-items: flex-end;">
    <button class="btn-action" onclick="sendPacket()">Transmit Packet</button>
    <button class="btn-action" style="background: #475569;" onclick="toggleAutoStream()" id="autoBtn">Auto Stream: Off</button>
    <button class="btn-action" style="background: #dc2626;" onclick="triggerBufferCongestion()">💥 Inject Queue Congestion</button>
  </div>
</div>

<canvas id="simCanvas"></canvas>

<div class="logger-terminal" id="logBox">
  <div class="log-entry">> SA-UDP Protocol Stack active. System ready.</div>
</div>

<script>
const canvas = document.getElementById("simCanvas");
const ctx = canvas.getContext("2d");

function resize() {
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = 380;
}
window.addEventListener("resize", resize);
resize();

let snr = 20.0;
let cwnd = 4.0;
let rto = 0.200;
let seqNum = 1;
let autoInterval = null;
let congestionFlash = 0;
let congestionActive = false;
const packets = [];

const snrSlider = document.getElementById("snrSlider");
const snrVal = document.getElementById("snrVal");
const snrTag = document.getElementById("snrTag");
const cwndVal = document.getElementById("cwndVal");
const rtoVal = document.getElementById("rtoVal");
const strategyVal = document.getElementById("strategyVal");
const logBox = document.getElementById("logBox");

function updateProtocolState() {
  snrVal.innerText = snr.toFixed(1);
  if (snr < 12.0) {
    snrTag.className = "badge tag-low";
    snrTag.innerText = "Low SNR (<12dB)";
    rto = 0.270;
    strategyVal.innerText = "Robust Telemetry Protection";
  } else if (snr > 22.0) {
    snrTag.className = "badge tag-high";
    snrTag.innerText = "High SNR (>22dB)";
    rto = 0.120;
    strategyVal.innerText = "High-Throughput Turbo";
  } else {
    snrTag.className = "badge tag-mid";
    snrTag.innerText = "Clean Baseline (12-22dB)";
    rto = 0.200;
    strategyVal.innerText = "Standard Adaptive Window";
  }
  rtoVal.innerText = rto.toFixed(3);
}

snrSlider.addEventListener("input", (e) => {
  snr = parseFloat(e.target.value);
  updateProtocolState();
});

function log(msg, type="info") {
  const line = document.createElement("div");
  line.className = "log-entry " + (type === "warn" ? "log-warn" : type === "err" ? "log-err" : type === "success" ? "log-success" : type === "telemetry" ? "log-telemetry" : "");
  line.innerText = "> " + msg;
  logBox.appendChild(line);
  logBox.scrollTop = logBox.scrollHeight;
}

function sendPacket() {
  const isProtected = snr < 12.0;
  const p = {
    id: seqNum++,
    type: "DATA",
    x: 180,
    y: 135,
    speed: snr > 22.0 ? 6.0 : (snr < 12.0 ? 3.5 : 4.5),
    protectedByTelemetry: isProtected,
    status: "in-flight",
    corrupted: false,
    alpha: 1.0
  };
  packets.push(p);
  log(`Sender dispatched datagram #${p.id} [18B Header, CRC32]` + (isProtected ? " with Low-SNR Telemetry Header" : ""));
}

function toggleAutoStream() {
  const btn = document.getElementById("autoBtn");
  if (autoInterval) {
    clearInterval(autoInterval);
    autoInterval = null;
    btn.innerText = "Auto Stream: Off";
    btn.style.background = "#475569";
  } else {
    const intervalRate = snr > 22.0 ? 500 : (snr < 12.0 ? 1000 : 750);
    autoInterval = setInterval(sendPacket, intervalRate);
    btn.innerText = "Auto Stream: On";
    btn.style.background = "#10b981";
  }
}

function triggerBufferCongestion() {
  congestionFlash = 35;
  congestionActive = true;
  
  for (let p of packets) {
    if (p.type === "DATA" && p.x < canvas.width / 2 + 50) {
      p.corrupted = true;
      p.isBufferDrop = true;
    }
  }

  if (snr >= 12.0) {
    const oldCwnd = cwnd;
    cwnd = Math.max(1.0, cwnd / 2.0);
    cwndVal.innerText = cwnd.toFixed(2);
    cwndVal.style.color = "#ef4444";
    setTimeout(() => { cwndVal.style.color = "#38bdf8"; }, 1000);
    log(`BUFFER OVERFLOW: Clean channel (${snr.toFixed(1)} dB). True network congestion detected! Halving CWND from ${oldCwnd.toFixed(2)} to ${cwnd.toFixed(2)} (Reno rule).`, "err");
  } else {
    cwndVal.style.color = "#10b981";
    setTimeout(() => { cwndVal.style.color = "#38bdf8"; }, 1000);
    log(`BUFFER DROP IGNORED: Low SNR (${snr.toFixed(1)} dB). Classified as wireless corruption. CWND preserved intact at ${cwnd.toFixed(2)}.`, "warn");
  }
}

function drawNodes() {
  // Sender Node
  ctx.fillStyle = "#1e293b";
  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2;
  ctx.fillRect(30, 60, 150, 260);
  ctx.strokeRect(30, 60, 150, 260);
  
  ctx.fillStyle = "#f8fafc";
  ctx.font = "bold 14px sans-serif";
  ctx.fillText("Sender (SA-UDP)", 45, 90);
  
  ctx.font = "11px monospace";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText(`CWND : ${cwnd.toFixed(2)} pkts`, 40, 125);
  ctx.fillText(`RTO  : ${rto.toFixed(3)}s`, 40, 145);
  ctx.fillText(`Mode : ${snr < 12.0 ? 'Paced/Robust' : (snr > 22.0 ? 'Turbo Mode' : 'Standard')}`, 40, 165);
  ctx.fillText(`Timer: ${snr < 12.0 ? '1.8x Scale' : (snr > 22.0 ? '0.6x Scale' : '1.0x Scale')}`, 40, 185);

  // Receiver Node
  const rxX = canvas.width - 180;
  ctx.fillStyle = "#1e293b";
  ctx.strokeStyle = "#10b981";
  ctx.fillRect(rxX, 60, 150, 260);
  ctx.strokeRect(rxX, 60, 150, 260);
  
  ctx.fillStyle = "#f8fafc";
  ctx.font = "bold 14px sans-serif";
  ctx.fillText("Receiver Node", rxX + 22, 90);
  
  ctx.font = "11px monospace";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText(`Telemetry SACK`, rxX + 15, 125);
  ctx.fillText(`Reported SNR: ${snr.toFixed(1)} dB`, rxX + 15, 145);
  ctx.fillText(`Loss Rate   : ${snr < 12.0 ? '15%' : '0%'}`, rxX + 15, 165);
  ctx.fillText(`Feedback    : 24B Frame`, rxX + 15, 185);

  // Wireless Channel representation
  const channelColor = snr < 12.0 
    ? "rgba(239, 68, 68, 0.20)" 
    : (snr > 22.0 ? "rgba(16, 185, 129, 0.20)" : "rgba(56, 189, 248, 0.12)");
    
  ctx.fillStyle = channelColor;
  ctx.fillRect(200, 100, canvas.width - 400, 180);
  ctx.strokeStyle = snr < 12.0 ? "#ef4444" : (snr > 22.0 ? "#10b981" : "#38bdf8");
  ctx.lineWidth = 1;
  ctx.setLineDash([6, 6]);
  ctx.strokeRect(200, 100, canvas.width - 400, 180);
  ctx.setLineDash([]);
  
  // Router Queue Box in the middle
  const midX = canvas.width / 2;
  ctx.fillStyle = congestionFlash > 0 ? "rgba(239, 68, 68, 0.4)" : "#0f172a";
  ctx.strokeStyle = congestionFlash > 0 ? "#ef4444" : "#475569";
  ctx.lineWidth = 2;
  ctx.fillRect(midX - 35, 120, 70, 60);
  ctx.strokeRect(midX - 35, 120, 70, 60);
  
  ctx.fillStyle = congestionFlash > 0 ? "#ef4444" : "#94a3b8";
  ctx.font = "bold 11px sans-serif";
  ctx.fillText("ROUTER", midX - 24, 142);
  ctx.font = "10px sans-serif";
  ctx.fillText(congestionFlash > 0 ? "OVERFLOW" : "QUEUE", midX - 25, 160);

  if (congestionFlash > 0) {
    ctx.strokeStyle = `rgba(239, 68, 68, ${congestionFlash / 35})`;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(midX, 150, (35 - congestionFlash) * 2 + 35, 0, Math.PI * 2);
    ctx.stroke();
    congestionFlash--;
  }
}

function update() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawNodes();

  for (let i = packets.length - 1; i >= 0; i--) {
    const p = packets[i];

    if (p.type === "DATA") {
      p.x += p.speed;

      // Wireless noise fading (only when SNR < 12)
      if (snr < 12.0 && p.x > canvas.width / 2 - 30 && !p.corrupted && !p.telemetryPaced) {
        if (Math.random() < 0.25) {
          p.corrupted = true;
          log(`Packet #${p.id} experienced RF fade. Preserving CWND (${cwnd.toFixed(2)}) and stretching RTO to ${rto.toFixed(3)}s.`, "warn");
        } else {
          p.telemetryPaced = true;
          log(`Packet #${p.id} navigated RF fade via low-SNR telemetry pacing.`, "telemetry");
        }
      }

      // Render packet
      if (!p.corrupted) {
        ctx.fillStyle = p.telemetryPaced ? "#c084fc" : (snr > 22.0 ? "#34d399" : "#38bdf8");
        ctx.fillRect(p.x, p.y, 38, 22);
        ctx.fillStyle = "#020617";
        ctx.font = "bold 10px monospace";
        ctx.fillText(`D#${p.id}`, p.x + 6, p.y + 15);
      } else {
        p.alpha -= 0.04;
        ctx.fillStyle = `rgba(239, 68, 68, ${Math.max(0, p.alpha)})`;
        ctx.beginPath();
        ctx.arc(p.x + 19, p.y + 11, (1 - p.alpha) * 22 + 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, p.alpha)})`;
        ctx.font = "9px sans-serif";
        ctx.fillText(p.isBufferDrop ? "DROP (BUFFER)" : "RF FADE", p.x - 10, p.y - 4);
      }

      // Arrival at Receiver
      if (p.x >= canvas.width - 200 && !p.corrupted) {
        packets.splice(i, 1);
        log(`Receiver verified CRC32 for datagram #${p.id}. Dispatching 24B Telemetry SACK.`, "success");
        
        packets.push({
          id: p.id,
          type: "SACK",
          x: canvas.width - 200,
          y: 220,
          speed: snr > 22.0 ? -6.5 : -5.0,
          snrReported: snr
        });
        continue;
      }

      if (p.corrupted && p.alpha <= 0) {
        packets.splice(i, 1);
      }

    } else if (p.type === "SACK") {
      p.x += p.speed;

      // Render Telemetry SACK Packet
      ctx.fillStyle = "#10b981";
      ctx.fillRect(p.x, p.y, 48, 22);
      ctx.fillStyle = "#022c22";
      ctx.font = "bold 9px monospace";
      ctx.fillText(`SACK#${p.id}`, p.x + 4, p.y + 14);

      // Arrival back at Sender
      if (p.x <= 180) {
        packets.splice(i, 1);
        if (p.snrReported < 12.0) {
          log(`Sender processed Telemetry SACK #${p.id}: SNR=${p.snrReported.toFixed(1)} dB. Window kept steady to prevent stalls.`, "telemetry");
        } else if (p.snrReported > 22.0) {
          cwnd = Math.min(16.0, cwnd + 0.50);
          cwndVal.innerText = cwnd.toFixed(2);
          log(`Sender processed Turbo SACK #${p.id}: SNR=${p.snrReported.toFixed(1)} dB. Boosted CWND to ${cwnd.toFixed(2)}.`, "success");
        } else {
          cwnd = Math.min(16.0, cwnd + 0.25);
          cwndVal.innerText = cwnd.toFixed(2);
          log(`Sender processed standard SACK #${p.id}. Incrementing CWND to ${cwnd.toFixed(2)}.`, "success");
        }
      }
    }
  }

  requestAnimationFrame(update);
}

update();
</script>

</body>
</html>
"""

components.html(animation_html, height=640)
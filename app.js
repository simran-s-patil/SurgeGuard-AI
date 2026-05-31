// ...existing code...
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [risk, setRisk] = useState(5);
  const [vitals, setVitals] = useState({ hr: 72, bp: "120/80" });
  const [logs, setLogs] = useState([{ time: new Date().toLocaleTimeString(), msg: "Neural Engine Linked. Port 8080 Secured.", type: "info" }]);
  const canvasRef = useRef(null);

  // SHARED demo key string (must match backend SECRET_KEY). In prod keep out of client.
  const SHARED_KEY_STRING = 'SurgeSense_Secure_Key_32_Bytes!!';
  const API_BASE = 'http://127.0.0.1:8080';

  // helpers
  const abToB64 = (ab) => {
    const u8 = new Uint8Array(ab);
    let CHUNK_SZ = 0x8000;
    let index = 0;
    let res = '';
    while (index < u8.length) {
      const slice = u8.subarray(index, Math.min(index + CHUNK_SZ, u8.length));
      res += String.fromCharCode.apply(null, slice);
      index += CHUNK_SZ;
    }
    return btoa(res);
  };

  async function importAesKey(rawKeyString) {
    const enc = new TextEncoder();
    const keyData = enc.encode(rawKeyString); // must be 32 bytes
    return await window.crypto.subtle.importKey(
      "raw",
      keyData,
      { name: "AES-GCM", length: 256 },
      false,
      ["encrypt"]
    );
  }

  async function encryptPayload(obj) {
    const key = await importAesKey(SHARED_KEY_STRING);
    const iv = window.crypto.getRandomValues(new Uint8Array(12)); // recommended 12 bytes
    const enc = new TextEncoder();
    const plaintext = enc.encode(JSON.stringify(obj));
    const ctBuffer = await window.crypto.subtle.encrypt(
      { name: "AES-GCM", iv: iv },
      key,
      plaintext
    );
    // WebCrypto appends the auth tag to ciphertext (last 16 bytes). Split for backend.
    const ct = new Uint8Array(ctBuffer);
    const tagLen = 16;
    const tag = ct.slice(ct.length - tagLen);
    const ciphertext = ct.slice(0, ct.length - tagLen);
    return {
      payload: abToB64(ciphertext.buffer),
      iv: abToB64(iv.buffer),
      tag: abToB64(tag.buffer)
    };
  }

  // EKG animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let x = 0;
    const draw = () => {
      ctx.fillStyle = "rgba(10, 10, 11, 0.05)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = risk > 50 ? "#e74c3c" : "#2ecc71";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x, 30 + Math.sin(x/10) * (risk > 50 ? 30 : 15));
      x = (x + 2) % canvas.width;
      ctx.lineTo(x, 30 + Math.sin(x/10) * (risk > 50 ? 30 : 15));
      ctx.stroke();
      requestAnimationFrame(draw);
    };
    draw();
  }, [risk]);

  async function ensureToken() {
    let token = sessionStorage.getItem('ss_token');
    if (token) return token;
    const resp = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'surgeon01', password: 'password123' })
    });
    if (!resp.ok) throw new Error('Login failed');
    const json = await resp.json();
    token = json.access_token;
    sessionStorage.setItem('ss_token', token);
    return token;
  }

  const triggerAnalysis = async (type) => {
    const mockData = type === 'bleed' ? { hr: 118, bp: 88, note: "bleed" } : { hr: 74, bp: 122 };
    try {
      const token = await ensureToken();
      const enc = await encryptPayload(mockData);
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({
          payload: enc.payload,
          iv: enc.iv,
          tag: enc.tag
        })
      });
      const data = await res.json();
      if (!res.ok) {
        setLogs(prev => [{ time: new Date().toLocaleTimeString(), msg: `[ERR] ${data.error || data.status}`, type: "error" }, ...prev]);
        return;
      }
      setRisk(data.risk * 100);
      setVitals({ hr: mockData.hr, bp: `${mockData.bp}/60` });
      setLogs(prev => [{ time: new Date().toLocaleTimeString(), msg: `[AUTH] HASH_VERIFIED: ${data.integrity_hash}`, type: data.risk > 0.5 ? "warn" : "info" }, ...prev]);
    } catch (e) {
      console.error(e);
      setLogs(prev => [{ time: new Date().toLocaleTimeString(), msg: `[ERR] ${e.message || e}`, type: "error" }, ...prev]);
    }
  };

  return (
    <div className="surgical-dashboard">
      <header className="glass-header">
        <div className="brand">SURGE<span>SENSE</span> <small>v1.0.4-BETA</small></div>
        <div className="system-metrics">
            <span>CPU: 14%</span> <span>LATENCY: 12ms</span> <span className="status-dot"></span>
        </div>
      </header>

      <main className="grid-layout">
        {/* LEFT: LIVE SURGICAL VIEW */}
        <section className="video-section">
          <div className="view-label">PRIMARY LAPAROSCOPIC FEED</div>
          <div className="ai-overlay">
            <div className={`target-box ${risk > 50 ? 'active' : ''}`}></div>
            <div className="scanning-line"></div>
          </div>
          <div className="video-bg"></div>
          <div className="corner-stats">60 FPS | 4K HDR</div>
        </section>

        {/* RIGHT: DATA & ANALYTICS */}
        <aside className="data-section">
          <div className="metric-card">
            <label>INTRAOPERATIVE RISK GAUGE</label>
            <div className={`big-risk ${risk > 50 ? 'pulse' : ''}`}>{risk.toFixed(1)}%</div>
            <progress value={risk} max="100"></progress>
          </div>

          <div className="vitals-grid">
            <div className="vital">
              <label>HEART RATE</label>
              <div className="val">{vitals.hr} <small>BPM</small></div>
              <canvas ref={canvasRef} width="150" height="60"></canvas>
            </div>
            <div className="vital">
              <label>MAP (EST.)</label>
              <div className="val">{vitals.bp}</div>
            </div>
          </div>

          <div className="interaction-panel">
            <button onClick={() => triggerAnalysis('normal')}>BASELINE</button>
            <button className="warn-btn" onClick={() => triggerAnalysis('bleed')}>HEMORRHAGE EVENT</button>
          </div>

          <div className="audit-terminal">
            <div className="term-header">SECURE_ENCLAVE_LOGS</div>
            <div className="term-body">
              {logs.map((l, i) => (
                <div key={i} className={`term-line ${l.type}`}>[{l.time}] {l.msg}</div>
              ))}
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
// ...existing code...
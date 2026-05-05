import { useEffect, useMemo, useRef, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import Hud from './components/hud'
import Cyber from './components/cyber'
import ActionHub from './components/action'
import VideoPicker from './components/video_picker'
import RiskGraph from './components/risk_graph'

function Dashboard() {
  const [connected, setConnected] = useState(false)
  const [attackMode, setAttackMode] = useState(false)
  const [frameData, setFrameData] = useState(null)
  const [history, setHistory] = useState([])
  const [telemetry, setTelemetry] = useState({ hr: [], bp: [], rr: [] })
  const [status, setStatus] = useState('Select a surgical video to stream')
  const [epsilon, setEpsilon] = useState(1.0)
  const [latency, setLatency] = useState(0)
  const [selectedFileName, setSelectedFileName] = useState('')
  const [videoPath, setVideoPath] = useState('')
  const wsRef = useRef(null)

  const riskTimeline = useMemo(() => history.slice(-40), [history])

  useEffect(() => {
    if (!videoPath) {
      return
    }

    const ws = new WebSocket('ws://localhost:8000/ws/stream')
    wsRef.current = ws
    setStatus(`Connecting to backend for ${selectedFileName || 'video'}...`)

    ws.onopen = () => {
      setConnected(true)
      setStatus(`Streaming ${selectedFileName || 'surgical footage'}...`)
      ws.send(JSON.stringify({ video_path: videoPath, attack_mode: attackMode, epsilon }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.error) {
        setStatus(`Error: ${data.error}`)
        return
      }
      setFrameData(data)
      setLatency(data.processing_latency_ms || 0)
      setStatus(data.security_status?.adversarial_attack ? 'ADVERSARIAL ATTACK DETECTED' : 'PROACTIVE MONITORING ACTIVE')
      setHistory((prev) => [...prev, data.risk_score])
      const vitals = data.anonymized_vitals || {}
      setTelemetry((prev) => ({
        hr: [...prev.hr.slice(-25), vitals.heart_rate || 72],
        bp: [...prev.bp.slice(-25), vitals.systolic_bp || 120],
        rr: [...prev.rr.slice(-25), vitals.respiratory_rate || 16],
      }))
    }

    ws.onclose = () => {
      setConnected(false)
      setStatus('Stream disconnected')
    }

    ws.onerror = () => {
      setStatus('WebSocket error')
    }

    return () => ws.close()
  }, [videoPath, attackMode, epsilon, selectedFileName])

  const handleToggleAttack = () => {
    setAttackMode((prev) => !prev)
  }

  const handleUploadComplete = ({ video_path, filename }) => {
    setSelectedFileName(filename)
    setVideoPath(video_path)
    setStatus(`Ready to stream ${filename}`)
  }

  const riskScore = frameData?.risk_score ?? 0
  const centroid = frameData?.centroid ?? [0, 0]
  const securityStatus = frameData?.security_status ?? {}

  return (
    <div className="min-h-screen bg-apollo-light text-slate-900 px-6 py-6">
      <header className="mb-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-500">SurgeGuard-Twin Phase 4</p>
          <h1 className="text-3xl font-semibold text-apollo-teal">SurgeGuard Command Center</h1>
          <p className="mt-2 text-slate-600 max-w-2xl">Integrated surgical video analytics, security telemetry, and live risk visualization for biomedical operations.</p>
        </div>
        <div className="space-y-4 rounded-3xl bg-white p-4 shadow-panel border border-slate-200">
          <div className="text-sm uppercase tracking-[0.18em] text-slate-500">System Status</div>
          <div className="mt-2 text-xl font-bold text-apollo-teal">{status}</div>
          <div className="mt-3 flex items-center gap-3 text-sm text-slate-600">
            <span className={`inline-flex h-3 w-3 rounded-full ${connected ? 'bg-emerald-500' : 'bg-slate-300'}`}></span>
            WebSocket {connected ? 'online' : 'offline'}
          </div>
          <VideoPicker onUpload={handleUploadComplete} />
        </div>
      </header>

      <main className="grid gap-6 xl:grid-cols-[1.8fr_0.9fr]">
        <section className="space-y-6">
          <Hud frameData={frameData} riskTimeline={riskTimeline} centroid={centroid} attackMode={attackMode} />
          <div className="grid gap-6 md:grid-cols-2">
            <Cyber status={securityStatus} epsilon={epsilon} latency={latency} attackMode={attackMode} />
            <ActionHub riskScore={riskScore} attackMode={attackMode} onToggleAttack={handleToggleAttack} />
          </div>
        </section>

        <aside className="space-y-6">
          <RiskGraph history={riskTimeline} />
          <div className="rounded-3xl bg-white p-6 shadow-panel border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Telemetry</p>
                <h2 className="text-xl font-semibold text-apollo-teal">Vitals Trajectory</h2>
              </div>
              <span className="rounded-full bg-apollo-teal/10 px-3 py-1 text-sm text-apollo-teal">ε = {epsilon}</span>
            </div>
            <div className="space-y-4">
              <div className="rounded-3xl bg-apollo-light p-4">
                <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
                  <span>Heart Rate</span>
                  <strong>{telemetry.hr.slice(-1)[0] ?? 72} bpm</strong>
                </div>
                <div className="h-20 rounded-2xl bg-white border border-slate-200"></div>
              </div>
              <div className="rounded-3xl bg-apollo-light p-4">
                <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
                  <span>Blood Pressure</span>
                  <strong>{telemetry.bp.slice(-1)[0] ?? 120}/80</strong>
                </div>
                <div className="h-20 rounded-2xl bg-white border border-slate-200"></div>
              </div>
              <div className="rounded-3xl bg-apollo-light p-4">
                <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
                  <span>Respiratory Rate</span>
                  <strong>{telemetry.rr.slice(-1)[0] ?? 16} rpm</strong>
                </div>
                <div className="h-20 rounded-2xl bg-white border border-slate-200"></div>
              </div>
            </div>
          </div>
        </aside>
      </main>
    </div>
  )
}

function Settings() {
  return (
    <div className="min-h-screen bg-apollo-light text-slate-900 px-6 py-6">
      <h1 className="text-3xl font-semibold text-apollo-teal">Settings</h1>
      <p>Configure system parameters here.</p>
    </div>
  )
}

function App() {
  return (
    <Router>
      <nav className="bg-white shadow-panel border-b border-slate-200 px-6 py-4">
        <div className="flex gap-6">
          <Link to="/" className="text-apollo-teal font-semibold">Dashboard</Link>
          <Link to="/settings" className="text-slate-600">Settings</Link>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Router>
  )
}

export default App

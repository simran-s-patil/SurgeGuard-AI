import { useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Shield, AlertTriangle, Monitor, LogOut, ChevronRight } from 'lucide-react'
import Hud from './components/hud'
import ActionHub from './components/action'
import VideoPicker from './components/video_picker'
import RiskGraph from './components/risk_graph'
import Login from './components/login'
import NotificationContainer from './components/notification'

function Dashboard() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [connected, setConnected] = useState(false)
  const [attackMode, setAttackMode] = useState(false)
  const [frameData, setFrameData] = useState(null)
  const [history, setHistory] = useState([])
  const [telemetry, setTelemetry] = useState({ hr: [], bp: [], rr: [] })
  const [status, setStatus] = useState('Standby - Waiting for Feed')
  const [epsilon, setEpsilon] = useState(0.1)
  const [latency, setLatency] = useState(0)
  const [selectedFileName, setSelectedFileName] = useState('')
  const [videoPath, setVideoPath] = useState('')
  const [notifications, setNotifications] = useState([])
  const wsRef = useRef(null)

  const riskTimeline = useMemo(() => history.slice(-40), [history])

  useEffect(() => {
    if (!videoPath || !isLoggedIn) return

    const ws = new WebSocket('ws://localhost:8000/ws/stream')
    wsRef.current = ws
    setStatus(`Initializing Link: ${selectedFileName}...`)

    ws.onopen = () => {
      setConnected(true)
      setStatus(`LIVE FOOTAGE: ${selectedFileName}`)
      ws.send(JSON.stringify({ video_path: videoPath, attack_mode: attackMode, epsilon }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.error) {
        setStatus(`System Fault: ${data.error}`)
        return
      }
      setFrameData(data)
      setLatency(data.processing_latency_ms || 0)
      
      if (data.security_status?.adversarial_attack) {
        setStatus('CRITICAL: ADVERSARIAL INTERFERENCE')
        addNotification('error', 'Adversarial attack detected! System integrity compromised.')
      } else {
        setStatus(`STABLE // ${selectedFileName}`)
      }

      if (data.is_bleeding && !frameData?.is_bleeding) {
        addNotification('warning', 'Occult bleeding detected! Immediate medical attention required.')
        playBuzzer()
      }

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
      setStatus('Feed Disconnected')
    }

    ws.onerror = () => setStatus('Neural Link Fault')

    return () => ws.close()
  }, [videoPath, attackMode, epsilon, selectedFileName, isLoggedIn])

  const playBuzzer = () => {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const oscillator = audioCtx.createOscillator()
      const gainNode = audioCtx.createGain()

      oscillator.type = 'sawtooth' // Harsh buzzer sound
      oscillator.frequency.setValueAtTime(440, audioCtx.currentTime)
      
      gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5)

      oscillator.connect(gainNode)
      gainNode.connect(audioCtx.destination)

      oscillator.start()
      oscillator.stop(audioCtx.currentTime + 0.5)
    } catch (e) {
      console.error('Buzzer failed:', e)
    }
  }

  const handleUploadComplete = ({ video_path, filename }) => {
    setSelectedFileName(filename)
    setVideoPath(video_path)
    addNotification('success', `Video feed "${filename}" successfully loaded and synchronized.`)
  }

  const addNotification = (type, message) => {
    const id = Date.now()
    setNotifications(prev => [...prev, { id, type, message }])
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id))
    }, 5000)
  }

  const closeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  if (!isLoggedIn) {
    return <Login onLogin={setIsLoggedIn} />
  }

  return (
    <div className="min-h-screen p-6 lg:p-8 max-w-[1600px] mx-auto overflow-hidden">
      {/* Dynamic Header */}
      <header className="mb-6 lg:mb-8 flex flex-col lg:flex-row lg:items-end justify-between gap-4 lg:gap-6">
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="flex items-center gap-3 text-cyan-400 mb-2">
            <Activity size={20} className="animate-pulse" />
            <span className="text-[10px] uppercase tracking-[0.4em] font-bold">SurgeGuard Command v4.0</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-glow font-outfit">Operation<span className="text-cyan-400">Intelligence</span></h1>
          <p className="mt-2 text-slate-400 max-w-xl text-sm leading-relaxed">
            Real-time neural segmentation and cryptographic integrity monitoring for surgical environments.
          </p>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card px-8 py-5 flex items-center gap-10"
        >
          <div className="space-y-1">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Mainframe Status</p>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-slate-600'}`}></div>
              <span className={`text-sm font-bold ${connected ? 'text-emerald-400' : 'text-slate-400'}`}>
                {connected ? 'ONLINE' : 'STBY'}
              </span>
            </div>
          </div>
          <div className="w-px h-10 bg-white/10"></div>
          <div className="space-y-1">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Latency</p>
            <p className="text-sm font-mono font-bold text-cyan-400">{latency}ms</p>
          </div>
          <button 
            onClick={() => setIsLoggedIn(false)}
            className="ml-4 p-2 rounded-full hover:bg-white/10 transition-colors text-slate-400 hover:text-white"
          >
            <LogOut size={20} />
          </button>
        </motion.div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_400px] gap-6 lg:gap-8">
        
        {/* Left Column: Primary Feed & Security */}
        <div className="space-y-8 min-w-0">
          <Hud 
            frameData={frameData} 
            riskTimeline={riskTimeline} 
            centroid={frameData?.centroid ?? [0,0]} 
            attackMode={attackMode} 
          />
          
          <div className="grid grid-cols-1 gap-8">
            <ActionHub 
              attackMode={attackMode} 
              onToggleAttack={() => setAttackMode(!attackMode)}
              epsilon={epsilon}
              setEpsilon={setEpsilon}
              status={status}
              onUpload={handleUploadComplete}
            />
          </div>
        </div>

        {/* Right Column: Telemetry & Analytics */}
        <aside className="space-y-8">
          <div className="glass-panel p-6 space-y-6 overflow-hidden">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">Biological Telemetry</h3>
              <Activity size={16} className="text-cyan-500" />
            </div>
            <RiskGraph history={history} />
          </div>

          <div className="glass-panel p-6 space-y-6">
            <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">Session Controls</h3>
            <VideoPicker onUpload={handleUploadComplete} />
            
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-between hover:bg-white/10 transition-colors cursor-pointer group">
                <div className="flex items-center gap-3">
                  <Shield size={18} className="text-emerald-400 group-hover:scale-110 transition-transform" />
                  <span className="text-xs font-medium">Auto-Encryption</span>
                </div>
                <div className="w-10 h-5 bg-emerald-500/20 rounded-full relative p-1">
                   <div className="w-3 h-3 bg-emerald-500 rounded-full ml-auto"></div>
                </div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center justify-between hover:bg-white/10 transition-colors cursor-pointer group">
                <div className="flex items-center gap-3">
                  <Monitor size={18} className="text-cyan-400 group-hover:scale-110 transition-transform" />
                  <span className="text-xs font-medium">Neural Upscaling</span>
                </div>
                <div className="w-10 h-5 bg-cyan-500/20 rounded-full relative p-1">
                   <div className="w-3 h-3 bg-cyan-500 rounded-full ml-auto"></div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
      
      {/* Notifications */}
      <NotificationContainer notifications={notifications} onClose={closeNotification} />
      
      {/* Background Decor */}
      <div className="fixed top-0 right-0 w-full h-full pointer-events-none -z-10 opacity-30">
        <div className="absolute top-[10%] right-[10%] w-[500px] h-[500px] bg-apollo-teal/20 rounded-full blur-[150px]"></div>
        <div className="absolute bottom-[20%] left-[5%] w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[120px]"></div>
      </div>
    </div>
  )
}

export default Dashboard

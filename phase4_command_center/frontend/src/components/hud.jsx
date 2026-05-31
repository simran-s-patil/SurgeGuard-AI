import { useState } from 'react'
import { motion } from 'framer-motion'
import { Video, Target, Activity, AlertCircle, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react'

const Hud = ({ frameData, riskTimeline, centroid, attackMode }) => {
  const imageSrc = frameData?.frame_base64 ? `data:image/jpeg;base64,${frameData.frame_base64}` : undefined
  const riskScore = (frameData?.risk_score ?? 0) * 100
  const isBleeding = frameData?.is_bleeding ?? false
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })

  return (
    <div className="glass-panel p-6 relative overflow-hidden">
      <div className="scanline"></div>
      
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-cyan-500/10 rounded-2xl border border-cyan-500/20">
            <Video className="text-cyan-400" size={24} />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-slate-500 font-bold">Neural Stream 01</p>
            <h2 className="text-xl font-bold tracking-tight text-glow">Live Procedural Feed</h2>
          </div>
        </div>
        
        <div className={`inline-flex items-center gap-3 rounded-full px-5 py-2 text-xs font-bold border transition-colors ${
          attackMode 
            ? 'bg-red-500/10 border-red-500/30 text-red-400' 
            : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
        }`}>
          <div className={`w-1.5 h-1.5 rounded-full ${attackMode ? 'bg-red-500' : 'bg-emerald-500'} animate-pulse`}></div>
          {attackMode ? 'INTERFERENCE DETECTED' : 'SYSTEM SECURE'}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_280px]">
        <div className="relative aspect-video rounded-3xl overflow-hidden border border-white/10 bg-slate-900 shadow-inner group">
          {imageSrc ? (
            <motion.img 
              src={imageSrc} 
              alt="surgery frame" 
              className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.02]" 
              style={{ 
                transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
                transformOrigin: 'center'
              }}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-4">
              <Activity className="animate-spin text-cyan-500/50" size={48} />
              <p className="text-xs uppercase tracking-widest font-medium">Synchronizing Neural Link...</p>
            </div>
          )}

          {/* Zoom Controls */}
          {imageSrc && (
            <div className="absolute top-4 right-4 flex flex-col gap-2">
              <button 
                onClick={() => setZoom(prev => Math.min(prev + 0.2, 3))}
                className="p-2 rounded-xl bg-black/50 backdrop-blur-sm border border-white/20 text-white hover:bg-black/70 transition-colors"
              >
                <ZoomIn size={16} />
              </button>
              <button 
                onClick={() => setZoom(prev => Math.max(prev - 0.2, 0.5))}
                className="p-2 rounded-xl bg-black/50 backdrop-blur-sm border border-white/20 text-white hover:bg-black/70 transition-colors"
              >
                <ZoomOut size={16} />
              </button>
              <button 
                onClick={() => {
                  setZoom(1)
                  setPan({ x: 0, y: 0 })
                }}
                className="p-2 rounded-xl bg-black/50 backdrop-blur-sm border border-white/20 text-white hover:bg-black/70 transition-colors"
              >
                <RotateCcw size={16} />
              </button>
            </div>
          )}

          {/* HUD Overlays */}
          <div className="absolute inset-0 pointer-events-none p-6">
             {/* Reticle UI */}
             <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-20 border border-cyan-500/40 rounded-full w-40 h-40 flex items-center justify-center">
                <div className="border-t-2 border-cyan-500 w-full h-0"></div>
                <div className="border-l-2 border-cyan-500 h-full w-0 absolute"></div>
             </div>

             <div className="absolute left-6 top-6 flex flex-col gap-3">
                <div className="glass-card px-4 py-2 flex items-center gap-3">
                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Bleed Risk</span>
                  <span className={`text-sm font-mono font-bold ${riskScore > 50 ? 'text-red-400' : 'text-cyan-400'}`}>
                    {riskScore.toFixed(1)}%
                  </span>
                </div>
                <div className="glass-card px-4 py-2 flex items-center gap-3">
                  <Target size={14} className="text-cyan-400" />
                  <span className="text-[10px] font-mono text-slate-300">
                    X: {centroid[0].toFixed(0)} Y: {centroid[1].toFixed(0)}
                  </span>
                </div>
             </div>

             {isBleeding && (
               <motion.div 
                 initial={{ opacity: 0, scale: 0.9 }}
                 animate={{ opacity: 1, scale: 1 }}
                 className="absolute bottom-6 left-6 glass-card bg-red-500/20 border-red-500/40 px-5 py-3 flex items-center gap-3"
               >
                 <AlertCircle size={20} className="text-red-400 animate-bounce" />
                 <span className="text-xs font-bold text-red-200 uppercase tracking-widest">Occult Bleed Alert</span>
               </motion.div>
             )}
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <div className="glass-card p-5 space-y-4">
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500">Analysis Summary</h3>
            <div className="space-y-4 text-xs">
              <div className="flex justify-between items-center text-slate-400">
                <span>Confidence</span>
                <span className="text-cyan-400 font-mono font-bold">HIGH</span>
              </div>
              <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                <motion.div 
                  className="bg-cyan-500 h-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${riskScore}%` }}
                />
              </div>
              <div className="flex justify-between items-center text-slate-400 pt-2 border-t border-white/5">
                <span>Morphology</span>
                <span className="text-white font-bold">{isBleeding ? 'ACTIVE' : 'STABLE'}</span>
              </div>
            </div>
          </div>

          <div className="glass-card p-5 flex-1 relative overflow-hidden group">
            <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-500 mb-4">Neural Attention Map</h3>
            <div className="h-32 rounded-2xl overflow-hidden bg-slate-900 border border-white/5 flex items-center justify-center">
               {frameData?.heatmap_base64 ? (
                 <img 
                   src={`data:image/jpeg;base64,${frameData.heatmap_base64}`} 
                   alt="attention map" 
                   className="h-full w-full object-cover"
                 />
               ) : (
                 <Activity className="text-cyan-500/20 animate-pulse" size={32} />
               )}
            </div>
            <p className="mt-4 text-[10px] text-slate-500 leading-relaxed uppercase tracking-tighter">
              Visualizing final layer feature weights using Grad-CAM.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Hud

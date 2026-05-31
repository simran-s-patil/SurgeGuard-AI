import { motion } from 'framer-motion'
import { Heart, Droplets, Wind } from 'lucide-react'

const VitalsPanel = ({ telemetry }) => {
  const latestHR = telemetry.hr[telemetry.hr.length - 1] || '--'
  const latestBP = telemetry.bp[telemetry.bp.length - 1] || '--'
  const latestRR = telemetry.rr[telemetry.rr.length - 1] || '--'

  const renderSparkline = (data, color) => (
    <div className="h-8 flex items-end gap-0.5">
      {data.map((val, i) => (
        <div 
          key={i} 
          className={`w-1 rounded-full ${color}`} 
          style={{ height: `${Math.min((val / 200) * 100, 100)}%`, opacity: 0.2 + (i / data.length) * 0.8 }}
        ></div>
      ))}
    </div>
  )

  return (
    <div className="glass-panel p-6 space-y-6">
      <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">Live Clinical Vitals</h3>
      
      <div className="space-y-4">
        {/* Heart Rate */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400 group-hover:scale-110 transition-transform">
              <Heart size={16} fill="currentColor" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-500">Heart Rate</p>
              <p className="text-xl font-bold font-mono text-white">{latestHR}<span className="text-[10px] ml-1 text-slate-500">BPM</span></p>
            </div>
          </div>
          {renderSparkline(telemetry.hr, 'bg-red-500')}
        </div>

        {/* Blood Pressure */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:scale-110 transition-transform">
              <Droplets size={16} fill="currentColor" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-500">Systolic BP</p>
              <p className="text-xl font-bold font-mono text-white">{latestBP}<span className="text-[10px] ml-1 text-slate-500">mmHg</span></p>
            </div>
          </div>
          {renderSparkline(telemetry.bp, 'bg-cyan-500')}
        </div>

        {/* Resp Rate */}
        <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-all group">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 group-hover:scale-110 transition-transform">
              <Wind size={16} />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-500">Resp. Rate</p>
              <p className="text-xl font-bold font-mono text-white">{latestRR}<span className="text-[10px] ml-1 text-slate-500">BrPM</span></p>
            </div>
          </div>
          {renderSparkline(telemetry.rr, 'bg-emerald-500')}
        </div>
      </div>
    </div>
  )
}

export default VitalsPanel

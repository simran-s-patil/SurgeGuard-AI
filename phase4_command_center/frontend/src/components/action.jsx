import { AlertTriangle, Upload, Zap, Eye, EyeOff } from 'lucide-react'

const ActionHub = ({ attackMode, onToggleAttack, epsilon, setEpsilon, status, onUpload }) => {
  return (
    <div className="glass-panel p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">Operation Control</h3>
          <Zap size={16} className="text-amber-400" />
        </div>

        <div className="space-y-6">
          <div className="p-5 rounded-2xl bg-white/5 border border-white/5">
             <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] uppercase font-bold tracking-widest text-slate-500">System Log</span>
                <div className="flex gap-1">
                   <div className="w-1 h-1 rounded-full bg-cyan-500"></div>
                   <div className="w-1 h-1 rounded-full bg-cyan-500/50"></div>
                   <div className="w-1 h-1 rounded-full bg-cyan-500/20"></div>
                </div>
             </div>
             <p className={`text-sm font-bold tracking-tight leading-tight ${status.includes('CRITICAL') ? 'text-red-400' : 'text-cyan-400'}`}>
                {status}
             </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold tracking-widest text-slate-500">Adversarial Bias</span>
              <span className="text-[10px] font-mono text-cyan-400 font-bold">ε = {epsilon.toFixed(2)}</span>
            </div>
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.05" 
              value={epsilon} 
              onChange={(e) => setEpsilon(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
          </div>
        </div>
      </div>

      <div className="flex gap-4 mt-8">
        <button 
          onClick={onToggleAttack}
          className={`flex-1 py-4 rounded-2xl font-bold text-xs uppercase tracking-widest transition-all flex items-center justify-center gap-2 border ${
            attackMode 
              ? 'bg-red-500/20 border-red-500/40 text-red-400 hover:bg-red-500/30' 
              : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10'
          }`}
        >
          {attackMode ? <Eye size={16} /> : <EyeOff size={16} />}
          {attackMode ? 'Deactivate Attack' : 'Simulate Attack'}
        </button>
        
        <label className="p-4 rounded-2xl bg-cyan-600 hover:bg-cyan-500 text-white transition-all cursor-pointer shadow-lg shadow-cyan-900/20">
          <Upload size={20} />
          <input 
            type="file" 
            className="hidden" 
            accept="video/*"
            onChange={async (e) => {
              const file = e.target.files[0]
              if (!file) return
              const formData = new FormData()
              formData.append('file', file)
              const res = await fetch('http://localhost:8000/upload/video', {
                method: 'POST',
                body: formData
              })
              const data = await res.json()
              onUpload(data)
              // Success notification will be handled by parent
            }}
          />
        </label>
      </div>
    </div>
  )
}

export default ActionHub

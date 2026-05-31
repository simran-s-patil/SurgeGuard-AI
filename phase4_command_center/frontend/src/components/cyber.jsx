import { Shield, Fingerprint, Lock, ShieldAlert } from 'lucide-react'

const Cyber = ({ data, attackMode }) => {
  const isAuthentic = data?.integrity_score === 100 && !attackMode
  const sig = data?.signature ? `${data.signature.substring(0, 16)}...` : 'PENDING'

  return (
    <div className="glass-panel p-6 relative overflow-hidden group">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl border ${isAuthentic ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
            <Shield size={20} className={isAuthentic ? '' : 'animate-pulse'} />
          </div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-slate-400">Cyber-Shield Telemetry</h3>
        </div>
        <span className="text-[10px] font-mono text-slate-500">Node: SG-ALPHA-09</span>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Integrity Index</p>
            <p className={`text-2xl font-bold font-mono ${isAuthentic ? 'text-emerald-400' : 'text-red-400'}`}>
              {isAuthentic ? '100.0' : '0.00'}
            </p>
          </div>
          <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Watermark</p>
            <p className="text-sm font-bold text-slate-300">
              {isAuthentic ? 'AUTHENTIC' : 'CORRUPTED'}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-500 font-bold">
            <span>Signature Hash (HMAC-SHA256)</span>
            <Lock size={12} />
          </div>
          <div className="p-4 rounded-2xl bg-slate-900/50 border border-white/10 font-mono text-[10px] text-cyan-400/70 break-all leading-relaxed">
            {sig}
          </div>
        </div>

        <div className={`p-4 rounded-2xl border transition-all ${
          isAuthentic 
            ? 'bg-emerald-500/5 border-emerald-500/10' 
            : 'bg-red-500/10 border-red-500/20'
        }`}>
          <div className="flex items-center gap-3">
            {isAuthentic ? (
              <Fingerprint size={16} className="text-emerald-400" />
            ) : (
              <ShieldAlert size={16} className="text-red-400" />
            )}
            <p className="text-[10px] uppercase tracking-widest font-bold leading-none">
              {isAuthentic ? 'Source Verified: Encrypted Tunnel Active' : 'CRITICAL: Data Stream Compromised'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Cyber

import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const RiskGraph = ({ history }) => {
  const points = history.slice(-30)
  const currentRisk = points[points.length - 1] || 0
  const previousRisk = points[points.length - 2] || 0
  const trend = currentRisk > previousRisk ? 'up' : currentRisk < previousRisk ? 'down' : 'stable'
  
  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp size={12} className="text-red-400" />
      case 'down': return <TrendingDown size={12} className="text-emerald-400" />
      default: return <Minus size={12} className="text-slate-400" />
    }
  }

  const getRiskLevel = (val) => {
    if (val > 0.7) return 'CRITICAL'
    if (val > 0.4) return 'HIGH'
    if (val > 0.2) return 'MODERATE'
    return 'LOW'
  }

  const getRiskColor = (val) => {
    if (val > 0.7) return 'text-red-400'
    if (val > 0.4) return 'text-amber-400'
    return 'text-cyan-400'
  }

  return (
    <div className="space-y-4">
      {/* Current Risk Summary */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Current Risk</span>
          {getTrendIcon()}
        </div>
        <div className="text-right">
          <p className={`text-lg font-bold font-mono ${getRiskColor(currentRisk)}`}>
            {(currentRisk * 100).toFixed(1)}%
          </p>
          <p className={`text-[10px] uppercase tracking-widest font-bold ${getRiskColor(currentRisk)}`}>
            {getRiskLevel(currentRisk)}
          </p>
        </div>
      </div>

      {/* Risk Thresholds */}
      <div className="flex justify-between text-[9px] uppercase tracking-widest text-slate-600 font-bold">
        <span>0%</span>
        <span className="text-amber-500/70">40%</span>
        <span className="text-red-500/70">70%</span>
        <span>100%</span>
      </div>

      {/* Graph */}
      <div className="h-32 flex items-end gap-0.5 px-1 relative">
        {/* Threshold Lines */}
        <div className="absolute top-0 left-0 right-0 h-px bg-amber-500/30" style={{ top: '40%' }}></div>
        <div className="absolute top-0 left-0 right-0 h-px bg-red-500/30" style={{ top: '30%' }}></div>

        {points.length === 0 && (
          <div className="w-full h-full flex items-center justify-center text-[10px] uppercase tracking-widest text-slate-700 font-bold">
            No Data Streamed
          </div>
        )}
        {points.map((val, i) => (
          <motion.div
            key={i}
            initial={{ height: 0 }}
            animate={{ height: `${Math.max(val * 100, 2)}%` }}
            transition={{ delay: i * 0.02 }}
            className={`flex-1 rounded-t-sm transition-all duration-300 hover:scale-110 ${
              val > 0.7 
                ? 'bg-gradient-to-t from-red-500/60 to-red-400 shadow-red-500/20' 
                : val > 0.4
                  ? 'bg-gradient-to-t from-amber-500/60 to-amber-400 shadow-amber-500/20'
                  : 'bg-gradient-to-t from-cyan-500/60 to-cyan-400 shadow-cyan-500/20'
            } shadow-sm`}
            style={{
              opacity: 0.4 + (i / points.length) * 0.6,
              boxShadow: val > 0.7 ? '0 0 8px rgba(239, 68, 68, 0.3)' : 
                        val > 0.4 ? '0 0 8px rgba(245, 158, 11, 0.3)' : '0 0 8px rgba(34, 211, 238, 0.3)'
            }}
            title={`Risk: ${(val * 100).toFixed(1)}%`}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-4 text-[9px] uppercase tracking-widest font-bold">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-cyan-500/60"></div>
          <span className="text-slate-500">Low</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-amber-500/60"></div>
          <span className="text-slate-500">Moderate</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-red-500/60"></div>
          <span className="text-slate-500">Critical</span>
        </div>
      </div>
    </div>
  )
}

export default RiskGraph

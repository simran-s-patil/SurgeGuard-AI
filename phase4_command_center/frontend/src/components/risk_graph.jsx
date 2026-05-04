const RiskGraph = ({ history }) => {
  const normalized = history.map((value) => Math.max(0, Math.min(1, value)))
  const points = normalized.map((value, index) => `${(index / Math.max(normalized.length - 1, 1)) * 300},${110 - value * 90}`).join(' ')
  const latest = normalized[normalized.length - 1] ?? 0
  const average = normalized.length ? normalized.reduce((sum, value) => sum + value, 0) / normalized.length : 0

  return (
    <div className="rounded-[2rem] bg-white p-6 shadow-panel border border-slate-200">
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Live Risk Graph</p>
          <h2 className="text-xl font-semibold text-apollo-teal">Risk Trend</h2>
        </div>
        <div className="rounded-full bg-apollo-yellow/10 px-3 py-1 text-sm font-semibold text-apollo-teal">Live</div>
      </div>

      <div className="mb-5 flex items-end gap-4">
        <div className="flex-1">
          <div className="text-5xl font-semibold text-slate-900">{(latest * 100).toFixed(1)}%</div>
          <div className="text-sm text-slate-500">Latest risk score</div>
        </div>
        <div className="rounded-3xl bg-apollo-light p-4 text-right">
          <div className="text-sm uppercase tracking-[0.24em] text-slate-500">Average</div>
          <div className="mt-2 text-2xl font-semibold text-slate-900">{(average * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="rounded-[2rem] bg-apollo-light p-4">
        <svg viewBox="0 0 300 120" className="w-full h-40">
          <defs>
            <linearGradient id="risk-gradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#0f5e5f" />
              <stop offset="100%" stopColor="#d72f2f" />
            </linearGradient>
          </defs>
          <polyline
            fill="none"
            stroke="url(#risk-gradient)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />
        </svg>
      </div>
    </div>
  )
}

export default RiskGraph

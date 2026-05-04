const ActionHub = ({ riskScore, attackMode, onToggleAttack }) => {
  const gaugeFill = Math.min(100, Math.max(0, riskScore * 120))
  return (
    <div className="rounded-[2rem] bg-white p-6 shadow-panel border border-slate-200">
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Response Control</p>
          <h2 className="text-xl font-semibold text-apollo-teal">Action Hub</h2>
        </div>
        <button
          onClick={onToggleAttack}
          className={`inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-semibold transition ${attackMode ? 'bg-apollo-success text-white' : 'bg-apollo-warn text-white'}`}
        >
          {attackMode ? 'Disable Hacker Demo' : 'Enable Hacker Demo'}
        </button>
      </div>

      <div className="space-y-6">
        <div className="rounded-[2rem] bg-apollo-light p-5 border border-slate-200">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Bleed Gauge</p>
          <div className="mt-4 flex items-end gap-4">
            <div className="h-28 w-20 overflow-hidden rounded-[1.5rem] bg-white shadow-inner border border-slate-200">
              <div className="bg-apollo-warn" style={{ height: `${gaugeFill}%`, transition: 'height 0.3s ease' }} />
            </div>
            <div>
              <div className="text-4xl font-semibold text-slate-900">{(riskScore * 100).toFixed(1)}%</div>
              <div className="mt-2 text-sm text-slate-600">Current bleed risk index</div>
            </div>
          </div>
        </div>

        <div className="rounded-[2rem] bg-apollo-light p-5 border border-slate-200">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Procedure Priority</p>
          <div className="mt-4 grid gap-3">
            <div className="rounded-3xl bg-white p-4 border border-slate-200">
              <div className="text-sm text-slate-500">Surgeon Alert</div>
              <div className="mt-2 font-semibold text-slate-900">{riskScore > 0.7 ? 'Immediate intervention' : 'Monitor closely'}</div>
            </div>
            <div className="rounded-3xl bg-white p-4 border border-slate-200">
              <div className="text-sm text-slate-500">Adaptive Shield</div>
              <div className="mt-2 font-semibold text-slate-900">{attackMode ? 'Reinforced denoise' : 'Standard protection'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ActionHub

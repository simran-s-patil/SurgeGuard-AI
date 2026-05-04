const Hud = ({ frameData, riskTimeline, centroid, attackMode }) => {
  const imageSrc = frameData?.frame_base64 ? `data:image/jpeg;base64,${frameData.frame_base64}` : undefined
  const riskScore = frameData?.risk_score ?? 0
  const isBleeding = frameData?.is_bleeding ?? false

  return (
    <div className="rounded-[2rem] bg-white p-6 shadow-panel border border-slate-200">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.22em] text-slate-500">Surgical Video Feed</p>
          <h2 className="text-2xl font-semibold text-apollo-teal">Live Procedural HUD</h2>
        </div>
        <div className="inline-flex items-center gap-3 rounded-full bg-apollo-light px-4 py-3 text-sm text-slate-600">
          <span className={`inline-flex h-2.5 w-2.5 rounded-full ${attackMode ? 'bg-apollo-warn' : 'bg-apollo-success'}`}></span>
          {attackMode ? 'Hacker Demo Mode' : 'Operational Safe Mode'}
        </div>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.55fr_0.45fr]">
        <div className="aspect-[16/10] overflow-hidden rounded-[2rem] border border-slate-200 bg-slate-100 relative">
          {imageSrc ? (
            <img src={imageSrc} alt="surgery frame" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-slate-500">Waiting for frame</div>
          )}
          <div className="absolute left-6 top-6 rounded-3xl bg-black/40 px-4 py-3 text-sm text-white backdrop-blur-sm">
            Risk: <span className="font-semibold">{(riskScore * 100).toFixed(1)}%</span>
          </div>
          <div className="absolute bottom-6 left-6 rounded-3xl bg-white/90 px-4 py-3 text-sm text-slate-700 shadow-xl">
            {isBleeding ? 'Bleeding event detected' : 'No bleeding detected'}
          </div>
          <div className="absolute right-6 top-6 rounded-full border border-white/60 bg-white/85 px-3 py-2 text-xs text-slate-700">
            Centroid: {centroid[0].toFixed(1)}, {centroid[1].toFixed(1)}
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-[2rem] bg-apollo-light p-5 border border-slate-200">
            <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Event Summary</p>
            <div className="mt-4 space-y-3 text-sm text-slate-700">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <span>Current Score</span>
                <strong>{(riskScore * 100).toFixed(1)}%</strong>
              </div>
              <div className="flex items-center justify-between border-b border-slate-200 pb-3 pt-3">
                <span>Bleeding Status</span>
                <strong>{isBleeding ? 'Critical' : 'Normal'}</strong>
              </div>
              <div className="pt-3 flex items-center justify-between">
                <span>Temporal Trend</span>
                <strong>{riskTimeline.length > 0 ? (riskTimeline[riskTimeline.length - 1] > riskTimeline[Math.max(0, riskTimeline.length - 2)] ? 'Growing' : 'Stable') : 'Pending'}</strong>
              </div>
            </div>
          </div>

          <div className="rounded-[2rem] bg-apollo-light p-5 border border-slate-200">
            <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Heatmap Overlay</p>
            <div className="mt-4 h-40 rounded-[1.5rem] bg-gradient-to-br from-apollo-yellow/20 via-apollo-warn/10 to-transparent"></div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Hud

const Cyber = ({ status, epsilon, latency, attackMode }) => {
  const vaultState = status.frame_hash ? 'Vault sealed' : 'No hash reported'
  const alertState = status.denoising_alert ? 'Denoising triggered' : 'Nominal'

  return (
    <div className="rounded-[2rem] bg-white p-6 shadow-panel border border-slate-200">
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Cyber Defense</p>
          <h2 className="text-xl font-semibold text-apollo-teal">Security Vault</h2>
        </div>
        <div className={`rounded-full px-3 py-1 text-sm font-medium ${attackMode ? 'bg-apollo-warn/10 text-apollo-warn' : 'bg-apollo-success/10 text-apollo-success'}`}>
          {attackMode ? 'Under Attack' : 'Secure'}
        </div>
      </div>

      <div className="space-y-4">
        <div className="rounded-3xl bg-apollo-light p-4 border border-slate-200">
          <div className="text-sm text-slate-500">Frame Hash</div>
          <div className="mt-2 break-all text-sm font-semibold text-slate-800">{status.frame_hash ?? 'pending...'}</div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-3xl bg-apollo-light p-4 border border-slate-200">
            <div className="text-sm text-slate-500">Integrity Check</div>
            <div className="mt-2 font-semibold text-slate-900">{vaultState}</div>
          </div>
          <div className="rounded-3xl bg-apollo-light p-4 border border-slate-200">
            <div className="text-sm text-slate-500">Attack Control</div>
            <div className="mt-2 font-semibold text-slate-900">{alertState}</div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-3xl bg-apollo-light p-4 border border-slate-200">
            <div className="text-sm text-slate-500">Processing Latency</div>
            <div className="mt-2 font-semibold text-slate-900">{latency.toFixed(0)} ms</div>
          </div>
          <div className="rounded-3xl bg-apollo-light p-4 border border-slate-200">
            <div className="text-sm text-slate-500">Adversarial Strength</div>
            <div className="mt-2 font-semibold text-slate-900">ε = {epsilon.toFixed(2)}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Cyber

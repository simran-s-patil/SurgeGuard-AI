import { useState } from 'react'

const VideoPicker = ({ onUpload }) => {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }
    setUploading(true)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/upload/video', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const data = await response.json()
      onUpload(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="rounded-3xl bg-white p-4 shadow-panel border border-slate-200">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.22em] text-slate-500">Video Selector</p>
          <h3 className="text-lg font-semibold text-slate-900">Upload surgical footage</h3>
        </div>
        <label className="cursor-pointer rounded-full bg-apollo-teal px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-700">
          {uploading ? 'Uploading...' : 'Choose file'}
          <input type="file" accept="video/*" className="hidden" onChange={handleFileChange} disabled={uploading} />
        </label>
      </div>
      {error && <div className="mt-3 rounded-3xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
    </div>
  )
}

export default VideoPicker

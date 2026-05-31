import { useState } from 'react'
import { Upload, FileVideo, AlertCircle, CheckCircle2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const VideoPicker = ({ onUpload }) => {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    
    setUploading(true)
    setError('')
    setSuccess(false)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://127.0.0.1:8000/upload/video', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error(`Link Fault: ${response.statusText}`)

      const data = await response.json()
      setSuccess(true)
      setTimeout(() => {
        onUpload(data)
        setSuccess(false)
      }, 1000)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <label className={`relative block group cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed transition-all p-6 ${
        uploading ? 'border-cyan-500/50 bg-cyan-500/5' : 
        success ? 'border-emerald-500/50 bg-emerald-500/5' :
        'border-white/10 hover:border-white/20 bg-white/5'
      }`}>
        <input type="file" accept="video/*" className="hidden" onChange={handleFileChange} disabled={uploading} />
        
        <div className="flex flex-col items-center text-center gap-3">
          <AnimatePresence mode="wait">
            {uploading ? (
              <motion.div 
                key="uploading"
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
              >
                <Upload className="text-cyan-400" size={24} />
              </motion.div>
            ) : success ? (
              <motion.div key="success" initial={{ scale: 0.5 }} animate={{ scale: 1 }}>
                <CheckCircle2 className="text-emerald-400" size={24} />
              </motion.div>
            ) : (
              <motion.div key="idle" className="group-hover:translate-y-[-2px] transition-transform">
                <FileVideo className="text-slate-500 group-hover:text-cyan-400" size={24} />
              </motion.div>
            )}
          </AnimatePresence>
          
          <div className="space-y-1">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-300">
              {uploading ? 'Transmitting Data...' : success ? 'Source Verified' : 'Ingest Surgical Feed'}
            </p>
            <p className="text-[10px] text-slate-500 uppercase tracking-tighter">MP4, AVI, or MKV Source Files</p>
          </div>
        </div>
      </label>

      {error && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-[10px] font-bold uppercase tracking-wider"
        >
          <AlertCircle size={14} />
          {error}
        </motion.div>
      )}
    </div>
  )
}

export default VideoPicker
